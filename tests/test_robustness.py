"""Robustness tests required by the extended assignment rubric."""

import importlib
from unittest.mock import Mock, patch

import pytest
import requests

from src import task4_chunking_indexing as task4
from src import task5_semantic_search as task5
from src import task6_lexical_search as task6
from src import task7_reranking as task7
from src import task8_pageindex_vectorless as task8
from src import task9_retrieval_pipeline as task9
from src import task10_generation as task10


@pytest.mark.parametrize("function", [task5.semantic_search, task6.lexical_search])
def test_empty_query(function):
    with pytest.raises(ValueError): function("   ")


@pytest.mark.parametrize("function", [task5.semantic_search, task6.lexical_search])
@pytest.mark.parametrize("top_k", [0, -1, True, 1.5])
def test_invalid_top_k(function, top_k):
    with pytest.raises(ValueError): function("học phí", top_k=top_k)


def test_missing_collection_returns_empty_with_clear_path():
    with patch.object(task4, "get_collection", side_effect=RuntimeError("Run Task 4 indexing first")):
        assert task5.semantic_search("học phí") == []


def test_index_twice_is_idempotent():
    class FakeCollection:
        def __init__(self): self.rows={}
        def upsert(self,ids,documents,embeddings,metadatas):
            self.rows.update({i:d for i,d in zip(ids,documents)})
        def count(self): return len(self.rows)
    collection=FakeCollection(); chunks=[{"id":"stable","content":"abc","embedding":[1.0],"metadata":{}}]
    with patch.object(task4,"get_collection",return_value=collection):
        task4.index_to_vectorstore(chunks); task4.index_to_vectorstore(chunks)
    assert collection.count() == 1


def test_duplicate_chunk_removed():
    docs=[{"content":"Nội dung giống nhau","metadata":{"source":"a"}},
          {"content":"Nội dung giống nhau","metadata":{"source":"a"}}]
    assert len(task4.chunk_documents(docs)) == 1


def test_bm25_empty_corpus_and_vietnamese_query():
    task6.refresh_index([]); assert task6.lexical_search("học phí") == []
    task6.refresh_index([{"content":"Chính sách học phí sinh viên Việt Nam","metadata":{"source":"x"}}])
    assert task6.lexical_search("học phí",1)[0]["score"] > 0


def test_missing_pageindex_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("PAGEINDEX_API_KEY",raising=False); monkeypatch.setattr(task8,"PAGEINDEX_API_KEY","")
    monkeypatch.setattr(task8,"MANIFEST_PATH",tmp_path/"missing.json")
    assert task8.pageindex_search("học phí") == []


def test_api_timeout_uses_reranker_fallback(monkeypatch):
    monkeypatch.setenv("JINA_API_KEY","test-only")
    candidates=[{"content":"quy định học phí","score":.8,"metadata":{"source":"x"}}]
    with patch.object(task7.requests,"post",side_effect=requests.Timeout):
        result=task7.rerank_cross_encoder("học phí",candidates,1)
    assert result and result[0]["metadata"]["source"] == "x"


def test_pageindex_fallback_and_irrelevant_query():
    fallback=[{"content":"external","score":1.0,"metadata":{"source":"p"},"source":"pageindex"}]
    with patch.object(task9,"semantic_search",return_value=[]),patch.object(task9,"lexical_search",return_value=[]),patch.object(task9,"pageindex_search",return_value=fallback):
        assert task9.retrieve("xyzabc123",score_threshold=.9)[0]["source"] == "pageindex"


def test_one_retriever_failure_does_not_stop_other():
    sparse=[{"content":"học phí được thanh toán mỗi kỳ","score":2.0,"metadata":{"source":"rmit"}}]
    with patch.object(task9,"semantic_search",side_effect=RuntimeError),patch.object(task9,"lexical_search",return_value=sparse),patch.object(task9,"pageindex_search",return_value=[]):
        assert task9.retrieve("học phí",score_threshold=0)[0]["source"] == "hybrid"


def test_citation_without_source_is_rejected():
    result=task10.generate_with_citation("học phí",[{"content":"Học phí là 1 đồng","score":1.0,"metadata":{}}])
    assert result["answer"] == task10.INSUFFICIENT_EVIDENCE


def test_generation_insufficient_evidence_exact_string():
    chunks=[{"content":"Thông tin về thư viện.","score":.1,"metadata":{"source":"library.md"}}]
    assert task10.generate_with_citation("giá vé máy bay",chunks)["answer"] == "I cannot verify this information"


def test_import_streamlit_app():
    module=importlib.import_module("app")
    assert module.PROJECT_ROOT.exists()
