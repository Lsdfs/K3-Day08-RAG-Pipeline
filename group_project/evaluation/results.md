# RAG Evaluation Report

Framework: **RAGAS 0.1.21 — official built-in metrics**.

Golden dataset: **20 cases**.

## Overall scores

| Metric | Config A: hybrid + rerank | Config B: dense-only | Delta |
|---|---:|---:|---:|
| Faithfulness | 0.606 | 0.597 | +0.009 |
| Answer Relevance | 0.111 | 0.097 | +0.014 |
| Context Recall | 0.300 | 0.300 | +0.000 |
| Context Precision | 0.302 | 0.331 | -0.029 |
| Average | 0.330 | 0.331 | -0.001 |

## A/B comparison

**Kết luận:** Config B (dense-only) có điểm trung bình cao hơn. So sánh giữ nguyên query, corpus và top-k để đo tác động của hybrid retrieval + reranking.

## Per-question results (Config A)

| # | Question | Faith. | Relev. | Recall | Precision | Avg. |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Vinh Ha Long duoc UNESCO cong nhan la Di san gi? | 1.00 | 0.43 | 1.00 | 1.00 | 0.86 |
| 2 | Vinh Ha Long duoc cong nhan la Di san the gioi vao nam nao? | 0.57 | 0.53 | 1.00 | 0.58 | 0.67 |
| 3 | Vinh Ha Long nam o tinh nao? | 0.38 | 0.00 | 1.00 | 0.95 | 0.58 |
| 4 | Vinh Ha Long co dien tich bao nhieu? | 0.17 | 0.00 | 0.00 | 0.50 | 0.17 |
| 5 | Khu vuc di san duoc cong nhan co dien tich bao nhieu? | 0.43 | 0.27 | 0.00 | 0.00 | 0.17 |
| 6 | Vinh Ha Long co bao nhieu dao da voi? | 0.67 | 0.00 | 0.00 | 0.00 | 0.17 |
| 7 | Vinh Ha Long thuoc vinh nao? | 0.50 | 0.00 | 0.00 | 0.00 | 0.12 |
| 8 | Dau Go nam o phia nao cua vinh Ha Long? | 1.00 | 0.00 | 0.00 | 0.00 | 0.25 |
| 9 | Cong Tay nam o phia nao cua vinh? | 0.45 | 0.00 | 0.00 | 0.00 | 0.11 |
| 10 | Dau Be nam o phia nao cua vinh? | 0.75 | 0.00 | 0.00 | 0.00 | 0.19 |
| 11 | Dao nao lon nhat gan vinh Ha Long? | 0.50 | 0.00 | 0.00 | 0.25 | 0.19 |
| 12 | Vuon Quoc gia Cat Ba duoc UNESCO cong nhan la gi? | 0.50 | 0.34 | 0.00 | 0.00 | 0.21 |
| 13 | Vuon Quoc gia Cat Ba duoc cong nhan vao nam nao? | 0.50 | 0.00 | 1.00 | 0.50 | 0.50 |
| 14 | Vinh Ha Long co gia tri noi bat nao? | 0.60 | 0.00 | 1.00 | 1.00 | 0.65 |
| 15 | Dac diem dia chat noi bat cua vinh Ha Long la gi? | 0.69 | 0.00 | 0.00 | 0.25 | 0.24 |
| 16 | Chat luong nuoc vinh Ha Long bi o nhiem boi gi? | 0.78 | 0.00 | 0.00 | 0.00 | 0.19 |
| 17 | Vinh Ha Long duoc cong nhan tai ky hop UNESCO nao? | 0.40 | 0.65 | 1.00 | 1.00 | 0.76 |
| 18 | Tac gia cua muc Vinh Ha Long la ai? | 0.80 | 0.00 | 0.00 | 0.00 | 0.20 |
| 19 | Khoa Dia chat thuoc truong dai hoc nao? | 0.67 | 0.00 | 0.00 | 0.00 | 0.17 |
| 20 | Vinh Ha Long nam trong khoang kinh do nao? | 0.78 | 0.00 | 0.00 | 0.00 | 0.19 |

## Worst performers

| Question | Score | Failure stage | Root cause |
|---|---:|---|---|
| Cong Tay nam o phia nao cua vinh? | 0.114 | Retrieval | Expected evidence was absent from the top-5 contexts. |
| Vinh Ha Long thuoc vinh nao? | 0.125 | Retrieval | Expected evidence was absent from the top-5 contexts. |
| Vinh Ha Long co dien tich bao nhieu? | 0.167 | Retrieval | Expected evidence was absent from the top-5 contexts. |

## Recommendations

1. Add query expansion for aliases, numbers and Vietnamese spelling variants.
2. Clean PDF OCR artifacts and enrich source/year metadata before indexing.
3. Tune the dense-score fallback threshold on this golden set and re-run A/B.
