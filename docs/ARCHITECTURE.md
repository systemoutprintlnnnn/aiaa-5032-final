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

## Target Architecture

```text
Runtime MOF data
  -> data source adapters
  -> normalized facts and documents
  -> local simple RAG retriever
  -> optional KG GraphRetriever
  -> HybridRetriever
  -> evidence-constrained answerer
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
- `app/services/`: orchestration logic.
- `app/answerer.py`: answer composition from retrieved evidence.

## Replacement Path

The current `KeywordRetriever` is deliberately simple and remains the local baseline. Extend it by adding retrievers behind the same interface:

- `GraphRetriever` for the KG teammate's output.
- `VectorRetriever` or `QdrantRetriever` for semantic retrieval after the local path is stable.
- `LLMAnswerer` after retrieval can provide reliable cited evidence.

Do not change the frontend contract when swapping retrieval internals.
