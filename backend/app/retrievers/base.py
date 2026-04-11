from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.knowledge_store import Fact


@dataclass(frozen=True)
class RetrievalResult:
    fact: Fact
    score: float


class Retriever(Protocol):
    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        """Return ranked facts for a natural-language query."""
