"""Task 5 — Dense retrieval with a dependency-free lexical-semantic fallback."""

from __future__ import annotations

import re

from .task4_chunking_indexing import get_chunks, get_collection, get_embedder


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ỹ]+", text.lower()))


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Return relevant chunks sorted descending, using embeddings when indexed."""
    collection, embedder = get_collection(), get_embedder()
    if collection is not None and embedder is not None:
        vector = embedder.encode([query], normalize_embeddings=True)[0].tolist()
        result = collection.query(query_embeddings=[vector], n_results=top_k,
                                  include=["documents", "metadatas", "distances"])
        return sorted([
            {"content": doc, "score": max(0.0, 1 - distance), "metadata": meta or {}, "source": "semantic"}
            for doc, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
        ], key=lambda item: item["score"], reverse=True)

    query_tokens = _tokens(query)
    results = []
    for chunk in get_chunks():
        chunk_tokens = _tokens(chunk["content"])
        score = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
        results.append({"content": chunk["content"], "score": score,
                        "metadata": chunk.get("metadata", {}), "source": "semantic"})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
