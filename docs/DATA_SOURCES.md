# Data Sources

## Reference Materials

`References/` contains papers and slide decks that guide project planning. These files are not runtime QA data.

Do not chunk, embed, or index `References/` unless the user explicitly changes the product requirement.

## Runtime Seed Data

The current MVP uses public sample data from:

```text
https://github.com/AI4ChemS/MOF_ChemUnity
```

Files copied into `backend/data/open_source/`:

- `demo.json`
- `MOF_names_and_CSD_codes.csv`
- `water_stability_chemunity_v0.1.0.csv`

License notes from upstream:

- code: MIT License;
- non-code data/content: Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

## Derived Runtime Indexes

Qdrant collections are derived runtime indexes over normalized evidence documents. They must be built from `backend/data/open_source/`, `reference_code/MOF_KG/3.MOF-Synthesis.json`, or another approved runtime source, not from `References/`.

Current collection names:

- `mof_evidence`: configured full evidence index for the seed corpus.
- `mof_evidence_smoke`: small local smoke-test collection used to verify Zhipu embeddings and Qdrant retrieval.

Do not commit generated vector stores, Qdrant storage, caches, or local `.env` files.

## Team KG Runtime Data

The KG adapter uses team/course-provided graph data, not `References/`.

Runtime export:

- `backend/data/kg/mof_kg.json`

Runtime synthesis evidence:

- `reference_code/MOF_KG/3.MOF-Synthesis.json`

Builder inputs:

- `reference_code/MOF_KG/1.water_stability_chemunity_v0.1.0.csv`
- `reference_code/MOF_KG/2.MOF_names_and_CSD_codes.csv`
- `reference_code/MOF_KG/3.MOF-Synthesis.json`

The synthesis JSON is loaded as row-level evidence documents in addition to
being used by the offline builder. Each row remains an independent runtime
evidence record so variants that share a CSD identifier are not silently merged.

Current checked-in runtime scale:

- `KnowledgeStore`: 100 demo materials, 47,823 normalized facts/documents, and 28,989 synthesis evidence rows.
- `KGGraphRetriever`: 218,662 graph facts from `backend/data/kg/mof_kg.json`.

No explicit public license was supplied with the KG package. Treat it as
project/course runtime data unless licensing is clarified.

## Benchmark And Evaluation Files

No benchmark spreadsheet or CSV files are loaded by the runtime QA path. If external benchmark files are added later, keep them separate from the default QA corpus unless the project explicitly promotes them to runtime data.

## Reference-Only Repositories

`MontageBai/KGFM` is useful as a method reference. It does not currently expose an explicit license, so do not import its data or code into this repository unless licensing is clarified.

## Optional Data Sources If The Project Is Reopened

Potential candidates remain:

- team-provided Neo4j graph or CSV export;
- course-provided MOF datasets;
- CoRE MOF / QMOF-derived properties, if license and access are compatible;
- new curated literature extraction outputs, if the project explicitly adds literature ingestion as a product feature.
