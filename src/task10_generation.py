"""Task 10 — Generation with Citations."""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve

TOP_K = 8  # More context = better answers
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")  # cheapest, $0.15/1M input
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")

SYSTEM_PROMPT = """Answer questions based on the provided context. Use the data given.
Rules:
- Answer in Vietnamese unless asked in English
- Use specific numbers and facts from the context
- If the context has partial info, answer with what you have and note what's missing
- Only say 'cannot verify' if the context is completely unrelated
- Cite sources as [Document N]
"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Reorder to combat 'lost in the middle': top at start/end, middle at center."""
    if len(chunks) <= 2:
        return chunks
    result = []
    for i in range(0, len(chunks), 2):
        result.append(chunks[i])
    for i in range(len(chunks) - 1, 0, -2):
        if i < len(chunks):
            result.append(chunks[i])
    return result


def format_context(chunks: list[dict]) -> str:
    """Format chunks into a context string with source labels."""
    parts = []
    for i, chunk in enumerate(chunks):
        source = chunk.get("metadata", {}).get("source", "unknown")
        ctype = chunk.get("metadata", {}).get("type", "unknown")
        parts.append(
            f"[Document {i+1} | Source: {source} | Type: {ctype}]\n"
            f"{chunk['content']}\n"
            f"---"
        )
    return "\n".join(parts)


def generate_with_citation(query: str, top_k: int = 5) -> dict:
    """Full RAG generation pipeline: retrieve → reorder → format → LLM."""
    results = retrieve(query, top_k=top_k)
    if not results:
        return {"answer": "I cannot verify this information from the provided documents.",
                "sources": [], "retrieval_source": "none"}

    chunks = reorder_for_llm(results)
    context = format_context(chunks)
    retrieval_source = results[0].get("source", "unknown") if results else "none"

    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    try:
        from openai import OpenAI
        if LLM_API_KEY:
            client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                top_p=0.9,
            )
            answer = resp.choices[0].message.content
        else:
            answer = f"[DEMO] Based on {len(results)} retrieved chunks about {results[0].get('metadata', {}).get('source', 'unknown')}."
    except Exception as e:
        answer = f"[LLM Error: {e}] Based on {len(results)} retrieved documents."

    return {
        "answer": answer,
        "sources": [{"content": r["content"][:200], "metadata": r.get("metadata", {})}
                    for r in results],
        "retrieval_source": retrieval_source,
    }
