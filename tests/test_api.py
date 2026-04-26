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
    assert data["api_base_url"] == "https://open.bigmodel.cn/api/paas/v4/"
    assert data["embedding_provider"] == "zhipu"
    assert data["embedding_model"] == "embedding-3"
    assert data["llm_provider"] == "zhipu"
    assert data["llm_model"] == "glm-4.6v"
    assert data["kg_enabled"] is True
    assert data["kg_graph_loaded"] is True
    assert data["kg_fact_count"] > 0
    assert data["kg_graph_path"].endswith("backend/data/kg/mof_kg.json")


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


def test_query_endpoint_supports_kg_solvent_question():
    response = client.post(
        "/api/query",
        json={"question": "What solvent is used in UNABAN?", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sources"]
    assert any(source["data_source"] == "MOF KG JSON" for source in data["sources"])
    assert any(fact["relation"] == "KG_USES_SOLVENT" for fact in data["kg_facts"])


def test_query_endpoint_shared_kg_question_excludes_seed_mof():
    response = client.post(
        "/api/query",
        json={"question": "What other MOFs use the same solvent as UNABAN?", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sources"]
    assert all(source["refcode"] != "UNABAN" for source in data["sources"])
    assert all("Material(UNABAN)" not in fact["path"] for fact in data["kg_facts"])


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
