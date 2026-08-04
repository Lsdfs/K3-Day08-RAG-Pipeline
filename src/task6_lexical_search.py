"""Task 6 — BM25 lexical search, with a local overlap fallback."""

from __future__ import annotations

import re

from .task4_chunking_indexing import get_chunks

_bm25 = None
_corpus = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ỹ]+", text.lower())


def build_bm25_index(corpus: list[dict] | None = None):
    global _bm25, _corpus
    _corpus = corpus or get_chunks()
    try:
        from rank_bm25 import BM25Okapi
        _bm25 = BM25Okapi([_tokenize(item["content"]) for item in _corpus])
    except ImportError:
        _bm25 = None
    return _bm25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    global _corpus
    if _corpus is None:
        build_bm25_index()
    if not _corpus:
        return []
    query_tokens = _tokenize(query)
    if _bm25 is not None:
        raw_scores = list(_bm25.get_scores(query_tokens))
    else:
        query_set = set(query_tokens)
        raw_scores = [len(query_set & set(_tokenize(item["content"]))) for item in _corpus]
    maximum = max(raw_scores) if raw_scores and max(raw_scores) > 0 else 1.0
    results = [
        {"content": item["content"], "score": float(score / maximum),
         "metadata": item.get("metadata", {}), "source": "lexical"}
        for item, score in zip(_corpus, raw_scores)
    ]
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
