from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

ZHIPU_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"


class Settings(BaseModel):
    app_name: str = "MOF KG-Enhanced RAG FastAPI MVP"
    data_source_label: str = "AI4ChemS/MOF_ChemUnity public sample data"
    backend_dir: Path = Path(__file__).resolve().parents[1]
    rag_retrieval_mode: str = "keyword"
    rag_api_key: str = ""
    rag_api_base_url: str = ZHIPU_API_BASE_URL
    rag_embedding_provider: str = "zhipu"
    rag_embedding_model: str = "embedding-3"
    rag_embedding_dimensions: int = 2048
    rag_embedding_batch_size: int = 64
    rag_vector_store_url: str = "http://127.0.0.1:6333"
    rag_qdrant_collection: str = "mof_evidence"
    rag_enable_llm: bool = False
    rag_llm_provider: str = "zhipu"
    rag_llm_model: str = "glm-4.6v"
    kg_enabled: bool = True
    kg_graph_path: Path | None = None
    kg_synthesis_path: Path | None = None

    @property
    def open_source_data_dir(self) -> Path:
        return self.backend_dir / "data" / "open_source"

    @property
    def resolved_kg_graph_path(self) -> Path:
        if self.kg_graph_path is None:
            return self.backend_dir / "data" / "kg" / "mof_kg.json"
        if self.kg_graph_path.is_absolute():
            return self.kg_graph_path
        return self.backend_dir.parent / self.kg_graph_path

    @property
    def resolved_kg_synthesis_path(self) -> Path:
        if self.kg_synthesis_path is None:
            return self.backend_dir.parent / "reference_code" / "MOF_KG" / "3.MOF-Synthesis.json"
        if self.kg_synthesis_path.is_absolute():
            return self.kg_synthesis_path
        return self.backend_dir.parent / self.kg_synthesis_path

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
            rag_api_base_url=os.getenv("RAG_API_BASE_URL", ZHIPU_API_BASE_URL),
            rag_embedding_provider=os.getenv("RAG_EMBEDDING_PROVIDER", "zhipu"),
            rag_embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "embedding-3"),
            rag_embedding_dimensions=int(os.getenv("RAG_EMBEDDING_DIMENSIONS", "2048")),
            rag_embedding_batch_size=int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "64")),
            rag_vector_store_url=os.getenv("RAG_VECTOR_STORE_URL", "http://127.0.0.1:6333"),
            rag_qdrant_collection=os.getenv("RAG_QDRANT_COLLECTION", "mof_evidence"),
            rag_enable_llm=parse_bool(os.getenv("RAG_ENABLE_LLM", "false")),
            rag_llm_provider=os.getenv("RAG_LLM_PROVIDER", "zhipu"),
            rag_llm_model=os.getenv("RAG_LLM_MODEL", "glm-4.6v"),
            kg_enabled=parse_bool(os.getenv("KG_ENABLED", "true")),
            kg_graph_path=Path(os.getenv("KG_GRAPH_PATH")) if os.getenv("KG_GRAPH_PATH") else None,
            kg_synthesis_path=Path(os.getenv("KG_SYNTHESIS_PATH")) if os.getenv("KG_SYNTHESIS_PATH") else None,
        )


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
