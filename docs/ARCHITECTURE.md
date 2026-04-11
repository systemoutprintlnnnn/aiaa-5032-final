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
NoResultGraphRetriever
  KG adapter slot until graph data is available
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
frontend/index.html
```

## API-First Real RAG Path

```text
KnowledgeStore facts/documents
        |
        v
EvidenceChunk builder
        |
        v
OpenAIEmbeddingProvider
        |
        v
QdrantVectorStore
        |
        v
VectorRetriever
        |
        +---- KeywordRetriever fallback
        |
        +---- NoResultGraphRetriever KG slot
        |
        v
HybridRetriever
        |
        v
OpenAILLMAnswerer or DeterministicAnswerer
        |
        v
FastAPI /api/query
```

## Target Architecture

```text
Runtime MOF data
  -> data source adapters
  -> normalized facts and documents
  -> API embedding model
  -> Qdrant vector store
  -> VectorRetriever
  -> local keyword fallback
  -> optional KG GraphRetriever
  -> HybridRetriever
  -> evidence-constrained LLM answerer
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

- `GraphRetriever` for the KG teammate's output.
- `VectorRetriever` backed by Qdrant for semantic retrieval.
- `OpenAILLMAnswerer` for evidence-grounded answer generation.

Do not change the frontend contract when swapping retrieval internals.
