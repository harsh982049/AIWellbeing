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

def _nz_count(vec: np.ndarray) -> int:
    return int(np.count_nonzero(np.asarray(vec)))


# ---------- Activity-aware EMA + hysteresis ----------
class TemporalSmoother:
    """
    Activity-aware EMA + hysteresis.

    - alpha_active: normal smoothing when there's activity
    - alpha_idle:   much faster convergence when idle (decay quickly)
    - after 'idle_reset_k' consecutive idle windows, reset EMA to baseline
    """
    def __init__(
        self,
        alpha_active: float = 0.35,
        alpha_idle: float   = 0.85,
        on_thresh: float    = 0.60,
        off_thresh: float   = 0.40,
        idle_reset_k: int   = 2,
        baseline: float     = 0.20,
    ):
        self.alpha_active = float(alpha_active)
        self.alpha_idle   = float(alpha_idle)
        self.on_t   = float(on_thresh)
        self.off_t  = float(off_thresh)
        self.idle_reset_k = int(idle_reset_k)
        self.baseline = float(baseline)

        self._ema: float | None = None
        self._state = 0
        self._idle_count = 0

    def step(self, p: float, is_idle: bool) -> tuple[float, int]:
        # choose alpha based on activity
        a = self.alpha_idle if is_idle else self.alpha_active

        if self._ema is None:
            self._ema = p
        else:
            self._ema = a * p + (1 - a) * self._ema

        # if idle repeatedly, snap back toward baseline quickly
        if is_idle:
            self._idle_count += 1
            if self._idle_count >= self.idle_reset_k:
                # hard reset EMA to baseline, and force calm
                self._ema = self.baseline
                self._state = 0
        else:
            self._idle_count = 0

        # hysteresis on the EMA
        if self._state == 0 and self._ema >= self.on_t:
            self._state = 1
        elif self._state == 1 and self._ema <= self.off_t:
            self._state = 0

        return float(self._ema), int(self._state)

    def force_off(self) -> None:
        self._state = 0


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
        # Only meaningful after fit(); callers should check is_fit()
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
def _is_idle(row: Dict, eps: float = 1e-6) -> bool:
    """Heuristic: absolutely no keyboard/mouse activity in this 30s window."""
    ks_events = float(row.get("ks_event_count", 0.0) or 0.0)
    kd = float(row.get("ks_keydowns", 0.0) or 0.0)
    ku = float(row.get("ks_keyups", 0.0) or 0.0)
    mm = float(row.get("mouse_move_count", 0.0) or 0.0)
    mc = float(row.get("mouse_click_count", 0.0) or 0.0)
    ms = float(row.get("mouse_scroll_count", 0.0) or 0.0)
    act = float(row.get("active_seconds_fraction", 0.0) or 0.0)
    return (ks_events <= eps and kd <= eps and ku <= eps and
            mm <= eps and mc <= eps and ms <= eps and
            act <= 0.02)  # ~ < 1 sec activity over 30s


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

        # Smoother defaults (less sticky); surfaced here for clarity
        self.alpha = 0.35
        self.on_delta = 0.10
        self.off_delta = 0.10

        # Idle clamp configuration
        self.idle_clamp = float(meta.get("idle_clamp_prob", 0.10))  # probability to use when fully idle

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
            has_cal = True
        else:
            cal_prob = raw_prob
            has_cal = False

        # Idle guard: if truly no activity, clamp low and force smoother off
        idle = _is_idle(row)
        if idle:
            cal_prob = min(cal_prob, self.idle_clamp)

        # Temporal smoothing + hysteresis (activity-aware)
        if smoother is None:
            smoother = TemporalSmoother(
                alpha_active=self.alpha,                             # normal smoothing
                alpha_idle=0.85,                                     # fast decay when idle
                on_thresh=self.default_thresh + self.on_delta,       # e.g., 0.60
                off_thresh=self.default_thresh - self.off_delta,     # e.g., 0.40
                idle_reset_k=2,                                      # consecutive idle windows to snap back
                baseline=0.20,                                       # calm baseline
            )
        smoothed, is_on = smoother.step(cal_prob, is_idle=idle)

        # If we clamped as idle, ensure label is Calm immediately
        if idle:
            smoother.force_off()
            is_on = 0
            # Keep smoothed as is (EMA continues), but decision is calm.

        return {
            "raw_prob": raw_prob,
            "calibrated_prob": cal_prob,
            "smoothed_prob": smoothed,
            "is_stressed": bool(is_on),
            "threshold_used": self.default_thresh,
            "has_calibrator": has_cal,
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
        # Show the effective smoother parameters we'll use
        alpha = 0.35
        on_t = float(meta.get("best_thresh", 0.5)) + 0.10
        off_t = float(meta.get("best_thresh", 0.5)) - 0.10
        return {
            "ok": bool(SCALER_PKL.exists() and head_path.exists()),
            "mode": meta.get("mode"),
            "features": meta.get("feature_names"),
            "artifacts_dir": str(ART),
            "labels_dir": str(LAB),
            "smoother": {"alpha": alpha, "on": on_t, "off": off_t},
            "idle_clamp_prob": float(meta.get("idle_clamp_prob", 0.10)),
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
            # IMPORTANT: use alpha_active / alpha_idle (no 'alpha' kw)
            smoother = TemporalSmoother(
                alpha_active=pred.alpha,
                alpha_idle=0.85,
                on_thresh=pred.default_thresh + pred.on_delta,
                off_thresh=pred.default_thresh - pred.off_delta,
                idle_reset_k=2,
                baseline=0.20,
            )
            _SMOOTHERS[uid] = smoother

    # Build x in the trained order so we can report non-zero count
    x = _extract_features(row, pred.feature_names)
    out = pred.predict({**row, "user_id": uid}, smoother)

    # Small debug summary so you can verify backend sees activity (or idle)
    activity_summary = {
        "ks_event_count": float(row.get("ks_event_count", 0.0) or 0.0),
        "ks_keydowns": float(row.get("ks_keydowns", 0.0) or 0.0),
        "ks_keyups": float(row.get("ks_keyups", 0.0) or 0.0),
        "mouse_move_count": float(row.get("mouse_move_count", 0.0) or 0.0),
        "mouse_click_count": float(row.get("mouse_click_count", 0.0) or 0.0),
        "mouse_scroll_count": float(row.get("mouse_scroll_count", 0.0) or 0.0),
        "active_seconds_fraction": float(row.get("active_seconds_fraction", 0.0) or 0.0),
    }

    return {
        "user_id": uid,
        **out,
        "feature_count": len(pred.feature_names),
        "nonzero_features": _nz_count(x),
        "activity": activity_summary,
    }

# ---- Return the latest 30s feature row from labels/stress_30s.csv ----
def latest_window_features(user_id: str | None = None) -> dict:
    """
    Loads the last row from labels/stress_30s.csv and returns ONLY the
    feature fields used at training time (meta.feature_names), coerced to float.
    Missing values => 0.0.
    """
    init_service()
    pred = get_predictor()

    csv_path = LAB / "stress_30s.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No CSV found at {csv_path}")

    # read only tail for speed
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        raise ValueError("CSV is empty.")

    last = df.iloc[-1].to_dict()

    # pick only the trained features
    out = {}
    for name in pred.feature_names:
        try:
            out[name] = float(last.get(name, 0.0) or 0.0)
        except Exception:
            out[name] = 0.0

    # prefer provided user_id, else from CSV (if present), else "harsh"
    uid = (user_id or last.get("user_id") or "harsh")
    out["user_id"] = str(uid)
    return out


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
