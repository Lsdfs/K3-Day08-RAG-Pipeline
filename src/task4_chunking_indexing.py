<<<<<<< HEAD
"""Task 4: deterministic chunking, multilingual embeddings and Chroma indexing."""
=======
"""Chunk and persist the Ha Long Markdown corpus for local retrieval."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

from __future__ import annotations

import hashlib
import json
<<<<<<< HEAD
import logging
import math
import re
import time
from functools import lru_cache
=======
import math
import re
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARDIZED_DIR = ROOT / "data" / "standardized"
<<<<<<< HEAD
CHROMA_DIR = ROOT / "chroma_db"

# 700 characters balances Vietnamese sentence context and retrieval precision;
# 100-character overlap preserves facts that cross chunk boundaries.
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"
# BGE-M3 is multilingual and performs well for both Vietnamese and English.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"
LOG = logging.getLogger(__name__)
LOCAL_INDEX_PATH = CHROMA_DIR / "local_collection.json"


def load_documents(standardized_dir: Path = STANDARDIZED_DIR) -> list[dict]:
    documents = []
    if not standardized_dir.exists():
        return documents
    for path in sorted(standardized_dir.rglob("*.md")):
        content = path.read_text(encoding="utf-8-sig").strip()
        if not content:
            continue
        relative = path.relative_to(standardized_dir)
        documents.append({"content": content, "metadata": {
            "source": relative.as_posix(), "source_path": str(path.resolve()),
            "type": relative.parts[0] if len(relative.parts) > 1 else "unknown"}})
    return documents


def _split_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        hard_end = min(start + CHUNK_SIZE, len(text))
        end = hard_end
        if hard_end < len(text):
            candidates = [text.rfind(sep, start + CHUNK_SIZE // 2, hard_end) for sep in ("\n\n", "\n", ". ", " ")]
            boundary = max(candidates)
=======
INDEX_PATH = ROOT / "group_project" / ".cache" / "ha_long_index.json"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
EMBEDDING_MODEL = "multilingual-hashing-v1"
EMBEDDING_DIM = 384
COLLECTION_NAME = "ha_long_tourism"


def load_documents() -> list[dict]:
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8-sig").strip()
        if len(content) < 100:
            continue
        source_match = re.search(r"\*\*Source:\*\*\s*(\S+)", content)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        documents.append({"content": content, "metadata": {
            "source": path.relative_to(ROOT).as_posix(),
            "source_url": source_match.group(1) if source_match else "",
            "title": title_match.group(1).strip() if title_match else path.stem,
            "type": path.parent.name,
        }})
    return documents


def _split(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]
    output, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            boundary = max(text.rfind(sep, start + CHUNK_SIZE // 2, end) for sep in ("\n\n", "\n", ". ", " "))
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
<<<<<<< HEAD
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    chunks = []
    seen = set()
    for doc in documents:
        for index, content in enumerate(_split_text(str(doc.get("content", "")).strip())):
            if not content:
                continue
            digest = hashlib.sha256((doc.get("metadata", {}).get("source", "") + "\0" + content).encode()).hexdigest()
=======
            output.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return output


def chunk_documents(documents: list[dict]) -> list[dict]:
    chunks, seen = [], set()
    for document in documents:
        for index, content in enumerate(_split(document["content"])):
            digest = hashlib.sha256((document["metadata"]["source"] + "\0" + content).encode("utf-8")).hexdigest()
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
            if digest in seen:
                continue
            seen.add(digest)
            chunks.append({"id": digest, "content": content,
<<<<<<< HEAD
                           "metadata": {**doc.get("metadata", {}), "chunk_index": index, "chunk_id": digest}})
    return chunks


@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(EMBEDDING_MODEL)
    except (ImportError, ModuleNotFoundError):
        LOG.warning("sentence-transformers unavailable; using deterministic multilingual hashing fallback")
        return _HashingEmbeddingModel(EMBEDDING_DIM)


class _HashingEmbeddingModel:
    """Offline fallback; word and character features preserve Unicode/Vietnamese text."""
    model_name = "local-multilingual-hashing-v1"
    def __init__(self, dimensions: int): self.dimensions = dimensions
    def _one(self, text: str) -> list[float]:
        vector=[0.0]*self.dimensions; normalized=" ".join(text.lower().split())
        features=re.findall(r"[^\W_]+",normalized,re.UNICODE)+[normalized[i:i+3] for i in range(max(0,len(normalized)-2))]
        for feature in features:
            digest=hashlib.blake2b(feature.encode("utf-8"),digest_size=8).digest()
            index=int.from_bytes(digest,"little")%self.dimensions
            vector[index] += 1.0 if digest[0]&1 else -1.0
        norm=math.sqrt(sum(x*x for x in vector)) or 1.0
        return [x/norm for x in vector]
    def encode(self, texts, **_kwargs):
        return self._one(texts) if isinstance(texts,str) else [self._one(x) for x in texts]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []
    embeddings = get_embedding_model().encode([c["content"] for c in chunks], normalize_embeddings=True,
                                               show_progress_bar=False)
    for chunk, vector in zip(chunks, embeddings):
        chunk["embedding"] = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    return chunks


def get_collection(create: bool = False):
    try:
        import chromadb
        if not CHROMA_DIR.exists() and not create:
            raise RuntimeError("Chroma index does not exist. Run Task 4 indexing first.")
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        if create: return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        return client.get_collection(COLLECTION_NAME)
    except (ImportError, ModuleNotFoundError):
        if not create and not LOCAL_INDEX_PATH.exists():
            raise RuntimeError("Vector index does not exist. Install ChromaDB or run Task 4 indexing first.")
        return _LocalPersistentCollection(LOCAL_INDEX_PATH)


class _LocalPersistentCollection:
    """API-compatible persistent fallback used only when ChromaDB is unavailable."""
    def __init__(self,path:Path):
        self.path=path; self.rows=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    def count(self): return len(self.rows)
    def upsert(self,ids,documents,embeddings,metadatas):
        for i,d,e,m in zip(ids,documents,embeddings,metadatas): self.rows[i]={"document":d,"embedding":e,"metadata":m}
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(self.rows,ensure_ascii=False),encoding="utf-8")
    def query(self,query_embeddings,n_results,include=None):
        q=query_embeddings[0]; ranked=[]
        for key,row in self.rows.items():
            score=sum(a*b for a,b in zip(q,row["embedding"])); ranked.append((1-score,key,row))
        ranked.sort(key=lambda x:x[0]); selected=ranked[:n_results]
        return {"ids":[[x[1] for x in selected]],"documents":[[x[2]["document"] for x in selected]],
                "metadatas":[[x[2]["metadata"] for x in selected]],"distances":[[x[0] for x in selected]]}


def index_to_vectorstore(chunks: list[dict]) -> dict:
    if not chunks:
        return {"indexed": 0, "collection": COLLECTION_NAME}
    collection = get_collection(create=True)
    collection.upsert(ids=[c["id"] for c in chunks], documents=[c["content"] for c in chunks],
                      embeddings=[c["embedding"] for c in chunks], metadatas=[c["metadata"] for c in chunks])
    return {"indexed": len(chunks), "collection_count": collection.count(), "collection": COLLECTION_NAME}


def run_pipeline() -> dict:
    started = time.perf_counter()
    docs = load_documents()
    chunks = chunk_documents(docs)
    embedded = embed_chunks(chunks)
    stats = index_to_vectorstore(embedded)
    model = get_embedding_model()
    model_used = getattr(model, "model_name", EMBEDDING_MODEL)
    stats.update(documents=len(docs), chunks=len(chunks), model_configured=EMBEDDING_MODEL, model_used=model_used,
                 duration_ms=round((time.perf_counter() - started) * 1000, 2))
    LOG.info("task_name=task4 documents=%s chunks=%s model=%s duration_ms=%s",
             len(docs), len(chunks), model_used, stats["duration_ms"])
=======
                "metadata": {**document["metadata"], "chunk_id": digest, "chunk_index": index}})
    return chunks


def embed_text(text: str) -> list[float]:
    normalized = " ".join(text.lower().split())
    features = re.findall(r"[^\W_]+", normalized, re.UNICODE)
    features += [normalized[i:i + 3] for i in range(max(0, len(normalized) - 2))]
    vector = [0.0] * EMBEDDING_DIM
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        vector[int.from_bytes(digest, "little") % EMBEDDING_DIM] += 1.0 if digest[0] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    return [{**chunk, "embedding": embed_text(chunk["content"])} for chunk in chunks]


def index_to_vectorstore(chunks: list[dict]) -> dict:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = {chunk["id"]: chunk for chunk in chunks if chunk.get("content", "").strip()}
    INDEX_PATH.write_text(json.dumps({"model": EMBEDDING_MODEL, "rows": rows}, ensure_ascii=False), encoding="utf-8")
    return {"indexed": len(rows), "collection": COLLECTION_NAME, "path": str(INDEX_PATH)}


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        run_pipeline()
    return list(json.loads(INDEX_PATH.read_text(encoding="utf-8"))["rows"].values())


def run_pipeline() -> dict:
    documents = load_documents()
    chunks = embed_chunks(chunk_documents(documents))
    stats = index_to_vectorstore(chunks)
    stats.update(documents=len(documents), chunks=len(chunks), model=EMBEDDING_MODEL)
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
    return stats


if __name__ == "__main__":
<<<<<<< HEAD
    logging.basicConfig(level=logging.INFO)
    print(run_pipeline())
=======
    print(json.dumps(run_pipeline(), ensure_ascii=False, indent=2))
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
