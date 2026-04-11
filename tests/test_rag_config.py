import pytest

from app.config import Settings, get_settings
from app.rag.embeddings import RAGConfigurationError


def test_settings_default_to_keyword_and_deterministic_mode():
    settings = Settings()

    assert settings.rag_retrieval_mode == "keyword"
    assert settings.rag_enable_llm is False
    assert settings.rag_qdrant_collection == "mof_evidence"
    assert settings.rag_embedding_batch_size == 128


def test_settings_require_api_key_for_vector_mode():
    settings = Settings(rag_retrieval_mode="hybrid", rag_api_key="")

    with pytest.raises(RAGConfigurationError, match="RAG_API_KEY"):
        settings.require_api_key("vector retrieval")


def test_get_settings_reads_rag_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "hybrid")
    monkeypatch.setenv("RAG_ENABLE_LLM", "true")
    monkeypatch.setenv("RAG_LLM_MODEL", "test-llm")

    settings = get_settings()

    assert settings.rag_api_key == "test-key"
    assert settings.rag_retrieval_mode == "hybrid"
    assert settings.rag_enable_llm is True
    assert settings.rag_llm_model == "test-llm"

    get_settings.cache_clear()
