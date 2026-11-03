# -------------------------------
# liveness.py - face detection + anti-spoofing (Real / Fake)
# Same model + pre-processing as your fake_real_face.py, but usable as a module
# (the original file is a camera loop, so it cannot be imported).
# -------------------------------
import os
import shutil
import tempfile
import threading
from collections import deque

import cv2
import numpy as np

import config

_BASE = os.path.dirname(os.path.abspath(__file__))
_lock = threading.Lock()
_model = None
_model_error = None
_detector = cv2.CascadeClassifier(os.path.join(_BASE, 'haarcascade_frontalface_default.xml'))

LABELS = ['Real', 'Fake']


def _load_model():
    """Try several loaders so it works with old and new TensorFlow / Keras versions."""
    path = os.path.join(_BASE, 'liveness.model')
    errors = []
    loaders = []
    try:
        from keras.models import load_model as km
        loaders.append(km)
    except Exception as e:
        errors.append(f'keras import: {e}')
    try:
        from tensorflow.keras.models import load_model as tm
        loaders.append(tm)
    except Exception as e:
        errors.append(f'tf.keras import: {e}')
    for loader in loaders:
        try:
            return loader(path, compile=False), None
        except Exception as e:
            errors.append(str(e)[:150])
        # Keras 3 refuses unknown extensions: retry from a temporary copy named .h5
        try:
            tmp = os.path.join(tempfile.gettempdir(), 'liveness_copy.h5')
            shutil.copyfile(path, tmp)
            return loader(tmp, compile=False), None
        except Exception as e:
            errors.append(str(e)[:150])
    return None, ' | '.join(errors) or 'unknown error'


def _get_model():
    global _model, _model_error
    if _model is None and _model_error is None:
        with _lock:
            if _model is None and _model_error is None:
                _model, _model_error = _load_model()
    return _model


def model_status():
    _get_model()
    return (_model is not None), _model_error


def detect_faces(frame_bgr):
    """
    Robust Haar detection (webcam frames, any lighting). Tries a few settings and returns
    a list of (x, y, w, h) sorted largest first.
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    attempts = [(gray, 1.1, 6, 60), (eq, 1.1, 6, 60), (gray, 1.1, 4, 50), (eq, 1.1, 4, 50)]
    for img, sf, mn, ms in attempts:
        faces = _detector.detectMultiScale(img, scaleFactor=sf, minNeighbors=mn, minSize=(ms, ms))
        if len(faces):
            faces = sorted([tuple(int(v) for v in f) for f in faces], key=lambda b: b[2] * b[3], reverse=True)
            return faces
    return []


class LivenessTracker:
    """Keeps a rolling average of the last 15 predictions for one interview."""

    def __init__(self):
        self.history = deque(maxlen=15)
        self.fake_streak = 0

    def check(self, frame_bgr):
        """Returns dict(face_count, label, confidence, is_fake, box)"""
        faces = detect_faces(frame_bgr)
        out = {'face_count': 0, 'label': 'No face', 'confidence': 0.0, 'is_fake': False, 'box': None}
        if not faces:
            self.fake_streak = 0
            return out

        x, y, w, h = faces[0]                        # largest face = the candidate
        # a 2nd face only counts if it is reasonably large (ignores small false detections)
        out['face_count'] = 1 + sum(1 for f in faces[1:] if f[2] >= 0.6 * w)
        out['box'] = [x, y, w, h]

        model = _get_model()
        if model is None:
            out['label'] = 'Model unavailable'
            return out

        face = cv2.resize(frame_bgr[max(y, 0):y + h, max(x, 0):x + w], (32, 32)).astype('float32') / 255.0
        face = np.expand_dims(face, axis=0)
        preds = model.predict(face, verbose=0)[0]
        self.history.append(preds)
        avg = np.mean(self.history, axis=0)
        conf = float(np.max(avg))
        out['confidence'] = conf
        if conf < config.LIVENESS_CONF:
            out['label'] = 'Checking...'
            return out
        idx = int(np.argmax(avg))
        out['label'] = LABELS[idx]
        out['is_fake'] = (LABELS[idx] == 'Fake')
        self.fake_streak = self.fake_streak + 1 if out['is_fake'] else 0
        return out
