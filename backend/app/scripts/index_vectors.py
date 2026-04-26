from __future__ import annotations

import sys
import time

from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.rag.chunks import EvidenceChunk, build_evidence_chunks
from app.rag.embeddings import OpenAIEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore

# Keep a conservative per-chunk character limit for Zhipu embedding-3.
# Some chemistry-heavy records below 8000 chars still exceed the API's request limits.
MAX_TEXT_LENGTH = 4000


def _truncate(chunk: EvidenceChunk) -> EvidenceChunk:
    if len(chunk.text) <= MAX_TEXT_LENGTH:
        return chunk
    return EvidenceChunk(
        id=chunk.id,
        text=chunk.text[:MAX_TEXT_LENGTH],
        payload=chunk.payload,
    )


def main() -> None:
    settings = get_settings()
    api_key = settings.require_api_key("vector indexing")
    store = KnowledgeStore(settings.open_source_data_dir, synthesis_data_path=settings.resolved_kg_synthesis_path)
    raw_chunks = build_evidence_chunks(store)
    chunks = [_truncate(c) for c in raw_chunks]

    truncated = sum(1 for r, c in zip(raw_chunks, chunks) if len(r.text) != len(c.text))
    if truncated:
        print(f"Truncated {truncated} chunks exceeding {MAX_TEXT_LENGTH} chars.", flush=True)

    embedding_provider = OpenAIEmbeddingProvider(
        model=settings.rag_embedding_model,
        api_key=api_key,
        base_url=settings.rag_api_base_url,
        dimensions=settings.rag_embedding_dimensions,
    )
    vector_store = QdrantVectorStore(
        url=settings.rag_vector_store_url,
        collection=settings.rag_qdrant_collection,
        dimensions=settings.rag_embedding_dimensions,
    )

    batch_size = settings.rag_embedding_batch_size
    indexed = 0
    skipped = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        try:
            vectors = embedding_provider.embed_texts([c.text for c in batch])
            vector_store.upsert_chunks(batch, vectors, start_index=start)
            indexed += len(batch)
        except Exception as err:
            # Skip the entire batch on failure
            skipped += len(batch)
            print(f"  skipping batch {start}-{start+len(batch)}: {err}", file=sys.stderr, flush=True)
        pct = min((start + len(batch)) / len(chunks) * 100, 100)
        print(f"[{pct:5.1f}%] {indexed} indexed, {skipped} skipped", flush=True)
        time.sleep(0.3)

    print(f"\nDone. {indexed}/{len(chunks)} chunks indexed into '{settings.rag_qdrant_collection}'.", flush=True)
    if skipped:
        print(f"  {skipped} chunks skipped due to API errors.", flush=True)


if __name__ == "__main__":
    main()
