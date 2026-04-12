# MOF KG-Enhanced RAG

This repository is currently focused on getting a complete local MOF QA flow working.

The default local baseline is a simple RAG-style system. The real RAG path can be enabled with Zhipu OpenAI-compatible API embeddings, Qdrant, and a Zhipu LLM. KG is an adapter layer and is not required for baseline execution.

Project planning docs live in `docs/`, especially `docs/PLAN.md`, `docs/ARCHITECTURE.md`, and `docs/API_CONTRACT.md`.

Important distinction:

- `References/` contains planning/reference papers and slides.
- Runtime QA knowledge does **not** come from `References/`.
- The current runtime seed data uses public MOF-ChemUnity sample data under `backend/data/open_source/`.

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

## Run Frontend

Open `frontend/index.html` in a browser while the backend is running.

Or serve the static frontend locally:

```bash
python3 -m http.server 5173 --directory frontend
```

Then open:

```text
http://127.0.0.1:5173/
```

The page calls:

```text
http://127.0.0.1:8000/api/query
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

Build the vector index:

```bash
PYTHONPATH=backend python3 -m app.scripts.index_vectors
```

Then start the backend and frontend using the same commands above.

For a fuller local checklist, see `docs/LOCAL_RUNBOOK.md`.

## Run Tests

```bash
PYTHONPATH=backend pytest -q
```

## Current Capabilities

- Loads public MOF-ChemUnity sample data.
- Normalizes materials, names, properties, synthesis facts, and water-stability facts into evidence-backed facts and document-style records.
- Supports a simple keyword/entity retriever, a Zhipu API embedding + Qdrant vector retriever, and an empty KG adapter slot through a hybrid retriever.
- Returns deterministic evidence-based answers with:
  - source cards,
  - DOI/refcode metadata,
  - graph-style fact paths.
- Can use an API LLM answerer when `RAG_ENABLE_LLM=true`.

## Next Upgrade

After this API-first real RAG path works end-to-end:

- connect the KG teammate's output through the graph retriever adapter;
- add evaluation scripts for keyword vs vector vs KG-enhanced retrieval;
- tighten citation verification for LLM answers.
