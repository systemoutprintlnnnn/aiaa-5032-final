# MOF KG-Enhanced RAG - Current Project Plan

## Non-Negotiable Boundary

`References/` is design context only. Do not chunk, embed, index, or answer runtime QA from PDFs or PPTX files in that directory.

Runtime QA knowledge must come from compatible runtime data:

- open-source MOF data with compatible license;
- team/project-provided MOF KG or data files;
- course-provided datasets;
- later, explicit literature ingestion if it becomes a planned product feature.

The current runtime seed is `AI4ChemS/MOF_ChemUnity` data under `backend/data/open_source/`. Keep license notes visible: code is MIT, data/content is CC BY-NC 4.0.

## Current Product Goal

Build a small but working MOF-specific QA system that can run locally and can be extended with KG output later.

The project currently supports:

- a FastAPI backend;
- a static browser frontend;
- evidence-backed answers with sources and graph-style facts;
- a default keyword/deterministic local path;
- an API-first real RAG path using Zhipu `embedding-3`, Qdrant, and Zhipu `glm-4.6v`;
- a replaceable KG adapter slot.

## Current Architecture

```text
MOF-ChemUnity runtime data
  -> KnowledgeStore
  -> normalized facts and evidence chunks
  -> KeywordRetriever fallback
  -> Qdrant VectorRetriever when enabled
  -> KG GraphRetriever slot when available
  -> HybridRetriever
  -> DeterministicAnswerer or Zhipu-backed OpenAI-compatible LLM answerer
  -> FastAPI /api/query
  -> frontend/index.html
```

The default local mode remains intentionally simple and should keep working without API keys, Qdrant, or KG data.

## Verified State

- Default local API answers seeded questions such as UTSA-67 BET surface area.
- `/api/health` reports the loaded MOF-ChemUnity seed data.
- `/api/rag/status` reports active retrieval/LLM configuration without exposing the API key.
- Zhipu `embedding-3` has been smoke-tested and returned 2048-dimensional vectors.
- Qdrant has been smoke-tested with a one-point `mof_evidence_smoke` collection.
- Zhipu `glm-4.6v` has been smoke-tested through the OpenAI-compatible chat completions path.

The full `mof_evidence` vector collection still needs an intentional full indexing run before vector retrieval should be considered ready for the complete seed corpus.

## Development Phases

### Phase 1: Local Baseline

Status: implemented.

- FastAPI `/api/health` and `/api/query`.
- MOF-ChemUnity seed data loader.
- Deterministic evidence-backed answerer.
- Static frontend.

### Phase 2: Replaceable Retrieval Core

Status: implemented.

- Formal retriever interface.
- Keyword/entity retriever.
- Hybrid retriever.
- Empty KG adapter slot.
- Tests for seeded sample questions.

### Phase 3: API-First Real RAG

Status: implemented and smoke-tested.

- Evidence chunk builder.
- Zhipu/OpenAI-compatible embedding provider.
- Qdrant vector store adapter.
- Vector retriever.
- Zhipu/OpenAI-compatible LLM answerer.
- Local `.env.example`, Qdrant compose service, and runbook.

### Phase 4: RAG Operations Hardening

Status: next priority.

- Add safe indexing controls such as `--collection`, `--limit`, `--refcode`, `--reset`, and `--dry-run`.
- Add a repeatable real RAG smoke command that checks `.env`, Qdrant health, collection count, retrieval, and LLM answering.
- Add clear handling for missing or empty Qdrant collections.
- Avoid accidental large embedding runs during development.

### Phase 5: Evaluation

Status: next priority after indexing hardening.

- Build a small demo/evaluation question set covering:
  - BET surface area;
  - water stability;
  - aliases/refcodes;
  - synthesis conditions;
  - application facts;
  - insufficient-evidence behavior.
- Compare default keyword mode against hybrid vector mode.
- Track retrieved fact IDs, source coverage, and answer mode.

### Phase 6: KG Adapter Integration

Status: pending external KG output.

- Define a graph fact import format.
- Implement a real `GraphRetriever` behind the existing retriever interface.
- Preserve the existing API response contract.
- Keep KG as an additive layer, not a blocker for local RAG.

## Immediate Priority

The next implementation slice should be indexing and verification tooling for the real RAG path. This turns the current manual smoke test into a repeatable command before the project spends more effort on KG or broader UI work.
