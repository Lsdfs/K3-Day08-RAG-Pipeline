"""Group Task 3: standardize Ha Long landing data as Markdown with provenance."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
LANDING_DIR = PROJECT_DIR / "data" / "landing"
OUTPUT_DIR = PROJECT_DIR / "data" / "standardized"
SOURCES_PATH = PROJECT_DIR / "sources.json"
REPORT_PATH = PROJECT_DIR / "reports" / "conversion_report.json"
SUPPORTED = {".pdf", ".docx", ".doc", ".html", ".htm", ".json", ".txt", ".md"}


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _convert(path: Path) -> tuple[str, dict, str]:
    suffix = path.suffix.lower(); metadata = {}
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8")); metadata = data
        return str(data.get("content") or data.get("content_markdown") or ""), metadata, "json_native"
    if suffix in {".txt", ".md"}: return path.read_text(encoding="utf-8-sig"), metadata, "text_native"
    if suffix in {".html", ".htm"}:
        soup=BeautifulSoup(path.read_text(encoding="utf-8-sig"),"html.parser")
        for node in soup.select("script,style,nav,footer,header,aside"): node.decompose()
        return (soup.select_one("main,article") or soup).get_text("\n",strip=True), metadata, "beautifulsoup"
    try:
        from markitdown import MarkItDown
        return str(MarkItDown().convert(str(path)).text_content or ""), metadata, "markitdown"
    except (ImportError, ModuleNotFoundError):
        if suffix == ".pdf":
            from pypdf import PdfReader
            text="\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
            return text, metadata, "pypdf_fallback"
        raise


def _source_map() -> dict:
    if not SOURCES_PATH.exists(): return {}
    records=json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    return {Path(x.get("local_path","")).name:x for x in records if x.get("local_path")}


def _front_matter(meta: dict) -> str:
    fields=("id","title","source_url","publisher","document_type","topic","language","downloaded_at","crawled_at","processed_at","original_file","content_hash")
    lines=["---"]
    for key in fields:
        value=meta.get(key)
        lines.append(f"{key}: {'null' if value is None else json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines+["---"])


def convert_all(landing_dir: Path = LANDING_DIR, output_dir: Path = OUTPUT_DIR) -> dict:
    report={"total_files":0,"successful_files":0,"failed_files":0,"skipped_files":0,"empty_files":0,"results":[]}
    sources=_source_map(); output_dir.mkdir(parents=True,exist_ok=True)
    for path in sorted(landing_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."): continue
        report["total_files"]+=1; result={"input":path.relative_to(landing_dir).as_posix()}
        if path.suffix.lower() not in SUPPORTED:
            result["status"]="skipped"; report["skipped_files"]+=1
        else:
            try:
                content,file_meta,converter=_convert(path); content=_clean(content)
                if len(content)<100: raise ValueError("empty or too-short converted content")
                source_meta=sources.get(path.name,{})
                title=file_meta.get("title") or source_meta.get("title")
                source_url=file_meta.get("source_url") or source_meta.get("source_url")
                if not title or not source_url: raise ValueError("missing required title/source_url provenance")
                digest=hashlib.sha256(content.encode("utf-8")).hexdigest(); now=datetime.now(timezone.utc).isoformat()
                try: original_file=path.relative_to(REPO_ROOT).as_posix()
                except ValueError: original_file=path.as_posix()
                metadata={"id":file_meta.get("id") or source_meta.get("id"),"title":title,"source_url":source_url,
                    "publisher":file_meta.get("publisher") or source_meta.get("publisher"),
                    "document_type":file_meta.get("content_type") or source_meta.get("document_type"),
                    "topic":file_meta.get("topic"),"language":file_meta.get("language") or ("vi" if "halongbay.com.vn" in source_url else None),
                    "downloaded_at":source_meta.get("downloaded_at"),"crawled_at":file_meta.get("crawled_at"),"processed_at":now,
                    "original_file":original_file,"content_hash":digest}
                target=output_dir/path.relative_to(landing_dir).with_suffix(".md"); target.parent.mkdir(parents=True,exist_ok=True)
                rendered=f"{_front_matter(metadata)}\n\n# {title}\n\n{content}\n"
                if target.exists() and f'content_hash: "{digest}"' in target.read_text(encoding="utf-8"):
                    result["status"]="skipped"; report["skipped_files"]+=1
                else:
                    target.write_text(rendered,encoding="utf-8"); result["status"]="success"; report["successful_files"]+=1
                result.update(output=target.relative_to(output_dir).as_posix(),converter=converter,content_hash=digest)
            except Exception as exc:
                result.update(status="failed",error_type=type(exc).__name__,error=str(exc)); report["failed_files"]+=1
                if "empty" in str(exc).lower() or "short" in str(exc).lower(): report["empty_files"]+=1
        report["results"].append(result)
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report


if __name__ == "__main__": print(json.dumps(convert_all(),ensure_ascii=False,indent=2))
