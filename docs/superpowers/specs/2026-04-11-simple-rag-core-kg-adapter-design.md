# Simple RAG Core With KG Adapter Slot Design

## Purpose

This project should first become a complete local MOF question-answering system, not a blocked KG integration project.

The primary milestone is a runnable simple RAG baseline:

```text
runtime MOF data
  -> data loading
  -> ingestion and normalization
  -> local document/fact store
  -> retrieval
  -> evidence-backed answer composition
  -> FastAPI API
  -> frontend UI
```

Knowledge graph support is an extension layer. It should be easy to attach once the teammate responsible for KG produces graph data, a graph service, or a retriever-compatible output format.

## Scope

In scope:

- local FastAPI backend;
- static local frontend;
- runtime MOF data from open/project/course sources;
- simple RAG-style retrieval over normalized MOF documents and facts;
- deterministic evidence-backed answer composition as the first answerer;
- tests and demo queries that prove the full path works;
- a KG adapter slot that can accept graph facts later.

Out of scope for the next implementation pass:

- using `References/` as the runtime QA corpus;
- requiring Neo4j before the core RAG path works;
- requiring Qdrant before the in-memory/local retriever works;
- requiring an LLM before deterministic evidence-backed answers work;
- deploying to Vercel or any remote host.

## Data Boundary

`References/` is planning context only. It must not be chunked, embedded, indexed, or used as runtime QA data.

Runtime QA data can come from:

- `backend/data/open_source/`;
- course-provided datasets;
- team-provided MOF data or KG exports;
- future literature ingestion, only if explicitly added as a product feature.

Every imported source should keep visible source and license metadata. Repositories with no explicit license remain reference-only unless the user approves using them.

## Target Architecture

The backend should be organized around replaceable interfaces:

```text
DataSource
  -> Ingestion / Normalizer
  -> InMemoryStore
  -> Retriever
  -> Answerer
  -> QueryService
  -> FastAPI routes
```

The KG extension path should preserve the same API:

```text
KG teammate output
  -> KGAdapter / GraphRetriever
  -> HybridRetriever
  -> QueryService
  -> same QueryResponse
```

The frontend should not need to know whether evidence came from simple RAG, KG, or hybrid retrieval. It should render the same response fields:

- `answer`;
- `sources`;
- `kg_facts`;
- `mode`;
- `retrieved_count`.

## Proposed Backend Layout

Keep existing working code where possible, but move toward this structure:

```text
backend/app/
  main.py
  config.py
  models.py

  data_sources/
    base.py
    open_source_mof.py

  ingestion/
    normalizer.py
    chunker.py

  stores/
    schemas.py
    in_memory.py

  retrievers/
    base.py
    keyword.py
    graph.py
    hybrid.py

  answerers/
    deterministic.py

  services/
    query_service.py
```

Current `knowledge_store.py` can be kept temporarily while extracting responsibilities. The implementation should avoid a large rewrite that breaks the current local MVP.

## Core Types

The RAG core needs two normalized runtime objects.

`Document` represents retrievable text:

```text
id: stable string
text: retrievable evidence text
metadata:
  material_id/refcode
  material_names
  source
  doi
  license
  relation/property when available
```

`Fact` represents structured evidence:

```text
id: stable string
subject/material
relation
value
evidence
source metadata
path
```

The current `Fact` dataclass already covers much of this. The next pass should add `Document` or a document-like equivalent without removing the existing evidence path.

## Retrieval Behavior

The default retrieval path should be simple and local:

1. Convert user question into searchable tokens.
2. Search normalized documents and facts.
3. Prefer explicit material/entity matches.
4. Prefer relation matches when the query asks for water stability, synthesis, surface area, pore volume, uptake, aliases, or similar hard facts.
5. Return ranked evidence items with source metadata.
6. Return insufficient evidence when no reasonable evidence is found.

This path is the baseline RAG system. It should work even without KG, vector search, or an LLM.

## KG Adapter Contract

The KG teammate should not need to change FastAPI or the frontend. They can integrate by providing a retriever that returns the same retrieval result shape.

`GraphRetriever` should accept a question and return graph-backed evidence with:

```text
fact/document id
score
subject/material
relation
value
path
evidence
source metadata
```

Possible KG input formats:

- local JSON export;
- local CSV edge/node export;
- Neo4j query result;
- a Python function or service that returns graph facts.

`HybridRetriever` should merge simple RAG results and graph results, deduplicate by source/material/relation/value, and preserve KG paths for display.

## Answering Behavior

The first answerer should remain deterministic and evidence-only:

- Do not invent facts.
- Cite the retrieved evidence.
- Include DOI/refcode/source when available.
- Show graph-style paths when present.
- Return an insufficient-evidence response when retrieval finds nothing.

An LLM answerer can be added later behind the same answerer interface, but it must only summarize retrieved evidence and must preserve citations.

## Frontend Behavior

The local frontend should remain minimal:

- question input;
- submit button;
- answer block;
- source cards;
- KG/fact path cards;
- clear failure message when the backend is not running.

The frontend can keep calling `http://127.0.0.1:8000/api/query` because the current project target is local execution.

## Testing And Demo Criteria

The next implementation pass should add tests that prove:

- seed data loads;
- normalized facts/documents include source metadata;
- a hard-fact query returns the expected evidence;
- an insufficient-evidence query returns the expected mode;
- the FastAPI `/api/health` endpoint returns loaded-data status;
- the FastAPI `/api/query` endpoint returns sources and fact paths;
- an empty/no-result `GraphRetriever` does not break the simple RAG path.

Demo queries should include:

- `What is the BET surface area of UTSA-67?`
- `Is Zn(LTP)2 water stable?`
- `What synthesis conditions are reported for UTSA-67?`
- `What names are associated with CSD ref code CUVVOG?`
- one unsupported question to demonstrate insufficient evidence.

## Build Order

1. Preserve the existing local working path.
2. Add tests around current behavior.
3. Introduce normalized document/store interfaces.
4. Extract data loading and normalization from `knowledge_store.py` gradually.
5. Add a no-op or fixture-backed `GraphRetriever` contract.
6. Add `HybridRetriever` that can merge keyword/RAG and graph evidence.
7. Update docs and demo commands.
8. Verify backend compile, tests, health endpoint, query endpoint, and frontend static serving.

## Success Definition

The project is ready for the next phase when:

- a fresh local run can start the FastAPI backend;
- the frontend can query the backend;
- at least four MOF demo questions return grounded answers;
- unsupported questions return insufficient evidence;
- tests cover the current simple RAG path;
- KG integration has a clear adapter contract but is not required for baseline execution.
