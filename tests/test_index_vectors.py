from app.rag.chunks import EvidenceChunk
from app.scripts.index_vectors import MAX_TEXT_LENGTH, _truncate


def test_index_vector_truncation_uses_embedding_safe_limit():
    chunk = EvidenceChunk(id="long", text="x" * (MAX_TEXT_LENGTH + 20), payload={"fact_id": "long"})

    truncated = _truncate(chunk)

    assert MAX_TEXT_LENGTH <= 4000
    assert len(truncated.text) == MAX_TEXT_LENGTH
    assert truncated.payload == chunk.payload
