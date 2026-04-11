from __future__ import annotations

from typing import Protocol

from openai import OpenAI


class RAGConfigurationError(RuntimeError):
    pass


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, query: str) -> list[float]:
        ...


class OpenAIEmbeddingProvider:
    def __init__(self, *, model: str, api_key: str, client: object | None = None) -> None:
        if not api_key:
            raise RAGConfigurationError("RAG_API_KEY is required for OpenAI embeddings.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [list(item.embedding) for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        vectors = self.embed_texts([query])
        return vectors[0]
