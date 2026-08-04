"""Task 4 — Load, chunk and optionally index the Hạ Long knowledge base.

Recursive character chunks keep paragraphs intact where possible. 800 characters
with 120 characters overlap is small enough for retrieval and preserves context
across paragraph boundaries.
"""

from __future__ import annotations
"""
Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB khuyến cáo — đơn giản, local, không cần Docker)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options (chọn 1, cân nhắc đánh đổi cài đặt nặng vs cần API key):
    - sentence-transformers/all-MiniLM-L6-v2 hoặc BAAI/bge-m3 — chạy local, không
      cần API key, nhưng cài nặng (~1-2GB vì kéo theo torch)
    - Google models/text-embedding-004 (768 dim) — nhẹ, cần GEMINI_API_KEY
    - OpenAI text-embedding-3-small (1536 dim) — nhẹ, cần OPENAI_API_KEY
    Gợi ý: đọc EMBEDDING_PROVIDER từ .env (os.getenv("EMBEDDING_PROVIDER", "sentence_transformers"))
    để cả nhóm có thể đổi provider mà không sửa code — nhớ đổi provider phải xoá
    chroma_db/ cũ và reindex vì dimension khác nhau (1024/768/1536) không tương thích ngược.

Vector store options:
    - ChromaDB (khuyến cáo: đơn giản, local persistent, không cần Docker)
    - Weaviate (hỗ trợ hybrid search built-in, cần Docker/Cloud)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""

from pathlib import Path
from typing import Any
import hashlib
import os
import re


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "halong_knowledge_base"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

_chunks_cache: list[dict[str, Any]] | None = None
_collection = None
_embedder = None


def load_documents(data_dir: Path = STANDARDIZED_DIR) -> list[dict[str, Any]]:
    """Read standardised Markdown files and retain provenance for citations."""
    documents = []
    if not data_dir.exists():
        return documents
    for path in sorted(data_dir.rglob("*.md")):
        if path.name.startswith("."):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue
        relative = path.relative_to(data_dir)
        documents.append({
            "content": content,
            "metadata": {
                "source": path.stem,
                "filename": path.name,
                "type": relative.parts[0] if len(relative.parts) > 1 else "document",
                "path": str(relative).replace("\\", "/"),
            },
        })
    return documents


def _split_text(text: str) -> list[str]:
    """Split on paragraph/sentence boundaries before falling back to characters."""
    blocks = re.split(r"(?<=\n)\s*\n+", text)
    chunks, current = [], ""
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) > CHUNK_SIZE:
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(block), CHUNK_SIZE - CHUNK_OVERLAP):
                chunks.append(block[start:start + CHUNK_SIZE])
            continue
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
        else:
            chunks.append(current)
            current = (current[-CHUNK_OVERLAP:] + "\n" + block).strip()
    if current:
        chunks.append(current)
    return chunks


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create character-bounded chunks while carrying document metadata."""
    chunks = []
    for document in documents:
        for index, content in enumerate(_split_text(document["content"])):
            metadata = dict(document.get("metadata", {}))
            metadata["chunk_index"] = index
            chunks.append({"content": content, "metadata": metadata})
    return chunks


def get_embedder():
    """Load embeddings only when explicitly enabled, never downloading during chat."""
    global _embedder
    if _embedder is not None:
        return _embedder
    # A first-time SentenceTransformer download can take minutes or hang on a
    # restricted network. The lightweight local retrieval path is the default
    # for a reliable web demo; set ENABLE_LOCAL_EMBEDDINGS=1 after pre-downloading
    # the model to use Chroma semantic vectors instead.
    if os.getenv("ENABLE_LOCAL_EMBEDDINGS", "0").lower() not in {"1", "true", "yes"}:
        _embedder = False
        return None
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        _embedder = False
    return _embedder if _embedder is not False else None


def build_index(chunks: list[dict[str, Any]] | None = None) -> int:
    """Persist embeddings to Chroma when optional dependencies are installed."""
    global _collection, _chunks_cache
    _chunks_cache = chunks or get_chunks()
    embedder = get_embedder()
    if not _chunks_cache or embedder is None:
        return len(_chunks_cache)
    try:
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        embeddings = embedder.encode([c["content"] for c in _chunks_cache], normalize_embeddings=True).tolist()
        _collection.add(
            ids=[f"chunk_{i}" for i in range(len(_chunks_cache))],
            documents=[c["content"] for c in _chunks_cache],
            embeddings=embeddings,
            metadatas=[c["metadata"] for c in _chunks_cache],
        )
    except Exception:
        _collection = None
    return len(_chunks_cache)


def get_collection():
    return _collection


def get_chunks() -> list[dict[str, Any]]:
    global _chunks_cache
    if _chunks_cache is None:
        _chunks_cache = chunk_documents(load_documents())
    return _chunks_cache
