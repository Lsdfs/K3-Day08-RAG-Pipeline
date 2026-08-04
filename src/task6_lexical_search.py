"""Task 6 — Lexical Search (BM25 or TF-IDF fallback)."""

from .task4_chunking_indexing import get_chunks

_bm25_index = None
_corpus = None


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_bm25_index(corpus: list[dict] = None):
    global _bm25_index, _corpus
    if corpus is None:
        corpus = get_chunks()
    _corpus = corpus
    try:
        from rank_bm25 import BM25Okapi
        tokenized = [_tokenize(doc["content"]) for doc in corpus]
        _bm25_index = BM25Okapi(tokenized)
    except ImportError:
        _bm25_index = None
    return _bm25_index


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    global _bm25_index, _corpus
    if _corpus is None:
        build_bm25_index()

    if _bm25_index is not None:
        tokenized_query = _tokenize(query)
        scores = _bm25_index.get_scores(tokenized_query)
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        docs_text = [doc["content"] for doc in _corpus]
        vectorizer = TfidfVectorizer(tokenizer=_tokenize, lowercase=False)
        tfidf = vectorizer.fit_transform(docs_text)
        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, tfidf)[0]

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0
    results = []
    for idx in top_indices:
        results.append({
            "content": _corpus[idx]["content"],
            "score": float(scores[idx]) / max_score if max_score > 0 else 0.0,
            "metadata": _corpus[idx].get("metadata", {}),
            "source": "lexical",
        })
    return results
