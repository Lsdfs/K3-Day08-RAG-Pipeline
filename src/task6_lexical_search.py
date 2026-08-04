"""Task 6: cached BM25 lexical search with Unicode/Vietnamese tokenization."""

from __future__ import annotations

import re
import math
import threading
from collections import Counter
import unicodedata

from .task4_chunking_indexing import chunk_documents, load_documents

CORPUS: list[dict] = []
_BM25 = None
_INDEX_INITIALIZED = False
_LOCK = threading.Lock()


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFC", " ".join(str(text).lower().split()))
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def build_bm25_index(corpus: list[dict]):
    if not corpus:
        return None
    tokenized=[tokenize(item["content"]) for item in corpus]
    try:
        from rank_bm25 import BM25Okapi
        return BM25Okapi(tokenized)
    except (ImportError,ModuleNotFoundError):
        return _BM25Fallback(tokenized)


class _BM25Fallback:
    def __init__(self,documents,k1=1.5,b=.75):
        self.docs=documents; self.k1=k1; self.b=b; self.avg=sum(map(len,documents))/max(1,len(documents))
        self.freq=[Counter(d) for d in documents]; self.df=Counter(t for d in documents for t in set(d)); self.n=len(documents)
    def get_scores(self,query):
        scores=[]
        for doc,freq in zip(self.docs,self.freq):
            score=0.0
            for term in query:
                tf=freq.get(term,0); idf=math.log(1+(self.n-self.df.get(term,0)+.5)/(self.df.get(term,0)+.5))
                denom=tf+self.k1*(1-self.b+self.b*len(doc)/max(1,self.avg)); score += idf*(tf*(self.k1+1)/denom if denom else 0)
            scores.append(score)
        return scores


def refresh_index(corpus: list[dict] | None = None):
    global CORPUS, _BM25, _INDEX_INITIALIZED
    with _LOCK:
        CORPUS = list(corpus) if corpus is not None else chunk_documents(load_documents())
        _BM25 = build_bm25_index(CORPUS)
        _INDEX_INITIALIZED = True
    return _BM25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    global _BM25
    if not _INDEX_INITIALIZED:
        refresh_index()
    if _BM25 is None or not CORPUS:
        return []
    scores = _BM25.get_scores(tokenize(query))
    indices = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
    results = []
    for index in indices:
        score = float(scores[index])
        content = str(CORPUS[index].get("content", "")).strip()
        if score <= 0 or not content:
            continue
        results.append({"content": content, "score": score,
                        "metadata": dict(CORPUS[index].get("metadata", {})), "source": "lexical"})
        if len(results) == top_k:
            break
    return results
