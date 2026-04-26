# Architecture

## Principle

This project is a FastAPI-based MOF QA system whose runtime knowledge must come from real MOF datasets or KG outputs. `References/` is only design context and must not be indexed into the QA corpus.

## Current Local Baseline

```text
backend/data/open_source/
  MOF-ChemUnity public sample data
reference_code/MOF_KG/3.MOF-Synthesis.json
  team/course synthesis evidence rows
backend/data/kg/mof_kg.json
  local JSON KG export
        |
        v
KnowledgeStore
  normalizes materials, aliases, properties, synthesis, evidence
  also loads row-level KG synthesis evidence documents
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
  merges keyword, vector, and graph evidence behind one retriever contract
        |
        v
QueryService
  retrieves facts and composes evidence-backed answer
        |
        v
FastAPI /api/query and /api/query/stream
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

## Delivered Architecture

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
- `app/data_sources/`: adapters for approved runtime files such as KG synthesis evidence.
- `app/models.py`: API contracts.
- `app/knowledge_store.py`: in-memory normalized store for the submitted local system.
- `app/stores/`: normalized evidence schemas.
- `app/retrievers/`: replaceable retrieval adapters.
- `app/answerers/`: answer composition implementations.
- `app/rag/`: chunk building, embedding provider, and vector store adapters.
- `app/scripts/`: setup commands such as vector indexing.
- `app/services/`: orchestration logic.
- `app/answerer.py`: answer composition from retrieved evidence.

## Extension Path

The current `KeywordRetriever` remains an exact-match fallback. If the project is reopened, extension work should preserve the same interfaces:

- `KGGraphRetriever` for the checked-in local JSON graph output.
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
- `mof_evidence` is the configured Qdrant collection name. `mof_evidence_smoke` was used only for a small live smoke check.
- `KGGraphRetriever` reads `backend/data/kg/mof_kg.json` when `KG_ENABLED=true`.
- `NoResultGraphRetriever` remains the fallback when the KG file is missing, disabled, or invalid.
- `KnowledgeStore` also loads `reference_code/MOF_KG/3.MOF-Synthesis.json` as row-level synthesis evidence documents when the file exists.
- The vector index is built over normalized evidence documents, including KG synthesis evidence, not over `References/`.
- With the current checked-in data, `KnowledgeStore` loads 100 demo materials, 47,823 normalized facts/documents, and 28,989 synthesis evidence rows; the KG graph retriever exposes 218,662 graph facts.
