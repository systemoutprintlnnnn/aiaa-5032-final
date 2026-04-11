from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.rag.chunks import EvidenceChunk


@dataclass(frozen=True)
class VectorHit:
    id: str
    score: float
    payload: dict[str, Any]


class QdrantVectorStore:
    def __init__(self, *, url: str, collection: str, dimensions: int, client: QdrantClient | None = None) -> None:
        self.collection = collection
        self.dimensions = dimensions
        self.client = client or QdrantClient(url=url)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.collection for collection in collections):
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.dimensions, distance=Distance.COSINE),
        )

    def upsert_chunks(self, chunks: list[EvidenceChunk], vectors: list[list[float]], start_index: int = 0) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        self.ensure_collection()
        points = [
            PointStruct(id=start_index + idx, vector=vector, payload={**chunk.payload, "chunk_id": chunk.id})
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], limit: int) -> list[VectorHit]:
        hits = self.client.query_points(collection_name=self.collection, query=query_vector, limit=limit).points
        return [
            VectorHit(id=str(hit.id), score=float(hit.score), payload=dict(hit.payload or {}))
            for hit in hits
        ]
