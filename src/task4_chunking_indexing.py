"""Chunk and persist the Ha Long Markdown corpus for local retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARDIZED_DIR = ROOT / "data" / "standardized"
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
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
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
            if digest in seen:
                continue
            seen.add(digest)
            chunks.append({"id": digest, "content": content,
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
    return stats


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), ensure_ascii=False, indent=2))
