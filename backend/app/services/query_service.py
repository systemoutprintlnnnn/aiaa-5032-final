from __future__ import annotations

from app.answerers.deterministic import DeterministicAnswerer
from app.models import QueryRequest, QueryResponse
from app.retrievers.base import Retriever


class QueryService:
    def __init__(self, retriever: Retriever, answerer: object | None = None) -> None:
        self.retriever = retriever
        self.answerer = answerer or DeterministicAnswerer()

    def answer(self, request: QueryRequest) -> QueryResponse:
        results = self.retriever.search(request.question, limit=request.top_k)
        matches = [(result.fact, result.score) for result in results]
        return self.answerer.answer(request.question, matches)
