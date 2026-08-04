"""
Task 5 — Semantic Search Module.
"""

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    import chromadb
    import os
    from dotenv import load_dotenv
    from openai import OpenAI
    
    load_dotenv()
    try:
        from src.task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
    except ModuleNotFoundError:
        from task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment or .env file")
        
    client = OpenAI(api_key=api_key)
    
    # Embed query bằng OpenAI
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    query_vector = response.data[0].embedding
    
    client_db = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client_db.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    
    output = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            score = max(0.0, 1.0 - dist)  # cosine distance → similarity
            output.append({"content": doc, "score": round(score, 4), "metadata": meta})
            
    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    results = semantic_search("what to do in Ha Long Bay", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
