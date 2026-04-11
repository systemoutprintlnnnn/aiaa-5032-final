from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_reports_loaded_data():
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["materials"] == 100
    assert data["facts"] > 0


def test_rag_status_endpoint_reports_default_runtime_mode_without_secret():
    response = client.get("/api/rag/status")

    assert response.status_code == 200
    data = response.json()
    assert data["retrieval_mode"] == "keyword"
    assert data["vector_store_enabled"] is False
    assert data["llm_enabled"] is False
    assert data["api_key_configured"] is False
    assert "api_key" not in data
    assert data["qdrant_collection"] == "mof_evidence"


def test_query_endpoint_returns_sources_and_fact_paths():
    response = client.post(
        "/api/query",
        json={"question": "What is the BET surface area of UTSA-67?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hard_fact_lookup"
    assert data["sources"]
    assert data["kg_facts"]
    assert "1137" in data["answer"]


def test_query_endpoint_supports_water_stability_demo_question():
    response = client.post(
        "/api/query",
        json={"question": "Is Zn(LTP)2 water stable?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hard_fact_lookup"
    assert data["sources"]
    assert any("Water Stability" in fact["relation"] for fact in data["kg_facts"])


def test_query_endpoint_supports_alias_demo_question():
    response = client.post(
        "/api/query",
        json={"question": "What names are associated with CSD ref code CUVVOG?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "alias_lookup"
    assert data["sources"]
    assert any("HAS_NAME" in fact["relation"] for fact in data["kg_facts"])


def test_query_endpoint_returns_insufficient_evidence_for_unknown_question():
    response = client.post(
        "/api/query",
        json={"question": "What is the unicorn conductivity of NOT_A_REAL_MOF_123?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "insufficient_evidence"
    assert data["sources"] == []
    assert data["kg_facts"] == []
