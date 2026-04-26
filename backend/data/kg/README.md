# Runtime KG Data

This directory stores the KG Builder JSON export used by the backend graph
retriever.

## Runtime File

- `mof_kg.json`: read-only runtime KG export loaded by `KGGraphRetriever`.

## Source Inputs

The offline builder input files are kept under `reference_code/MOF_KG/`:

- `1.water_stability_chemunity_v0.1.0.csv`
- `2.MOF_names_and_CSD_codes.csv`
- `3.MOF-Synthesis.json`

## Regenerate

From the repository root:

```bash
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format json
```

The copied builder is configured to read `reference_code/MOF_KG/` and write
`backend/data/kg/mof_kg.json`.

## Data Boundary

`References/` is planning and design context only. It is not indexed, chunked,
embedded, or used as the runtime QA corpus.

The KG files are team/course-provided runtime data. No explicit public data
license was supplied with the KG package, so do not describe this data as open
source unless licensing is clarified.
