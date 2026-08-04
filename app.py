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

        from src.task10_generation import generate_with_citation

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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("FLASK_DEBUG", "0") == "1")
