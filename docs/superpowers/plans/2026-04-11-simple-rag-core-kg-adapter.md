# Simple RAG Core With KG Adapter Slot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current working FastAPI MVP into a complete local simple RAG baseline with a clean KG adapter slot.

**Architecture:** Preserve the existing local behavior while extracting stable interfaces around normalized evidence, retrieval, and answer composition. The default path remains local/in-memory and deterministic; KG can later enter through `GraphRetriever` and `HybridRetriever` without changing FastAPI or the frontend contract.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, Starlette/FastAPI TestClient, static HTML/JavaScript frontend.

---

## File Map

- Modify: `backend/requirements.txt` to add test dependencies.
- Create: `backend/app/stores/__init__.py`.
- Create: `backend/app/stores/schemas.py` for `Document` and `Fact`.
- Modify: `backend/app/knowledge_store.py` to use store schemas and expose document-style evidence.
- Create: `backend/app/answerers/__init__.py`.
- Create: `backend/app/answerers/deterministic.py` for deterministic evidence-only answers.
- Modify: `backend/app/answerer.py` as a compatibility wrapper.
- Create: `backend/app/retrievers/graph.py` for the empty/no-result KG integration point.
- Create: `backend/app/retrievers/hybrid.py` for merging simple RAG and graph retrieval results.
- Modify: `backend/app/retrievers/__init__.py` to export new retrievers.
- Modify: `backend/app/main.py` to wire `HybridRetriever([KeywordRetriever, NoResultGraphRetriever])`.
- Create: `tests/test_knowledge_store.py`.
- Create: `tests/test_retrievers.py`.
- Create: `tests/test_api.py`.
- Modify: `README.md` to document tests and KG adapter boundary.
- Modify: `docs/ARCHITECTURE.md` to reflect simple RAG core plus KG slot.
- Modify: `docs/ROADMAP.md` to make simple RAG the next milestone and KG the extension layer.

## Task 1: Add Test Dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add pytest and httpx**

Expected file content:

```text
fastapi
uvicorn[standard]
pydantic
pytest
httpx
```

- [ ] **Step 2: Verify dependency file has no duplicates**

Run:

```bash
sort backend/requirements.txt | uniq -d
```

Expected: no output.

## Task 2: Introduce Store Schemas

**Files:**
- Create: `backend/app/stores/__init__.py`
- Create: `backend/app/stores/schemas.py`
- Modify: `backend/app/knowledge_store.py`

- [ ] **Step 1: Create `backend/app/stores/schemas.py`**

Use:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    refcode: str | None
    material_names: tuple[str, ...]
    relation: str
    source: str
    doi: str | None
    license: str | None
    fact_id: str


@dataclass(frozen=True)
class Fact:
    id: str
    refcode: str | None
    material_names: tuple[str, ...]
    relation: str
    value: str
    evidence: str
    doi: str | None
    data_source: str
    path: str
    search_text: str
```

- [ ] **Step 2: Create `backend/app/stores/__init__.py`**

Use:

```python
from app.stores.schemas import Document, Fact

__all__ = ["Document", "Fact"]
```

- [ ] **Step 3: Update `backend/app/knowledge_store.py`**

Remove the local `Fact` dataclass and import:

```python
from app.stores import Document, Fact
```

Add `self.documents: list[Document] = []` in `KnowledgeStore.__init__`.

After appending each `Fact`, append a matching `Document`:

```python
fact = Fact(...)
self.facts.append(fact)
self.documents.append(
    Document(
        id=f"doc-{fact.id}",
        text=f"{fact.relation}: {fact.value}. Evidence: {fact.evidence}",
        refcode=fact.refcode,
        material_names=fact.material_names,
        relation=fact.relation,
        source=fact.data_source,
        doi=fact.doi,
        license=OPEN_SOURCE_LICENSE,
        fact_id=fact.id,
    )
)
```

- [ ] **Step 4: Run focused import check**

Run:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
store = KnowledgeStore(get_settings().open_source_data_dir)
assert store.facts
assert store.documents
assert len(store.documents) == len(store.facts)
print(len(store.facts), len(store.documents))
PY
```

Expected: prints matching non-zero counts.

## Task 3: Move Deterministic Answerer Behind an Answerer Module

**Files:**
- Create: `backend/app/answerers/__init__.py`
- Create: `backend/app/answerers/deterministic.py`
- Modify: `backend/app/answerer.py`

- [ ] **Step 1: Create deterministic answerer module**

Move the current `compose_answer` and `infer_mode` implementation into `backend/app/answerers/deterministic.py`, preserving the same function signatures.

- [ ] **Step 2: Create `backend/app/answerers/__init__.py`**

Use:

```python
from app.answerers.deterministic import compose_answer, infer_mode

__all__ = ["compose_answer", "infer_mode"]
```

- [ ] **Step 3: Keep `backend/app/answerer.py` as a wrapper**

Use:

```python
from app.answerers.deterministic import compose_answer, infer_mode

__all__ = ["compose_answer", "infer_mode"]
```

- [ ] **Step 4: Run focused import check**

Run:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.answerer import compose_answer
from app.answerers import infer_mode
print(compose_answer.__name__, infer_mode.__name__)
PY
```

Expected:

```text
compose_answer infer_mode
```

## Task 4: Add KG Adapter Slot And Hybrid Retriever

**Files:**
- Create: `backend/app/retrievers/graph.py`
- Create: `backend/app/retrievers/hybrid.py`
- Modify: `backend/app/retrievers/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create `backend/app/retrievers/graph.py`**

Use:

```python
from __future__ import annotations

from app.retrievers.base import RetrievalResult


class NoResultGraphRetriever:
    """KG adapter slot until the graph team provides graph-backed evidence."""

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        return []
```

- [ ] **Step 2: Create `backend/app/retrievers/hybrid.py`**

Use:

```python
from __future__ import annotations

from app.retrievers.base import RetrievalResult, Retriever


class HybridRetriever:
    """Merge simple RAG retrieval with optional KG retrieval."""

    def __init__(self, retrievers: list[Retriever]) -> None:
        self.retrievers = retrievers

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        merged: list[RetrievalResult] = []
        seen: set[tuple[str | None, str, str]] = set()

        for retriever in self.retrievers:
            for result in retriever.search(query, limit=limit):
                key = (result.fact.refcode, result.fact.relation, result.fact.value)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(result)

        merged.sort(key=lambda item: item.score, reverse=True)
        return merged[:limit]
```

- [ ] **Step 3: Export retrievers**

Update `backend/app/retrievers/__init__.py` to export:

```python
from app.retrievers.base import RetrievalResult, Retriever
from app.retrievers.graph import NoResultGraphRetriever
from app.retrievers.hybrid import HybridRetriever
from app.retrievers.keyword import KeywordRetriever

__all__ = [
    "HybridRetriever",
    "KeywordRetriever",
    "NoResultGraphRetriever",
    "RetrievalResult",
    "Retriever",
]
```

- [ ] **Step 4: Wire hybrid retriever in `backend/app/main.py`**

Use:

```python
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever

keyword_retriever = KeywordRetriever(store)
graph_retriever = NoResultGraphRetriever()
retriever = HybridRetriever([keyword_retriever, graph_retriever])
query_service = QueryService(retriever)
```

- [ ] **Step 5: Run API import check**

Run:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.main import app
print(app.title)
PY
```

Expected: prints the FastAPI app title.

## Task 5: Add Tests For Store, Retrievers, And API

**Files:**
- Create: `tests/test_knowledge_store.py`
- Create: `tests/test_retrievers.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Create `tests/test_knowledge_store.py`**

Cover:

```python
from app.config import get_settings
from app.knowledge_store import KnowledgeStore


def test_store_loads_facts_and_documents():
    store = KnowledgeStore(get_settings().open_source_data_dir)

    assert store.material_count == 100
    assert len(store.facts) > 0
    assert len(store.documents) == len(store.facts)


def test_store_search_returns_bet_surface_area_evidence():
    store = KnowledgeStore(get_settings().open_source_data_dir)

    results = store.search("What is the BET surface area of UTSA-67?", limit=3)

    assert results
    assert any("BET Surface Area" in fact.relation for fact, _score in results)
    assert any("1137" in fact.value for fact, _score in results)
```

- [ ] **Step 2: Create `tests/test_retrievers.py`**

Cover:

```python
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever


def test_hybrid_retriever_keeps_simple_rag_path_working_with_empty_graph():
    store = KnowledgeStore(get_settings().open_source_data_dir)
    retriever = HybridRetriever([KeywordRetriever(store), NoResultGraphRetriever()])

    results = retriever.search("What is the BET surface area of UTSA-67?", limit=3)

    assert results
    assert any("BET Surface Area" in result.fact.relation for result in results)
```

- [ ] **Step 3: Create `tests/test_api.py`**

Cover:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_reports_loaded_data():
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["materials"] == 100
    assert data["facts"] > 0


def test_query_endpoint_returns_sources_and_fact_paths():
    response = client.post(
        "/api/query",
        json={"question": "What is the BET surface area of UTSA-67?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hard_fact_lookup"
    assert data["sources"]
    assert data["kg_facts"]
    assert "1137" in data["answer"]
```

- [ ] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=backend pytest -q
```

Expected: all tests pass.

## Task 6: Update Docs For The New Build Strategy

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Update `README.md`**

Add a section that states:

```text
The local baseline is a simple RAG-style system. KG is an adapter layer and is not required for baseline execution.
```

Add test command:

```bash
PYTHONPATH=backend pytest -q
```

- [ ] **Step 2: Update `docs/ARCHITECTURE.md`**

Make the current architecture show:

```text
MOF-ChemUnity runtime data
  -> KnowledgeStore facts/documents
  -> KeywordRetriever
  -> NoResultGraphRetriever
  -> HybridRetriever
  -> QueryService
  -> deterministic answerer
  -> FastAPI
  -> frontend
```

- [ ] **Step 3: Update `docs/ROADMAP.md`**

Make Milestone 2 the simple RAG core hardening milestone and Milestone 4 the KG integration milestone.

## Task 7: Final Local Verification

**Files:**
- No source edits unless verification exposes a concrete failure.

- [ ] **Step 1: Compile backend**

Run:

```bash
python3 -m compileall backend
```

Expected: exit code 0.

- [ ] **Step 2: Run tests**

Run:

```bash
PYTHONPATH=backend pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Start API**

Run:

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Expected: Uvicorn starts on `http://127.0.0.1:8000`.

- [ ] **Step 4: Check API endpoints**

Run:

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the BET surface area of UTSA-67?","top_k":3}'
```

Expected: health returns loaded data and query returns an answer containing `1137`.

- [ ] **Step 5: Check static frontend**

Run:

```bash
python3 -m http.server 5173 --directory frontend
curl -s -I http://127.0.0.1:5173/
```

Expected: HTTP 200 for the frontend page.

- [ ] **Step 6: Stop temporary servers**

Send Ctrl-C to Uvicorn and the static file server. Then run:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

Expected: no listening process output for both ports.
