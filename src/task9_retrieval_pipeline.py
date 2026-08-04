"""Task 9 — Retrieval Pipeline (semantic + lexical → RRF → rerank → fallback)."""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf, rerank
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.20  # Below original cosine score -> fallback to PageIndex


def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.3,
             use_reranking: bool = True) -> list[dict]:
    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    # Merge with RRF
    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)

    # Rerank with cross_encoder (uses existing scores)
    if use_reranking:
        merged = rerank(query, merged, top_k=top_k, method="cross_encoder")

    # Fallback check: use original dense score, not RRF score
    top_dense_score = dense_results[0]["score"] if dense_results else 0.0
    if top_dense_score < score_threshold:
        fallback = pageindex_search(query, top_k=top_k)
        for r in fallback:
            r["source"] = "pageindex"
        return fallback

    for r in merged:
        r["source"] = "hybrid"

    return merged[:top_k]
