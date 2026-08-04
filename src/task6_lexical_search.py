"""
Task 6 — Lexical Search Module (BM25).
"""

from pathlib import Path

# Global cache variables
_corpus: list[dict] = []
_bm25 = None


def get_corpus_and_bm25():
    """
    Tải corpus và khởi tạo BM25 index một cách lazy.
    Thử tải từ ChromaDB trước, nếu không được thì tải trực tiếp từ file Markdown.
    """
    global _corpus, _bm25
    if _bm25 is not None:
        return _corpus, _bm25
        
    # Thử load từ ChromaDB
    try:
        import chromadb
        try:
            from src.task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME
        except ModuleNotFoundError:
            from task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME
            
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name=COLLECTION_NAME)
        results = collection.get()
        if results and results["documents"]:
            _corpus = [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(results["documents"], results["metadatas"])
            ]
            print(f"Loaded {len(_corpus)} chunks from ChromaDB for BM25.")
    except Exception as e:
        print(f"Could not load corpus from ChromaDB: {e}. Falling back to manual load.")
        
    # Nếu ChromaDB trống hoặc lỗi, tải thủ công từ thư mục standardized
    if not _corpus:
        try:
            try:
                from src.task4_chunking_indexing import load_documents, chunk_documents
            except ModuleNotFoundError:
                from task4_chunking_indexing import load_documents, chunk_documents
            docs = load_documents()
            _corpus = chunk_documents(docs)
            print(f"Loaded {len(_corpus)} chunks manually for BM25.")
        except Exception as e2:
            print(f"Manual load failed: {e2}")
            
    # Xây dựng BM25 index
    if _corpus:
        _bm25 = build_bm25_index(_corpus)
        
    return _corpus, _bm25


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    from rank_bm25 import BM25Okapi
    # Tokenize đơn giản bằng lowercase và split
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    corpus, bm25_index = get_corpus_and_bm25()
    if not bm25_index:
        return []
        
    tokenized_query = query.lower().split()
    scores = bm25_index.get_scores(tokenized_query)
    
    # Lấy top_k kết quả có điểm cao nhất
    import numpy as np
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "content": corpus[idx]["content"],
                "score": float(scores[idx]),
                "metadata": corpus[idx]["metadata"]
            })
    return results


if __name__ == "__main__":
    # Test thử lexical search
    results = lexical_search("Ha Long Bay", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
