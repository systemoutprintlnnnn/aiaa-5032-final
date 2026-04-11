from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "MOF KG-Enhanced RAG FastAPI MVP"
    data_source_label: str = "AI4ChemS/MOF_ChemUnity public sample data"
    backend_dir: Path = Path(__file__).resolve().parents[1]
    rag_retrieval_mode: str = "keyword"
    rag_api_key: str = ""
    rag_embedding_provider: str = "openai"
    rag_embedding_model: str = "text-embedding-3-small"
    rag_embedding_dimensions: int = 1536
    rag_embedding_batch_size: int = 128
    rag_vector_store_url: str = "http://127.0.0.1:6333"
    rag_qdrant_collection: str = "mof_evidence"
    rag_enable_llm: bool = False
    rag_llm_provider: str = "openai"
    rag_llm_model: str = "gpt-4.1-mini"

    @property
    def open_source_data_dir(self) -> Path:
        return self.backend_dir / "data" / "open_source"

    def require_api_key(self, feature: str) -> str:
        from app.rag.embeddings import RAGConfigurationError

        if not self.rag_api_key:
            raise RAGConfigurationError(f"RAG_API_KEY is required for {feature}.")
        return self.rag_api_key

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            rag_retrieval_mode=os.getenv("RAG_RETRIEVAL_MODE", "keyword"),
            rag_api_key=os.getenv("RAG_API_KEY", ""),
            rag_embedding_provider=os.getenv("RAG_EMBEDDING_PROVIDER", "openai"),
            rag_embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
            rag_embedding_dimensions=int(os.getenv("RAG_EMBEDDING_DIMENSIONS", "1536")),
            rag_embedding_batch_size=int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "128")),
            rag_vector_store_url=os.getenv("RAG_VECTOR_STORE_URL", "http://127.0.0.1:6333"),
            rag_qdrant_collection=os.getenv("RAG_QDRANT_COLLECTION", "mof_evidence"),
            rag_enable_llm=parse_bool(os.getenv("RAG_ENABLE_LLM", "false")),
            rag_llm_provider=os.getenv("RAG_LLM_PROVIDER", "openai"),
            rag_llm_model=os.getenv("RAG_LLM_MODEL", "gpt-4.1-mini"),
        )


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
