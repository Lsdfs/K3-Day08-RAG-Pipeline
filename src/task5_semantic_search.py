"""Dense-style semantic search over the persistent local Ha Long index."""

from __future__ import annotations

from .task4_chunking_indexing import embed_text, load_index


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    vector = embed_text(query)
    output = []
    for row in load_index():
        content = row.get("content", "").strip()
        if not content:
            continue
        score = sum(a * b for a, b in zip(vector, row["embedding"]))
        output.append({"content": content, "score": max(0.0, min(1.0, score)),
                       "metadata": row["metadata"], "source": "semantic"})
    return sorted(output, key=lambda item: item["score"], reverse=True)[:top_k]
