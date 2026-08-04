<<<<<<< HEAD
"""Task 3: fault-tolerant conversion of landing files to UTF-8 Markdown."""

from __future__ import annotations

=======
"""Task 3: Convert landing documents to Markdown."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

<<<<<<< HEAD
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
=======
LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

def convert_legal_docs():
<<<<<<< HEAD
    return convert_all(LANDING_DIR / "legal", OUTPUT_DIR / "legal")


def convert_news_articles():
    return convert_all(LANDING_DIR / "news", OUTPUT_DIR / "news")

=======
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            'PDF conversion requires: pip install "markitdown[pdf]"'
        ) from exc
    source, target = LANDING_DIR / "legal", OUTPUT_DIR / "legal"
    target.mkdir(parents=True, exist_ok=True)
    converter, saved = MarkItDown(), []
    for path in source.iterdir():
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        text = converter.convert(str(path)).text_content.strip()
        if not text:
            raise ValueError(f"No text extracted from {path}")
        output = target / f"{path.stem}.md"
        output.write_text(text + "\n", encoding="utf-8")
        saved.append(output)
    return saved

def convert_news_articles():
    source, target = LANDING_DIR / "news", OUTPUT_DIR / "news"
    target.mkdir(parents=True, exist_ok=True)
    saved = []
    for path in source.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        output = target / f"{path.stem}.md"
        text = f"# {data.get('title', 'Unknown')}\n\n**Source:** {data.get('url', 'N/A')}\n\n**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n{data.get('content_markdown', '')}\n"
        output.write_text(text, encoding="utf-8")
        saved.append(output)
    return saved

def convert_all():
    # JSON conversion has no optional dependency, so do it first. This also
    # preserves useful output if the PDF extra is not installed yet.
    saved = convert_news_articles()
    saved.extend(convert_legal_docs())
    return saved
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(convert_all(), ensure_ascii=False, indent=2))
