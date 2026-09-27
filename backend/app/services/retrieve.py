"""Hybrid retrieval: vector + keyword -> RRF fusion -> optional cross-encoder rerank."""
from ..config import settings
from .embeddings import embed_query
from .fusion import rrf
from .store import search_keyword, search_vector
from .text_utils import tokenize


def retrieve(query: str, top_n: int, user_id: int, doc_ids: list[int] | None = None) -> list[dict]:
    k = settings.retrieve_candidates
    vec = search_vector(embed_query(query), k, user_id, doc_ids)
    kw = search_keyword(tokenize(query), k, user_id, doc_ids)

    by_id = {r["id"]: r for r in kw + vec}  # vector rows win (cosine score)
    order = rrf([[r["id"] for r in vec], [r["id"] for r in kw]])
    candidates = [by_id[i] for i in order[:k]]

    if settings.use_reranker:
        from .reranker import rerank

        candidates = rerank(query, candidates)
    return candidates[:top_n]
