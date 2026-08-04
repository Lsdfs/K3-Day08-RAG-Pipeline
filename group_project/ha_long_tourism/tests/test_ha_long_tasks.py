import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from group_project.ha_long_tourism.src import task1_collect_ha_long_docs as task1
from group_project.ha_long_tourism.src import task2_crawl_ha_long_articles as task2
from group_project.ha_long_tourism.src import task3_convert_ha_long_markdown as task3


def response(body=b"%PDF-1.4\n" + b"x" * 1200, content_type="application/pdf", status=200):
    item = Mock(status_code=status, content=body, headers={"Content-Type": content_type})
    item.text = body.decode("utf-8", errors="replace")
    item.raise_for_status.side_effect = requests.HTTPError() if status >= 400 else None
    return item


def source(index=1):
    return {"id":f"halong-legal-{index:03d}","title":"Official document","source_url":"https://example.test/a.pdf",
            "publisher":"Official authority","document_type":"regulation","filename":f"document-{index}.pdf"}


def test_task1_safe_filename_windows_and_traversal():
    assert task1.safe_filename("Hạ Long: Vé 2026.PDF") == "ha-long-ve-2026.pdf"
    assert "/" not in task1.safe_filename("../safe.pdf")


def test_task1_metadata_schema_and_output(tmp_path):
    session=Mock(); session.get.return_value=response()
    item=task1.collect_source(source(),session=session,output_dir=tmp_path,known_hashes=set())
    required={"id","title","source_url","publisher","document_type","file_type","downloaded_at","local_path","http_status","content_type","status","sha256"}
    assert required <= item.keys() and item["status"] == "success"


def test_task1_rejects_html_disguised_as_pdf(tmp_path):
    session=Mock(); session.get.return_value=response(b"<html>error</html>","text/html")
    assert task1.collect_source(source(),session, tmp_path,set())["status"] == "failed"
    assert not list(tmp_path.glob("*.pdf"))


def test_task1_detects_duplicate_and_continues(tmp_path):
    session=Mock(); session.get.side_effect=[response(),response(),response(status=500)]
    seen=set(); results=[task1.collect_source(source(i),session,tmp_path,seen) for i in range(1,4)]
    assert [x["status"] for x in results] == ["success","duplicate","failed"]


HTML="""<html><head><title>Hướng dẫn Hạ Long</title><script>bad()</script><style>x{{}}</style></head>
<body><nav>Menu</nav><main><h1>Hướng dẫn Hạ Long</h1><p>{}</p></main><footer>Footer</footer></body></html>""".format("Thông tin tham quan vịnh Hạ Long. "*20)


def test_task2_clean_html_removes_script_style_navigation():
    title,content,published=task2.clean_html(HTML)
    assert title and "bad()" not in content and "Footer" not in content and published is None


def test_task2_requests_fallback_schema_and_no_fake_date():
    with patch.object(task2.requests,"get",return_value=response(HTML.encode(),"text/html")):
        item=task2.crawl_with_requests({"id":"halong-news-001","url":"https://halongbay.com.vn/x","topic":"visitor_guide"})
    assert item["status"] == "success" and item["source_url"] and item["crawled_at"]
    assert item["published_at"] is None and item["crawler"] == "requests_beautifulsoup"


def test_task2_timeout_is_not_swallowed_as_data():
    with patch.object(task2.requests,"get",side_effect=requests.Timeout):
        with pytest.raises(requests.Timeout):
            task2.crawl_with_requests({"id":"x","url":"https://halongbay.com.vn/x","topic":"x"})


def test_task2_duplicate_hash_detection(tmp_path):
    async def fake(_source):
        return {"id":_source["id"],"title":"x","source_url":_source["url"],"crawled_at":"now","content":"real content",
                "content_hash":"same","status":"success"}
    sources=[{"id":"a","url":"u1"},{"id":"b","url":"u2"}]
    with patch.object(task2,"OUTPUT_DIR",tmp_path/"news"),patch.object(task2,"REPORT_PATH",tmp_path/"report.json"),patch.object(task2,"crawl_article",fake):
        report=asyncio.run(task2.crawl_all(sources))
    assert report["successful"] == 1 and report["duplicate_pages"] == 1


def _article(identifier="halong-news-001"):
    return {"id":identifier,"title":"Hướng dẫn tham quan Vịnh Hạ Long","source_url":"https://halongbay.com.vn/p/1",
            "publisher":"Ban Quản lý Vịnh Hạ Long","crawled_at":"2026-01-01T00:00:00Z","language":"vi",
            "content_type":"tourism_article","topic":"visitor_guide","content":"Thông tin thực tế về tham quan Vịnh Hạ Long. "*10}


def test_task3_json_frontmatter_utf8_and_structure(tmp_path):
    landing=tmp_path/"landing"; (landing/"news").mkdir(parents=True); (landing/"legal").mkdir()
    (landing/"news"/"article.json").write_text(json.dumps(_article(),ensure_ascii=False),encoding="utf-8")
    output=tmp_path/"standardized"
    with patch.object(task3,"SOURCES_PATH",tmp_path/"missing.json"),patch.object(task3,"REPORT_PATH",tmp_path/"report.json"):
        report=task3.convert_all(landing,output)
    rendered=(output/"news"/"article.md").read_text(encoding="utf-8")
    assert report["successful_files"] == 1 and rendered.startswith("---")
    assert "source_url:" in rendered and "Vịnh Hạ Long" in rendered
    assert (output/"news").is_dir() and (output/"legal").is_dir() is False


def test_task3_corrupt_file_does_not_stop_batch(tmp_path):
    landing=tmp_path/"landing"/"news"; landing.mkdir(parents=True)
    (landing/"bad.json").write_text("{",encoding="utf-8")
    (landing/"good.json").write_text(json.dumps(_article("good"),ensure_ascii=False),encoding="utf-8")
    with patch.object(task3,"SOURCES_PATH",tmp_path/"none"),patch.object(task3,"REPORT_PATH",tmp_path/"report.json"):
        report=task3.convert_all(tmp_path/"landing",tmp_path/"standardized")
    assert report["total_files"] == 2 and report["successful_files"] == 1 and report["failed_files"] == 1


def test_task3_empty_content_creates_no_markdown(tmp_path):
    landing=tmp_path/"landing"/"news"; landing.mkdir(parents=True)
    item=_article(); item["content"]=""
    (landing/"empty.json").write_text(json.dumps(item),encoding="utf-8")
    with patch.object(task3,"SOURCES_PATH",tmp_path/"none"),patch.object(task3,"REPORT_PATH",tmp_path/"report.json"):
        report=task3.convert_all(tmp_path/"landing",tmp_path/"standardized")
    assert report["empty_files"] == 1 and not list((tmp_path/"standardized").rglob("*.md"))
