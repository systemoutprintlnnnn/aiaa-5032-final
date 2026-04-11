from __future__ import annotations

from app.retrievers.base import RetrievalResult


class NoResultGraphRetriever:
    """KG adapter slot until the graph team provides graph-backed evidence."""

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        return []
