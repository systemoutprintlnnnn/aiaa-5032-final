# API-First Real RAG Design

## Purpose

The current project is a runnable local MOF QA baseline, but its retrieval is keyword/entity-based. The next phase should turn it into a real RAG system that uses:

- an embedding model API;
- a vector database;
- an LLM API for evidence-grounded answer generation.

The implementation should keep the existing FastAPI, frontend, source metadata, and KG adapter boundary intact.

## Chosen Approach

Use a lightweight in-repo RAG pipeline rather than making LangChain or LlamaIndex the central architecture.

The core path becomes:

```text
MOF runtime data
  -> KnowledgeStore
  -> DocumentBuilder / Chunker
  -> EmbeddingProvider
  -> QdrantVectorStore
  -> VectorRetriever
       +
     KeywordRetriever fallback
       +
     GraphRetriever later
  -> HybridRetriever
  -> LLMAnswerer
  -> FastAPI /api/query
  -> frontend/index.html
```

LangChain or LlamaIndex can be reconsidered later, but the next implementation pass should not depend on their abstractions. The existing code already has `Retriever`, `HybridRetriever`, `Answerer`, and `QueryService` seams, so a small custom pipeline is easier to debug and easier for KG integration.

## Runtime Data Boundary

`References/` remains planning context only and must not be indexed as the runtime QA corpus.

The initial vector index should be built from runtime MOF data already normalized from:

- `backend/data/open_source/demo.json`;
- `backend/data/open_source/water_stability_chemunity_v0.1.0.csv`;
- `backend/data/open_source/mof_names_and_csd_codes.csv`.

Future course/team data can enter through the same document-building path.

## New Components

### Document Builder

Responsibility:

- turn current `KnowledgeStore.documents` and facts into embedding-ready chunks;
- preserve metadata needed for citations and answer grounding.

Each chunk should include:

```text
id
text
refcode
material_names
relation
source
doi
license
fact_id
path
```

Initial chunking should stay conservative: one fact/document-style evidence item per chunk. This keeps citations stable and avoids mixing unrelated materials in one vector point.

### Embedding Provider

Responsibility:

- call the configured embedding API;
- return numeric vectors for documents and user queries;
- centralize provider configuration and API-key handling.

Interface shape:

```text
embed_texts(texts: list[str]) -> list[list[float]]
embed_query(query: str) -> list[float]
```

Configuration:

```text
RAG_EMBEDDING_PROVIDER
RAG_EMBEDDING_MODEL
RAG_API_KEY
```

The provider should raise a clear configuration error if API credentials or model settings are missing.

### Qdrant Vector Store

Responsibility:

- create or reuse a MOF collection;
- upsert embedded chunks with metadata payload;
- search by query vector and return scored chunks.

Configuration:

```text
RAG_VECTOR_STORE_URL
RAG_QDRANT_COLLECTION
```

The vector store should not silently rebuild every query. Indexing should be an explicit setup step or startup command so the API path stays predictable.

### Vector Retriever

Responsibility:

- embed the user query;
- search Qdrant;
- map vector results back into the existing retrieval result shape;
- preserve metadata for `sources` and `kg_facts`.

It should return the same kind of evidence-bearing object expected by the answerer and `HybridRetriever`.

### LLM Answerer

Responsibility:

- generate a natural-language answer from retrieved evidence only;
- preserve citations/source ids;
- refuse to answer when no evidence exists;
- keep deterministic answerer as fallback when LLM configuration is unavailable.

Prompt rules:

- use only provided evidence;
- do not use `References/` as knowledge;
- cite source ids like `[S1]`, `[S2]`;
- if evidence is insufficient, say so;
- include DOI/refcode/source metadata through the response payload, not only prose.

Configuration:

```text
RAG_LLM_PROVIDER
RAG_LLM_MODEL
RAG_API_KEY
```

## Retrieval Strategy

The default API-first retrieval strategy should be:

```text
VectorRetriever
  -> primary semantic retrieval from Qdrant

KeywordRetriever
  -> fallback for exact refcode/material/property matches

GraphRetriever
  -> future KG teammate output

HybridRetriever
  -> dedupe and rank combined evidence
```

This keeps exact material/property lookups from regressing while adding true semantic retrieval.

## Indexing Flow

Add an explicit indexing command or script:

```text
load KnowledgeStore
  -> build chunks
  -> call EmbeddingProvider.embed_texts
  -> upsert into QdrantVectorStore
```

This should be runnable before starting the API:

```bash
python -m app.scripts.index_vectors
```

The API should fail with a clear message if vector mode is enabled but the vector index is missing.

## API Behavior

Keep the existing request/response contract:

```text
POST /api/query
  request: question, top_k
  response: query, mode, answer, sources, kg_facts, retrieved_count
```

Add modes such as:

```text
vector_rag
hybrid_rag
insufficient_evidence
```

Do not require the frontend to understand whether the answer came from vector, keyword, or graph retrieval.

## Frontend Behavior

The frontend can remain simple for the first real RAG pass:

- question input;
- answer block;
- source cards;
- KG/fact path cards;
- clear error when backend/vector setup is not ready.

Optional later enhancement:

- show `mode`;
- show retrieved source count;
- show whether vector/keyword/KG contributed evidence.

## Error Handling

The real RAG path must fail loudly and usefully:

- missing API key: return setup/configuration error, not a fabricated answer;
- Qdrant unreachable: return a backend error with a clear message;
- empty vector index: return setup guidance;
- no evidence retrieved: return `insufficient_evidence`;
- LLM unavailable: use deterministic evidence-only fallback if retrieval succeeded.

## Testing Criteria

The next implementation pass should add tests for:

- chunk building preserves source metadata;
- missing embedding config raises a clear error;
- vector retriever maps vector hits into the existing retrieval result shape;
- hybrid retrieval can combine vector and keyword evidence;
- no-evidence queries return `insufficient_evidence`;
- LLM answerer refuses to answer without evidence;
- API still returns the existing schema.

External API and Qdrant calls should be tested with fakes/mocks in unit tests. End-to-end live API/Qdrant verification can be an optional manual check because it requires credentials and a running vector database.

## Build Order

1. Add configuration fields for embedding, LLM, and Qdrant.
2. Add document chunk builder over current `KnowledgeStore.documents`.
3. Add `EmbeddingProvider` interface and API implementation.
4. Add `QdrantVectorStore`.
5. Add explicit vector indexing script.
6. Add `VectorRetriever`.
7. Update `HybridRetriever` wiring to prefer vector retrieval while retaining keyword fallback and graph slot.
8. Add `LLMAnswerer` with deterministic fallback.
9. Update README with environment variables, Qdrant startup, indexing, API startup, and frontend startup.
10. Add tests and manual verification notes.

## Success Definition

The real RAG phase is complete when:

- a vector index can be built from MOF runtime data;
- `POST /api/query` can retrieve evidence from Qdrant;
- the answer can be generated by an LLM from retrieved evidence;
- sources and KG/fact paths remain visible in the API response;
- keyword fallback still handles exact material/property lookups;
- KG integration remains an adapter layer, not a blocker;
- the project still has a documented local run path.
