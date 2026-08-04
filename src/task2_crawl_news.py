"""Task 2: Crawl five public articles about Ha Long tourism."""

import asyncio
import json
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
]


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
