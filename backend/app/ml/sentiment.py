import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from loguru import logger
from typing import Optional
import os
from app.core.config import settings


# ─── Singleton Loader ────────────────────────────────────

_tokenizer: Optional[DistilBertTokenizer] = None
_model: Optional[DistilBertForSequenceClassification] = None
_device: Optional[torch.device] = None


def load_sentiment_model():
    global _tokenizer, _model, _device

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Loading sentiment model on device: {_device}")

    model_path = settings.SENTIMENT_MODEL_PATH

    # Load from local saved_models/ if exists, else from HuggingFace Hub
    if os.path.exists(model_path):
        logger.info(f"Loading sentiment model from local path: {model_path}")
        _tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        _model = DistilBertForSequenceClassification.from_pretrained(model_path)
    else:
        logger.info("Local model not found — loading base distilbert-base-uncased")
        _tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
        _model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels=2
        )
    _model.to(_device)
    _model.eval()
    logger.info("Sentiment model loaded and ready")


def get_model():
    if _model is None or _tokenizer is None:
        load_sentiment_model()
    return _tokenizer, _model, _device


# ─── Single Inference ────────────────────────────────────

def predict_sentiment(text: str) -> dict:
    tokenizer, model, device = get_model()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)
        predicted_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][predicted_class].item()

    label = "positive" if predicted_class == 1 else "negative"

    return {
        "label": label,
        "confidence": round(confidence, 4)
    }


# ─── Batch Inference ─────────────────────────────────────

def predict_sentiment_batch(texts: list[str]) -> list[dict]:
    tokenizer, model, device = get_model()

    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)
        predicted_classes = torch.argmax(probs, dim=1).tolist()
        confidences = probs.max(dim=1).values.tolist()

    results = []
    for cls, conf in zip(predicted_classes, confidences):
        results.append({
            "label": "positive" if cls == 1 else "negative",
            "confidence": round(conf, 4)
        })

    logger.info(f"Batch inference complete — {len(texts)} texts processed")
    return results


# ─── Sentiment Score (0-1 float) ─────────────────────────

def get_sentiment_score(text: str) -> float:
    """
    Returns a float 0-1 representing positivity.
    Used by recommender for sentiment boost logic.
    """
    result = predict_sentiment(text)
    if result["label"] == "positive":
        return result["confidence"]
    else:
        return 1.0 - result["confidence"]