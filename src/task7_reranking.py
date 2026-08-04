<<<<<<< HEAD
"""Task 7: robust reranking with optional Jina API and local fallbacks."""
=======
"""Local reranking and Reciprocal Rank Fusion utilities."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

from __future__ import annotations

import hashlib
<<<<<<< HEAD
import math
import os
import re
import time

import requests


def _validate(query: str, top_k: int):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")


def _deduplicate(candidates: list[dict]) -> list[dict]:
    seen, output = set(), []
=======
import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", text.lower(), re.UNICODE))


def _unique(candidates: list[dict]) -> list[dict]:
    output, seen = [], set()
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
    for item in candidates:
        content = " ".join(str(item.get("content", "")).split())
        key = item.get("metadata", {}).get("chunk_id") or hashlib.sha256(content.encode()).hexdigest()
        if content and key not in seen:
            seen.add(key)
            output.append({**item, "content": content})
    return output


<<<<<<< HEAD
def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE))


def rerank_heuristic(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    q = _tokens(query)
    scored = []
    for item in _deduplicate(candidates):
        d = _tokens(item["content"])
        overlap = len(q & d) / max(1, len(q))
        original = float(item.get("score", 0.0))
        normalized_original = max(0.0, min(1.0, original if original <= 1 else original / (original + 1)))
        score = 0.7 * overlap + 0.3 * normalized_original
        scored.append({**item, "original_score": original, "rerank_score": score, "score": score})
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    for rank, item in enumerate(scored[:top_k], 1):
        item["rank"] = rank
    return scored[:top_k]


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    key = os.getenv("JINA_API_KEY")
    if not key:
        return rerank_heuristic(query, candidates, top_k)
    unique = _deduplicate(candidates)
    for attempt in range(2):
        try:
            response = requests.post("https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "jina-reranker-v2-base-multilingual", "query": query,
                      "documents": [c["content"] for c in unique], "top_n": min(top_k, len(unique))}, timeout=30)
            response.raise_for_status()
            output = []
            for rank, row in enumerate(response.json().get("results", []), 1):
                base = unique[int(row["index"])]
                score = float(row["relevance_score"])
                output.append({**base, "original_score": float(base.get("score", 0)),
                               "rerank_score": score, "score": score, "rank": rank})
            return output
        except (requests.RequestException, KeyError, ValueError, IndexError):
            if attempt == 0:
                time.sleep(0.25)
    return rerank_heuristic(query, unique, top_k)


def _cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / denom if denom else 0.0


def rerank_mmr(query_embedding: list[float], candidates: list[dict], top_k: int = 5,
               lambda_param: float = 0.7) -> list[dict]:
    if not 0 <= lambda_param <= 1:
        raise ValueError("lambda_param must be in [0, 1]")
    remaining, selected = _deduplicate(candidates), []
    while remaining and len(selected) < top_k:
        def score(item):
            emb = item.get("embedding") or []
            relevance = _cosine(query_embedding, emb)
            redundancy = max((_cosine(emb, x.get("embedding") or []) for x in selected), default=0.0)
            return lambda_param * relevance - (1 - lambda_param) * redundancy
        original_chosen = max(remaining, key=score)
        chosen = {**original_chosen, "original_score": float(original_chosen.get("score", 0)),
                  "rerank_score": score(original_chosen)}
        chosen["score"] = chosen["rerank_score"]
        selected.append(chosen)
        remaining.remove(original_chosen)
    for rank, item in enumerate(selected, 1): item["rank"] = rank
    return selected


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    scores, items = {}, {}
    for ranked in ranked_lists:
        local_seen = set()
        for rank, item in enumerate(ranked, 1):
            content = " ".join(str(item.get("content", "")).split())
            key = item.get("metadata", {}).get("chunk_id") or hashlib.sha256(content.encode()).hexdigest()
            if not content or key in local_seen: continue
            local_seen.add(key); scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            items.setdefault(key, item)
    output = []
    for rank, key in enumerate(sorted(scores, key=scores.get, reverse=True)[:top_k], 1):
        original = float(items[key].get("score", 0))
        output.append({**items[key], "original_score": original, "rrf_score": scores[key],
                       "rerank_score": scores[key], "score": scores[key], "rank": rank})
    return output


def rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "heuristic") -> list[dict]:
    _validate(query, top_k)
    if not candidates: return []
    if method in {"heuristic", "local"}: return rerank_heuristic(query, candidates, top_k)
    if method == "cross_encoder": return rerank_cross_encoder(query, candidates, top_k)
    if method == "rrf": return rerank_heuristic(query, candidates, top_k)
    raise ValueError(f"Unknown rerank method: {method}")
=======
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
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
