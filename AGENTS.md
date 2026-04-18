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

The first milestone was end-to-end behavior, not a perfect RAG stack. That milestone is now implemented.

Build in this order:

1. Deterministic backend API with evidence-backed answers. Implemented.
2. Minimal frontend that calls the API and displays answer, sources, and KG-style facts. Implemented.
3. Replaceable retrieval interfaces. Implemented.
4. Qdrant vector retrieval. Implemented as an API-first path and smoke-tested with Zhipu embeddings.
5. LLM generation. Implemented through a Zhipu OpenAI-compatible chat completions adapter.
6. Neo4j/Text-to-Cypher graph retrieval. Future KG adapter work.
7. Citation verification and evaluation. Next hardening work.

Do not let Qdrant, KG, or LLM failures break the default keyword/deterministic local path.

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

Health/status checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/rag/status
```

Example query:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the BET surface area of UTSA-67?","top_k":3}'
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/` while the backend is running. The frontend is a
Next.js + TypeScript app and calls `NEXT_PUBLIC_API_BASE_URL` when provided,
otherwise `http://127.0.0.1:8000`.

Run Qdrant:

```bash
docker compose up -d qdrant
```

Configure API-first real RAG locally:

```bash
cp .env.example .env
# Fill RAG_API_KEY in .env. Do not commit .env.
set -a
source .env
set +a
```

Build the vector index:

```bash
PYTHONPATH=backend python3 -m app.scripts.index_vectors
```

Run tests:

```bash
PYTHONPATH=backend pytest -q
cd frontend && npm test && npm run typecheck && npm run build
```
