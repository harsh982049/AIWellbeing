# services/stress_behavior_service.py
# CPU-only inference for behavior-based stress (keyboard/mouse aggregates).
# Exposes:
#   - init_service()
#   - health_check() -> dict
#   - predict_from_row(row: dict, user_id: str) -> dict
#   - train_user_calibrator(user_id: str = "harsh", min_rows: int = 200) -> str (path)
#
# Place this file in your project's services/ folder.
# Project layout (example):
#   <project_root>/
#     artifacts/
#       global_head_regression_behavior.joblib
#       global_head_scaler.joblib
#       global_head_meta.json
#       calibrators/ (optional; created later)
#     labels/
#       stress_30s.csv
#     services/
#       stress_behavior_service.py
#     app.py

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import threading

import numpy as np
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

# ---------- Paths (LOCAL, for VS Code) ----------
# Root is one level up from this file (../)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ART = PROJECT_ROOT / "artifacts"
LAB = PROJECT_ROOT / "labels"
CAL_DIR = ART / "calibrators"

SCALER_PKL = ART / "global_head_scaler.joblib"
META_JSON  = ART / "global_head_meta.json"

# ---------- Internal singletons ----------
_LOCK = threading.Lock()
_PREDICTOR = None  # type: Optional[BehaviorPredictor]
_SMOOTHERS: Dict[str, "TemporalSmoother"] = {}  # per-user smoothing state


# ---------- Utilities ----------
def _load_meta() -> dict:
    if not META_JSON.exists():
        raise FileNotFoundError(f"Missing meta JSON at {META_JSON}")
    with open(META_JSON, "r") as f:
        return json.load(f)

def _autodiscover_head(meta: dict) -> Path:
    """Find the saved global head based on meta naming; fallback to latest."""
    mode = meta.get("mode", "regression")
    # We saved head as: global_head_{mode}_behavior.joblib
    preferred = ART / f"global_head_{mode}_behavior.joblib"
    if preferred.exists():
        return preferred
    # Fallback: any global_head_*.joblib
    cands = sorted(ART.glob("global_head_*.joblib"))
    if not cands:
        raise FileNotFoundError(f"No global_head_*.joblib found in {ART}")
    return cands[-1]

def _extract_features(row: Dict, feature_names) -> np.ndarray:
    """Build a [1, D] feature vector; missing fields default to 0.0."""
    return np.array([float(row.get(name, 0.0) or 0.0) for name in feature_names], dtype=np.float32)[None, :]


# ---------- Smoother / Hysteresis ----------
class TemporalSmoother:
    """Simple EMA + hysteresis to stabilize predictions across windows."""
    def __init__(self, alpha: float = 0.5, on_thresh: float = 0.55, off_thresh: float = 0.45):
        self.alpha = float(alpha)
        self.on_t = float(on_thresh)
        self.off_t = float(off_thresh)
        self._ema = None  # type: Optional[float]
        self._state = 0   # 0=off, 1=on

    def step(self, p: float) -> Tuple[float, int]:
        if self._ema is None:
            self._ema = p
        else:
            self._ema = self.alpha * p + (1 - self.alpha) * self._ema
        if self._state == 0 and self._ema >= self.on_t:
            self._state = 1
        elif self._state == 1 and self._ema <= self.off_t:
            self._state = 0
        return float(self._ema), int(self._state)


# ---------- Per-user Platt calibrator ----------
class PlattCalibrator:
    """Logistic calibration of head scores -> calibrated probabilities."""
    def __init__(self, coef_: Optional[float] = None, intercept_: Optional[float] = None):
        self.coef_ = coef_
        self.intercept_ = intercept_

    def is_fit(self) -> bool:
        return (self.coef_ is not None) and (self.intercept_ is not None)

    def fit(self, scores: np.ndarray, y: np.ndarray):
        # Convert weak labels to binary with 0.5 threshold (simple, effective)
        yb = (y >= 0.5).astype(int)
        lr = LogisticRegression(max_iter=1000, solver="liblinear")
        lr.fit(scores.reshape(-1, 1), yb)
        self.coef_ = float(lr.coef_[0, 0])
        self.intercept_ = float(lr.intercept_[0])

    def predict_proba(self, scores: np.ndarray) -> np.ndarray:
        if not self.is_fit():
            # identity-ish fallback
            return 1.0 / (1.0 + np.exp(-scores))
        z = self.coef_ * scores + self.intercept_
        return 1.0 / (1.0 + np.exp(-z))

    def to_dict(self) -> dict:
        return {"coef_": self.coef_, "intercept_": self.intercept_}

    @classmethod
    def from_file(cls, path: Path) -> "PlattCalibrator":
        if not path.exists():
            return cls()
        with open(path, "r") as f:
            d = json.load(f)
        return cls(d.get("coef_"), d.get("intercept_"))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# ---------- Core predictor ----------
class BehaviorPredictor:
    def __init__(self):
        meta = _load_meta()
        self.meta = meta
        self.feature_names = meta.get("feature_names")
        if not self.feature_names or not isinstance(self.feature_names, list):
            raise ValueError("Missing or invalid 'feature_names' in meta. Re-train Stage B to include them.")

        head_path = _autodiscover_head(meta)
        if not SCALER_PKL.exists():
            raise FileNotFoundError(f"Missing scaler at {SCALER_PKL}")
        self.scaler = joblib.load(SCALER_PKL)
        self.head   = joblib.load(head_path)

        # thresholds from training (used to set hysteresis)
        self.default_thresh = float(meta.get("best_thresh", 0.5))
        self.alpha = 0.5  # EMA strength (can be tuned)

    def _head_prob(self, Xz: np.ndarray) -> float:
        # LogisticRegression: use predict_proba
        if hasattr(self.head, "predict_proba"):
            return float(self.head.predict_proba(Xz)[0, 1])
        # Ridge regression: clip to [0,1]
        return float(np.clip(self.head.predict(Xz)[0], 0.0, 1.0))

    def predict(self, row: Dict, smoother: Optional[TemporalSmoother] = None) -> Dict:
        x = _extract_features(row, self.feature_names)
        xz = self.scaler.transform(x)
        raw_prob = self._head_prob(xz)

        # Optional per-user calibration
        user_id = str(row.get("user_id", "harsh"))
        cal = load_user_calibrator(user_id)
        if cal.is_fit():
            cal_prob = float(cal.predict_proba(np.array([raw_prob]))[0])
        else:
            cal_prob = raw_prob

        # Temporal smoothing + hysteresis
        if smoother is None:
            # default hysteresis around the training threshold
            smoother = TemporalSmoother(
                alpha=self.alpha,
                on_thresh=self.default_thresh + 0.05,
                off_thresh=self.default_thresh - 0.05,
            )
        smoothed, is_on = smoother.step(cal_prob)

        return {
            "raw_prob": raw_prob,
            "calibrated_prob": cal_prob,
            "smoothed_prob": smoothed,
            "is_stressed": bool(is_on),
            "threshold_used": self.default_thresh,
            "has_calibrator": cal.is_fit(),
        }


# ---------- Service lifecycle ----------
def init_service() -> None:
    """Initialize the predictor singleton; call once at app startup."""
    global _PREDICTOR
    with _LOCK:
        if _PREDICTOR is None:
            _PREDICTOR = BehaviorPredictor()

def get_predictor() -> BehaviorPredictor:
    if _PREDICTOR is None:
        init_service()
    return _PREDICTOR


# ---------- Public API for app.py ----------
def health_check() -> Dict:
    """Return a lightweight health snapshot for a /health endpoint."""
    try:
        meta = _load_meta()
        head_path = _autodiscover_head(meta)
        ok = SCALER_PKL.exists() and head_path.exists()
        return {
            "ok": bool(ok),
            "mode": meta.get("mode"),
            "features": meta.get("feature_names"),
            "artifacts_dir": str(ART),
            "labels_dir": str(LAB),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def predict_from_row(row: Dict, user_id: Optional[str] = None) -> Dict:
    """
    row: dict with behavior features (same names as training in meta.feature_names).
         Missing features are defaulted to 0.0 inside the service.
         Optionally include row['user_id'] for calibrator & smoother key.
    user_id: if provided, overrides row['user_id'] for smoother/calibrator lookup.
    """
    pred = get_predictor()
    uid = str(user_id or row.get("user_id") or "harsh")
    with _LOCK:
        smoother = _SMOOTHERS.get(uid)
        if smoother is None:
            smoother = TemporalSmoother(
                alpha=pred.alpha,
                on_thresh=pred.default_thresh + 0.05,
                off_thresh=pred.default_thresh - 0.05,
            )
            _SMOOTHERS[uid] = smoother
    out = pred.predict({**row, "user_id": uid}, smoother)
    return {"user_id": uid, **out, "feature_count": len(pred.feature_names)}


# ---------- Calibrator helpers ----------
def load_user_calibrator(user_id: str) -> PlattCalibrator:
    path = CAL_DIR / f"cal_{user_id}.json"
    return PlattCalibrator.from_file(path)

def train_user_calibrator(user_id: str = "harsh", min_rows: int = 200) -> str:
    """
    Fit a Platt calibrator mapping head scores -> binary labels from face,
    using rows in labels/stress_30s.csv. Saves to artifacts/calibrators/cal_<user>.json.
    """
    init_service()
    pred = get_predictor()

    csv_path = LAB / "stress_30s.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")

    df = pd.read_csv(csv_path)

    # Filter by user and quality if present
    if "user_id" in df.columns:
        df = df[df["user_id"].astype(str) == str(user_id)]
    if {"confident", "coverage"}.issubset(df.columns):
        df = df[(df["confident"] == 1) & (df["coverage"] >= pred.meta.get("conf_coverage_min", 0.30))]
    df = df.dropna(subset=["stress_prob"])
    if len(df) < min_rows:
        raise ValueError(f"Need at least {min_rows} rows for calibration; found {len(df)}.")

    # Build features in the same order used at training time
    X = df[pred.feature_names].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(np.float32).values
    Xz = pred.scaler.transform(X)

    # Head scores on these rows
    if hasattr(pred.head, "predict_proba"):
        scores = pred.head.predict_proba(Xz)[:, 1]
    else:
        scores = np.clip(pred.head.predict(Xz), 0, 1)

    y = df["stress_prob"].values.astype(np.float32)

    cal = PlattCalibrator()
    cal.fit(scores, y)

    CAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CAL_DIR / f"cal_{user_id}.json"
    cal.save(out_path)
    return str(out_path)
