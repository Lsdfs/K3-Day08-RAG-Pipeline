"""Task 9: resilient hybrid retrieval, fusion, reranking and PageIndex fallback."""

from __future__ import annotations

import time

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def _validate(query: str, top_k: int, threshold: float):
    if not isinstance(query, str) or not query.strip(): raise ValueError("query must be non-empty")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0: raise ValueError("top_k must be positive")
    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1: raise ValueError("score_threshold must be in [0,1]")


def retrieve(query: str, top_k: int = DEFAULT_TOP_K, score_threshold: float = SCORE_THRESHOLD,
             use_reranking: bool = True) -> list[dict]:
    _validate(query, top_k, score_threshold)
    query = query.strip(); latency = {}; errors = {}
    started = time.perf_counter()
    try: dense = semantic_search(query, top_k * 2)
    except Exception as exc: dense = []; errors["semantic"] = type(exc).__name__
    latency["semantic_ms"] = round((time.perf_counter() - started) * 1000, 2)
    started = time.perf_counter()
    try: sparse = lexical_search(query, top_k * 2)
    except Exception as exc: sparse = []; errors["lexical"] = type(exc).__name__
    latency["lexical_ms"] = round((time.perf_counter() - started) * 1000, 2)

    started = time.perf_counter()
    merged = rerank_rrf([dense, sparse], top_k * 2)
    for item in merged:
        item["source"] = "hybrid"
    latency["fusion_ms"] = round((time.perf_counter() - started) * 1000, 2)
    started = time.perf_counter()
    final = rerank(query, merged, top_k, method="heuristic") if use_reranking else merged[:top_k]
    latency["rerank_ms"] = round((time.perf_counter() - started) * 1000, 2)

    # Confidence is relevance-based, never the rank-only RRF score.
    semantic_confidence = max((float(x["score"]) for x in dense), default=0.0)
    rerank_confidence = max((float(x.get("rerank_score", 0)) for x in final), default=0.0)
    confidence = max(semantic_confidence, rerank_confidence)
    fallback_triggered = not final or confidence < score_threshold
    if fallback_triggered:
        started = time.perf_counter()
        try: fallback = pageindex_search(query, top_k)
        except Exception as exc: fallback = []; errors["pageindex"] = type(exc).__name__
        latency["pageindex_ms"] = round((time.perf_counter() - started) * 1000, 2)
        if fallback: final = fallback
    for item in final:
        item.setdefault("source", "hybrid")
        item.setdefault("metadata", {})["retrieval"] = {
            "latency_ms": latency, "errors": errors, "confidence": confidence,
            "semantic_candidates": len(dense), "lexical_candidates": len(sparse),
            "fused_candidates": len(merged), "fallback_triggered": fallback_triggered}
    return final[:top_k]
