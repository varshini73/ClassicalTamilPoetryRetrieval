"""Cached CPU inference for the project's pretrained emotion stage."""
from __future__ import annotations

import os
from functools import lru_cache

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
MODEL_LABELS = ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
_LOAD_ERROR = ""

@lru_cache(maxsize=1)
def get_emotion_pipeline():
    """Load once per Python process; Transformers caches weights outside the repo."""
    global _LOAD_ERROR
    if _LOAD_ERROR:
        raise RuntimeError(_LOAD_ERROR)
    try:
        from transformers import pipeline
        return pipeline("text-classification", model=MODEL_NAME, tokenizer=MODEL_NAME, top_k=None, device=-1)
    except Exception as exc:
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        raise

def format_pretrained_output(output):
    """Normalize Transformer pipeline output into a stable API shape."""
    candidates = output[0] if output and isinstance(output[0], list) else output
    scores = {str(item["label"]).casefold(): float(item["score"]) for item in candidates}
    ordered = sorted(scores, key=lambda label: (-scores[label], label))
    primary = ordered[0] if ordered else "neutral"
    return {
        "method": "pretrained Hugging Face Transformers model",
        "model_name": MODEL_NAME,
        "primary": primary,
        "secondary": ordered[1:3],
        "confidence": scores.get(primary, 0.0),
        "confidence_label": "model probability score",
        "alternative_scores": {label: scores.get(label, 0.0) for label in MODEL_LABELS},
        "evidence": {"model_labels": list(MODEL_LABELS)},
        "fallback_reason": "",
    }

def detect_pretrained_emotions(sentence, fallback):
    """Run pretrained inference or call the supplied explicit rule fallback."""
    if os.getenv("CLASSICAL_TAMIL_EMOTION_FORCE_FALLBACK") == "1":
        result = fallback(sentence)
        result.update({"method":"rule-based fallback (pretrained model deliberately disabled)", "model_name":MODEL_NAME, "fallback_reason":"CLASSICAL_TAMIL_EMOTION_FORCE_FALLBACK=1"})
        return result
    try:
        return format_pretrained_output(get_emotion_pipeline()(sentence, truncation=True))
    except Exception as exc:  # offline, missing package, or unavailable model
        result = fallback(sentence)
        result.update({"method":"rule-based fallback (pretrained model unavailable)", "model_name":MODEL_NAME, "fallback_reason":f"{type(exc).__name__}: {exc}"})
        return result
