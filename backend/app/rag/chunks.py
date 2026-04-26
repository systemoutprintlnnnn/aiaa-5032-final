from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge_store import KnowledgeStore


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    text: str
    payload: dict[str, Any]


def build_evidence_chunks(store: KnowledgeStore) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    fact_by_id = {fact.id: fact for fact in store.facts}
    for document in store.documents:
        fact = fact_by_id.get(document.fact_id)
        chunks.append(
            EvidenceChunk(
                id=document.id,
                text=document.text,
                payload={
                    "fact_id": document.fact_id,
                    "refcode": document.refcode,
                    "material_names": list(document.material_names),
                    "relation": document.relation,
                    "value": fact.value if fact else "",
                    "evidence": fact.evidence if fact else "",
                    "doi": document.doi,
                    "source": document.source,
                    "license": document.license,
                    "path": fact.path if fact else "",
                    "text": document.text,
                },
            )
        )
    return chunks
