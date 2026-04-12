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

Qdrant collections are derived runtime indexes over normalized MOF-ChemUnity facts. They must be built from `backend/data/open_source/` or another approved runtime source, not from `References/`.

Current collection names:

- `mof_evidence`: intended full evidence index for the seed corpus.
- `mof_evidence_smoke`: small local smoke-test collection used to verify Zhipu embeddings and Qdrant retrieval.

Do not commit generated vector stores, Qdrant storage, caches, or local `.env` files.

## Reference-Only Repositories

`MontageBai/KGFM` is useful as a method reference. It does not currently expose an explicit license, so do not import its data or code into this repository unless licensing is clarified.

## Future Data Sources

Candidates:

- team-provided Neo4j graph or CSV export;
- course-provided MOF datasets;
- CoRE MOF / QMOF-derived properties, if license and access are compatible;
- new curated literature extraction outputs, if that becomes a planned product feature.
