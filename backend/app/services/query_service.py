from __future__ import annotations

from app.answerer import compose_answer
from app.models import QueryRequest, QueryResponse
from app.retrievers.base import Retriever


class QueryService:
    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    def answer(self, request: QueryRequest) -> QueryResponse:
        results = self.retriever.search(request.question, limit=request.top_k)
        matches = [(result.fact, result.score) for result in results]
        return compose_answer(request.question, matches)
