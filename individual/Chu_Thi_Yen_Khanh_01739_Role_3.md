# Bài cá nhân — Role 3: Vector Database & Dense Search

| Thông tin | Giá trị |
|---|---|
| Họ và tên | Chu Thị Yến Khanh |
| MSSV | 2A202601739 (01739) |
| Vai trò | Role 3 — Vector Database & Dense Search Developer |
| Phạm vi thực hiện | Task 4: Chunking & Indexing; Task 5: Semantic Search + Query Expansion |

## 1. Task 4 — Chunking & Indexing

File thực hiện: `src/task4_chunking_indexing.py`.

- Đọc tài liệu Markdown đã chuẩn hóa từ `data/standardized/` và giữ metadata nguồn.
- Chia tài liệu thành chunks với `CHUNK_SIZE=800` và `CHUNK_OVERLAP=100`.
- Tạo embedding, lưu/chạy truy vấn với ChromaDB trong `chroma_db/`.
- Có cơ chế fallback để pipeline vẫn hoạt động khi embedding service hoặc vector store không sẵn sàng.

## 2. Task 5 — Semantic Search và Query Expansion

File thực hiện: `src/task5_semantic_search.py`.

- `semantic_search(query, top_k)` trả về các chunks theo điểm giảm dần, gồm `content`, `score`, `metadata` và `source`.
- Khi ChromaDB và embedder sẵn sàng, hệ thống dùng dense retrieval trên embedding đã chuẩn hóa.
- Khi không sẵn sàng, hệ thống dùng token-overlap fallback để không làm ngắt pipeline.
- `expand_query(query)` thực hiện Query Expansion offline trước dense retrieval để tăng recall với alias/thuật ngữ cùng domain Hạ Long.

Ví dụ mở rộng:

| Trigger | Terms được thêm |
|---|---|
| `unesco` | `di san thien nhien the gioi`, `world heritage` |
| `địa chất` | `karst`, `đá vôi`, `kiến tạo` |
| `ô nhiễm` | `môi trường`, `chất lượng nước`, `e.coli` |

## 3. Kiểm chứng

Chạy từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_individual.py -q
```

Kết quả xác nhận tại thời điểm bàn giao: **35 passed**. Các kiểm thử liên quan trực tiếp đến Role 3 gồm Task 4 (chunking/indexing) và Task 5 (semantic search).

## 4. Cách demo

```powershell
.\.venv\Scripts\python.exe -c "from src.task5_semantic_search import expand_query; print(expand_query('UNESCO'))"
```

Lệnh trên cho thấy truy vấn được mở rộng trước khi semantic search. Có thể tiếp tục chạy `semantic_search()` để quan sát danh sách chunks, score và metadata nguồn.
