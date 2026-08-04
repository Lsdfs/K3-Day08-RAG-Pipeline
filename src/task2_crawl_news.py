<<<<<<< HEAD
"""Task 2: crawl official RMIT student-service pages with safe fallbacks."""

from __future__ import annotations
=======
"""Task 2: Crawl five public articles about Ha Long tourism."""
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

import asyncio
import hashlib
import json
<<<<<<< HEAD
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "landing" / "news"
TIMEOUT = 30
ARTICLE_URLS = [
    "https://www.rmit.edu.vn/study-at-rmit/tuition-fees",
    "https://www.rmit.edu.vn/study-at-rmit/scholarships",
    "https://www.rmit.edu.vn/students/my-studies/fees-and-payments",
    "https://www.rmit.edu.vn/students/my-studies/important-dates-and-academic-calendar",
    "https://www.rmit.edu.vn/students/my-studies/fees-and-payments/tuition-fees-faq-and-support",
=======
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Vietnam.travel is the official tourism website of Vietnam.
ARTICLE_URLS = [
    "https://vietnam.travel/node/57",    # Ha Long destination guide
    "https://vietnam.travel/node/1368",  # Things to do in Ha Long Bay
    "https://vietnam.travel/node/959",   # Ways to see the Gulf of Tonkin
    "https://vietnam.travel/node/1363",  # Living at a heritage site
    "https://vietnam.travel/node/1834",  # Vietnam's natural landscapes
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
]
LOG = logging.getLogger(__name__)


def setup_directory() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def clean_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "")
    for tag in soup.select("script,style,noscript,nav,footer,header,aside,form,.cookie,.breadcrumb,.related"):
        tag.decompose()
    main = soup.select_one("main, article, [role=main]") or soup.body or soup
    text = "\n".join(line.strip() for line in main.get_text("\n").splitlines() if line.strip())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title.strip(), text


def crawl_article_requests(url: str) -> dict:
    response = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                            headers={"User-Agent": "Educational-RAG-Pipeline/1.0"})
    response.raise_for_status()
    if "html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError("Expected an HTML page")
    title, content = clean_html(response.text)
    if len(content) < 200:
        raise ValueError("Page content is empty or too short")
    now = datetime.now(timezone.utc).isoformat()
    return {"url": url, "source_url": url, "title": title, "date_crawled": now,
            "crawled_at": now, "published_at": None, "publisher": "RMIT University Vietnam",
            "content_type": "university_service_article", "crawl_status": "success",
            "status": "success", "content_markdown": content, "content": content,
            "content_hash": hashlib.sha256(" ".join(content.lower().split()).encode()).hexdigest(),
            "crawler": "requests_beautifulsoup"}


class ArticleHTMLParser(HTMLParser):
    BLOCK_TAGS = {"h1", "h2", "h3", "p", "li"}
    SKIP_TAGS = {"script", "style", "nav", "footer", "form", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_tag = None
        self.current_text = []
        self.blocks = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif not self.skip_depth and tag in self.BLOCK_TAGS:
            self.current_tag, self.current_text = tag, []

    def handle_data(self, data):
        if not self.skip_depth and self.current_tag:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif not self.skip_depth and tag == self.current_tag:
            value = re.sub(r"\s+", " ", " ".join(self.current_text)).strip()
            if len(value) >= 2:
                self.blocks.append((tag, value))
            self.current_tag, self.current_text = None, []


def setup_directory():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


async def crawl_article(url: str) -> dict:
<<<<<<< HEAD
    """Prefer Crawl4AI; fall back to requests + BeautifulSoup."""
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await asyncio.wait_for(crawler.arun(url=url), timeout=TIMEOUT)
        content = str(getattr(result, "markdown", "") or "").strip()
        if len(content) < 200:
            raise ValueError("Crawl4AI returned empty content")
        metadata = getattr(result, "metadata", {}) or {}
        now = datetime.now(timezone.utc).isoformat()
        return {"url": url, "source_url": url, "title": metadata.get("title") or url,
                "date_crawled": now, "crawled_at": now, "published_at": None,
                "publisher": "RMIT University Vietnam", "content_type": "university_service_article",
                "crawl_status": "success", "status": "success", "content_markdown": content,
                "content": content, "content_hash": hashlib.sha256(" ".join(content.lower().split()).encode()).hexdigest(),
                "crawler": "crawl4ai"}
    except Exception as exc:
        LOG.info("Crawl4AI unavailable for %s (%s); using fallback", url, type(exc).__name__)
        return await asyncio.to_thread(crawl_article_requests, url)


async def crawl_all(urls: list[str] | None = None) -> list[dict]:
    setup_directory()
    results: list[dict] = []
    seen: set[str] = set()
    for index, url in enumerate(urls or ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            if article["content_hash"] in seen:
                article["status"] = article["crawl_status"] = "duplicate"
            else:
                seen.add(article["content_hash"])
                path = DATA_DIR / f"rmit-article-{index:02d}.json"
                path.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(article)
        except Exception as exc:
            LOG.warning("crawl failed source_url=%s error_type=%s", url, type(exc).__name__)
            results.append({"url": url, "source_url": url, "crawled_at": datetime.now(timezone.utc).isoformat(),
                            "status": "failed", "crawl_status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(json.dumps(asyncio.run(crawl_all()), ensure_ascii=False, indent=2))
=======
    response = await asyncio.to_thread(
        requests.get,
        url,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0 (educational RAG lab)"},
    )
    response.raise_for_status()
    parser = ArticleHTMLParser()
    parser.feed(response.text)

    title = next((text for tag, text in parser.blocks if tag == "h1"), "Unknown")
    markdown_blocks = []
    for tag, value in parser.blocks:
        prefix = {"h1": "# ", "h2": "## ", "h3": "### ", "li": "- "}.get(tag, "")
        markdown_blocks.append(prefix + value)
    content = "\n\n".join(markdown_blocks)
    if len(content) < 500:
        raise ValueError(f"Crawled content too short ({len(content)} chars): {url}")

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().astimezone().isoformat(),
        "topic": "Du lich Ha Long",
        "content_markdown": content,
    }


async def crawl_all() -> list[Path]:
    setup_directory()
    saved = []
    for index, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)
        path = DATA_DIR / f"ha_long_{index:02d}.json"
        path.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved: {path.name}")
        saved.append(path)
    return saved


if __name__ == "__main__":
    asyncio.run(crawl_all())
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
