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
    indexed = 0
    for start in range(0, len(chunks), settings.rag_embedding_batch_size):
        batch = chunks[start : start + settings.rag_embedding_batch_size]
        vectors = embedding_provider.embed_texts([chunk.text for chunk in batch])
        vector_store.upsert_chunks(batch, vectors, start_index=start)
        indexed += len(batch)
        print(f"Indexed {indexed}/{len(chunks)} chunks...")
    print(f"Indexed {len(chunks)} chunks into {settings.rag_qdrant_collection}.")


if __name__ == "__main__":
    main()
