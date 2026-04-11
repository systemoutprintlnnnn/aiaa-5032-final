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

## `GET /api/rag/status`

Returns runtime RAG configuration status without exposing secrets.

Response:

```json
{
  "retrieval_mode": "keyword",
  "vector_store_enabled": false,
  "llm_enabled": false,
  "api_key_configured": false,
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "vector_store_url": "http://127.0.0.1:6333",
  "qdrant_collection": "mof_evidence",
  "llm_provider": "openai",
  "llm_model": "gpt-4.1-mini"
}
```

## Contract Rules

- `sources` must contain the evidence used by the answer.
- `kg_facts` must point to a source via `source_id`.
- `mode` should remain stable enough for frontend filtering and future ablation demos.
- If evidence is missing, return `mode = "insufficient_evidence"` with empty `sources` and `kg_facts`.
