# RAG Evaluation Report

Framework: **RAGAS-compatible offline evaluator** (deterministic proxies; no judge API required).

Golden dataset: **20 cases**.

## Overall scores

| Metric | Config A: hybrid + rerank | Config B: dense-only | Delta |
|---|---:|---:|---:|
| Faithfulness | 0.992 | 0.992 | -0.001 |
| Answer Relevance | 0.491 | 0.491 | +0.000 |
| Context Recall | 0.615 | 0.621 | -0.006 |
| Context Precision | 0.620 | 0.620 | +0.000 |
| Average | 0.679 | 0.681 | -0.002 |

## A/B comparison

**Kết luận:** Config B (dense-only) có điểm trung bình cao hơn. So sánh giữ nguyên query, corpus và top-k để đo tác động của hybrid retrieval + reranking.

## Per-question results (Config A)

| # | Question | Faith. | Relev. | Recall | Precision | Avg. |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Vinh Ha Long duoc UNESCO cong nhan la Di san gi? | 1.00 | 0.85 | 0.83 | 1.00 | 0.92 |
| 2 | Vinh Ha Long duoc cong nhan la Di san the gioi vao nam nao? | 1.00 | 0.94 | 1.00 | 0.20 | 0.78 |
| 3 | Vinh Ha Long nam o tinh nao? | 1.00 | 0.28 | 1.00 | 0.20 | 0.62 |
| 4 | Vinh Ha Long co dien tich bao nhieu? | 1.00 | 0.35 | 0.00 | 0.00 | 0.34 |
| 5 | Khu vuc di san duoc cong nhan co dien tich bao nhieu? | 1.00 | 0.13 | 0.00 | 0.00 | 0.28 |
| 6 | Vinh Ha Long co bao nhieu dao da voi? | 0.99 | 0.62 | 0.75 | 1.00 | 0.84 |
| 7 | Vinh Ha Long thuoc vinh nao? | 1.00 | 0.48 | 0.67 | 1.00 | 0.79 |
| 8 | Dau Go nam o phia nao cua vinh Ha Long? | 0.99 | 0.25 | 1.00 | 0.40 | 0.66 |
| 9 | Cong Tay nam o phia nao cua vinh? | 0.98 | 0.60 | 1.00 | 0.60 | 0.80 |
| 10 | Dau Be nam o phia nao cua vinh? | 0.99 | 0.60 | 1.00 | 1.00 | 0.90 |
| 11 | Dao nao lon nhat gan vinh Ha Long? | 0.98 | 0.25 | 0.00 | 0.00 | 0.31 |
| 12 | Vuon Quoc gia Cat Ba duoc UNESCO cong nhan la gi? | 0.98 | 0.32 | 0.43 | 1.00 | 0.68 |
| 13 | Vuon Quoc gia Cat Ba duoc cong nhan vao nam nao? | 1.00 | 0.81 | 1.00 | 0.20 | 0.75 |
| 14 | Vinh Ha Long co gia tri noi bat nao? | 0.98 | 0.79 | 1.00 | 0.80 | 0.89 |
| 15 | Dac diem dia chat noi bat cua vinh Ha Long la gi? | 0.99 | 0.40 | 0.38 | 1.00 | 0.69 |
| 16 | Chat luong nuoc vinh Ha Long bi o nhiem boi gi? | 0.97 | 0.34 | 0.43 | 1.00 | 0.68 |
| 17 | Vinh Ha Long doc cong nhan tai ky hop UNESCO nao? | 1.00 | 0.79 | 0.78 | 1.00 | 0.89 |
| 18 | Tac gia cua muc Vinh Ha Long la ai? | 1.00 | 0.25 | 0.33 | 0.40 | 0.50 |
| 19 | Khoa Dia chat thuoc truong dai hoc nao? | 0.98 | 0.32 | 0.33 | 1.00 | 0.66 |
| 20 | Vinh Ha Long nam trong khoang kinh do nao? | 0.99 | 0.47 | 0.38 | 0.60 | 0.61 |

## Worst performers

| Question | Score | Failure stage | Root cause |
|---|---:|---|---|
| Khu vuc di san duoc cong nhan co dien tich bao nhieu? | 0.283 | Retrieval | Expected evidence was absent from the top-5 contexts. |
| Dao nao lon nhat gan vinh Ha Long? | 0.308 | Retrieval | Expected evidence was absent from the top-5 contexts. |
| Vinh Ha Long co dien tich bao nhieu? | 0.338 | Retrieval | Expected evidence was absent from the top-5 contexts. |

## Recommendations

1. Add query expansion for aliases, numbers and Vietnamese spelling variants.
2. Clean PDF OCR artifacts and enrich source/year metadata before indexing.
3. Tune the dense-score fallback threshold on this golden set and re-run A/B.
