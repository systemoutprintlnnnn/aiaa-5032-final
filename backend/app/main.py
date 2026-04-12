from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.answerers.deterministic import DeterministicAnswerer
from app.answerers.llm import OpenAILLMAnswerer
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.models import HealthResponse, QueryRequest, QueryResponse, RAGStatusResponse
from app.rag.embeddings import OpenAIEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever, VectorRetriever
from app.services import QueryService


settings = get_settings()
store = KnowledgeStore(settings.open_source_data_dir)
retrievers = []

if settings.rag_retrieval_mode in {"vector", "hybrid"}:
    api_key = settings.require_api_key("vector retrieval")
    embedding_provider = OpenAIEmbeddingProvider(
        model=settings.rag_embedding_model,
        api_key=api_key,
        base_url=settings.rag_api_base_url,
        dimensions=settings.rag_embedding_dimensions,
    )
    vector_store = QdrantVectorStore(
        url=settings.rag_vector_store_url,
        collection=settings.rag_qdrant_collection,
        dimensions=settings.rag_embedding_dimensions,
    )
    retrievers.append(VectorRetriever(store=store, embedding_provider=embedding_provider, vector_store=vector_store))

if settings.rag_retrieval_mode in {"keyword", "hybrid"}:
    retrievers.append(KeywordRetriever(store))

retrievers.append(NoResultGraphRetriever())
retriever = HybridRetriever(retrievers)

answerer = DeterministicAnswerer()
if settings.rag_enable_llm:
    api_key = settings.require_api_key("LLM answering")
    answerer = OpenAILLMAnswerer(model=settings.rag_llm_model, api_key=api_key, base_url=settings.rag_api_base_url)

query_service = QueryService(retriever, answerer=answerer)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        materials=store.material_count,
        facts=len(store.facts),
        data_source=settings.data_source_label,
    )


@app.get("/api/rag/status", response_model=RAGStatusResponse)
def rag_status() -> RAGStatusResponse:
    return RAGStatusResponse(
        retrieval_mode=settings.rag_retrieval_mode,
        vector_store_enabled=settings.rag_retrieval_mode in {"vector", "hybrid"},
        llm_enabled=settings.rag_enable_llm,
        api_key_configured=bool(settings.rag_api_key),
        api_base_url=settings.rag_api_base_url,
        embedding_provider=settings.rag_embedding_provider,
        embedding_model=settings.rag_embedding_model,
        vector_store_url=settings.rag_vector_store_url,
        qdrant_collection=settings.rag_qdrant_collection,
        llm_provider=settings.rag_llm_provider,
        llm_model=settings.rag_llm_model,
    )


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return query_service.answer(request)
