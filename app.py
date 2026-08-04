"""Web server cho Hạ Long Travel RAG Chatbot.

Chạy local:
    python app.py
Sau đó mở http://127.0.0.1:8000

Lớp này chỉ lo giao diện/API. Logic RAG vẫn nằm trong src/task10_generation.py.
"""

from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory


PROJECT_ROOT = Path(__file__).parent
WEB_DIR = PROJECT_ROOT / "web"
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("message", "")).strip()
    top_k = payload.get("top_k", 5)

    if not query:
        return jsonify({"error": "Vui lòng nhập câu hỏi."}), 400

    try:
        top_k = max(3, min(int(top_k), 10))
        from src.task10_generation import generate_with_citation

        result = generate_with_citation(query, top_k=top_k)
        return jsonify({
            "answer": result.get("answer", "Chưa thể tạo câu trả lời."),
            "sources": result.get("sources", []),
            "retrieval_source": result.get("retrieval_source", "hybrid"),
        })
    except NotImplementedError:
        return jsonify({
            "error": "RAG pipeline chưa hoàn thiện. Hãy implement Task 10 để chatbot trả lời từ tài liệu.",
        }), 503
    except Exception as exc:  # Giữ lỗi kỹ thuật ở server, trả thông báo rõ ràng cho UI.
        app.logger.exception("RAG chat request failed")
        return jsonify({"error": f"Không thể kết nối RAG pipeline: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
