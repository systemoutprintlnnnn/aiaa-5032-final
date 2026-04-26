from __future__ import annotations

from app.knowledge_store import KG_RUNTIME_LICENSE_NOTICE, KG_SYNTHESIS_DATA_SOURCE, OPEN_SOURCE_LICENSE
from app.models import KGFact, QueryResponse, Source
from app.stores import Fact

KG_LICENSE_NOTICE = "Team/course-provided MOF KG data; no explicit public license supplied."


def compose_answer(query: str, matches: list[tuple[Fact, float]]) -> QueryResponse:
    if not matches:
        return QueryResponse(
            query=query,
            mode="insufficient_evidence",
            answer=(
                "I could not find enough evidence in the current runtime MOF knowledge store. "
                "The References folder is intentionally not used as the QA corpus; add or connect a real MOF data source to answer this."
            ),
            sources=[],
            kg_facts=[],
            retrieved_count=0,
        )

    sources: list[Source] = []
    kg_facts: list[KGFact] = []
    lines: list[str] = []

    for idx, (fact, _score) in enumerate(matches, start=1):
        source_id = f"S{idx}"
        subject = fact.refcode or (fact.material_names[0] if fact.material_names else "material")
        lines.append(f"[{source_id}] {subject}: {fact.relation} = {fact.value}. Evidence: {fact.evidence}")
        sources.append(
            Source(
                id=source_id,
                title=f"{fact.data_source} ({subject})",
                doi=fact.doi,
                refcode=fact.refcode,
                evidence=fact.evidence,
                data_source=fact.data_source,
                license=source_license(fact),
            )
        )
        kg_facts.append(
            KGFact(
                path=fact.path,
                relation=fact.relation,
                value=fact.value,
                source_id=source_id,
            )
        )

    mode = infer_mode(matches)
    answer = "Found evidence in the runtime MOF knowledge store:\n\n" + "\n\n".join(lines)
    return QueryResponse(
        query=query,
        mode=mode,
        answer=answer,
        sources=sources,
        kg_facts=kg_facts,
        retrieved_count=len(matches),
    )


def infer_mode(matches: list[tuple[Fact, float]]) -> str:
    relations = " ".join(fact.relation.lower() for fact, _ in matches)
    if "water stability" in relations or "experimental_property" in relations or "computational_property" in relations:
        return "hard_fact_lookup"
    if "synthesis" in relations:
        return "descriptive_synthesis_lookup"
    if "has_name" in relations:
        return "alias_lookup"
    return "keyword_retrieval"


class DeterministicAnswerer:
    def answer(self, query: str, matches: list[tuple[Fact, float]]) -> QueryResponse:
        return compose_answer(query, matches)


def source_license(fact: Fact) -> str:
    if fact.data_source == "MOF KG JSON":
        return KG_LICENSE_NOTICE
    if fact.data_source == KG_SYNTHESIS_DATA_SOURCE:
        return KG_RUNTIME_LICENSE_NOTICE
    return OPEN_SOURCE_LICENSE
