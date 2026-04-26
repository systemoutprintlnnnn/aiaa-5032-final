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
            results.append(RetrievalResult(fact=fact, score=hit.score, retrieval_sources=("embedding",)))
        return results
