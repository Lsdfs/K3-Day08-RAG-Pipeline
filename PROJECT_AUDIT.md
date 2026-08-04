# PROJECT AUDIT — RAG Pipeline và dữ liệu Du lịch Hạ Long

## Executive Summary

Mục tiêu là hoàn thiện Individual Task 1–10 cho chủ đề University Services/RMIT và Group Task 1–3 cho chủ đề Du lịch Hạ Long, giữ hai dataset tách biệt. Ban đầu repository chủ yếu là scaffold: 7 test pass, 4 fail, 24 skip; chưa có dữ liệu và các Task 4–10 còn `NotImplementedError`. Trạng thái cuối: dữ liệu thật đã được tải/crawl/chuẩn hóa, pipeline local chạy end-to-end, Streamlit trả HTTP 200 và toàn bộ 67 test pass.

ChromaDB/BGE-M3 chưa được chạy thật vì hai lần cài dependency nặng timeout trong môi trường hiện tại. Task 4 đã có code ưu tiên Chroma/BGE nhưng lần E2E được ghi đúng là persistent local hashing-vector fallback. PageIndex live API là `BLOCKED` vì không có `PAGEINDEX_API_KEY`; không có kết quả PageIndex giả.

## Initial Audit

| Hạng mục | Phạm vi | Trạng thái trước | Vấn đề | Hành động |
|---|---|---:|---|---|
| Individual Task 1 | Cá nhân | FAIL | Không có downloader/dữ liệu | Downloader retry, MIME/signature, metadata; tải 3 PDF RMIT |
| Individual Task 2 | Cá nhân | FAIL | URL rỗng, crawler chưa làm | Crawl4AI ưu tiên, requests/BS4 fallback; crawl 5 trang |
| Individual Task 3 | Cá nhân | FAIL | Converter chưa làm | Batch converter, provenance, report, PDF fallback |
| Individual Task 4 | Cá nhân | FAIL | Load/chunk/embed/index chưa làm | Chunk ổn định, upsert, BGE/Chroma ưu tiên, local fallback |
| Individual Task 5 | Cá nhân | FAIL | `NotImplementedError` | Validate, cosine similarity, missing-index handling |
| Individual Task 6 | Cá nhân | FAIL | `NotImplementedError` | Cached BM25 và Unicode tokenization |
| Individual Task 7 | Cá nhân | FAIL | Mọi reranker chưa làm | Jina optional + retry/timeout + local heuristic/MMR/RRF |
| Individual Task 8 | Cá nhân | BLOCKED | Chưa có code/API key | Upload manifest, query parser, no-key safe state |
| Individual Task 9 | Cá nhân | FAIL | Pipeline chưa làm | Hybrid fusion, dedupe, confidence fallback, latency |
| Individual Task 10 | Cá nhân | FAIL | Reorder/generation chưa làm | Grounded citations, injection boundary, API/local fallback |
| Group Task 1 | Hạ Long | FAIL | Chưa có package/dữ liệu | Tải 3 PDF chính thống, SHA-256 và report |
| Group Task 2 | Hạ Long | FAIL | Chưa có crawler/dữ liệu | Crawl hữu hạn 5 trang Ban Quản lý Vịnh Hạ Long |
| Group Task 3 | Hạ Long | FAIL | Chưa có converter/output | 8 Markdown có front matter và report |

Initial test results: **7 passed, 4 failed, 24 skipped, 0 errors**.

## Individual Task Status

| Task | Before | After | Evidence |
|---|---:|---:|---|
| 1 | FAIL | PASS | 3 PDF thật + `data/landing/legal/sources.json` |
| 2 | FAIL | PASS | 5 JSON thật có URL/crawl time/content hash |
| 3 | FAIL | PASS | 8 Markdown; report 8 success, 0 fail |
| 4 | FAIL | PARTIAL | 8 documents/464 chunks; local persistent fallback chạy, Chroma/BGE chưa chạy thật |
| 5 | FAIL | PASS | Semantic output/schema/sort/validation tests |
| 6 | FAIL | PASS | Cached BM25, corpus thật, Vietnamese test |
| 7 | FAIL | PASS | Dedupe, score/rank, API timeout fallback tests |
| 8 | BLOCKED | BLOCKED | Code hoàn thiện; thiếu API key nên live API chưa test |
| 9 | FAIL | PASS | Hybrid E2E, failure isolation, PageIndex fallback tests |
| 10 | FAIL | PASS | Local grounded answer, source-bound citation, insufficient-evidence tests |

## Ha Long Group Task Status

| Task | Before | After | Evidence |
|---|---:|---:|---|
| Group Task 1 | FAIL | PASS | `collection_report.json`: 3 success, 0 fail, 0 duplicate |
| Group Task 2 | FAIL | PASS | `crawl_report.json`: 5 success, 0 fail/empty/duplicate |
| Group Task 3 | FAIL | PASS | 8 Markdown hiện hữu; front matter + UTF-8 tests |

Group Task 4+ không được triển khai.

## Ha Long Dataset Summary

```text
Legal documents downloaded: 3
Tourism pages crawled: 5
Markdown files generated/present: 8
Failed sources: 0
Duplicate sources: 0
Empty sources: 0
```

### Source Quality

| ID | Title | Publisher | Quality | Status |
|---|---|---|---|---|
| halong-legal-001 | Management Plan 2021–2025 | UNESCO World Heritage Centre | UNESCO/international authority | success |
| halong-legal-002 | Kế hoạch quản lý rừng đặc dụng Vịnh Hạ Long 2024 | Ban Quản lý Vịnh Hạ Long | Official management authority | success |
| halong-legal-003 | Kế hoạch vùng vui chơi giải trí trên Vịnh | Ban Quản lý Vịnh Hạ Long | Official management authority | success |
| halong-news-001 | Mức phí tham quan Vịnh Hạ Long | Ban Quản lý Vịnh Hạ Long | Official tourism portal | success |
| halong-news-002 | Quy định sử dụng vé tham quan | Ban Quản lý Vịnh Hạ Long | Official tourism portal | success |
| halong-news-003 | Miễn, giảm phí tham quan | Ban Quản lý Vịnh Hạ Long | Official tourism portal | success |
| halong-news-004 | Siết chặt an toàn tàu du lịch | Ban Quản lý Vịnh Hạ Long | Official tourism portal | success |
| halong-news-005 | Khám phá đảo Bồ Hòn | Ban Quản lý Vịnh Hạ Long | Official tourism portal | success |

URL và local path đầy đủ nằm trong `sources.json`, `collection_report.json` và `crawl_report.json`; không liệt kê nguồn lỗi như nguồn thành công.

## Bugs Fixed

- `src/task1_collect_legal_docs.py`: downloader mẫu không timeout/status/type check; thay bằng retry hữu hạn, signature validation và batch isolation. Xác minh bằng tải thật và file PDF signature.
- `src/task2_crawl_news.py`: URL rỗng và chỉ phụ thuộc browser; thêm danh sách chính thức, content cleaning và requests/BeautifulSoup fallback. Xác minh 5 JSON.
- `src/task3_convert_markdown.py`: dừng ở file đầu; chuyển sang per-file error handling và report. MarkItDown không cài được nên ghi đúng `pypdf_fallback`.
- `src/task4_chunking_indexing.py`: chunk ID không tồn tại; thêm SHA-256 ổn định, dedupe và upsert. Xác minh index hai lần không tăng bản ghi.
- `src/task5_semantic_search.py`: nhầm đường chạy chưa index; thêm validation và cosine distance → similarity.
- `src/task6_lexical_search.py`: build lại/không hỗ trợ tiếng Việt; thêm cache và tokenizer Unicode.
- `src/task7_reranking.py`: không có fallback; thêm Jina timeout/retry và local reranking giữ metadata.
- `src/task8_pageindex_vectorless.py`: query/upload lẫn nhau; tách manifest upload khỏi query và trả `[]` khi thiếu key.
- `src/task9_retrieval_pipeline.py`: nguy cơ dùng RRF để threshold; dùng semantic/rerank confidence, cách ly lỗi từng retriever và ghi latency.
- `src/task10_generation.py`: chưa chống prompt injection/citation giả; định ranh giới DATA, kiểm citation với metadata và exact insufficient-evidence response.
- `app.py`: thêm clear conversation, cảnh báo chưa index/API key và local fallback.

## End-to-End Result

Query thực chạy: `RMIT Việt Nam thanh toán học phí bằng những phương thức nào?`

```text
Semantic candidates: 10
Lexical candidates: 10
Fused candidates: 10
Top/rerank score: 0.1915846994535519
Fallback triggered: false
Citation source: legal/rmit-student-fees-and-charges-guide-2026.md
Stage latency: semantic 126.71 ms; lexical 39.92 ms; fusion 0.25 ms; rerank 0.57 ms
Total measured latency including generation: 2444.59 ms
```

Answer được sinh extractive từ context, không hardcode. Terminal PowerShell hiện tại hiển thị dấu tiếng Việt trong query thành `?` khi pipe here-string; file UTF-8 và unit test Vietnamese vẫn đúng.

## Commands Executed

Các lệnh chính đã thực sự chạy:

```powershell
python -m pytest -v
python -m pip install beautifulsoup4
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
python -m group_project.ha_long_tourism.src.task1_collect_ha_long_docs
python -m group_project.ha_long_tourism.src.task2_crawl_ha_long_articles
python -m group_project.ha_long_tourism.src.task3_convert_ha_long_markdown
python -m pytest group_project/ha_long_tourism/tests -v
python -m pytest -q
python -m streamlit run app.py --server.headless=true --server.port=8765
```

`pip install "markitdown[pdf]>=0.1.0"` và `pip install chromadb rank-bm25` đã được thử nhưng timeout; không được ghi nhận là cài thành công.

## Test Results

```text
Individual + robustness + Ha Long group:
Passed: 67
Failed: 0
Skipped: 0

Streamlit startup:
HTTP status: 200
```

## Remaining Limitations

- ChromaDB, Sentence Transformers/BGE-M3 và MarkItDown chưa có trong runtime hiện tại; code ưu tiên chúng nhưng E2E dùng fallback có ghi nhãn.
- PageIndex live API chưa test vì thiếu API key (`BLOCKED`).
- Crawl4AI không có trong runtime; crawl thật dùng requests/BeautifulSoup fallback.
- Một số PDF có layout bảng phức tạp nên extraction bằng pypdf có thể không giữ bảng hoàn hảo.
- Website nguồn có thể đổi URL/HTML hoặc áp dụng chặn crawler trong tương lai.
- Group Task 4+ nằm ngoài phạm vi.

## Final Checklist

- [x] Đã đọc repository và rubric
- [x] Đã chạy test ban đầu
- [x] Individual Task 1–3 hoàn thành
- [x] Individual Task 4–7 có implementation và fallback chạy thật
- [x] Individual Task 8 có fallback rõ ràng; live API `BLOCKED`
- [x] Individual Task 9–10 hoàn thành
- [x] Group Task 1–3 Hạ Long hoàn thành
- [x] Dữ liệu Hạ Long tách riêng
- [x] Nguồn Hạ Long có thể kiểm chứng
- [x] Không có dữ liệu giả/Markdown rỗng/secret phát hiện được
- [x] Tests và Streamlit startup đã chạy
- [x] README đã cập nhật
- [x] Group Task 4+ không triển khai
