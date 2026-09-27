from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def _prefix(kind: str) -> str:
    # E5 models need "query: " / "passage: " prefixes for best retrieval.
    return f"{kind}: " if "e5" in settings.embedding_model.lower() else ""


def embed_passages(texts: list[str]) -> np.ndarray:
    p = _prefix("passage")
    return _model().encode([p + t for t in texts], normalize_embeddings=True, batch_size=32)


def embed_query(query: str) -> np.ndarray:
    return _model().encode(_prefix("query") + query, normalize_embeddings=True)
