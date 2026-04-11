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
