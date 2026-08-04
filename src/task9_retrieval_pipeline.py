<<<<<<< HEAD
"""Task 9: resilient hybrid retrieval, fusion, reranking and PageIndex fallback."""
=======
"""Hybrid Ha Long retrieval with A/B-configurable execution."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

from __future__ import annotations

import time

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

<<<<<<< HEAD
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
=======
SCORE_THRESHOLD = .08
DEFAULT_TOP_K = 5

_BILINGUAL_TERMS = {
    "di sản": "world heritage", "công nhận": "declared", "năm nào": "year",
    "diện tích": "area square kilometres km2", "san hô": "coral reefs species",
    "cống đỏ": "Cong Do", "phần trăm": "percent", "bao nhiêu ngày": "days cruise",
    "chèo kayak": "kayak paddle", "thời điểm": "ideal time", "hoàng hôn": "sunset",
    "tháng 9": "September", "tháng 11": "November", "gió mùa": "monsoon season",
    "tháng 6": "June", "tháng 8": "August", "nội bài": "Noi Bai International Airport",
    "thủy phi cơ": "seaplane", "mất bao lâu": "minutes", "kéo dài bao lâu": "minutes duration",
    "trong ngày": "day trip excursion", "hang động": "caves", "sửng sốt": "Sung Sot Cave",
    "mê cung": "Me Cung", "thiên cung": "Thien Cung", "làng chài nổi": "floating villages",
    "ban đêm": "at night", "mực": "squid fishing", "đảo khỉ": "Monkey Island",
    "cát bà": "Cat Ba", "bao xa": "kilometer distance", "gà chọi": "Hon Ga Choi",
    "cao bao nhiêu": "meters above water", "ít đông": "lesser explored", "vịnh nào": "bay",
}


def expand_query(query: str) -> str:
    lowered = query.lower()
    additions = [english for vietnamese, english in _BILINGUAL_TERMS.items() if vietnamese in lowered]
    return f"{query} {' '.join(additions)}".strip()


def retrieve(query: str, top_k: int = DEFAULT_TOP_K, score_threshold: float = SCORE_THRESHOLD,
             use_reranking: bool = True, dense_only: bool = False) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be positive")
    search_query = expand_query(query)
    timings, errors = {}, {}
    started = time.perf_counter()
    try:
        dense = semantic_search(search_query, top_k * 2)
    except Exception as exc:
        dense, errors["semantic"] = [], type(exc).__name__
    timings["semantic_ms"] = round((time.perf_counter() - started) * 1000, 2)
    sparse = []
    if not dense_only:
        started = time.perf_counter()
        try:
            sparse = lexical_search(search_query, top_k * 2)
        except Exception as exc:
            errors["lexical"] = type(exc).__name__
        timings["lexical_ms"] = round((time.perf_counter() - started) * 1000, 2)
    merged = dense[:top_k * 2] if dense_only else rerank_rrf([dense, sparse], top_k * 2)
    final = rerank(search_query, merged, top_k) if use_reranking else merged[:top_k]
    confidence = max([item.get("rerank_score", item.get("score", 0)) for item in final] or [0])
    fallback_triggered = confidence < score_threshold
    if fallback_triggered:
        fallback = pageindex_search(query, top_k)
        if fallback:
            final = fallback
    method = "dense" if dense_only else "hybrid"
    for item in final:
        item["source"] = item.get("source") if item.get("source") == "pageindex" else method
        item.setdefault("metadata", {})["retrieval"] = {"method": method, "latency_ms": timings,
            "errors": errors, "fallback_triggered": fallback_triggered, "confidence": confidence}
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
    return final[:top_k]
