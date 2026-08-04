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

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|---|---|---|---|
| Chu Thị Yến Khanh | 2A202601739 | Role 1 — Team Leader & RAG Architect | Hoàn thành |
| Nguyễn Quang Huy | 2A202601873 | Role 2 — Data Engineering & Scraping Dev | Hoàn thành |
| Trương Đình Khoa | 2A202601297 | Role 3 — Vector Database & Dense Search Dev | Hoàn thành |
| Lương Đăng Doanh | 2A202601209 | Role 4 — Sparse Retrieval & Fallback Dev | Hoàn thành |
| Nguyễn Quốc Việt | 2A202601737 | Role 5 — Frontend UI & App Integration Dev | Hoàn thành |
| Vũ Quang Tùng | 2A202601545 | Role 6 — Evaluation & Benchmark QA Dev | Hoàn thành |

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

## Deploy trên Render

Repo có sẵn `render.yaml` và `requirements-deploy.txt` để deploy nhẹ, không tải
Torch/Chroma/RAGAS trên web service. Quy trình:

1. Push branch `main` lên GitHub.
2. Trên Render chọn **New → Blueprint** và kết nối repository này.
3. Render tự đọc `render.yaml`; chọn **Apply**.
4. Chờ health check `/api/health` chuyển sang trạng thái **Live**.
5. Mở URL dạng `https://ha-long-rag-chatbot.onrender.com` và lưu URL vào báo cáo.

App mặc định dùng extractive generation, local retrieval và không cần secret.
Nếu bật LLM, thêm `OPENROUTER_API_KEY` hoặc `OPENAI_API_KEY` trong Render
Environment; không đưa key vào Git.

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
