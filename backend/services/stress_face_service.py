# services/stress_face_service.py
# Runtime: Python 3.13 (no TensorFlow required)
import os
import time
import base64
from typing import Tuple, Optional

import numpy as np
import cv2
import onnxruntime as ort
from flask import jsonify, Request

# ----------------------------
# Config
# ----------------------------
# Default: backend/export/emotion.onnx
_DEFAULT_MODEL = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "export", "emotion.onnx")
)
EMOTION_ONNX_PATH = os.getenv("EMOTION_ONNX_PATH", _DEFAULT_MODEL)

# Keep the same mapping you used in face.py
EMOTION_LABELS = [
    "Anxiety", "Anxiety", "Anxiety", "No Anxiety", "Anxiety", "Anxiety", "No Anxiety"
]

# ----------------------------
# Model & detector (loaded once)
# ----------------------------
_session: Optional[ort.InferenceSession] = None
_in_name: Optional[str] = None
_out_name: Optional[str] = None
_detector: Optional[cv2.CascadeClassifier] = None

def _load_once():
    """Load ONNX model and Haar face detector exactly once."""
    global _session, _in_name, _out_name, _detector

    if _session is None:
        providers = ["CPUExecutionProvider"]  # Optional: add 'DmlExecutionProvider' if installed
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _session = ort.InferenceSession(EMOTION_ONNX_PATH, sess_options=so, providers=providers)
        _in_name = _session.get_inputs()[0].name
        _out_name = _session.get_outputs()[0].name
        print(f"✅ ONNX loaded: {_in_name} -> {_out_name} from {EMOTION_ONNX_PATH}")

    if _detector is None:
        _detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if _detector.empty():
            raise RuntimeError("Failed to load Haar cascade for face detection.")

# Call at import
try:
    _load_once()
except Exception as e:
    print(f"❌ ONNX/Detector init failed: {e}")

# ----------------------------
# Helpers
# ----------------------------
def _read_image_from_request(req: Request) -> Optional[np.ndarray]:
    """
    Accepts:
      - multipart/form-data with field 'image' (binary file)
      - JSON {"image": "data:image/jpeg;base64,...."}  OR  {"image": "<base64>"}
    Returns BGR ndarray or None.
    """
    if req.files and "image" in req.files:
        data = np.frombuffer(req.files["image"].read(), np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    j = req.get_json(silent=True) or {}
    v = j.get("image")
    if isinstance(v, str) and v:
        if v.startswith("data:"):
            v = v.split(",", 1)[-1]
        try:
            buf = base64.b64decode(v, validate=True)
            data = np.frombuffer(buf, np.uint8)
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            return None
    return None

def _preprocess_face(bgr: np.ndarray, bbox) -> np.ndarray:
    x, y, w, h = map(int, bbox)
    gray = cv2.cvtColor(bgr[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    face = cv2.resize(gray, (48, 48))
    face = face.astype(np.float32) / 255.0
    face = face[np.newaxis, :, :, np.newaxis]  # (1,48,48,1) NHWC
    return face

# ----------------------------
# Public API (called from app.py)
# ----------------------------
def face_health():
    ok = (
        _session is not None
        and _in_name is not None
        and _out_name is not None
        and _detector is not None
        and not _detector.empty()
        and os.path.exists(EMOTION_ONNX_PATH)
    )
    status = 200 if ok else 500
    return jsonify({"ok": ok, "model_path": EMOTION_ONNX_PATH}), status

def face_predict(req: Request):
    if _session is None:
        return jsonify({"error": "Model not loaded. Check EMOTION_ONNX_PATH."}), 500

    bgr = _read_image_from_request(req)
    if bgr is None:
        return jsonify({"error": "No/invalid image"}), 400

    t0 = time.time()

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = _detector.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    if len(faces) == 0:
        return jsonify({
            "faces": 0,
            "elapsed_ms": int((time.time() - t0) * 1000)
        }), 200

    # Pick the largest face; you can loop through all if needed
    faces = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)
    face_tensor = _preprocess_face(bgr, faces[0])

    # ONNX inference
    outputs = _session.run([_out_name], {_in_name: face_tensor})[0]  # (1,7)
    probs = outputs[0].astype(float).tolist()
    idx = int(np.argmax(probs))
    label = EMOTION_LABELS[idx]
    conf = float(probs[idx])

    x, y, w, h = map(int, faces[0])
    return jsonify({
        "faces": len(faces),
        "bbox": [x, y, w, h],
        "label": label,
        "confidence": conf,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }), 200
