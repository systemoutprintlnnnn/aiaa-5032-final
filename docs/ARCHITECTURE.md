# Architecture

## Principle

This project is a FastAPI-based MOF QA system whose runtime knowledge must come from real MOF datasets or KG outputs. `References/` is only design context and must not be indexed into the QA corpus.

## Current Local Baseline

```text
backend/data/open_source/
  MOF-ChemUnity public sample data
        |
        v
KnowledgeStore
  normalizes materials, aliases, properties, synthesis, evidence
  exposes facts and document-style records
        |
        v
KeywordRetriever
  simple local RAG-style retrieval
        |
        v
KGGraphRetriever
  optional local JSON graph evidence from backend/data/kg/mof_kg.json
        |
        v
HybridRetriever
  merges simple RAG evidence and future graph evidence
        |
        v
QueryService
  retrieves facts and composes evidence-backed answer
        |
        v
FastAPI /api/query
        |
        v
frontend Next.js TypeScript workbench
```

## API-First Real RAG Path

```text
KnowledgeStore facts/documents
        |
        v
EvidenceChunk builder
        |
        v
Zhipu/OpenAI-compatible OpenAIEmbeddingProvider
        |
        v
QdrantVectorStore
        |
        v
VectorRetriever
        |
        +---- KeywordRetriever fallback
        |
        +---- KGGraphRetriever local JSON graph layer
        |
        v
HybridRetriever
        |
        v
Zhipu/OpenAI-compatible OpenAILLMAnswerer or DeterministicAnswerer
        |
        v
FastAPI /api/query
```

## Target Architecture

```text
Runtime MOF data
  -> data source adapters
  -> normalized facts and documents
  -> Zhipu embedding-3 API
  -> Qdrant vector store
  -> VectorRetriever
  -> local keyword fallback
  -> optional KG GraphRetriever
  -> HybridRetriever
  -> evidence-constrained Zhipu glm-4.6v answerer
  -> answer + citations + KG fact paths
```

## Backend Boundaries

- `app/main.py`: FastAPI app construction and route registration.
- `app/config.py`: paths and runtime settings.
- `app/models.py`: API contracts.
- `app/knowledge_store.py`: temporary in-memory normalized store.
- `app/stores/`: normalized evidence schemas.
- `app/retrievers/`: replaceable retrieval adapters.
- `app/answerers/`: answer composition implementations.
- `app/rag/`: chunk building, embedding provider, and vector store adapters.
- `app/scripts/`: setup commands such as vector indexing.
- `app/services/`: orchestration logic.
- `app/answerer.py`: answer composition from retrieved evidence.

## Replacement Path

The current `KeywordRetriever` remains an exact-match fallback. Extend or replace the real RAG path behind the same interfaces:

- `KGGraphRetriever` for the KG teammate's JSON graph output.
- `VectorRetriever` backed by Qdrant for semantic retrieval.
- `OpenAILLMAnswerer` for evidence-grounded answer generation through OpenAI-compatible chat completions. It currently targets Zhipu `glm-4.6v`.

Do not change the frontend contract when swapping retrieval internals. The
frontend API client lives under `frontend/lib/` and expects the same
`/api/query` and `/api/rag/status` response shapes documented in
`docs/API_CONTRACT.md`.

## Current Operational Notes

- Default startup uses `RAG_RETRIEVAL_MODE=keyword` and `RAG_ENABLE_LLM=false`, so no API key or Qdrant service is required.
- API-first real RAG uses local `.env` values. `.env` must stay ignored by Git.
- Zhipu `embedding-3` uses 2048-dimensional vectors in this project.
- The manually verified smoke collection is `mof_evidence_smoke`; the full `mof_evidence` collection still needs an intentional full indexing run.
- `KGGraphRetriever` reads `backend/data/kg/mof_kg.json` when `KG_ENABLED=true`.
- `NoResultGraphRetriever` remains the fallback when the KG file is missing, disabled, or invalid.
