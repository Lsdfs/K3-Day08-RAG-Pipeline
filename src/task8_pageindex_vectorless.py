"""Task 8 — PageIndex vectorless remote retrieval with an offline fallback."""

from __future__ import annotations

import os
import re

from dotenv import load_dotenv

load_dotenv()


def _remote_search(query: str, top_k: int) -> list[dict] | None:
    """Query PageIndex's OpenAI-compatible document chat API.

    The document must first be uploaded in PageIndex.  Its id is configured via
    PAGEINDEX_DOC_ID (or a comma-separated PAGEINDEX_DOC_IDS value).
    """
    if os.getenv("ENABLE_PAGEINDEX_CLOUD", "0").lower() not in {"1", "true", "yes"}:
        return None
    api_key = os.getenv("PAGEINDEX_API_KEY", "").strip()
    raw_ids = os.getenv("PAGEINDEX_DOC_IDS") or os.getenv("PAGEINDEX_DOC_ID", "")
    doc_ids = [value.strip() for value in raw_ids.split(",") if value.strip()]
    if not api_key or not doc_ids:
        return None

    import requests

    base_url = os.getenv("PAGEINDEX_API_URL", "https://api.pageindex.ai").rstrip("/")
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "messages": [{"role": "user", "content": query}],
            "doc_id": doc_ids[0] if len(doc_ids) == 1 else doc_ids,
            "stream": False,
        },
        timeout=float(os.getenv("PAGEINDEX_TIMEOUT_SECONDS", "30")),
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return []
    citations = payload.get("citations") or payload.get("references") or []
    return [{
        "content": content,
        "score": 1.0,
        "metadata": {"backend": "pageindex-cloud", "doc_ids": ",".join(doc_ids),
                     "citations": str(citations[:top_k])},
        "source": "pageindex",
    }]


def _local_vectorless_search(query: str, top_k: int) -> list[dict]:
    """Deterministic tree-less fallback used only when cloud credentials are absent."""
    from .task4_chunking_indexing import get_chunks

    terms = set(re.findall(r"[\wÀ-ỹ]+", query.lower()))
    scored = []
    for chunk in get_chunks():
        words = set(re.findall(r"[\wÀ-ỹ]+", chunk["content"].lower()))
        score = len(terms & words) / max(len(terms), 1)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{"content": chunk["content"], "score": score,
             "metadata": {**chunk.get("metadata", {}), "backend": "pageindex-local-fallback"},
             "source": "pageindex"} for score, chunk in scored[:top_k]]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Return PageIndex results; degrade locally if credentials/network are unavailable."""
    try:
        remote = _remote_search(query, top_k)
        if remote is not None:
            return remote[:top_k]
    except Exception:
        # The main RAG pipeline must remain available during an offline demo.
        pass
    local = _local_vectorless_search(query, top_k)
    return local or [{"content": "No results found.", "score": 0.0,
                      "metadata": {"backend": "pageindex-local-fallback"},
                      "source": "pageindex"}]
