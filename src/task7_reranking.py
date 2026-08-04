"""Task 7 — Reranking (Cross-Encoder passthrough, MMR, RRF)."""


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank using the original scores (no external API). Candidates already sorted."""
    return sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]


def rerank_mmr(query_embedding: list[float], candidates: list[dict], top_k: int = 5,
               lambda_param: float = 0.7) -> list[dict]:
    """Maximal Marginal Relevance — diversity-aware reranking."""
    if not candidates:
        return []

    remaining = list(candidates)
    selected = []

    for _ in range(min(top_k, len(candidates))):
        best_idx = 0
        best_score = float("-inf")
        for i, c in enumerate(remaining):
            sim_query = c.get("score", 0.0)
            max_sim_selected = 0.0
            if selected:
                emb_c = c.get("embedding", [])
                for s in selected:
                    emb_s = s.get("embedding", [])
                    if emb_c and emb_s:
                        dot = sum(x * y for x, y in zip(emb_c, emb_s))
                        norm_c = sum(x * x for x in emb_c) ** 0.5
                        norm_s = sum(x * x for x in emb_s) ** 0.5
                        sim = dot / (norm_c * norm_s) if norm_c > 0 and norm_s > 0 else 0
                        max_sim_selected = max(max_sim_selected, sim)
            mmr = lambda_param * sim_query - (1 - lambda_param) * max_sim_selected
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        selected.append(remaining.pop(best_idx))

    return selected


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion — merge multiple ranked lists."""
    scores = {}
    docs = {}
    for lst in ranked_lists:
        for rank, doc in enumerate(lst):
            key = doc.get("content", "")[:100]
            rrf = 1.0 / (k + rank + 1)
            scores[key] = scores.get(key, 0.0) + rrf
            docs[key] = doc

    merged = [(scores[k], docs[k]) for k in docs]
    merged.sort(key=lambda x: x[0], reverse=True)

    result = []
    for score, doc in merged[:top_k]:
        result.append({**doc, "score": score})
    return result


def rerank(query, candidates, top_k=5, method="rrf", query_embedding=None, ranked_lists=None):
    """Unified reranking interface."""
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr" and query_embedding is not None:
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf" and ranked_lists is not None:
        return rerank_rrf(ranked_lists, top_k)
    return candidates[:top_k]
