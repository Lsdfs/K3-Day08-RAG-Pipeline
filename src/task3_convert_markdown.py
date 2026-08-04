"""Task 3: Convert landing documents to Markdown."""
import json
from pathlib import Path
from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

def convert_legal_docs():
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
    return convert_legal_docs() + convert_news_articles()

if __name__ == "__main__":
    convert_all()
