# Architecture

## Principle

This project is a FastAPI-based MOF QA system whose runtime knowledge must come from real MOF datasets or KG outputs. `References/` is only design context and must not be indexed into the QA corpus.

## Current MVP

```text
backend/data/open_source/
  MOF-ChemUnity public sample data
        |
        v
KnowledgeStore
  normalizes materials, aliases, properties, synthesis, evidence
        |
        v
KeywordRetriever
  temporary entity/keyword retrieval
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
       |                         |
       v                         v
  Neo4j graph               Qdrant vector store
       |                         |
       v                         v
  GraphRetriever            VectorRetriever
       +-----------+-------------+
                   v
             Retrieval fusion
                   |
                   v
         evidence-constrained LLM answerer
                   |
                   v
      answer + citations + KG fact paths
```

## Backend Boundaries

- `app/main.py`: FastAPI app construction and route registration.
- `app/config.py`: paths and runtime settings.
- `app/models.py`: API contracts.
- `app/knowledge_store.py`: temporary in-memory normalized store.
- `app/retrievers/`: replaceable retrieval adapters.
- `app/services/`: orchestration logic.
- `app/answerer.py`: answer composition from retrieved evidence.

## Replacement Path

The current `KeywordRetriever` is deliberately simple. Replace it by adding new retrievers behind the same interface:

- `QdrantRetriever` for semantic retrieval.
- `Neo4jRetriever` for graph facts and Text-to-Cypher.
- `HybridRetriever` for fusion and reranking.

Do not change the frontend contract when swapping retrieval internals.
