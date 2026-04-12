# Local Runbook

## Default Local Path

This path does not require an API key, Qdrant, or KG data.

```bash
python3 -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Check the backend:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/rag/status
```

Ask a seeded MOF question:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the BET surface area of UTSA-67?","top_k":3}'
```

## API-First Real RAG Path

Start Qdrant:

```bash
docker compose up -d qdrant
```

Configure the API-backed RAG path. The example file uses Zhipu `embedding-3`, `glm-4.6v`, and the OpenAI-compatible base URL `https://open.bigmodel.cn/api/paas/v4/`.

```bash
cp .env.example .env
# Fill RAG_API_KEY in .env, then export it in your shell or source it.
set -a
source .env
set +a
```

Build the vector index:

```bash
PYTHONPATH=backend python3 -m app.scripts.index_vectors
```

This indexes all normalized evidence chunks into `RAG_QDRANT_COLLECTION`. With the current MOF-ChemUnity seed data this is a real embedding API run, so do it intentionally.

Run the backend:

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Use `/api/rag/status` to confirm the active mode without exposing the API key:

```bash
curl http://127.0.0.1:8000/api/rag/status
```

Expected real RAG status after sourcing `.env`:

```json
{
  "retrieval_mode": "hybrid",
  "vector_store_enabled": true,
  "llm_enabled": true,
  "api_key_configured": true,
  "api_base_url": "https://open.bigmodel.cn/api/paas/v4/",
  "embedding_provider": "zhipu",
  "embedding_model": "embedding-3",
  "vector_store_url": "http://127.0.0.1:6333",
  "qdrant_collection": "mof_evidence",
  "llm_provider": "zhipu",
  "llm_model": "glm-4.6v"
}
```

The manually verified smoke path used `mof_evidence_smoke` with one UTSA-67 BET evidence chunk. The full `mof_evidence` collection should be indexed before using hybrid mode broadly.

## Frontend

Open `frontend/index.html` while the backend is running, or serve it locally:

```bash
python3 -m http.server 5173 --directory frontend
```

Then open `http://127.0.0.1:5173/`.
