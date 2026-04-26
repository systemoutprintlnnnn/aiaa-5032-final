# MOF KG-Enhanced RAG

This repository is currently focused on a local MOF QA system that can run in two modes:

- default local mode: keyword/entity/KG retrieval with deterministic evidence-backed answers;
- API-first real RAG mode: Zhipu OpenAI-compatible embeddings, Qdrant vector retrieval, and a Zhipu LLM answerer.

KG is an adapter layer and is not required for baseline execution.

Project planning docs live in `docs/`, especially `docs/PLAN.md`, `docs/ARCHITECTURE.md`, and `docs/API_CONTRACT.md`.

Important distinction:

- `References/` contains planning/reference papers and slides.
- Runtime QA knowledge does **not** come from `References/`.
- The current runtime seed data uses public MOF-ChemUnity sample data under `backend/data/open_source/`.
- The local KG adapter reads team/course-provided graph data from `backend/data/kg/mof_kg.json`.
- The RAG evidence layer also reads team/course-provided synthesis evidence from `reference_code/MOF_KG/3.MOF-Synthesis.json`.

## Run Backend

```bash
python3 -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Health check:

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

KG-backed example query:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What solvent is used in UNABAN?","top_k":5}'
```

Synthesis evidence example query:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What synthesis evidence is available for YEXLAR?","top_k":5}'
```

Regenerate the runtime KG JSON from the copied builder and source data:

```bash
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format json
```

## Run Frontend

The frontend is a Next.js + TypeScript app. Start it while the backend is
running:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:5173/
```

The app calls:

```text
http://127.0.0.1:8000/api/query
```

To point the frontend at a different backend URL, set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Run API-First Real RAG

Start Qdrant:

```bash
docker compose up -d qdrant
```

Configure API-backed retrieval and answering:

```bash
cp .env.example .env
# Fill RAG_API_KEY in .env.
set -a
source .env
set +a
```

The example configuration uses Zhipu `embedding-3` for embeddings and `glm-4.6v` for LLM answers through the OpenAI-compatible base URL.

Keep `.env` local. It is ignored by Git and must contain the real API key only on your machine.

Build the vector index:

```bash
PYTHONPATH=backend python3 -m app.scripts.index_vectors
```

The index is built from normalized evidence documents. That includes the
MOF-ChemUnity seed facts and row-level KG synthesis evidence documents when
`reference_code/MOF_KG/3.MOF-Synthesis.json` is present.

Then start the backend and frontend using the same commands above.

For a fuller local checklist, see `docs/LOCAL_RUNBOOK.md`.

Current verified smoke path:

- Zhipu `embedding-3` returned 2048-dimensional vectors.
- Qdrant accepted and retrieved a smoke `mof_evidence_smoke` point.
- Backend returned `mode=hybrid_rag` for the UTSA-67 BET surface area question with Zhipu `glm-4.6v`.

Before treating the vector path as production-ready for the whole seed dataset, build the full `mof_evidence` Qdrant collection with the indexing script.

## Run Tests

```bash
PYTHONPATH=backend pytest -q
cd frontend && npm test && npm run typecheck && npm run build
```

## Current Capabilities

- Loads public MOF-ChemUnity sample data.
- Normalizes materials, names, properties, synthesis facts, KG synthesis evidence rows, and water-stability facts into evidence-backed facts and document-style records.
- Supports a simple keyword/entity retriever, a Zhipu API embedding + Qdrant vector retriever, and a local JSON KG graph retriever through a hybrid retriever.
- Returns deterministic evidence-based answers with:
  - source cards,
  - DOI/refcode metadata,
  - graph-style fact paths.
- Can use an API LLM answerer when `RAG_ENABLE_LLM=true`.
- Provides a Next.js + TypeScript local workbench for querying FastAPI and
  reviewing answer evidence.

## Next Upgrade

The next practical upgrades are:

- make vector indexing safer to operate with CLI flags such as `--limit`, `--refcode`, `--collection`, and `--reset`;
- add a small evaluation set for keyword vs hybrid vector vs KG retrieval;
- tighten citation verification for LLM answers;
