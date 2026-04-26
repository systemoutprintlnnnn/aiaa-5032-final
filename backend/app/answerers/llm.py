from __future__ import annotations

from typing import Iterator

from openai import OpenAI

from app.answerers.deterministic import compose_answer
from app.models import QueryResponse
from app.retrievers.base import RetrievalMatch, normalize_retrieval_results


SYSTEM_PROMPT = (
    "Answer using only the evidence provided. Cite source ids like [S1]. "
    "If the evidence is insufficient, say that the current runtime knowledge store does not contain enough evidence."
)
MAX_EVIDENCE_TEXT_LENGTH = 1800


def _format_evidence(matches: list[RetrievalMatch]) -> str:
    results = normalize_retrieval_results(matches)
    return "\n".join(
        (
            f"[S{idx}] refcode={result.fact.refcode or 'material'} | relation={result.fact.relation} | "
            f"value={_truncate(result.fact.value)} | retrieval={','.join(result.retrieval_sources) or 'unknown'} | "
            f"source={result.fact.data_source} | doi={result.fact.doi or 'none'} | path={result.fact.path} | "
            f"evidence={_truncate(result.fact.evidence)}"
        )
        for idx, result in enumerate(results, start=1)
    )


def _truncate(text: str) -> str:
    if len(text) <= MAX_EVIDENCE_TEXT_LENGTH:
        return text
    return text[: MAX_EVIDENCE_TEXT_LENGTH - 3].rstrip() + "..."


class OpenAILLMAnswerer:
    def __init__(self, *, model: str, api_key: str, base_url: str | None = None, client: object | None = None) -> None:
        if not api_key:
            raise RuntimeError("RAG_API_KEY is required for OpenAI LLM answering.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)

    def answer(self, query: str, matches: list[RetrievalMatch]) -> QueryResponse:
        response = compose_answer(query, matches)
        if not matches:
            return response

        llm_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {query}\n\nEvidence:\n{_format_evidence(matches)}"},
            ],
        )
        answer_text = llm_response.choices[0].message.content.strip()
        if answer_text:
            response.answer = answer_text
            response.mode = "hybrid_rag"
        return response

    def stream_tokens(self, query: str, matches: list[RetrievalMatch]) -> Iterator[str]:
        if not matches:
            return
        stream = self.client.chat.completions.create(
            model=self.model,
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {query}\n\nEvidence:\n{_format_evidence(matches)}"},
            ],
        )
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            text = getattr(delta, "content", None) if delta is not None else None
            if text:
                yield text
