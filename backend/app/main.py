from __future__ import annotations

import json
from typing import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.answerers.deterministic import DeterministicAnswerer
from app.answerers.llm import OpenAILLMAnswerer
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.models import HealthResponse, QueryRequest, QueryResponse, RAGStatusResponse
from app.rag.embeddings import OpenAIEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.retrievers import HybridRetriever, KGGraphRetriever, KeywordRetriever, NoResultGraphRetriever, VectorRetriever
from app.services import QueryService


settings = get_settings()
store = KnowledgeStore(settings.open_source_data_dir, synthesis_data_path=settings.resolved_kg_synthesis_path)
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

graph_retriever = NoResultGraphRetriever()
if settings.kg_enabled:
    candidate_graph_retriever = KGGraphRetriever(settings.resolved_kg_graph_path)
    if candidate_graph_retriever.is_loaded:
        graph_retriever = candidate_graph_retriever

retrievers.append(graph_retriever)
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
        kg_enabled=settings.kg_enabled,
        kg_graph_path=str(settings.resolved_kg_graph_path),
        kg_graph_loaded=graph_retriever.is_loaded,
        kg_fact_count=graph_retriever.fact_count,
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


@app.post("/api/query/stream")
def query_stream(request: QueryRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_query(request),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _encode(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def _stream_query(request: QueryRequest) -> Iterator[str]:
    try:
        matches = query_service.retrieve_matches(request)
        baseline = query_service.baseline_response(request, matches)
    except Exception as exc:
        yield _encode({"type": "error", "message": str(exc)})
        return

    use_llm = settings.rag_enable_llm and bool(matches) and isinstance(answerer, OpenAILLMAnswerer)
    final_mode = "hybrid_rag" if use_llm else baseline.mode

    yield _encode(
        {
            "type": "meta",
            "query": baseline.query,
            "mode": final_mode,
            "sources": [source.model_dump() for source in baseline.sources],
            "kg_facts": [fact.model_dump() for fact in baseline.kg_facts],
            "retrieved_count": baseline.retrieved_count,
        }
    )

    answer_text = ""
    try:
        if use_llm:
            for token in answerer.stream_tokens(request.question, matches):
                if not token:
                    continue
                answer_text += token
                yield _encode({"type": "token", "text": token})
            if not answer_text.strip():
                answer_text = baseline.answer
                final_mode = baseline.mode
                yield _encode({"type": "token", "text": baseline.answer})
        else:
            answer_text = baseline.answer
            yield _encode({"type": "token", "text": baseline.answer})
    except Exception as exc:
        yield _encode({"type": "error", "message": str(exc)})
        return

    yield _encode({"type": "done", "mode": final_mode, "answer": answer_text})
