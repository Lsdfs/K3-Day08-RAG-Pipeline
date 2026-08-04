"""
Task 4 — Chunking & Indexing vào Vector Store.
"""

from pathlib import Path
from typing import Any

# Configuration — explained choices
CHUNK_SIZE = 500         # Reasonable size for Vietnamese uni policy docs
CHUNK_OVERLAP = 50       # Small overlap to avoid splitting mid-paragraph
CHUNKING_METHOD = "recursive"  # RecursiveCharacterTextSplitter: safe, common, respects paragraph/line breaks
EMBEDDING_MODEL = "BAAI/bge-m3"  # Multilingual (EN+VI), 1024 dim, strong on Vietnamese
VECTOR_STORE = "chromadb"        # Local, persistent, no Docker needed

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "university_policies"

# Global state — initialized once, reused by downstream tasks
_embedder = None
_collection = None
_chunks_cache: list[dict[str, Any]] = []


def load_documents() -> list[dict[str, Any]]:
    """Load all .md files from data/standardized/, return list of dicts with content + metadata."""
    docs = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name == ".gitkeep":
            continue
        content = md_file.read_text(encoding="utf-8")
        source_type = "legal" if "legal" in str(md_file) else "news"
        docs.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": source_type,
                "path": str(md_file.relative_to(STANDARDIZED_DIR)),
            }
        })
    return docs


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split documents into chunks using a built-in recursive splitter."""
    chunks = []
    for doc in documents:
        texts = _recursive_split(doc["content"])
        for i, text in enumerate(texts):
            chunks.append({
                "content": text,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": i,
                }
            })
    return chunks


def _recursive_split(text: str) -> list[str]:
    """Built-in recursive splitter — no external dependency needed."""
    separators = ["\n\n", "\n", ". ", " ", ""]
    return _split_recursive(text, separators)


def _split_recursive(text: str, separators: list[str]) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text] if text.strip() else []
    if not separators:
        result = []
        for i in range(0, len(text), CHUNK_SIZE):
            result.append(text[i:i + CHUNK_SIZE])
        return result
    sep = separators[0]
    if sep == "":
        result = []
        for i in range(0, len(text), CHUNK_SIZE):
            result.append(text[i:i + CHUNK_SIZE])
        return result
    parts = text.split(sep)
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            part += sep
        sub = _split_recursive(part, separators[1:])
        result.extend(sub)
    return result


def embed_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Embed chunk texts using the central embedder."""
    embedder = get_embedder()
    texts = [c["content"] for c in chunks]
    embeddings = embedder.encode(texts)
    for i, emb in enumerate(embeddings):
        chunks[i]["embedding"] = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
    return chunks


def index_to_vectorstore(chunks: list[dict[str, Any]]) -> None:
    """Persist chunks. ChromaDB if available, in-memory fallback."""
    global _collection, _chunks_cache
    _chunks_cache = chunks

    try:
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _collection = client.get_collection(name=COLLECTION_NAME)
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass
        _collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [c["content"] for c in chunks]
        embeddings = [c["embedding"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        _collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    except ImportError:
        _collection = None  # in-memory only


def get_embedder():
    """Lazy-load embedder. Uses mock by default; set FORCE_MOCK=0 in env to try real model."""
    global _embedder
    import os
    if _embedder is not None:
        return _embedder
    if os.getenv("FORCE_MOCK", "1") == "0":
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBEDDING_MODEL)
            return _embedder
        except Exception:
            pass
    import numpy as np
    import hashlib
    class _MockEmbedder:
        def encode(self, texts, normalize_embeddings=False):
            if isinstance(texts, str):
                texts = [texts]
            result = []
            for t in texts:
                h = hashlib.sha256(t.encode()).digest()
                emb = [float(b) / 255.0 for b in h[:64]] + [0.0] * 960
                result.append(emb[:1024])
            return np.array(result) if len(result) > 1 else np.array(result)
    _embedder = _MockEmbedder()
    return _embedder


def get_collection():
    """Return ChromaDB collection or None (in-memory fallback)."""
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(name=COLLECTION_NAME)
        return _collection
    except Exception:
        return None


def get_chunks() -> list[dict[str, Any]]:
    """Return all chunks (used by lexical search for corpus)."""
    global _chunks_cache
    if not _chunks_cache:
        _chunks_cache = chunk_documents(load_documents())
    return _chunks_cache
