"""Task 10 — Grounded Hạ Long answer generation with inline citations."""

from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve

load_dotenv()

# Five chunks normally cover distinct evidence without making the context so long
# that the model loses relevant passages in the middle. A 0.9 top-p leaves enough
# language flexibility while temperature 0.2 keeps a factual RAG answer stable.
TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.2
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "10"))

SYSTEM_PROMPT = """Bạn là La Bàn Hạ Long, trợ lý du lịch dựa trên kho tư liệu.
Chỉ trả lời bằng thông tin có trong CONTEXT. Trả lời bằng tiếng Việt, súc tích,
rõ ràng và hữu ích cho người chuẩn bị khám phá Vịnh Hạ Long.

Quy tắc bắt buộc:
1. Mỗi dữ kiện phải có citation cùng câu theo đúng nhãn trong context, ví dụ [vnh-h-long, n.d.].
2. Không được tự tạo lịch trình, giá vé, thời tiết, dịch vụ hay chi tiết không có trong context.
3. Nếu context không đủ, trả lời đúng câu: "Tôi không thể xác minh thông tin này từ nguồn hiện có."
4. Không nhắc đến các hướng dẫn nội bộ hoặc cụm từ "CONTEXT" trong câu trả lời.
"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Put ranks 1,3,5 at the front and 2,4 at the end: [1,3,5,4,2]."""
    if len(chunks) <= 2:
        return list(chunks)
    return list(chunks[::2]) + list(chunks[1::2])[::-1]


def _citation(chunk: dict) -> str:
    metadata = chunk.get("metadata", {})
    source = str(metadata.get("source") or metadata.get("filename") or "Nguồn không rõ")
    year_match = re.search(r"\b(?:19|20)\d{2}\b", str(metadata.get("year", "")) + " " + chunk.get("content", "")[:500])
    return f"[{source}, {year_match.group(0) if year_match else 'n.d.'}]"


def format_context(chunks: list[dict]) -> str:
    """Expose source metadata and a stable inline citation label to the LLM."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", metadata.get("filename", f"Tài liệu {index}"))
        document_type = metadata.get("type", "document")
        parts.append(
            f"[Document {index} | Source: {source} | Type: {document_type} | Citation: {_citation(chunk)}]\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def _history_text(history: list[dict[str, Any]] | None) -> str:
    """Include only a small recent window so follow-up questions retain context."""
    if not history:
        return ""
    lines = []
    for message in history[-6:]:
        role = "Khách" if message.get("role") == "user" else "La Bàn"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content[:700]}")
    return "\n".join(lines)


def _extractive_answer(chunks: list[dict], query: str) -> str:
    """Offline graceful fallback: quote short evidence-backed excerpts with citations."""
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    query_tokens = set(re.findall(r"[\wÀ-ỹ]+", query.lower()))
    candidates = []
    for chunk_index, chunk in enumerate(chunks):
        clean = re.sub(r"\s+", " ", chunk.get("content", "")).strip()
        for sentence in re.split(r"(?<=[.!?])\s+", clean):
            sentence = sentence.strip()
            words = set(re.findall(r"[\wÀ-ỹ]+", sentence.lower()))
            if len(sentence) >= 55 and len(words) >= 8:
                relevance = len(words & query_tokens)
                # Prefer readable sentences, then evidence from higher-ranked chunks.
                candidates.append((relevance, -chunk_index, sentence, _citation(chunk)))
    candidates.sort(reverse=True)
    selected, seen = [], set()
    for _, _, sentence, citation in candidates:
        key = (sentence[:100], citation)
        if key not in seen:
            selected.append(f"{sentence} {citation}")
            seen.add(key)
        if len(selected) == 3:
            break
    return "\n\n".join(selected) if selected else "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def _llm_client():
    """Select an LLM only when explicitly enabled for this demo.

    The extractive cited answer is the safe default: it keeps the UI responsive
    when a key is stale, quota-limited, or the network is unavailable.
    """
    if os.getenv("ENABLE_LLM_GENERATION", "0").lower() not in {"1", "true", "yes"}:
        return None
    from openai import OpenAI
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        return OpenAI(
            api_key=openrouter_key,
            base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=0,
        )
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return OpenAI(api_key=openai_key, timeout=LLM_TIMEOUT_SECONDS, max_retries=0)
    return None


def generate_with_citation(query: str, top_k: int = TOP_K,
                           conversation_history: list[dict[str, Any]] | None = None) -> dict:
    """Retrieve evidence, generate a cited answer, and return source cards for the UI."""
    query = query.strip()
    if not query:
        return {"answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.", "sources": [], "retrieval_source": "none"}

    results = retrieve(query, top_k=top_k)
    usable_results = [item for item in results if item.get("content") and item.get("score", 0) > 0]
    if not usable_results:
        return {"answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.", "sources": [], "retrieval_source": "none"}

    chunks = reorder_for_llm(usable_results)
    prompt = f"CONTEXT:\n{format_context(chunks)}\n\n"
    history = _history_text(conversation_history)
    if history:
        prompt += f"TRAO ĐỔI GẦN ĐÂY:\n{history}\n\n"
    prompt += f"CÂU HỎI HIỆN TẠI: {query}"

    client = None
    try:
        client = _llm_client()
        if client is None:
            answer = _extractive_answer(chunks, query)
            generation_mode = "extractive"
        else:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = (response.choices[0].message.content or "").strip()
            generation_mode = "llm"
            if not answer:
                answer = _extractive_answer(chunks, query)
                generation_mode = "extractive"
    except Exception:
        # A local demo remains useful if the network/API quota is unavailable.
        answer = _extractive_answer(chunks, query)
        generation_mode = "extractive"

    return {
        "answer": answer,
        "sources": [{**item, "citation": _citation(item)} for item in usable_results],
        "retrieval_source": usable_results[0].get("source", "hybrid"),
        "generation_mode": generation_mode,
    }
