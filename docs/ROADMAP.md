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

Status: partially implemented.

## Milestone 2: Cleaner Retrieval

- Move retrieval behind a formal retriever interface.
- Keep the keyword/entity retriever as fallback.
- Add smoke tests for key sample questions.

## Milestone 3: Vector Retrieval

- Add Qdrant adapter.
- Add embedding config.
- Keep keyword/entity fallback and compare retrieval output.

## Milestone 4: Graph Retrieval

- Add Neo4j adapter.
- Add template Cypher for hard facts.
- Later add constrained Text-to-Cypher.

## Milestone 5: LLM Answering

- Add LLM adapter only after retrieval is stable.
- Enforce evidence-only answer generation.
- Add citation verification and insufficient-evidence handling.

## Milestone 6: Evaluation And Demo

- Build a small question set.
- Compare keyword, vector, and graph-enhanced modes.
- Prepare demo examples for property QA and synthesis/descriptive QA.
