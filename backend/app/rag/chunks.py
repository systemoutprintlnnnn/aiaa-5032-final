from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge_store import KnowledgeStore, OPEN_SOURCE_LICENSE


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    text: str
    payload: dict[str, Any]


def build_evidence_chunks(store: KnowledgeStore) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for fact in store.facts:
        subject = fact.refcode or (fact.material_names[0] if fact.material_names else "material")
        text = f"{subject}. {fact.relation}: {fact.value}. Evidence: {fact.evidence}"
        chunks.append(
            EvidenceChunk(
                id=fact.id,
                text=text,
                payload={
                    "fact_id": fact.id,
                    "refcode": fact.refcode,
                    "material_names": list(fact.material_names),
                    "relation": fact.relation,
                    "value": fact.value,
                    "evidence": fact.evidence,
                    "doi": fact.doi,
                    "source": fact.data_source,
                    "license": OPEN_SOURCE_LICENSE,
                    "path": fact.path,
                    "text": text,
                },
            )
        )
    return chunks
