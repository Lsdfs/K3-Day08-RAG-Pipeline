"""Cached BM25 retrieval for Vietnamese and English Ha Long content."""

from __future__ import annotations

import math
import re
from collections import Counter

from .task4_chunking_indexing import load_index

CORPUS: list[dict] = []
_TOKENIZED: list[list[str]] = []
_FREQ: list[Counter] = []
_DF: Counter = Counter()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", " ".join(text.lower().split()), re.UNICODE)


def build_bm25_index(corpus: list[dict]):
    global CORPUS, _TOKENIZED, _FREQ, _DF
    CORPUS = list(corpus)
    _TOKENIZED = [tokenize(item["content"]) for item in CORPUS]
    _FREQ = [Counter(tokens) for tokens in _TOKENIZED]
    _DF = Counter(term for tokens in _TOKENIZED for term in set(tokens))
    return {"documents": len(CORPUS)}


def _ensure_index():
    if not CORPUS:
        build_bm25_index(load_index())


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    _ensure_index()
    if not CORPUS:
        return []
    query_tokens = tokenize(query)
    average_length = sum(map(len, _TOKENIZED)) / len(_TOKENIZED)
    scored = []
    for row, tokens, frequencies in zip(CORPUS, _TOKENIZED, _FREQ):
        score = 0.0
        for term in query_tokens:
            tf = frequencies.get(term, 0)
            idf = math.log(1 + (len(CORPUS) - _DF.get(term, 0) + .5) / (_DF.get(term, 0) + .5))
            denominator = tf + 1.5 * (1 - .75 + .75 * len(tokens) / max(1, average_length))
            score += idf * (tf * 2.5 / denominator if denominator else 0)
        if score > 0:
            scored.append({"content": row["content"], "score": score,
                           "metadata": row["metadata"], "source": "lexical"})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]
