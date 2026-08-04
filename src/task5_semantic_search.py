<<<<<<< HEAD
"""Task 5: cosine semantic search over the Task 4 Chroma collection."""

from __future__ import annotations

import logging

LOG = logging.getLogger(__name__)


def _validate(query: str, top_k: int) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    return query.strip()


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    query = _validate(query, top_k)
    from .task4_chunking_indexing import get_collection, get_embedding_model
    try:
        collection = get_collection()
    except RuntimeError as exc:
        LOG.warning("semantic search unavailable: %s", exc)
        return []
    count = collection.count()
    if not count:
        return []
    encoded = get_embedding_model().encode(query, normalize_embeddings=True)
    vector = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)
    raw = collection.query(query_embeddings=[vector], n_results=min(top_k, count),
                           include=["documents", "metadatas", "distances"])
    output = []
    ids = (raw.get("ids") or [[]])[0]
    for chunk_id, content, metadata, distance in zip(ids, raw["documents"][0], raw["metadatas"][0], raw["distances"][0]):
        if not str(content).strip():
            continue
        similarity = max(-1.0, min(1.0, 1.0 - float(distance)))
        output.append({"content": content, "score": similarity,
                       "metadata": {**(metadata or {}), "chunk_id": chunk_id}, "source": "semantic"})
=======
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
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
    return sorted(output, key=lambda item: item["score"], reverse=True)[:top_k]
