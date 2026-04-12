from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    title: str
    doi: str | None = None
    refcode: str | None = None
    evidence: str
    data_source: str
    license: str | None = None


class KGFact(BaseModel):
    path: str
    relation: str
    value: str
    source_id: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=6, ge=1, le=20)


class QueryResponse(BaseModel):
    query: str
    mode: str
    answer: str
    sources: list[Source]
    kg_facts: list[KGFact]
    retrieved_count: int


class HealthResponse(BaseModel):
    status: str
    materials: int
    facts: int
    data_source: str


class RAGStatusResponse(BaseModel):
    retrieval_mode: str
    vector_store_enabled: bool
    llm_enabled: bool
    api_key_configured: bool
    api_base_url: str
    embedding_provider: str
    embedding_model: str
    vector_store_url: str
    qdrant_collection: str
    llm_provider: str
    llm_model: str
