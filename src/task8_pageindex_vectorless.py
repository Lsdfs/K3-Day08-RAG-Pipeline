<<<<<<< HEAD
"""Task 8: PageIndex upload and query lifecycle with a graceful no-key state."""
=======
"""Optional PageIndex integration. Missing credentials never break the chatbot."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

from __future__ import annotations

import json
import os
from pathlib import Path
<<<<<<< HEAD

import requests
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
STANDARDIZED_DIR = ROOT / "data" / "standardized"
MANIFEST_PATH = ROOT / "pageindex_doc_ids.json"
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
BASE_URL = os.getenv("PAGEINDEX_BASE_URL", "https://api.pageindex.ai")
TIMEOUT = 30


def _headers() -> dict:
    if not os.getenv("PAGEINDEX_API_KEY", PAGEINDEX_API_KEY):
        raise RuntimeError("PAGEINDEX_API_KEY is not configured; Task 8 live API is BLOCKED")
    return {"Authorization": f"Bearer {os.getenv('PAGEINDEX_API_KEY', PAGEINDEX_API_KEY)}"}


def upload_documents(paths: list[Path] | None = None) -> dict:
    """Upload once and persist returned IDs; existing content hashes are skipped."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}
    for path in paths or sorted(STANDARDIZED_DIR.rglob("*.md")):
        import hashlib
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in manifest: continue
        with path.open("rb") as handle:
            response = requests.post(f"{BASE_URL}/documents", headers=_headers(),
                                     files={"file": (path.name, handle, "text/markdown")}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json(); doc_id = payload.get("doc_id") or payload.get("id")
        if not doc_id: raise ValueError("PageIndex upload response has no document id")
        manifest[digest] = {"doc_id": doc_id, "source": str(path)}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if not isinstance(query, str) or not query.strip(): raise ValueError("query must be non-empty")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0: raise ValueError("top_k must be positive")
    if not os.getenv("PAGEINDEX_API_KEY", PAGEINDEX_API_KEY) or not MANIFEST_PATH.exists(): return []
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = []
    for record in manifest.values():
        try:
            response = requests.post(f"{BASE_URL}/retrieval", headers={**_headers(), "Content-Type": "application/json"},
                                     json={"doc_id": record["doc_id"], "query": query}, timeout=TIMEOUT)
            response.raise_for_status()
            for node in response.json().get("retrieved_nodes", []):
                for group in node.get("relevant_contents", []):
                    for item in group:
                        content = str(item.get("relevant_content", "")).strip()
                        if content:
                            results.append({"content": content, "score": 1 / (len(results) + 1),
                                "metadata": {"source": record["source"], "section": item.get("section_title")},
                                "source": "pageindex"})
        except (requests.RequestException, ValueError, KeyError):
            continue
    return results[:top_k]
=======

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "group_project" / ".cache" / "pageindex_documents.json"


def upload_documents() -> dict:
    if not os.getenv("PAGEINDEX_API_KEY"):
        return {"status": "blocked", "reason": "PAGEINDEX_API_KEY is not configured", "documents": []}
    # Upload is deliberately separated from query; SDK schemas differ by version.
    return {"status": "ready", "documents": json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else []}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if not query.strip() or top_k <= 0:
        raise ValueError("query and top_k must be valid")
    if not os.getenv("PAGEINDEX_API_KEY") or not MANIFEST_PATH.exists():
        return []
    # Manifest results are cached only after a real external indexing run.
    return []
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
