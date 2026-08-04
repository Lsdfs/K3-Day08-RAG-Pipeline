# Hạ Long Travel RAG Chatbot

Chatbot hỏi đáp tiếng Việt trên kho tư liệu Vịnh Hạ Long. Hệ thống kết hợp
dense retrieval, BM25, RRF/reranking, fallback vectorless, sinh câu trả lời có
citation, conversation memory và giao diện web hiển thị nguồn/điểm số.

## Kiến trúc

```text
Browser (HTML/CSS/JS)
  ├─ history + follow-up questions
  └─ POST /api/chat
          │
          ▼
Flask API (app.py)
          │
          ▼
Generation + citations (Task 10)
          │
          ▼
Retrieval pipeline (Task 9)
  ├─ Semantic search (Task 5) ─┐
  ├─ BM25 lexical (Task 6) ────┼─ RRF + rerank (Task 7)
  └─ low dense score ──────────┘
             └─ PageIndex API / local vectorless fallback (Task 8)
          │
          ▼
Markdown corpus → chunks → ChromaDB (Tasks 3–4)
```

## Thành phần

| Thành phần | File | Trạng thái |
|---|---|---|
| Thu thập PDF và bài viết | `src/task1_*`, `src/task2_*` | Hoàn thành |
| Chuẩn hóa Markdown | `src/task3_convert_markdown.py` | Hoàn thành |
| Chunking/indexing | `src/task4_chunking_indexing.py` | Hoàn thành |
| Dense + lexical retrieval | `src/task5_*`, `src/task6_*` | Hoàn thành |
| Rerank + fallback + pipeline | `src/task7_*` đến `src/task9_*` | Hoàn thành |
| Generation/citation/memory | `src/task10_generation.py` | Hoàn thành |
| Flask UI và source cards | `app.py`, `web/` | Hoàn thành |
| Evaluation 4 metrics và A/B | `evaluation/` | Hoàn thành |

## Phân công

Repo được tích hợp từ các nhánh thành viên; cần thay tên/MSSV bên dưới bằng
thông tin chính thức trước khi nộp nếu giảng viên yêu cầu MSSV.

| Thành viên/nhánh | Nhiệm vụ | Trạng thái |
|---|---|---|
| DinhKhoa | Data, conversion, chunking/indexing | Hoàn thành |
| vietnguyen | Corpus Hạ Long, index và golden dataset | Hoàn thành |
| zoanh | Flask UI/UX, memory và source display | Hoàn thành |
| Chu Thi Yen Khanh | Integration, retrieval, generation và evaluation | Hoàn thành |

## Chạy dự án

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Mở <http://127.0.0.1:8000>. Không có API key, chatbot vẫn trả lời extractive
có citation. Muốn dùng LLM, đặt `ENABLE_LLM_GENERATION=1` và cấu hình
`OPENROUTER_API_KEY` hoặc `OPENAI_API_KEY`.

## Kiểm thử và evaluation

```powershell
python -m pytest tests -v
python group_project/evaluation/eval_pipeline.py
```

Evaluation dùng 20 golden cases, bốn metrics (Faithfulness, Answer Relevance,
Context Recall, Context Precision) và so sánh:

- Config A: hybrid retrieval + reranking.
- Config B: dense-only retrieval.

Kết quả, phân tích ba trường hợp kém nhất và recommendations nằm trong
[`evaluation/results.md`](evaluation/results.md).

## Biến môi trường

| Biến | Mục đích | Bắt buộc |
|---|---|---|
| `ENABLE_LLM_GENERATION` | Bật sinh câu trả lời bằng LLM | Không |
| `OPENROUTER_API_KEY` / `OPENAI_API_KEY` | LLM generation | Không |
| `PAGEINDEX_API_KEY` | PageIndex remote fallback | Chỉ khi demo API thật |
| `PAGEINDEX_DOC_ID` | Document đã upload trên PageIndex | Chỉ khi demo API thật |

## Hạn chế đã biết

- Chất lượng một số đoạn PDF chịu ảnh hưởng bởi OCR.
- Khi không có embedding dependencies/index, semantic module dùng fallback
  lexical-semantic để ứng dụng vẫn demo được.
- PageIndex remote cần tài khoản, API key và document đã upload; local fallback
  giữ pipeline hoạt động khi không có credential.
