import json

from app import app
from group_project.evaluation import eval_pipeline
from src.task10_generation import generate_with_citation
from src.task4_chunking_indexing import chunk_documents, load_documents, run_pipeline
from src.task9_retrieval_pipeline import retrieve


def test_group_corpus_and_index_are_real():
    documents = load_documents()
    assert len(documents) >= 5
    assert all(doc["metadata"]["source_url"].startswith("https://") for doc in documents)
    stats = run_pipeline()
    assert stats["documents"] >= 5 and stats["chunks"] > stats["documents"]


def test_chunk_ids_are_stable_and_unique():
    first = chunk_documents(load_documents())
    second = chunk_documents(load_documents())
    assert [row["id"] for row in first] == [row["id"] for row in second]
    assert len({row["id"] for row in first}) == len(first)


def test_hybrid_retrieval_returns_sources():
    results = retrieve("Ha Long Bay UNESCO World Heritage 1994", top_k=3)
    assert results and all(row["metadata"].get("source_url") for row in results)
    assert all(row["source"] == "hybrid" for row in results)


def test_generation_has_verifiable_citation():
    result = generate_with_citation("When was Ha Long Bay declared a UNESCO World Heritage Site?")
    assert result["sources"]
    assert "[" in result["answer"] and "]" in result["answer"]


def test_chat_api_validation_health_and_answer():
    client = app.test_client()
    assert client.get("/api/health").get_json()["documents"] >= 5
    assert client.post("/api/chat", json={"message":""}).status_code == 400
    response = client.post("/api/chat", json={"message":"UNESCO công nhận Hạ Long năm nào?", "top_k":3})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["answer"] and payload["sources"]


def test_follow_up_memory_request():
    client = app.test_client()
    response = client.post("/api/chat", json={"message":"Thế còn hoạt động ở đó?", "history":[
        {"role":"user","content":"Hãy giới thiệu Vịnh Hạ Long"},
        {"role":"assistant","content":"Thông tin có nguồn."}]})
    assert response.status_code == 200


def test_golden_dataset_schema_and_size():
    dataset = eval_pipeline.load_golden_dataset()
    assert len(dataset) >= 15
    assert len({item["id"] for item in dataset}) == len(dataset)


def test_ab_evaluation_and_export(tmp_path, monkeypatch):
    from src import task10_generation as pipeline
    dataset = eval_pipeline.load_golden_dataset()[:3]
    comparison = eval_pipeline.compare_configs(pipeline, dataset)
    assert set(comparison) == {"A — Hybrid + rerank", "B — Dense only"}
    for result in comparison.values():
        assert all(0 <= score <= 1 for score in result["metrics"].values())
    monkeypatch.setattr(eval_pipeline, "RESULTS_PATH", tmp_path / "results.md")
    rendered = eval_pipeline.export_results(comparison["A — Hybrid + rerank"], comparison)
    assert "Worst Performers" in rendered and eval_pipeline.RESULTS_PATH.exists()
