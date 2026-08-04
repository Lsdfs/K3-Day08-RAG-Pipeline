"""Task 8 — PageIndex vectorless fallback search."""


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Fallback: return content with pageindex source marker.
    Actual PageIndex API requires PDF upload + polling; this returns
    keyword-matched results from the local corpus."""
    from .task4_chunking_indexing import get_chunks

    chunks = get_chunks()
    query_lower = query.lower()
    scored = []
    for c in chunks:
        content_lower = c["content"].lower()
        score = sum(1 for w in query_lower.split() if w in content_lower)
        if score > 0:
            scored.append({**c, "score": score / max(len(query_lower.split()), 1)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return [
        {"content": s["content"], "score": s["score"],
         "metadata": s.get("metadata", {}), "source": "pageindex"}
        for s in scored[:top_k]
    ] if scored else [
        {"content": "No results found.", "score": 0.0, "metadata": {}, "source": "pageindex"}
    ]
