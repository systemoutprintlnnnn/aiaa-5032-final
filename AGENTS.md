# Project Instructions

Detailed build planning lives in `docs/`. Start with `docs/PLAN.md`, `docs/ARCHITECTURE.md`, and `docs/API_CONTRACT.md` before making architectural changes.

## Core Correction

`References/` is only for planning and design context. Do **not** index, chunk, embed, or use files in `References/` as the runtime QA knowledge corpus.

Runtime knowledge must come from one of these sources:

- open-source MOF data with compatible license;
- team/project-provided MOF KG or data files;
- course-provided datasets;
- later, real literature ingestion when explicitly added as a product feature.

The current runtime seed data is in `backend/data/open_source/` and comes from `AI4ChemS/MOF_ChemUnity`. Keep its license notes visible: code is MIT, data/content is CC BY-NC 4.0.

## Coding Strategy

The first milestone is end-to-end behavior, not a perfect RAG stack.

Build in this order:

1. Deterministic backend API with evidence-backed answers.
2. Minimal frontend that calls the API and displays answer, sources, and KG-style facts.
3. Replaceable retrieval interfaces.
4. Qdrant vector retrieval.
5. Neo4j/Text-to-Cypher graph retrieval.
6. LLM generation and citation verification.

Do not add Qdrant, Neo4j, or an LLM dependency before the simple local path is stable.

## Architecture Boundaries

Keep backend modules small and replaceable:

- `knowledge_store.py`: load and normalize runtime data into facts.
- `retrievers/`: retrieve facts/chunks for a query behind replaceable interfaces.
- `services/`: orchestrate retrieval and answer composition.
- `answerer.py`: compose an answer from retrieved evidence.
- `models.py`: Pydantic request/response/data contracts.
- `main.py`: FastAPI wiring only.

Future adapters should preserve the same shape:

- `VectorRetriever` can replace keyword retrieval.
- `Neo4jRetriever` can replace or supplement in-memory KG facts.
- `LLMAnswerer` can replace deterministic answer composition, but must still cite supplied evidence.

## Answering Rules

- Every factual answer must be grounded in retrieved facts or evidence.
- If evidence is not found, return an insufficient-evidence answer.
- Include DOI/refcode/source metadata whenever available.
- Keep graph-style paths visible, e.g. `Material(CUVVOG) -> HAS_PROPERTY -> BET Surface Area`.
- Do not answer from the reference papers/slides unless the user is asking about the project plan itself.

## Data Rules

- Do not silently mix design references with runtime QA data.
- Keep source and license metadata close to imported datasets.
- Avoid committing generated caches or local secrets.
- If a repository has no explicit license, treat it as reference-only unless the user approves using it.

## Current Useful Commands

Run backend:

```bash
python3 -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Example query:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the BET surface area of UTSA-67?","top_k":3}'
```

Static frontend:

```text
frontend/index.html
```

Open it in a browser while the backend is running.
