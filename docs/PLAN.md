# MOF KG-Enhanced RAG - Completed Project Plan

## Non-Negotiable Boundary

`References/` is design context only. Do not chunk, embed, index, or answer runtime QA from PDFs or PPTX files in that directory.

Runtime QA knowledge must come from compatible runtime data:

- open-source MOF data with compatible license;
- team/project-provided MOF KG or data files;
- course-provided datasets;
- explicit literature ingestion only if it becomes an approved product feature.

The current runtime seed is `AI4ChemS/MOF_ChemUnity` data under `backend/data/open_source/`. Keep license notes visible: code is MIT, data/content is CC BY-NC 4.0.

## Completed Product Scope

The project delivers a small working MOF-specific QA system that runs locally and can optionally use API-backed vector retrieval and LLM answering.

The completed scope supports:

- a FastAPI backend;
- a Next.js + TypeScript browser frontend;
- evidence-backed answers with sources and graph-style facts;
- a default keyword/deterministic local path;
- an API-first real RAG path using Zhipu `embedding-3`, Qdrant, and Zhipu `glm-4.6v`;
- local JSON KG retrieval through `KGGraphRetriever`;
- streamed query responses through `/api/query/stream`.

## Current Architecture

```text
MOF-ChemUnity runtime data
  -> KnowledgeStore
  -> normalized facts and evidence chunks
  -> KeywordRetriever fallback
  -> Qdrant VectorRetriever when enabled
  -> KGGraphRetriever when KG is enabled and backend/data/kg/mof_kg.json is valid
  -> HybridRetriever
  -> DeterministicAnswerer or Zhipu-backed OpenAI-compatible LLM answerer
  -> FastAPI /api/query and /api/query/stream
  -> frontend Next.js workbench
```

The default local mode remains intentionally simple and should keep working without API keys, Qdrant, or KG data.

## Verified State

- Default local API answers seeded questions such as UTSA-67 BET surface area, Zn(LTP)2 water stability, KG solvent lookups, and synthesis-evidence questions.
- `/api/health` reports 100 loaded MOF-ChemUnity demo materials and 47,823 normalized facts with the current checked-in data.
- `/api/rag/status` reports active retrieval/LLM configuration without exposing the API key.
- The checked-in local KG JSON loads successfully and exposes 218,662 graph facts through `KGGraphRetriever`.
- Zhipu `embedding-3` has been smoke-tested and returned 2048-dimensional vectors.
- Qdrant has been smoke-tested with a one-point `mof_evidence_smoke` collection.
- Zhipu `glm-4.6v` has been smoke-tested through the OpenAI-compatible chat completions path.
- Unit tests cover backend API, retrieval, KG graph retrieval, vector adapters, LLM answerer behavior, indexing truncation, and frontend presentation helpers.

## Development Phases

### Phase 1: Local Baseline

Status: implemented.

- FastAPI `/api/health` and `/api/query`.
- MOF-ChemUnity seed data loader.
- Deterministic evidence-backed answerer.
- Next.js + TypeScript frontend workbench.

### Phase 2: Replaceable Retrieval Core

Status: implemented.

- Formal retriever interface.
- Keyword/entity retriever.
- Hybrid retriever.
- Local JSON KG graph retriever and empty fallback retriever.
- Tests for seeded sample questions.

### Phase 3: API-First Real RAG

Status: implemented and smoke-tested.

- Evidence chunk builder.
- Zhipu/OpenAI-compatible embedding provider.
- Qdrant vector store adapter.
- Vector retriever.
- Zhipu/OpenAI-compatible LLM answerer.
- Local `.env.example`, Qdrant compose service, and runbook.

### Phase 4: RAG Operations Hardening Ideas

Status: archived, not an active next milestone for the completed submission.

- Safe indexing flags such as `--collection`, `--limit`, `--refcode`, `--reset`, and `--dry-run` were considered for a larger operations-focused iteration.
- The current submitted code keeps indexing explicit through `PYTHONPATH=backend python3 -m app.scripts.index_vectors`.
- Default keyword/deterministic mode remains independent from Qdrant, API keys, and LLM availability.

### Phase 5: Evaluation Ideas

Status: archived, not an active next milestone for the completed submission.

- If the project is reopened, an evaluation slice could compare questions covering:
  - BET surface area;
  - water stability;
  - aliases/refcodes;
  - synthesis conditions;
  - application facts;
  - insufficient-evidence behavior.
- Current automated tests already cover the main local demo behaviors and insufficient-evidence behavior.

### Phase 6: KG Adapter Integration

Status: implemented as a local JSON graph adapter.

- Use `backend/data/kg/mof_kg.json` as the runtime KG export.
- Implement a real `KGGraphRetriever` behind the existing retriever interface.
- Preserve the existing API response contract.
- Keep KG as an additive layer, not a blocker for local RAG.

## Active Priority

There is no active next implementation milestone. Treat this document as the completed project plan for the current codebase.
