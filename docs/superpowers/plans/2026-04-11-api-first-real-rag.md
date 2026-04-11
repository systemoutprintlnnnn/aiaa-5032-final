# API-First Real RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real RAG path that uses API embeddings, Qdrant vector search, and API LLM answer generation while preserving the current keyword fallback and KG adapter slot.

**Architecture:** Runtime MOF facts become embedding-ready chunks, chunks are embedded through an OpenAI-compatible API and stored in Qdrant, queries are embedded and retrieved through `VectorRetriever`, and `LLMAnswerer` generates evidence-grounded answers. `KeywordRetriever` remains an exact-match fallback and `NoResultGraphRetriever` remains the KG adapter slot.

**Tech Stack:** Python, FastAPI, Pydantic, OpenAI Python SDK, Qdrant Python client, pytest, httpx, static HTML frontend.

---

## File Map

- Modify: `backend/requirements.txt` to add `openai` and `qdrant-client`.
- Modify: `backend/app/config.py` to add RAG provider, model, Qdrant, and mode settings.
- Create: `backend/app/rag/__init__.py`.
- Create: `backend/app/rag/chunks.py` for `EvidenceChunk` and `build_evidence_chunks`.
- Create: `backend/app/rag/embeddings.py` for `EmbeddingProvider`, `OpenAIEmbeddingProvider`, and config errors.
- Create: `backend/app/rag/vector_store.py` for `VectorHit` and `QdrantVectorStore`.
- Create: `backend/app/scripts/__init__.py`.
- Create: `backend/app/scripts/index_vectors.py` for explicit indexing.
- Modify: `backend/app/retrievers/vector.py` to add `VectorRetriever`.
- Modify: `backend/app/retrievers/__init__.py` to export `VectorRetriever`.
- Create: `backend/app/answerers/llm.py` for `OpenAILLMAnswerer`.
- Modify: `backend/app/answerers/deterministic.py` to expose `DeterministicAnswerer`.
- Modify: `backend/app/services/query_service.py` to accept an answerer object.
- Modify: `backend/app/main.py` to wire vector and LLM features based on settings.
- Modify: `README.md`, `docs/ARCHITECTURE.md`, and `docs/ROADMAP.md`.
- Add tests under `tests/` for chunking, embeddings config, vector retriever, LLM answerer, and API fallback behavior.

## Task 1: Add Dependencies And Config

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`
- Test: `tests/test_rag_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_rag_config.py`:

```python
import pytest

from app.config import Settings
from app.rag.embeddings import RAGConfigurationError


def test_settings_default_to_keyword_and_deterministic_mode():
    settings = Settings()

    assert settings.rag_retrieval_mode == "keyword"
    assert settings.rag_enable_llm is False
    assert settings.rag_qdrant_collection == "mof_evidence"


def test_settings_require_api_key_for_vector_mode():
    settings = Settings(rag_retrieval_mode="hybrid", rag_api_key="")

    with pytest.raises(RAGConfigurationError, match="RAG_API_KEY"):
        settings.require_api_key("vector retrieval")
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_config.py -q
```

Expected: fails because `app.rag.embeddings` and the new settings do not exist.

- [ ] **Step 3: Add dependencies**

Append to `backend/requirements.txt`:

```text
openai
qdrant-client
```

- [ ] **Step 4: Add settings and config error**

Create `backend/app/rag/__init__.py`:

```python
"""RAG building blocks for embeddings, vector stores, and LLM answers."""
```

Create `backend/app/rag/embeddings.py` with at least:

```python
class RAGConfigurationError(RuntimeError):
    pass
```

Modify `backend/app/config.py`:

```python
class Settings(BaseModel):
    app_name: str = "MOF KG-Enhanced RAG FastAPI MVP"
    data_source_label: str = "AI4ChemS/MOF_ChemUnity public sample data"
    backend_dir: Path = Path(__file__).resolve().parents[1]
    rag_retrieval_mode: str = "keyword"
    rag_api_key: str = ""
    rag_embedding_provider: str = "openai"
    rag_embedding_model: str = "text-embedding-3-small"
    rag_embedding_dimensions: int = 1536
    rag_vector_store_url: str = "http://127.0.0.1:6333"
    rag_qdrant_collection: str = "mof_evidence"
    rag_enable_llm: bool = False
    rag_llm_provider: str = "openai"
    rag_llm_model: str = "gpt-4.1-mini"

    def require_api_key(self, feature: str) -> str:
        from app.rag.embeddings import RAGConfigurationError

        if not self.rag_api_key:
            raise RAGConfigurationError(f"RAG_API_KEY is required for {feature}.")
        return self.rag_api_key
```

- [ ] **Step 5: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_config.py -q
```

Expected: passes.

## Task 2: Add Evidence Chunk Builder

**Files:**
- Create: `backend/app/rag/chunks.py`
- Test: `tests/test_rag_chunks.py`

- [ ] **Step 1: Write failing chunk tests**

Create `tests/test_rag_chunks.py`:

```python
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.rag.chunks import build_evidence_chunks


def test_build_evidence_chunks_preserves_source_metadata():
    store = KnowledgeStore(get_settings().open_source_data_dir)

    chunks = build_evidence_chunks(store)

    assert chunks
    chunk = chunks[0]
    assert chunk.id
    assert chunk.text
    assert chunk.payload["fact_id"]
    assert chunk.payload["source"]
    assert "path" in chunk.payload
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_chunks.py -q
```

Expected: fails because `app.rag.chunks` does not exist.

- [ ] **Step 3: Implement chunk builder**

Create `backend/app/rag/chunks.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge_store import KnowledgeStore, OPEN_SOURCE_LICENSE


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    text: str
    payload: dict[str, Any]


def build_evidence_chunks(store: KnowledgeStore) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for fact in store.facts:
        subject = fact.refcode or (fact.material_names[0] if fact.material_names else "material")
        text = f"{subject}. {fact.relation}: {fact.value}. Evidence: {fact.evidence}"
        chunks.append(
            EvidenceChunk(
                id=fact.id,
                text=text,
                payload={
                    "fact_id": fact.id,
                    "refcode": fact.refcode,
                    "material_names": list(fact.material_names),
                    "relation": fact.relation,
                    "value": fact.value,
                    "evidence": fact.evidence,
                    "doi": fact.doi,
                    "source": fact.data_source,
                    "license": OPEN_SOURCE_LICENSE,
                    "path": fact.path,
                    "text": text,
                },
            )
        )
    return chunks
```

- [ ] **Step 4: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_chunks.py -q
```

Expected: passes.

## Task 3: Add OpenAI Embedding Provider

**Files:**
- Modify: `backend/app/rag/embeddings.py`
- Test: `tests/test_rag_embeddings.py`

- [ ] **Step 1: Write failing embedding provider tests**

Create `tests/test_rag_embeddings.py`:

```python
from app.rag.embeddings import OpenAIEmbeddingProvider


class FakeEmbeddingClient:
    class Embeddings:
        def create(self, model, input):
            class Item:
                embedding = [0.1, 0.2, 0.3]

            class Response:
                data = [Item() for _ in input]

            return Response()

    embeddings = Embeddings()


def test_openai_embedding_provider_embeds_texts_with_client():
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", client=FakeEmbeddingClient())

    vectors = provider.embed_texts(["a", "b"])

    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]


def test_openai_embedding_provider_embeds_query():
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", client=FakeEmbeddingClient())

    vector = provider.embed_query("hello")

    assert vector == [0.1, 0.2, 0.3]
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_embeddings.py -q
```

Expected: fails because `OpenAIEmbeddingProvider` does not exist.

- [ ] **Step 3: Implement embedding provider**

Add to `backend/app/rag/embeddings.py`:

```python
from __future__ import annotations

from typing import Protocol

from openai import OpenAI


class RAGConfigurationError(RuntimeError):
    pass


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, query: str) -> list[float]:
        ...


class OpenAIEmbeddingProvider:
    def __init__(self, *, model: str, api_key: str, client: object | None = None) -> None:
        if not api_key:
            raise RAGConfigurationError("RAG_API_KEY is required for OpenAI embeddings.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [list(item.embedding) for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        vectors = self.embed_texts([query])
        return vectors[0]
```

- [ ] **Step 4: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_rag_embeddings.py -q
```

Expected: passes.

## Task 4: Add Qdrant Vector Store

**Files:**
- Create: `backend/app/rag/vector_store.py`
- Test: `tests/test_vector_store.py`

- [ ] **Step 1: Write failing vector store mapping tests**

Create `tests/test_vector_store.py`:

```python
from app.rag.vector_store import VectorHit


def test_vector_hit_keeps_payload_and_score():
    hit = VectorHit(id="fact-1", score=0.9, payload={"fact_id": "fact-1"})

    assert hit.id == "fact-1"
    assert hit.score == 0.9
    assert hit.payload["fact_id"] == "fact-1"
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_vector_store.py -q
```

Expected: fails because `app.rag.vector_store` does not exist.

- [ ] **Step 3: Implement vector store wrapper**

Create `backend/app/rag/vector_store.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.rag.chunks import EvidenceChunk


@dataclass(frozen=True)
class VectorHit:
    id: str
    score: float
    payload: dict[str, Any]


class QdrantVectorStore:
    def __init__(self, *, url: str, collection: str, dimensions: int, client: QdrantClient | None = None) -> None:
        self.collection = collection
        self.dimensions = dimensions
        self.client = client or QdrantClient(url=url)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.collection for collection in collections):
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.dimensions, distance=Distance.COSINE),
        )

    def upsert_chunks(self, chunks: list[EvidenceChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        self.ensure_collection()
        points = [
            PointStruct(id=idx, vector=vector, payload={**chunk.payload, "chunk_id": chunk.id})
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], limit: int) -> list[VectorHit]:
        hits = self.client.query_points(collection_name=self.collection, query=query_vector, limit=limit).points
        return [
            VectorHit(id=str(hit.id), score=float(hit.score), payload=dict(hit.payload or {}))
            for hit in hits
        ]
```

- [ ] **Step 4: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_vector_store.py -q
```

Expected: passes.

## Task 5: Add Vector Retriever

**Files:**
- Create: `backend/app/retrievers/vector.py`
- Modify: `backend/app/retrievers/__init__.py`
- Test: `tests/test_vector_retriever.py`

- [ ] **Step 1: Write failing vector retriever tests**

Create `tests/test_vector_retriever.py`:

```python
from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.rag.vector_store import VectorHit
from app.retrievers.vector import VectorRetriever


class FakeEmbeddingProvider:
    def embed_query(self, query):
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self, fact_id):
        self.fact_id = fact_id

    def search(self, query_vector, limit):
        return [VectorHit(id="point-1", score=0.9, payload={"fact_id": self.fact_id})]


def test_vector_retriever_maps_vector_hit_to_retrieval_result():
    store = KnowledgeStore(get_settings().open_source_data_dir)
    fact = store.facts[0]
    retriever = VectorRetriever(
        store=store,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(fact.id),
    )

    results = retriever.search("query", limit=1)

    assert len(results) == 1
    assert results[0].fact.id == fact.id
    assert results[0].score == 0.9
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_vector_retriever.py -q
```

Expected: fails because `VectorRetriever` does not exist.

- [ ] **Step 3: Implement vector retriever**

Create `backend/app/retrievers/vector.py`:

```python
from __future__ import annotations

from app.knowledge_store import KnowledgeStore
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.retrievers.base import RetrievalResult


class VectorRetriever:
    def __init__(self, *, store: KnowledgeStore, embedding_provider: EmbeddingProvider, vector_store: QdrantVectorStore) -> None:
        self.store = store
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        query_vector = self.embedding_provider.embed_query(query)
        hits = self.vector_store.search(query_vector, limit=limit)
        fact_by_id = {fact.id: fact for fact in self.store.facts}
        results: list[RetrievalResult] = []
        for hit in hits:
            fact_id = hit.payload.get("fact_id")
            fact = fact_by_id.get(str(fact_id))
            if fact is None:
                continue
            results.append(RetrievalResult(fact=fact, score=hit.score))
        return results
```

Update `backend/app/retrievers/__init__.py` to export `VectorRetriever`.

- [ ] **Step 4: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_vector_retriever.py -q
```

Expected: passes.

## Task 6: Add Vector Indexing Script

**Files:**
- Create: `backend/app/scripts/__init__.py`
- Create: `backend/app/scripts/index_vectors.py`

- [ ] **Step 1: Create indexing script**

Create `backend/app/scripts/__init__.py`:

```python
"""Command modules for setup and maintenance."""
```

Create `backend/app/scripts/index_vectors.py`:

```python
from __future__ import annotations

from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.rag.chunks import build_evidence_chunks
from app.rag.embeddings import OpenAIEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore


def main() -> None:
    settings = get_settings()
    api_key = settings.require_api_key("vector indexing")
    store = KnowledgeStore(settings.open_source_data_dir)
    chunks = build_evidence_chunks(store)
    embedding_provider = OpenAIEmbeddingProvider(model=settings.rag_embedding_model, api_key=api_key)
    vectors = embedding_provider.embed_texts([chunk.text for chunk in chunks])
    vector_store = QdrantVectorStore(
        url=settings.rag_vector_store_url,
        collection=settings.rag_qdrant_collection,
        dimensions=settings.rag_embedding_dimensions,
    )
    vector_store.upsert_chunks(chunks, vectors)
    print(f"Indexed {len(chunks)} chunks into {settings.rag_qdrant_collection}.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify import without running external API**

Run:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.scripts.index_vectors import main
print(main.__name__)
PY
```

Expected:

```text
main
```

## Task 7: Add LLM Answerer

**Files:**
- Modify: `backend/app/answerers/deterministic.py`
- Create: `backend/app/answerers/llm.py`
- Test: `tests/test_llm_answerer.py`

- [ ] **Step 1: Write failing LLM answerer tests**

Create `tests/test_llm_answerer.py`:

```python
from app.answerers.llm import OpenAILLMAnswerer


class FakeResponse:
    output_text = "UTSA-67 has a reported BET surface area of 1137 m2 g-1 [S1]."


class FakeResponses:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    responses = FakeResponses()


def test_llm_answerer_refuses_without_evidence():
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=FakeClient())

    response = answerer.answer("question", [])

    assert response.mode == "insufficient_evidence"
    assert response.sources == []


def test_llm_answerer_uses_evidence_when_matches_exist():
    from app.config import get_settings
    from app.knowledge_store import KnowledgeStore

    store = KnowledgeStore(get_settings().open_source_data_dir)
    fact = store.search("What is the BET surface area of UTSA-67?", limit=1)[0][0]
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=FakeClient())

    response = answerer.answer("What is the BET surface area of UTSA-67?", [(fact, 1.0)])

    assert "1137" in response.answer
    assert response.sources
    assert response.kg_facts
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_llm_answerer.py -q
```

Expected: fails because `OpenAILLMAnswerer` does not exist.

- [ ] **Step 3: Add deterministic answerer class**

Add to `backend/app/answerers/deterministic.py`:

```python
class DeterministicAnswerer:
    def answer(self, query: str, matches: list[tuple[Fact, float]]) -> QueryResponse:
        return compose_answer(query, matches)
```

- [ ] **Step 4: Implement LLM answerer**

Create `backend/app/answerers/llm.py`:

```python
from __future__ import annotations

from openai import OpenAI

from app.answerers.deterministic import compose_answer
from app.models import QueryResponse
from app.stores import Fact


class OpenAILLMAnswerer:
    def __init__(self, *, model: str, api_key: str, client: object | None = None) -> None:
        if not api_key:
            raise RuntimeError("RAG_API_KEY is required for OpenAI LLM answering.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def answer(self, query: str, matches: list[tuple[Fact, float]]) -> QueryResponse:
        response = compose_answer(query, matches)
        if not matches:
            return response

        evidence = "\n".join(
            f"[S{idx}] {fact.refcode or 'material'} | {fact.relation} | {fact.value} | {fact.evidence}"
            for idx, (fact, _score) in enumerate(matches, start=1)
        )
        llm_response = self.client.responses.create(
            model=self.model,
            instructions=(
                "Answer using only the evidence provided. Cite source ids like [S1]. "
                "If the evidence is insufficient, say that the current runtime knowledge store does not contain enough evidence."
            ),
            input=f"Question: {query}\n\nEvidence:\n{evidence}",
        )
        answer_text = getattr(llm_response, "output_text", "").strip()
        if answer_text:
            response.answer = answer_text
            response.mode = "hybrid_rag"
        return response
```

- [ ] **Step 5: Run the green test**

Run:

```bash
PYTHONPATH=backend pytest tests/test_llm_answerer.py -q
```

Expected: passes.

## Task 8: Wire Real RAG Into FastAPI

**Files:**
- Modify: `backend/app/services/query_service.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Update query service to accept answerer**

Modify `backend/app/services/query_service.py`:

```python
from __future__ import annotations

from app.answerers.deterministic import DeterministicAnswerer
from app.models import QueryRequest, QueryResponse
from app.retrievers.base import Retriever


class QueryService:
    def __init__(self, retriever: Retriever, answerer: object | None = None) -> None:
        self.retriever = retriever
        self.answerer = answerer or DeterministicAnswerer()

    def answer(self, request: QueryRequest) -> QueryResponse:
        results = self.retriever.search(request.question, limit=request.top_k)
        matches = [(result.fact, result.score) for result in results]
        return self.answerer.answer(request.question, matches)
```

- [ ] **Step 2: Update FastAPI wiring**

Modify `backend/app/main.py` so default keyword mode remains working, and vector/LLM are enabled only by env:

```python
retrievers = []
if settings.rag_retrieval_mode in {"vector", "hybrid"}:
    api_key = settings.require_api_key("vector retrieval")
    embedding_provider = OpenAIEmbeddingProvider(model=settings.rag_embedding_model, api_key=api_key)
    vector_store = QdrantVectorStore(
        url=settings.rag_vector_store_url,
        collection=settings.rag_qdrant_collection,
        dimensions=settings.rag_embedding_dimensions,
    )
    retrievers.append(VectorRetriever(store=store, embedding_provider=embedding_provider, vector_store=vector_store))

if settings.rag_retrieval_mode in {"keyword", "hybrid"}:
    retrievers.append(KeywordRetriever(store))

retrievers.append(NoResultGraphRetriever())
retriever = HybridRetriever(retrievers)

answerer = DeterministicAnswerer()
if settings.rag_enable_llm:
    api_key = settings.require_api_key("LLM answering")
    answerer = OpenAILLMAnswerer(model=settings.rag_llm_model, api_key=api_key)

query_service = QueryService(retriever, answerer=answerer)
```

- [ ] **Step 3: Run API tests**

Run:

```bash
PYTHONPATH=backend pytest tests/test_api.py -q
```

Expected: passes with default keyword/deterministic configuration.

## Task 9: Update Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Document real RAG setup**

Add README section:

```bash
docker run -p 6333:6333 qdrant/qdrant
export RAG_API_KEY=...
export RAG_RETRIEVAL_MODE=hybrid
export RAG_ENABLE_LLM=true
export RAG_VECTOR_STORE_URL=http://127.0.0.1:6333
export RAG_EMBEDDING_MODEL=text-embedding-3-small
export RAG_LLM_MODEL=gpt-4.1-mini
PYTHONPATH=backend python3 -m app.scripts.index_vectors
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Update architecture docs**

Document:

```text
VectorRetriever -> primary real RAG path
KeywordRetriever -> fallback
NoResultGraphRetriever -> KG slot
OpenAILLMAnswerer -> evidence-grounded LLM answers
```

- [ ] **Step 3: Update roadmap**

Mark vector/LLM as the active next milestone and keep KG adapter as independent.

## Task 10: Final Verification

**Files:**
- No source edits unless verification exposes a concrete failure.

- [ ] **Step 1: Run formatting/whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Compile backend**

Run:

```bash
python3 -m compileall backend
```

Expected: exit code 0.

- [ ] **Step 3: Run all tests**

Run:

```bash
PYTHONPATH=backend pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Verify default local API still works**

Run:

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the BET surface area of UTSA-67?","top_k":3}'
```

Expected: health returns loaded data and query returns `1137`.

- [ ] **Step 5: Stop local server and check ports**

Run:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Expected: no listening process after shutdown.
