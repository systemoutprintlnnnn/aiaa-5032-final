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
