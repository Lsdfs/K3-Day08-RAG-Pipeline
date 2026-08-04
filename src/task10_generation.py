"""Grounded extractive generation with verifiable citations."""

from __future__ import annotations

import re

from .task9_retrieval_pipeline import expand_query, retrieve

TOP_K = 5
INSUFFICIENT_EVIDENCE = "I cannot verify this information"


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    chunks = list(chunks)
    return chunks if len(chunks) <= 2 else chunks[::2] + chunks[1::2][::-1]


def format_context(chunks: list[dict]) -> str:
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("title") or metadata.get("source")
        if source and chunk.get("content", "").strip():
            parts.append(f"[DATA {index} | {source} | {metadata.get('source_url', '')}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def _tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "is", "of", "and", "to", "in", "có", "là", "gì", "và", "của", "ở", "như", "nào"}
    return {term for term in re.findall(r"[^\W_]+", text.lower(), re.UNICODE) if term not in stop and len(term) > 1}


def generate_with_citation(query: str, context_chunks: list[dict] | None = None,
                           top_k: int = TOP_K, dense_only: bool = False,
                           use_reranking: bool = True) -> dict:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty")
    chunks = context_chunks if context_chunks is not None else retrieve(
        query, top_k=top_k, dense_only=dense_only, use_reranking=use_reranking)
    chunks = [chunk for chunk in chunks if chunk.get("content", "").strip() and
              (chunk.get("metadata", {}).get("title") or chunk.get("metadata", {}).get("source"))]
    if not chunks:
        return {"answer": INSUFFICIENT_EVIDENCE, "sources": [], "retrieval_source": "none"}
    query_tokens = _tokens(expand_query(query))
    candidates = []
    for chunk in reorder_for_llm(chunks):
        metadata = chunk["metadata"]
        label = metadata.get("title") or metadata["source"]
        clean = re.sub(r"^#{1,6}\s*", "", chunk["content"], flags=re.MULTILINE)
        for sentence in re.split(r"(?<=[.!?])\s+|\n{2,}", clean):
            sentence = " ".join(sentence.split())
            overlap = len(query_tokens & _tokens(sentence))
            if overlap and 35 <= len(sentence) <= 600:
                candidates.append((overlap, chunk.get("score", 0), sentence, label))
    if not candidates:
        answer = INSUFFICIENT_EVIDENCE
    else:
        candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
        selected, seen = [], set()
        for _, _, sentence, label in candidates:
            if sentence.lower() not in seen:
                seen.add(sentence.lower())
                selected.append(f"{sentence} [{label}]")
            if len(selected) == 3:
                break
        answer = "\n\n".join(selected)
    return {"answer": answer, "sources": chunks,
            "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none"}
