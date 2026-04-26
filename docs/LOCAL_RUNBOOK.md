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

This indexes all normalized evidence chunks into `RAG_QDRANT_COLLECTION`. The
current corpus includes MOF-ChemUnity seed facts plus row-level KG synthesis
evidence from `reference_code/MOF_KG/3.MOF-Synthesis.json` when that file is
present. This is a real embedding API run, so do it intentionally.

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
  "kg_enabled": true,
  "kg_graph_path": "/absolute/path/backend/data/kg/mof_kg.json",
  "kg_graph_loaded": true,
  "kg_fact_count": 218662,
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

Useful smoke questions after indexing:

- `What synthesis evidence is available for YEXLAR?`
- `What solvent is used in RAPXEN?`
- `What is the water stability of Zn(LTP)2?`
- `What other MOFs use the same solvent as RAPXEN?`

## Frontend

The frontend is a Next.js + TypeScript app. Run it while the backend is
available on `http://127.0.0.1:8000`:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://127.0.0.1:5173/`.

Use `NEXT_PUBLIC_API_BASE_URL` only if the backend is running somewhere else:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Frontend verification:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```
