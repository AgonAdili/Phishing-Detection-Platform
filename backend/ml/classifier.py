from __future__ import annotations

import json
import os
from typing import Dict

from ml.indicators import detect_indicators, heuristic_score

HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(HERE, "model.joblib")
METRICS_PATH = os.path.join(HERE, "metrics.json")

_model = None
_metrics: Dict = {}
_backend = "heuristic"


def _try_load() -> None:
    global _model, _metrics, _backend
    if _model is not None:
        return
    try:
        import joblib
        if os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
            _backend = "ml"
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH) as fh:
                _metrics = json.load(fh)
    except Exception:
        _model = None
        _backend = "heuristic"


def is_ready() -> bool:
    _try_load()
    return _backend == "ml"


def get_metrics() -> Dict:
    _try_load()
    if _metrics:
        return {**_metrics, "backend": _backend}
    return {
        "model": "Heuristic rule engine (fallback)",
        "backend": _backend,
        "note": "Trained model not found. Run `python -m ml.train` to enable ML.",
    }


def _risk_band(prob: float) -> str:
    if prob >= 0.7:
        return "high"
    if prob >= 0.4:
        return "medium"
    return "low"


def analyze(subject: str, body: str) -> Dict:
    _try_load()
    text = f"{subject}\n{body}".strip()

    indicators = detect_indicators(text)

    if _backend == "ml" and _model is not None:
        prob = float(_model.predict_proba([text])[0][1])
        source = "ml"
    else:
        prob = heuristic_score(text)
        source = "heuristic"

    return {
        "phishing_probability": round(prob, 4),
        "risk_band": _risk_band(prob),
        "verdict": "phishing" if prob >= 0.5 else "legitimate",
        "backend": source,
        "indicators": indicators,
        "indicator_count": len(indicators),
    }
