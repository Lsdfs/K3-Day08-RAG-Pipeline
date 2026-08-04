"""Optional PageIndex integration. Missing credentials never break the chatbot."""

from __future__ import annotations

import json
import os
from pathlib import Path

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
