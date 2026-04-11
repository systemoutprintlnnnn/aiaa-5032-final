# Roadmap

## Milestone 0: Project Rules

- Keep `References/` as design context only.
- Keep planning docs under `docs/`.
- Keep runtime data and license notes under `backend/data/`.

## Milestone 1: FastAPI MVP

- FastAPI health endpoint.
- Query endpoint with stable response schema.
- Runtime seed data loader.
- Deterministic evidence-backed answerer.
- Minimal frontend.

Status: implemented as the local baseline path.

## Milestone 2: Simple RAG Core Hardening

- Keep runtime facts and document-style evidence visible in the store.
- Move retrieval behind a formal retriever interface.
- Keep the keyword/entity retriever as fallback.
- Add a hybrid retriever that can merge simple RAG and future KG evidence.
- Add smoke tests for key sample questions.

## Milestone 3: KG Adapter Integration

- Accept the KG teammate's graph facts through `GraphRetriever`.
- Preserve graph-style paths in `kg_facts`.
- Keep the simple RAG path working if the graph retriever returns no results.

## Milestone 4: Vector Retrieval

- Add vector retrieval only after the local baseline and KG adapter contract are stable.
- Keep keyword/entity fallback and compare retrieval output.

## Milestone 5: LLM Answering

- Add LLM adapter only after retrieval is stable and cited evidence is reliable.
- Enforce evidence-only answer generation.
- Add citation verification and insufficient-evidence handling.

## Milestone 6: Evaluation And Demo

- Build a small question set.
- Compare keyword, vector, and graph-enhanced modes.
- Prepare demo examples for property QA and synthesis/descriptive QA.
