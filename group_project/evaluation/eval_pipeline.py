"""Reproducible RAG evaluation with four RAGAS-style metrics and A/B configs.

The default evaluator is deterministic and offline, so the classroom demo does
not depend on an LLM judge or API quota.  It exports the same four dimensions
required by RAGAS: faithfulness, answer relevance, context recall and context
precision.  Config A is hybrid retrieval with reranking; config B disables
reranking.  Run from the repository root:

    python group_project/evaluation/eval_pipeline.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.task9_retrieval_pipeline import retrieve
from src.task5_semantic_search import semantic_search
from src.task10_generation import generate_with_citation

HERE = Path(__file__).parent
GOLDEN_PATH = HERE / "golden_dataset.json"
RESULTS_PATH = HERE / "results.md"


def tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFD", text.lower())
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    stop = {"la", "co", "cua", "o", "va", "duoc", "gi", "nao", "bao", "nhieu"}
    return {w for w in re.findall(r"[a-z0-9]+", ascii_text) if len(w) > 1 and w not in stop}


def overlap(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / max(len(a), 1)


@dataclass
class Scores:
    faithfulness: float
    answer_relevance: float
    context_recall: float
    context_precision: float

    @property
    def average(self) -> float:
        return sum((self.faithfulness, self.answer_relevance,
                    self.context_recall, self.context_precision)) / 4


def score_case(question: str, expected: str, answer: str, contexts: list[str]) -> Scores:
    joined = " ".join(contexts)
    useful = [c for c in contexts if overlap(expected, c) > 0]
    # Citation plus answer support in retrieved text is a deterministic
    # groundedness proxy when an LLM judge is unavailable.
    citation = 1.0 if re.search(r"\[[^\]]+,\s*(?:n\.d\.|\d{4})\]", answer) else 0.0
    support = overlap(answer, joined)
    faithfulness = min(1.0, 0.75 * support + 0.25 * citation)
    answer_relevance = min(1.0, 0.65 * overlap(expected, answer) + 0.35 * overlap(question, answer))
    context_recall = min(1.0, overlap(expected, joined))
    context_precision = len(useful) / max(len(contexts), 1)
    return Scores(faithfulness, answer_relevance, context_recall, context_precision)


def run_config(items: list[dict], *, use_reranking: bool) -> list[dict]:
    rows = []
    for item in items:
        question = item["question"]
        expected = item.get("expected_answer", item.get("answer", ""))
        contexts_raw = (retrieve(question, top_k=5, use_reranking=True)
                        if use_reranking else semantic_search(question, top_k=5))
        contexts = [c.get("content", "") for c in contexts_raw]
        generated = generate_with_citation(question, top_k=5)
        answer = generated["answer"]
        score = score_case(question, expected, answer, contexts)
        rows.append({"question": question, "expected": expected, "answer": answer,
                     "scores": score, "sources": contexts_raw})
    return rows


def averages(rows: list[dict]) -> Scores:
    n = max(len(rows), 1)
    return Scores(*[sum(getattr(r["scores"], field) for r in rows) / n for field in
                    ("faithfulness", "answer_relevance", "context_recall", "context_precision")])


def export(config_a: list[dict], config_b: list[dict]) -> None:
    a, b = averages(config_a), averages(config_b)
    metrics = (("Faithfulness", "faithfulness"), ("Answer Relevance", "answer_relevance"),
               ("Context Recall", "context_recall"), ("Context Precision", "context_precision"),
               ("Average", "average"))
    lines = ["# RAG Evaluation Report", "", "Framework: **RAGAS-compatible offline evaluator** "
             "(deterministic proxies; no judge API required).", "", f"Golden dataset: **{len(config_a)} cases**.", "",
             "## Overall scores", "", "| Metric | Config A: hybrid + rerank | Config B: dense-only | Delta |",
             "|---|---:|---:|---:|"]
    for label, field in metrics:
        av, bv = getattr(a, field), getattr(b, field)
        lines.append(f"| {label} | {av:.3f} | {bv:.3f} | {av-bv:+.3f} |")
    winner = "A (hybrid + rerank)" if a.average >= b.average else "B (dense-only)"
    lines += ["", "## A/B comparison", "", f"**Kết luận:** Config {winner} có điểm trung bình cao hơn. "
              "So sánh giữ nguyên query, corpus và top-k để đo tác động của hybrid retrieval + reranking.", "",
              "## Per-question results (Config A)", "",
              "| # | Question | Faith. | Relev. | Recall | Precision | Avg. |", "|---:|---|---:|---:|---:|---:|---:|"]
    for i, row in enumerate(config_a, 1):
        s = row["scores"]
        lines.append(f"| {i} | {row['question'].replace('|', '/')} | {s.faithfulness:.2f} | "
                     f"{s.answer_relevance:.2f} | {s.context_recall:.2f} | {s.context_precision:.2f} | {s.average:.2f} |")
    worst = sorted(config_a, key=lambda r: r["scores"].average)[:3]
    lines += ["", "## Worst performers", "", "| Question | Score | Failure stage | Root cause |",
              "|---|---:|---|---|"]
    for row in worst:
        s = row["scores"]
        if s.context_recall < 0.5:
            stage, cause = "Retrieval", "Expected evidence was absent from the top-5 contexts."
        elif s.faithfulness < 0.5:
            stage, cause = "Generation", "Answer had weak lexical support or missing citation."
        else:
            stage, cause = "Answer relevance", "Retrieved evidence did not directly answer the question."
        lines.append(f"| {row['question'].replace('|', '/')} | {s.average:.3f} | {stage} | {cause} |")
    lines += ["", "## Recommendations", "",
              "1. Add query expansion for aliases, numbers and Vietnamese spelling variants.",
              "2. Clean PDF OCR artifacts and enrich source/year metadata before indexing.",
              "3. Tune the dense-score fallback threshold on this golden set and re-run A/B.", ""]
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    items = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    if len(items) < 15:
        raise ValueError("Golden dataset must contain at least 15 cases")
    config_a = run_config(items, use_reranking=True)
    config_b = run_config(items, use_reranking=False)
    export(config_a, config_b)
    print(f"Evaluated {len(items)} cases x 2 configs; report: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
