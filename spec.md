# AI SPEC — University Services RAG Pipeline
## Nhóm K3 | Role 2: Data & Dense Search Dev | Nguyễn Quốc Việt

---

## §1. User & Job

- **Job executor**: University student/staff looking up policies, fees, deadlines
- **Core JTBD**: When I need to find specific university policy information (tuition costs, library hours, scholarship requirements), I want to ask a natural language question and get an accurate, sourced answer immediately, so I don't have to browse multiple web pages or PDFs.
- **Problem statement**: University policy documents are scattered across multiple PDFs and web pages. Students waste 15-20 minutes per search browsing through documents manually.
- **Evidence**: Survey of 20+ students confirmed 80%+ spend >10 minutes finding policy info. 30% of Discord questions are "where do I find X policy?"

---

## §2. Impact & Decision

| Candidate | Users × Frequency × Impact | Chosen? |
|-----------|---------------------------|:---:|
| RAG Pipeline for university docs | 1000+ students × daily × 15 min saved | ✅ |
| Simple search bar (no AI) | Same reach but poor Vietnamese matching | ❌ (rule-based fails on synonyms) |
| Manual FAQ page | Requires constant updating, no semantic understanding | ❌ |

**Chosen**: RAG Pipeline with hybrid retrieval (dense + sparse) because it handles Vietnamese synonyms and provides cited answers.

---

## §3. Similar Solutions Studied

- **Notion AI Q&A**: Good for single workspace, doesn't handle multi-source PDF ingestion
- **OpenAI Assistants with file search**: Good quality but $0.10/query, too expensive at scale
- **LangChain RAG templates**: Solid foundation, adapted for our Vietnamese university context

---

## §4. Design

- **Slice**: A student types "Thư viện mở cửa lúc mấy giờ?" → RAG pipeline retrieves relevant chunks → LLM answers with citations
- **Non-goals**: User authentication, multi-language beyond VI/EN, real-time document syncing, document editing
- **Prototype level**: Working (real embeddings + real LLM + ChromaDB)
- **Automation**: Augment — LLM suggests answers but user verifies (citation trail)

### Principles Applied (>4)
| Principle | Applied where |
|-----------|---------------|
| HAX: Make it safe | LLM cites sources, refuses to invent when context is insufficient |
| HAX: Make it fast | ChromaDB in-memory search <100ms, OpenRouter API ~2s |
| PAIR: Guide the model | Structured system prompt with citation rules |
| PAIR: Test with real data | 20 golden set cases, honest metric recording |

---

## §5. Error Types (4 layers)

| Layer | Example |
|-------|---------|
| ① No evidence | Asking about RMIT-specific fees → fallback to PageIndex |
| ② Ambiguous query | "học phí" without specifying program → retrieve all fee docs |
| ③ Out of scope | "Help me write a Python script" → clarify refusal |
| ④ Domain-specific | Wrong deadline date → student misses payment (highest risk) |

---

## §6. Four Experience Paths

- **Happy path**: Query → semantic+lexical retrieval → RRF merge → LLM with citations → answer
- **Low-confidence**: Retrieval score <0.20 → PageIndex keyword fallback → honest "limited results" note
- **Failure**: No chunks found → "I cannot verify this information"
- **Correction**: User asks follow-up with more detail → agent re-retrieves with refined context

---

## §7. Testing

- **Quality dimensions**: Answer accuracy, Source citation rate, Retrieval precision
- **Golden set**: 20 cases covering all 4 error layers
- **Quality bar**: 50% accuracy on golden set (current: 40%, improving)
- **Results**: See `group_project/evaluation/results.md`

---

## §8. Team

- Nguyễn Quốc Việt — Role 2: Data collection, chunking, embedding, dense search
