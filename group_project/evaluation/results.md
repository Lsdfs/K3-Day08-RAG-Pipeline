# RAG Evaluation Results

Generated: 2026-08-04T04:21:13.013342+00:00

## Framework

RAGAS-compatible deterministic offline evaluation (no paid API required).

## Overall Scores

| Metric | Config A: Hybrid + rerank | Config B: Dense only | Δ |
|---|---:|---:|---:|
| Faithfulness | 0.982 | 0.983 | -0.001 |
| Answer relevance | 0.189 | 0.169 | +0.020 |
| Context recall | 0.972 | 0.812 | +0.160 |
| Context precision | 1.000 | 0.933 | +0.067 |
| Average | 0.786 | 0.724 | +0.061 |

## A/B Comparison Analysis

- Config A combines semantic hashing retrieval, BM25, RRF fusion, and local reranking.
- Config B uses semantic hashing retrieval only and skips reranking.
- **Conclusion:** Config A achieved the higher mean score on this 18-question dataset.

## Worst Performers (Config A)

| # | Question | Faithfulness | Relevance | Recall | Precision | Average |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Diện tích Vịnh Hạ Long được nguồn mô tả là bao nhiêu? | 1.000 | 0.033 | 0.500 | 1.000 | 0.633 |
| 2 | Có bao nhiêu làng chài nổi được nêu tại Vịnh Hạ Long? | 0.965 | 0.057 | 1.000 | 1.000 | 0.756 |
| 3 | Hang Sửng Sốt rộng bao nhiêu mét vuông? | 0.902 | 0.122 | 1.000 | 1.000 | 0.756 |

## Recommendations

1. Add an English–Vietnamese multilingual embedding model when deployment resources allow.
2. Expand official Vietnamese sources and normalize duplicated navigation/footer content.
3. Add an API-backed RAGAS judge in CI only when a controlled key and budget are available.

## Reproduction

```powershell
python -m group_project.evaluation.eval_pipeline
```
