# MOF KG-Enhanced RAG - Corrected End-to-End Plan

## Key Correction

`References/` is **not** the runtime knowledge base.

The files in `References/` are design references: they explain what a good MOF literature assistant should look like, which data sources are valuable, and which architecture patterns are worth borrowing. They should not be chunked into the product QA corpus.

Runtime knowledge should come from:

- open-source MOF datasets and KG samples, when licenses allow;
- the project/team KG implementation;
- any course-provided MOF datasets;
- later, real literature ingestion or database integration, if time permits.

For the first end-to-end milestone, the runtime knowledge seed data will use public MOF-ChemUnity sample data from `AI4ChemS/MOF_ChemUnity`:

- code: MIT License;
- data: CC BY-NC 4.0;
- useful files: `demo.json`, `MOF_names_and_CSD_codes.csv`, `water_stability_chemunity_v0.1.0.csv`.

`MontageBai/KGFM` is useful as a method reference, but because the repository has no explicit license at the time of inspection, do not directly import its data into this project unless permission/licensing is clarified.

## Product Goal

Build a small but working MOF-specific question-answering system with:

- a backend query API;
- a minimal frontend;
- runtime MOF knowledge from open/project data, not from the reference PDFs/PPTX;
- graph-style facts and evidence;
- a path to replace the local store with Neo4j/Qdrant later.

The immediate priority is to run end-to-end, even if the first retrieval implementation is simple.

## Architecture

```text
Open/project MOF data
  -> seed-data normalizer
  -> local knowledge store
        |
        +--> graph-style facts
        +--> searchable text records

User question
  -> query router
  -> hard-fact lookup
  -> text retrieval fallback
  -> answer composer
  -> citations / evidence / KG facts

Frontend
  -> POST /api/query
  -> answer + source cards + graph facts
```

Later upgrade path:

```text
local knowledge store
  -> Qdrant for vector retrieval
  -> Neo4j for KG/Text-to-Cypher
  -> LLM generation + citation verification
```

## What The References Teach Us

From the PDF/PPTX references, we keep these ideas:

- MOF knowledge should be material-centric: names, CSD ref codes, properties, applications, synthesis, evidence, and publication sources should connect around the material.
- Hard facts such as surface area, pore volume, gas uptake, and water stability are better represented as structured facts.
- Soft knowledge such as synthesis rationale, mechanism, and high-level recommendations can use text retrieval.
- Answers must show sources and evidence.
- The demo should distinguish property-specific QA from descriptive/synthesis generation.

But the references themselves are not the knowledge corpus.

## Immediate End-to-End Milestone

Build a minimal full stack:

- `backend/`: FastAPI API.
- `backend/data/open_source/`: downloaded open-source MOF-ChemUnity sample data.
- `backend/app/knowledge_store.py`: loads and normalizes the sample data.
- `backend/app/retrievers/`: keyword/BM25-like fallback retrieval over normalized facts, later replaceable with Qdrant/Neo4j retrievers.
- `backend/app/services/`: query orchestration.
- `backend/app/answerer.py`: deterministic evidence-based answer composer first; LLM adapter later.
- `frontend/`: simple browser UI that calls the backend.

The first version should answer queries like:

- "What is the BET surface area of UTSA-67?"
- "Is Zn(LTP)2 water stable?"
- "What synthesis conditions are reported for UTSA-67?"
- "What names are associated with CSD ref code CUVVOG?"

## Development Plan

### Phase 1: Minimal Backend

- Add FastAPI skeleton.
- Add `/api/health`.
- Add `/api/query`.
- Load MOF-ChemUnity seed data at startup.
- Return `answer`, `sources`, `kg_facts`, and `mode`.

### Phase 2: Runtime Knowledge Seed Data

- Normalize `demo.json` into material records.
- Normalize `water_stability_chemunity_v0.1.0.csv` into water-stability records.
- Normalize `MOF_names_and_CSD_codes.csv` into alias records.
- Keep source DOI, CSD ref code, property name, value, units, and evidence/summary.

### Phase 3: Retrieval And Answering

- Route obvious hard-fact questions to structured lookup:
  - surface area
  - pore volume
  - pore diameter
  - gas uptake
  - water stability
  - synthesis
  - names / aliases
- Use keyword retrieval as fallback.
- Compose answers only from retrieved facts.
- If no evidence is found, return an insufficient-evidence response.

### Phase 4: Frontend

- Add a minimal query page.
- Show the answer, sources, and graph-style facts.
- Keep it simple enough to debug quickly.

### Phase 5: Upgrade Path

After end-to-end works:

- replace keyword search with Qdrant embeddings;
- replace in-memory graph facts with Neo4j;
- add Text-to-Cypher for hard facts;
- add LLM generation and citation verification;
- add ablation modes for final presentation.

## Current Priority

Run the smallest credible system end-to-end before adding sophisticated RAG or KG infrastructure.
