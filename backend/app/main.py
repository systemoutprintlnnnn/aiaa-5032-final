from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.models import HealthResponse, QueryRequest, QueryResponse
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever
from app.services import QueryService


settings = get_settings()
store = KnowledgeStore(settings.open_source_data_dir)
keyword_retriever = KeywordRetriever(store)
graph_retriever = NoResultGraphRetriever()
retriever = HybridRetriever([keyword_retriever, graph_retriever])
query_service = QueryService(retriever)

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


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return query_service.answer(request)
