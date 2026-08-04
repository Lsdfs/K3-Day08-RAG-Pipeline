"""Web server cho Hạ Long Travel RAG Chatbot.

Chạy local:
    python app.py
Sau đó mở http://127.0.0.1:8000

Lớp này chỉ lo giao diện/API. Logic RAG vẫn nằm trong src/task10_generation.py.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys

from flask import Flask, jsonify, request, send_from_directory


PROJECT_ROOT = Path(__file__).parent
WEB_DIR = PROJECT_ROOT / "web"
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("message", "")).strip()
    top_k = payload.get("top_k", 5)
    history = payload.get("history", [])

    if not query:
        return jsonify({"error": "Vui lòng nhập câu hỏi."}), 400

    try:
        top_k = max(3, min(int(top_k), 10))
        if not isinstance(history, list):
            history = []
        safe_history = [item for item in history[-6:] if isinstance(item, dict)
                        and item.get("role") in {"user", "assistant"}]
        retrieval_query = query
        follow_up_markers = ("nó", "đó", "nơi này", "ở đây", "thế còn", "còn gì")
        if any(marker in query.lower() for marker in follow_up_markers):
            previous = next((str(item.get("content", "")) for item in reversed(safe_history)
                             if item.get("role") == "user" and item.get("content")), "")
            if previous:
                retrieval_query = f"{previous}\nCâu hỏi tiếp theo: {query}"

<<<<<<< HEAD
    if st.button("🗑️ Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

    if not (PROJECT_ROOT / "chroma_db").exists():
        st.warning("Chưa có index. Chạy `python -m src.task4_chunking_indexing`.")
    if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")):
        st.info("Chưa cấu hình API key LLM; ứng dụng sẽ dùng câu trả lời extractive local.")

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")
=======
        from src.task10_generation import generate_with_citation
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14

        result = generate_with_citation(retrieval_query, top_k=top_k)
        return jsonify({
            "answer": result.get("answer", "Chưa thể tạo câu trả lời."),
            "sources": result.get("sources", []),
            "retrieval_source": result.get("retrieval_source", "hybrid"),
        })
    except Exception:  # Chi tiết lỗi chỉ nằm trong server log.
        app.logger.exception("RAG chat request failed")
        return jsonify({"error": "Không thể kết nối RAG pipeline. Vui lòng thử lại."}), 500


@app.get("/api/health")
def health():
    from src.task4_chunking_indexing import load_documents
    return jsonify({"status": "ok", "documents": len(load_documents())})


<<<<<<< HEAD
# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Unknown")
                    doc_type = meta.get("type", "unknown")
                    score = src.get("score", 0)
                    st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:300] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

# Xử lý khi bấm nút gợi ý hoặc nhập câu hỏi mới
user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách/dịch vụ đại học...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy hoàn thành `src/task10_generation.py` để kết nối pipeline vào UI!"
                sources = []
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:300] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
=======
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("FLASK_DEBUG", "0") == "1")
>>>>>>> 173f144f03a85668d76317c5d406a5e8a4bf7b14
