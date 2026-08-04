"""Group Task 2: crawl finite, official Ha Long tourism pages."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "data" / "landing" / "news"
REPORT_PATH = PROJECT_DIR / "reports" / "crawl_report.json"
TIMEOUT = 30
LOG = logging.getLogger(__name__)
ARTICLE_SOURCES = [
    {"id":"halong-news-001","url":"https://halongbay.com.vn/vi/p/58-muc-phi-tham-quan-vinh-ha-long","topic":"ticket_policy"},
    {"id":"halong-news-002","url":"https://halongbay.com.vn/p/59-quy-dinh-chung-trong-viec-su-dung-ve-tham-quan-vinh-ha-long","topic":"ticket_rules"},
    {"id":"halong-news-003","url":"https://halongbay.com.vn/p/57-mien-giam-phi-tham-quan-vinh-ha-long","topic":"ticket_exemptions"},
    {"id":"halong-news-004","url":"https://halongbay.com.vn/vi/p/708-siet-chat-an-toan-tau-du-lich-ngay-tu-goc","topic":"tourism_safety"},
    {"id":"halong-news-005","url":"https://halongbay.com.vn/p/290-kham-pha-dao-bo-hon","topic":"visitor_guide"},
]


def clean_html(html: str) -> tuple[str, str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script,style,noscript,nav,footer,header,aside,form,.cookie,.breadcrumb,.related"):
        node.decompose()
    title_node = soup.select_one("h1") or soup.title
    title = title_node.get_text(" ", strip=True) if title_node else ""
    main = soup.select_one("main,article,.detail-content,.content") or soup.body or soup
    content = "\n".join(x.strip() for x in main.get_text("\n").splitlines() if x.strip())
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    published = None
    time_node = soup.select_one("time[datetime]")
    if time_node: published = time_node.get("datetime") or None
    return title, content, published


def crawl_with_requests(source: dict) -> dict:
    response = requests.get(source["url"], timeout=TIMEOUT, allow_redirects=True,
        headers={"User-Agent":"HaLong-Educational-RAG/1.0"}); response.raise_for_status()
    if "html" not in response.headers.get("Content-Type", "").lower(): raise ValueError("expected HTML")
    title, content, published = clean_html(response.text)
    if not title or len(content) < 200: raise ValueError("empty or too-short article")
    now = datetime.now(timezone.utc).isoformat(); digest = hashlib.sha256(" ".join(content.lower().split()).encode()).hexdigest()
    return {"id":source["id"],"title":title,"source_url":source["url"],"publisher":"Ban Quản lý Vịnh Hạ Long",
        "published_at":published,"crawled_at":now,"language":"vi","content_type":"tourism_article",
        "topic":source["topic"],"content":content,"content_hash":digest,"status":"success","crawler":"requests_beautifulsoup"}


async def crawl_article(source: dict) -> dict:
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await asyncio.wait_for(crawler.arun(url=source["url"]), timeout=TIMEOUT)
        content = str(getattr(result,"markdown","") or "").strip()
        if len(content) < 200: raise ValueError("empty Crawl4AI result")
        meta = getattr(result,"metadata",{}) or {}; now = datetime.now(timezone.utc).isoformat()
        return {"id":source["id"],"title":meta.get("title") or source["url"],"source_url":source["url"],
            "publisher":"Ban Quản lý Vịnh Hạ Long","published_at":meta.get("published_time") or None,
            "crawled_at":now,"language":"vi","content_type":"tourism_article","topic":source["topic"],
            "content":content,"content_hash":hashlib.sha256(" ".join(content.lower().split()).encode()).hexdigest(),
            "status":"success","crawler":"crawl4ai"}
    except Exception as exc:
        LOG.info("Crawl4AI fallback source_url=%s error_type=%s", source["url"], type(exc).__name__)
        return await asyncio.to_thread(crawl_with_requests, source)


async def crawl_all(sources: list[dict] | None = None) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); seen=set(); results=[]
    for source in sources or ARTICLE_SOURCES:
        try:
            item=await crawl_article(source)
            if item["content_hash"] in seen: item["status"]="duplicate"
            else:
                seen.add(item["content_hash"]); (OUTPUT_DIR/f"{item['id']}.json").write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding="utf-8")
        except Exception as exc:
            item={"id":source.get("id"),"source_url":source.get("url"),"crawled_at":datetime.now(timezone.utc).isoformat(),"status":"failed","error_type":type(exc).__name__,"error":str(exc)}
        results.append(item)
    report={"total_urls":len(results),"successful":sum(x["status"]=="success" for x in results),"failed":sum(x["status"]=="failed" for x in results),
        "empty_pages":sum(x.get("error_type")=="ValueError" for x in results),"duplicate_pages":sum(x["status"]=="duplicate" for x in results),"results":results}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); print(json.dumps(asyncio.run(crawl_all()),ensure_ascii=False,indent=2))
