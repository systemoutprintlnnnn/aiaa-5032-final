from __future__ import annotations

from app.knowledge_store import KG_RUNTIME_LICENSE_NOTICE, KG_SYNTHESIS_DATA_SOURCE, OPEN_SOURCE_LICENSE
from app.models import KGFact, QueryResponse, Source
from app.retrievers.base import RetrievalMatch, normalize_retrieval_results
from app.stores import Fact

KG_LICENSE_NOTICE = "Team/course-provided MOF KG data; no explicit public license supplied."


def compose_answer(query: str, matches: list[RetrievalMatch]) -> QueryResponse:
    results = normalize_retrieval_results(matches)
    if not results:
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

    for idx, result in enumerate(results, start=1):
        fact = result.fact
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
                retrieval_sources=list(result.retrieval_sources),
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

    mode = infer_mode(results)
    answer = "Found evidence in the runtime MOF knowledge store:\n\n" + "\n\n".join(lines)
    return QueryResponse(
        query=query,
        mode=mode,
        answer=answer,
        sources=sources,
        kg_facts=kg_facts,
        retrieved_count=len(results),
    )


def infer_mode(matches: list[RetrievalMatch]) -> str:
    results = normalize_retrieval_results(matches)
    relations = " ".join(result.fact.relation.lower() for result in results)
    if "water stability" in relations or "experimental_property" in relations or "computational_property" in relations:
        return "hard_fact_lookup"
    if "synthesis" in relations:
        return "descriptive_synthesis_lookup"
    if "has_name" in relations:
        return "alias_lookup"
    return "keyword_retrieval"


class DeterministicAnswerer:
    def answer(self, query: str, matches: list[RetrievalMatch]) -> QueryResponse:
        return compose_answer(query, matches)


def source_license(fact: Fact) -> str:
    if fact.data_source == "MOF KG JSON":
        return KG_LICENSE_NOTICE
    if fact.data_source == KG_SYNTHESIS_DATA_SOURCE:
        return KG_RUNTIME_LICENSE_NOTICE
    return OPEN_SOURCE_LICENSE
