"""Group Task 1: download official Ha Long tourism/heritage documents."""

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

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_DIR / "data" / "landing" / "legal"
SOURCES_PATH = PROJECT_DIR / "sources.json"
REPORT_PATH = PROJECT_DIR / "reports" / "collection_report.json"
TIMEOUT = (10, 45)
LOG = logging.getLogger(__name__)

SOURCE_CATALOG = [
    {"id": "halong-legal-001", "title": "Management Plan for Ha Long Bay - Cat Ba Archipelago 2021-2025",
     "source_url": "https://whc.unesco.org/document/190339", "publisher": "UNESCO World Heritage Centre",
     "document_type": "management_plan", "filename": "ha-long-cat-ba-management-plan-2021-2025.pdf"},
    {"id": "halong-legal-002", "title": "Kế hoạch quản lý khu rừng đặc dụng bảo vệ cảnh quan vịnh Hạ Long năm 2024",
     "source_url": "https://halongbay.com.vn/Data/files/49_KH-BQLVHL_%20K%E1%BA%BE%20HO%E1%BA%A0CH%20QL%20R%E1%BB%AANG%20%C4%90%E1%BA%B6C%20D%E1%BB%A4NG%20V%E1%BB%8ANH%20H%E1%BA%A0%20LONG_signed.pdf",
     "publisher": "Ban Quản lý Vịnh Hạ Long", "document_type": "conservation_plan",
     "filename": "ha-long-special-use-forest-management-plan-2024.pdf"},
    {"id": "halong-legal-003", "title": "Kế hoạch triển khai vùng hoạt động vui chơi giải trí trên vịnh Hạ Long",
     "source_url": "https://halongbay.com.vn/Data/files/N%C4%82M%202024/14_KH%20tri%E1%BB%83n%20khai%20Quy%E1%BA%BFt%20%C4%91%E1%BB%8Bnh%20s%E1%BB%91%20152Q%C4%90%20UBND%20v%E1%BB%81%20c%C3%B4ng%20b%E1%BB%91%20v%C3%B9ng%20h%C4%91%20vui%20ch%C6%A1i%20gi%E1%BA%A3i%20tr%C3%AD%20Ba%20Hang%20T%C3%B9ng%20S%C3%A2u%20V.pdf",
     "publisher": "Ban Quản lý Vịnh Hạ Long", "document_type": "visitor_safety_plan",
     "filename": "ha-long-water-recreation-safety-plan-2024.pdf"},
]


def safe_filename(value: str) -> str:
    name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    name = re.sub(r"[^a-z0-9._-]+", "-", name).strip(".-")[:180]
    if not name or Path(name).name != name: raise ValueError("unsafe filename")
    return name


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry)); session.headers["User-Agent"] = "HaLong-Educational-RAG/1.0"
    return session


def collect_source(source: dict, session: requests.Session | None = None,
                   output_dir: Path = OUTPUT_DIR, known_hashes: set[str] | None = None) -> dict:
    started = datetime.now(timezone.utc); known_hashes = known_hashes if known_hashes is not None else set()
    item = {k: v for k, v in source.items() if k != "filename"}
    item.update(file_type="pdf", downloaded_at=started.isoformat(), status="failed")
    try:
        response = (session or make_session()).get(source["source_url"], timeout=TIMEOUT, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
        item.update(http_status=response.status_code, content_type=content_type); response.raise_for_status()
        if not response.content.startswith(b"%PDF-") or "html" in content_type.lower():
            raise ValueError("invalid PDF signature or HTML response")
        digest = hashlib.sha256(response.content).hexdigest(); item["sha256"] = digest
        if digest in known_hashes:
            item["status"] = "duplicate"
        else:
            known_hashes.add(digest); output_dir.mkdir(parents=True, exist_ok=True)
            target = output_dir / safe_filename(source["filename"])
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
                item["status"] = "skipped_duplicate"
            else:
                target.write_bytes(response.content); item["status"] = "success"
            try:
                item["local_path"] = target.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                item["local_path"] = target.as_posix()
    except Exception as exc:
        item.update(error_type=type(exc).__name__, error=str(exc)); LOG.warning("source_url=%s status=failed error_type=%s", source.get("source_url"), type(exc).__name__)
    item["duration_ms"] = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return item


def collect_all(sources: list[dict] | None = None) -> dict:
    known: set[str] = set(); session = make_session()
    results = [collect_source(source, session, known_hashes=known) for source in (sources or SOURCE_CATALOG)]
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"total_sources": len(results), "successful": sum(x["status"] in {"success", "skipped_duplicate"} for x in results),
              "failed": sum(x["status"] == "failed" for x in results), "duplicates": sum("duplicate" in x["status"] for x in results), "results": results}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True); REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); print(json.dumps(collect_all(), ensure_ascii=False, indent=2))
