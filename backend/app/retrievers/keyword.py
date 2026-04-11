from __future__ import annotations

from app.knowledge_store import KnowledgeStore
from app.retrievers.base import RetrievalResult


class KeywordRetriever:
    """Temporary entity/keyword retriever until Qdrant and Neo4j are connected."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        return [RetrievalResult(fact=fact, score=score) for fact, score in self.store.search(query, limit=limit)]
