from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.stores import Fact

RetrievalSource = str


@dataclass(frozen=True)
class RetrievalResult:
    fact: Fact
    score: float
    retrieval_sources: tuple[RetrievalSource, ...] = ()


RetrievalMatch = RetrievalResult | tuple[Fact, float]


def normalize_retrieval_results(matches: list[RetrievalMatch]) -> list[RetrievalResult]:
    results: list[RetrievalResult] = []
    for match in matches:
        if isinstance(match, RetrievalResult):
            results.append(match)
        else:
            fact, score = match
            results.append(RetrievalResult(fact=fact, score=score))
    return results


class Retriever(Protocol):
    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        """Return ranked facts for a natural-language query."""
