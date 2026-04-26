# Completed Roadmap

This roadmap records the final implementation state for the current submission. There is no active next milestone.

## Milestone 0: Project Rules

Status: implemented and enforced in docs.

- Keep `References/` as design context only.
- Keep planning docs under `docs/`.
- Keep runtime data and license notes under `backend/data/`.

## Milestone 1: FastAPI MVP

Status: implemented.

- FastAPI health endpoint.
- Query endpoint with stable response schema.
- Runtime seed data loader.
- Deterministic evidence-backed answerer.
- Minimal frontend.
- Next.js + TypeScript frontend polish.

## Milestone 2: Simple RAG Core Hardening

Status: implemented.

- Runtime facts and document-style evidence are visible in the store.
- Retrieval is behind a formal retriever interface.
- Keyword/entity retrieval remains the default fallback.
- Hybrid retrieval merges local keyword, vector, and KG evidence.
- Smoke tests cover key sample questions.

## Milestone 3: API-First Real RAG

Status: implemented and smoke-tested.

- Zhipu/OpenAI-compatible embedding provider.
- Qdrant vector store wrapper.
- Explicit indexing script.
- Vector retriever.
- Zhipu/OpenAI-compatible LLM answerer with deterministic fallback.
- `/api/rag/status` readiness endpoint.
- Local `.env.example` and Docker Compose Qdrant setup.

## Milestone 4: RAG Operations Hardening Ideas

Status: archived, not part of the completed submission scope.

- Safer vector indexing controls, repeatable live RAG smoke commands, and collection readiness checks were considered for a larger operations iteration.
- The submitted code keeps vector indexing as an explicit command and keeps the default keyword path independent from Qdrant and API availability.

## Milestone 5: Evaluation Ideas

Status: archived, not part of the completed submission scope.

- A larger evaluation slice could compare keyword, vector, and KG retrieval modes.
- Current automated tests cover the delivered demo behaviors, retrieval contracts, and insufficient-evidence behavior.

## Milestone 6: KG Adapter Integration

Status: implemented as local JSON KG retrieval.

- Accept the KG graph export from `backend/data/kg/mof_kg.json` through `KGGraphRetriever`.
- Preserve graph-style paths in `kg_facts`.
- Keep KG as an additive extension.

## Milestone 7: Demo Polish

Status: implemented.

- Prepared demo examples for property QA, KG solvent QA, shared-neighbor KG QA, and synthesis/descriptive QA.
- Added concise project walkthrough docs.
- Keep frontend contract stable while improving presentation.
- Keep the local workbench focused on query, answer, sources, and KG-style
  facts.
