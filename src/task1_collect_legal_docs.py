"""Task 1: download verified university-service documents."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "landing" / "legal"
METADATA_PATH = DATA_DIR / "sources.json"
TIMEOUT = (10, 45)

SOURCES = [
    {
        "id": "rmit-legal-001",
        "title": "RMIT Vietnam Student Fees and Charges Guide 2026",
        "source_url": "https://www.rmit.edu.vn/assets/vn/en/assets-for-production/documents/pdfs/study-at-rmit/tuition-fees/student-fees-and-charges-guide-06-2026.pdf",
        "publisher": "RMIT University Vietnam",
        "filename": "rmit-student-fees-and-charges-guide-2026.pdf",
        "document_type": "fees_policy",
    },
    {
        "id": "rmit-legal-002",
        "title": "RMIT Vietnam Factsheet 2025-2026",
        "source_url": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/pdfs/global-experiences/rmit-vietnam-fact-sheet-2025-2026.pdf",
        "publisher": "RMIT University Vietnam",
        "filename": "rmit-vietnam-factsheet-2025-2026.pdf",
        "document_type": "student_services_guide",
    },
    {
        "id": "rmit-legal-003",
        "title": "RMIT Vietnam Guide for Parents and Families 2026",
        "source_url": "https://www.rmit.edu.vn/assets/vn/en/assets-for-production/documents/pdfs/vn-parents-guide/en-parents-guide-2026.pdf",
        "publisher": "RMIT University Vietnam",
        "filename": "rmit-parents-and-families-guide-2026.pdf",
        "document_type": "student_support_guide",
    },
]

LOG = logging.getLogger(__name__)


def setup_directory() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def safe_filename(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-").lower()
    if not value or value in {"con", "prn", "aux", "nul"}:
        raise ValueError("Unsafe or empty filename")
    return value[:180]


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, connect=2, read=2, backoff_factor=0.5,
                  status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "Educational-RAG-Pipeline/1.0"
    return session


def download_file(source: dict, output_dir: Path = DATA_DIR,
                  session: requests.Session | None = None) -> dict:
    """Download one PDF/DOCX, rejecting HTML/error bodies."""
    started = datetime.now(timezone.utc)
    result = {**source, "downloaded_at": started.isoformat(), "status": "failed"}
    try:
        filename = safe_filename(source["filename"])
        response = (session or _session()).get(source["source_url"], timeout=TIMEOUT,
                                                allow_redirects=True)
        result.update(http_status=response.status_code,
                      content_type=response.headers.get("Content-Type", "").split(";", 1)[0])
        response.raise_for_status()
        body = response.content
        suffix = Path(filename).suffix.lower()
        signature_ok = (suffix == ".pdf" and body.startswith(b"%PDF-")) or (
            suffix in {".docx", ".doc"} and (body.startswith(b"PK\x03\x04") or body.startswith(b"\xd0\xcf\x11\xe0")))
        content_type = result["content_type"].lower()
        if not signature_ok or "html" in content_type:
            raise ValueError("Response is not a valid PDF/DOCX")
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / filename
        if target.exists() and hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(body).digest():
            result["status"] = "skipped_duplicate"
        else:
            target.write_bytes(body)
            result["status"] = "success"
        result.update(local_path=target.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
        LOG.warning("download failed source_url=%s error_type=%s", source.get("source_url"), type(exc).__name__)
    result["duration_ms"] = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return result


def collect_all(sources: list[dict] | None = None) -> list[dict]:
    setup_directory()
    session = _session()
    results = [download_file(source, session=session) for source in (sources or SOURCES)]
    METADATA_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    done = collect_all()
    print(json.dumps({"successful": sum(r["status"] in {"success", "skipped_duplicate"} for r in done),
                      "failed": sum(r["status"] == "failed" for r in done)}, indent=2))
