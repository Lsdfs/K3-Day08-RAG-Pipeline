"""Local reranking and Reciprocal Rank Fusion utilities."""

from __future__ import annotations

import hashlib
import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", text.lower(), re.UNICODE))


def _unique(candidates: list[dict]) -> list[dict]:
    output, seen = [], set()
    for item in candidates:
        content = " ".join(str(item.get("content", "")).split())
        key = item.get("metadata", {}).get("chunk_id") or hashlib.sha256(content.encode()).hexdigest()
        if content and key not in seen:
            seen.add(key)
            output.append({**item, "content": content})
    return output


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Free local relevance heuristic used as a deterministic reranker."""
    return rerank(query, candidates, top_k)


def rerank_mmr(query_embedding: list[float], candidates: list[dict], top_k: int = 5,
               lambda_param: float = .7) -> list[dict]:
    # Candidates without embeddings still retain relevance ordering.
    selected = sorted(_unique(candidates), key=lambda item: item.get("score", 0), reverse=True)[:top_k]
    for rank, item in enumerate(selected, 1):
        item.update(original_score=item.get("score", 0), rerank_score=item.get("score", 0), rank=rank)
    return selected


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    scores, rows = {}, {}
    for ranked in ranked_lists:
        for rank, item in enumerate(_unique(ranked), 1):
            key = item.get("metadata", {}).get("chunk_id") or hashlib.sha256(item["content"].encode()).hexdigest()
            scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
            rows.setdefault(key, item)
    output = []
    for rank, key in enumerate(sorted(scores, key=scores.get, reverse=True)[:top_k], 1):
        output.append({**rows[key], "original_score": rows[key].get("score", 0),
                       "rrf_score": scores[key], "score": scores[key], "rank": rank})
    return output


def rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "local") -> list[dict]:
    if not query.strip() or top_k <= 0:
        raise ValueError("query and top_k must be valid")
    query_tokens = _tokens(query)
    scored = []
    for item in _unique(candidates):
        overlap = len(query_tokens & _tokens(item["content"])) / max(1, len(query_tokens))
        original = float(item.get("score", 0))
        normalized = original if 0 <= original <= 1 else original / (1 + original)
        rerank_score = .75 * overlap + .25 * max(0, normalized)
        scored.append({**item, "original_score": original, "rerank_score": rerank_score, "score": rerank_score})
    scored.sort(key=lambda item: item["rerank_score"], reverse=True)
    for rank, item in enumerate(scored[:top_k], 1):
        item["rank"] = rank
    return scored[:top_k]
