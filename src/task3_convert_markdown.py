"""Task 3: fault-tolerant conversion of landing files to UTF-8 Markdown."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANDING_DIR = ROOT / "data" / "landing"
OUTPUT_DIR = ROOT / "data" / "standardized"
REPORT_PATH = OUTPUT_DIR / "conversion_report.json"
SUPPORTED = {".pdf", ".docx", ".doc", ".html", ".htm", ".json", ".txt", ".md"}
LOG = logging.getLogger(__name__)


def _json_to_markdown(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    title = str(data.get("title") or "Untitled").strip()
    source = data.get("source_url") or data.get("url")
    content = data.get("content_markdown") or data.get("content") or data.get("text") or ""
    return f"# {title}\n\n**Source:** {source or 'N/A'}\n\n{str(content).strip()}"


def convert_file(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _json_to_markdown(path), "json_native"
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8-sig"), "text_native"
    if suffix in {".html", ".htm"}:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding="utf-8-sig"), "html.parser")
        for tag in soup.select("script,style,nav,footer,header,aside"):
            tag.decompose()
        return (soup.select_one("main,article") or soup).get_text("\n", strip=True), "beautifulsoup"
    try:
        from markitdown import MarkItDown
        return str(MarkItDown().convert(str(path)).text_content or ""), "markitdown"
    except (ImportError, ModuleNotFoundError):
        if suffix == ".pdf":
            from pypdf import PdfReader
            return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages), "pypdf_fallback"
        raise


def convert_all(landing_dir: Path = LANDING_DIR, output_dir: Path = OUTPUT_DIR) -> dict:
    report = {"total_files": 0, "successful_files": 0, "failed_files": 0,
              "skipped_files": 0, "empty_files": 0, "results": []}
    output_dir.mkdir(parents=True, exist_ok=True)
    source_records = {}
    metadata_file = landing_dir / "legal" / "sources.json"
    if metadata_file.exists():
        source_records = {Path(x.get("local_path", "")).name: x for x in json.loads(metadata_file.read_text(encoding="utf-8")) if x.get("local_path")}
    for path in sorted(landing_dir.rglob("*")):
        if not path.is_file() or path.name.startswith(".") or path.name == "sources.json":
            continue
        report["total_files"] += 1
        item = {"input": path.relative_to(landing_dir).as_posix()}
        if path.suffix.lower() not in SUPPORTED:
            item["status"] = "skipped"
            report["skipped_files"] += 1
        else:
            try:
                content, converter = convert_file(path)
                content = "\n".join(line.rstrip() for line in content.replace("\r\n", "\n").splitlines()).strip()
                if not content:
                    raise ValueError("Converted content is empty")
                target = output_dir / path.relative_to(landing_dir).with_suffix(".md")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = source_records.get(path.name)
                if source:
                    header = (f"---\ntitle: {json.dumps(source.get('title'), ensure_ascii=False)}\n"
                              f"source_url: {json.dumps(source.get('source_url'), ensure_ascii=False)}\n"
                              f"publisher: {json.dumps(source.get('publisher'), ensure_ascii=False)}\n---\n\n")
                    content = header + content
                target.write_text(content + "\n", encoding="utf-8")
                item.update(status="success", output=target.relative_to(output_dir).as_posix(), converter=converter)
                report["successful_files"] += 1
            except Exception as exc:
                item.update(status="failed", error_type=type(exc).__name__, error=str(exc))
                report["failed_files"] += 1
                if isinstance(exc, ValueError) and "empty" in str(exc).lower():
                    report["empty_files"] += 1
                LOG.warning("conversion failed file_path=%s error_type=%s", path, type(exc).__name__)
        report["results"].append(item)
    report["processed_at"] = datetime.now(timezone.utc).isoformat()
    (output_dir / "conversion_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def convert_legal_docs():
    return convert_all(LANDING_DIR / "legal", OUTPUT_DIR / "legal")


def convert_news_articles():
    return convert_all(LANDING_DIR / "news", OUTPUT_DIR / "news")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(convert_all(), ensure_ascii=False, indent=2))
