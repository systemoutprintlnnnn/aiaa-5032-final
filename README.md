# MOF KG-Enhanced RAG

This repository is currently focused on getting a complete local MOF QA flow working.

The local baseline is a simple RAG-style system. KG is an adapter layer and is not required for baseline execution.

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

## Run Tests

```bash
PYTHONPATH=backend pytest -q
```

## Current Capabilities

- Loads public MOF-ChemUnity sample data.
- Normalizes materials, names, properties, synthesis facts, and water-stability facts into evidence-backed facts and document-style records.
- Supports a simple keyword/entity retriever and an empty KG adapter slot through a hybrid retriever.
- Returns deterministic evidence-based answers with:
  - source cards,
  - DOI/refcode metadata,
  - graph-style fact paths.

## Next Upgrade

After this simple local RAG baseline works end-to-end:

- connect the KG teammate's output through the graph retriever adapter;
- add vector retrieval only after the local baseline is stable;
- add LLM answer generation only after retrieval can provide cited evidence reliably.
