from __future__ import annotations

from app.answerers.deterministic import DeterministicAnswerer, compose_answer
from app.models import QueryRequest, QueryResponse
from app.retrievers.base import RetrievalResult
from app.retrievers.base import Retriever


class QueryService:
    def __init__(self, retriever: Retriever, answerer: object | None = None) -> None:
        self.retriever = retriever
        self.answerer = answerer or DeterministicAnswerer()

    def answer(self, request: QueryRequest) -> QueryResponse:
        matches = self._retrieve(request)
        return self.answerer.answer(request.question, matches)

    def retrieve_matches(self, request: QueryRequest) -> list[RetrievalResult]:
        return self._retrieve(request)

    def baseline_response(self, request: QueryRequest, matches: list[RetrievalResult]) -> QueryResponse:
        return compose_answer(request.question, matches)

    def _retrieve(self, request: QueryRequest) -> list[RetrievalResult]:
        return self.retriever.search(request.question, limit=request.top_k)
