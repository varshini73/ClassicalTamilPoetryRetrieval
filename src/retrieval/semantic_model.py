"""Lazy CPU-only multilingual semantic embeddings for optional retrieval."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
CACHE_ENV = "CLASSICAL_TAMIL_EMBEDDING_CACHE_DIR"
DISABLE_ENV = "CLASSICAL_TAMIL_SEMANTIC_DISABLE"
PROGRESS_ENV = "CLASSICAL_TAMIL_EMBEDDING_PROGRESS"
BATCH_SIZE = 16


class SemanticModelUnavailable(RuntimeError):
    """Raised when optional local semantic inference cannot be used."""


def embedding_cache_dir() -> Path:
    """Keep generated vectors outside the repository and source control."""
    configured = os.getenv(CACHE_ENV)
    return Path(configured) if configured else Path.home() / ".cache" / "classical_tamil_poetry_retrieval"


@lru_cache(maxsize=1)
def get_semantic_model():
    """Load tokenizer/model once, on CPU, only when semantic search is requested."""
    if os.getenv(DISABLE_ENV) == "1":
        raise SemanticModelUnavailable(f"{DISABLE_ENV}=1")
    try:
        from transformers import AutoModel, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
        model = AutoModel.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
        model.eval()
        return tokenizer, model
    except Exception as exc:
        raise SemanticModelUnavailable(f"{type(exc).__name__}: {exc}") from exc


def encode(texts: list[str], prefix: str) -> np.ndarray:
    """Mean-pool e5 embeddings and L2-normalize them for cosine similarity."""
    import torch

    tokenizer, model = get_semantic_model()
    vectors: list[np.ndarray] = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_number, start in enumerate(range(0, len(texts), BATCH_SIZE), 1):
        batch = [prefix + text for text in texts[start:start + BATCH_SIZE]]
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            hidden = model(**inputs).last_hidden_state
        mask = inputs["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
        pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        vectors.append(torch.nn.functional.normalize(pooled, p=2, dim=1).cpu().numpy())
        if os.getenv(PROGRESS_ENV) == "1" and (batch_number == 1 or batch_number % 8 == 0 or batch_number == total_batches):
            print(f"embedding batch {batch_number}/{total_batches}", file=sys.stderr, flush=True)
    return np.vstack(vectors).astype(np.float32)


def corpus_cache_key(documents: list[str], prefix: str = "passage: ") -> str:
    digest = hashlib.sha256()
    digest.update(f"{MODEL_NAME}@{MODEL_REVISION}|{prefix}".encode())
    for document in documents:
        digest.update(document.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()

def _legacy_corpus_cache_key(documents: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update(f"{MODEL_NAME}@{MODEL_REVISION}".encode())
    for document in documents:
        digest.update(document.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def corpus_embeddings(documents: list[str]) -> np.ndarray:
    """Reuse a corpus matrix until either corpus documents or model revision changes."""
    cache_dir = embedding_cache_dir()
    cache_file = cache_dir / f"semantic-corpus-{corpus_cache_key(documents)}.npy"
    metadata_file = cache_file.with_suffix(".meta.json")
    if cache_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            cached = np.load(cache_file, allow_pickle=False)
            if metadata == {"prefix": "passage: ", "records": len(documents)} and cached.shape[0] == len(documents):
                return cached
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    legacy_cache = cache_dir / f"semantic-corpus-{_legacy_corpus_cache_key(documents)}.npy"
    if legacy_cache.exists():
        raise SemanticModelUnavailable("cached corpus embeddings do not record the required 'passage: ' prefix; remove that cache file manually before regenerating")
    vectors = encode(documents, "passage: ")
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary_file = cache_file.with_suffix(".tmp.npy")
    np.save(temporary_file, vectors, allow_pickle=False)
    temporary_file.replace(cache_file)
    temporary_metadata = metadata_file.with_suffix(".tmp.json")
    temporary_metadata.write_text(json.dumps({"prefix": "passage: ", "records": len(documents)}) + "\n", encoding="utf-8")
    temporary_metadata.replace(metadata_file)
    return vectors
