# Roadmap

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

## Milestone 2: Simple RAG Core Hardening

Status: implemented.

- Runtime facts and document-style evidence are visible in the store.
- Retrieval is behind a formal retriever interface.
- Keyword/entity retrieval remains the default fallback.
- Hybrid retrieval merges local and future KG/vector evidence.
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

## Milestone 4: RAG Operations Hardening

Status: next.

- Add safer vector indexing controls.
- Add a repeatable real RAG smoke command.
- Add collection readiness checks and better errors for missing vector indexes.
- Keep the default keyword path independent from Qdrant and API availability.

## Milestone 5: Evaluation

Status: planned.

- Build a small question set.
- Compare keyword and hybrid vector modes.
- Record retrieved fact IDs, source coverage, answer mode, and insufficient-evidence behavior.
- Use results to tune retrieval order and citation verification.

## Milestone 6: KG Adapter Integration

Status: pending KG output.

- Accept the KG teammate's graph facts through a real `GraphRetriever`.
- Preserve graph-style paths in `kg_facts`.
- Compare keyword, vector, and graph-enhanced modes.
- Keep KG as an additive extension.

## Milestone 7: Demo Polish

Status: planned.

- Prepare demo examples for property QA and synthesis/descriptive QA.
- Add a concise project walkthrough.
- Keep frontend contract stable while improving presentation.
