from __future__ import annotations

from openai import OpenAI

from app.answerers.deterministic import compose_answer
from app.models import QueryResponse
from app.stores import Fact


class OpenAILLMAnswerer:
    def __init__(self, *, model: str, api_key: str, client: object | None = None) -> None:
        if not api_key:
            raise RuntimeError("RAG_API_KEY is required for OpenAI LLM answering.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def answer(self, query: str, matches: list[tuple[Fact, float]]) -> QueryResponse:
        response = compose_answer(query, matches)
        if not matches:
            return response

        evidence = "\n".join(
            f"[S{idx}] {fact.refcode or 'material'} | {fact.relation} | {fact.value} | {fact.evidence}"
            for idx, (fact, _score) in enumerate(matches, start=1)
        )
        llm_response = self.client.responses.create(
            model=self.model,
            instructions=(
                "Answer using only the evidence provided. Cite source ids like [S1]. "
                "If the evidence is insufficient, say that the current runtime knowledge store does not contain enough evidence."
            ),
            input=f"Question: {query}\n\nEvidence:\n{evidence}",
        )
        answer_text = getattr(llm_response, "output_text", "").strip()
        if answer_text:
            response.answer = answer_text
            response.mode = "hybrid_rag"
        return response
