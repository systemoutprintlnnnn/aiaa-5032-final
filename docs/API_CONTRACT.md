# API Contract

## `GET /api/health`

Returns backend and loaded-data status.

Response:

```json
{
  "status": "ok",
  "materials": 100,
  "facts": 18834,
  "data_source": "AI4ChemS/MOF_ChemUnity public sample data"
}
```

Run the API with:

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

## `POST /api/query`

Request:

```json
{
  "question": "What is the BET surface area of UTSA-67?",
  "top_k": 3
}
```

Response:

```json
{
  "query": "What is the BET surface area of UTSA-67?",
  "mode": "hard_fact_lookup",
  "answer": "...",
  "sources": [
    {
      "id": "S1",
      "title": "MOF-ChemUnity demo.json (CUVVOG)",
      "doi": "10.1039/C5CC08210B",
      "refcode": "CUVVOG",
      "evidence": "...",
      "data_source": "MOF-ChemUnity demo.json",
      "retrieval_sources": ["embedding", "keyword"],
      "license": "MOF-ChemUnity data: CC BY-NC 4.0; code: MIT"
    }
  ],
  "kg_facts": [
    {
      "path": "Material(CUVVOG) -> HAS_EXPERIMENTAL_PROPERTY -> BET Surface Area",
      "relation": "HAS_EXPERIMENTAL_PROPERTY: BET Surface Area",
      "value": "1137 m2 g-1",
      "source_id": "S1"
    }
  ],
  "retrieved_count": 1
}
```

Modes currently used:

- `hard_fact_lookup`: deterministic answer from structured property-like evidence.
- `alias_lookup`: deterministic answer for material aliases/refcodes.
- `keyword_retrieval`: deterministic fallback answer from retrieved evidence.
- `hybrid_rag`: LLM answer composed from retrieved evidence.
- `insufficient_evidence`: no runtime evidence found.

## `GET /api/rag/status`

Returns runtime RAG configuration status without exposing secrets.

Response:

```json
{
  "retrieval_mode": "keyword",
  "vector_store_enabled": false,
  "kg_enabled": true,
  "kg_graph_path": "/absolute/path/backend/data/kg/mof_kg.json",
  "kg_graph_loaded": true,
  "kg_fact_count": 218662,
  "llm_enabled": false,
  "api_key_configured": false,
  "api_base_url": "https://open.bigmodel.cn/api/paas/v4/",
  "embedding_provider": "zhipu",
  "embedding_model": "embedding-3",
  "vector_store_url": "http://127.0.0.1:6333",
  "qdrant_collection": "mof_evidence",
  "llm_provider": "zhipu",
  "llm_model": "glm-4.6v"
}
```

## Contract Rules

- `sources` must contain the evidence used by the answer.
- `sources[].retrieval_sources` reports how the evidence was retrieved. Current values are `kg`, `embedding`, and `keyword`.
- `kg_facts` must point to a source via `source_id`.
- `mode` should remain stable enough for frontend filtering and future ablation demos.
- If evidence is missing, return `mode = "insufficient_evidence"` with empty `sources` and `kg_facts`.
- `api_key_configured` may be `true`, but the API key itself must never be returned.
- KG fields report graph availability only; they must not expose secrets.
- The response contract must stay stable when swapping keyword, vector, LLM, or KG internals.
