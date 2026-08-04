"""Task 5 — Semantic Search (dense retrieval)."""

from .task4_chunking_indexing import get_embedder, get_collection, get_chunks


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    embedder = get_embedder()
    query_emb = embedder.encode([query], normalize_embeddings=True)[0].tolist()
    collection = get_collection()

    if collection is not None:
        results = collection.query(query_embeddings=[query_emb], n_results=top_k,
                                   include=["documents", "metadatas", "distances"])
        output = []
        for i in range(len(results["ids"][0])):
            dist = results["distances"][0][i]
            score = 1.0 - dist
            output.append({
                "content": results["documents"][0][i],
                "score": score,
                "metadata": results["metadatas"][0][i] if results["metadatas"][0] else {},
                "source": "semantic",
            })
        return sorted(output, key=lambda x: x["score"], reverse=True)

    # In-memory fallback
    chunks = get_chunks()
    scored = []
    for c in chunks:
        emb = c.get("embedding", [])
        if emb:
            dot = sum(qe * e for qe, e in zip(query_emb, emb))
            scored.append((dot, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"content": c["content"], "score": s, "metadata": c.get("metadata", {}), "source": "semantic"}
        for s, c in scored[:top_k]
    ]
