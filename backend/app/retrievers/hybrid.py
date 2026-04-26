from __future__ import annotations

from dataclasses import replace

from app.knowledge_store import extract_explicit_identifiers, normalize_for_search
from app.retrievers.base import RetrievalResult, Retriever
from app.stores import Fact


class HybridRetriever:
    """Merge simple RAG retrieval with optional KG retrieval."""

    def __init__(self, retrievers: list[Retriever]) -> None:
        self.retrievers = retrievers

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        merged_by_key: dict[tuple[str | None, str, str], RetrievalResult] = {}

        for retriever in self.retrievers:
            for result in retriever.search(query, limit=limit):
                key = (result.fact.refcode, result.fact.relation, result.fact.value)
                existing = merged_by_key.get(key)
                if existing is None:
                    merged_by_key[key] = result
                    continue
                merged_by_key[key] = replace(
                    existing,
                    score=max(existing.score, result.score),
                    retrieval_sources=_merge_sources(existing.retrieval_sources, result.retrieval_sources),
                )

        merged = list(merged_by_key.values())
        merged.sort(key=lambda item: item.score, reverse=True)

        seed_identifiers = extract_explicit_identifiers(query)
        if _is_shared_neighbor_query(query):
            if seed_identifiers:
                merged = [result for result in merged if not _fact_matches_identifier(result.fact, seed_identifiers)]
            kg_results = [result for result in merged if result.fact.data_source == "MOF KG JSON"]
            if kg_results:
                merged = kg_results
        else:
            if seed_identifiers:
                merged = [result for result in merged if _fact_matches_identifier(result.fact, seed_identifiers)]
            if _is_synthesis_evidence_query(query):
                merged.sort(key=lambda item: (_synthesis_priority(item.fact), _synthesis_completeness(item.fact), item.score), reverse=True)

        return merged[:limit]


def _is_shared_neighbor_query(query: str) -> bool:
    query_text = f" {normalize_for_search(query).strip()} "
    shared_terms = [" same ", " shared ", " share ", " common ", " also use ", " also uses "]
    if any(term in query_text for term in shared_terms):
        return True

    relation_terms = [
        " use ",
        " uses ",
        " used ",
        " solvent ",
        " precursor ",
        " linker ",
        " method ",
        " stability ",
        " stable ",
        " source ",
        " paper ",
        " doi ",
    ]
    material_terms = [" mof ", " mofs ", " material ", " materials "]
    return (
        " other " in query_text
        and any(term in query_text for term in material_terms)
        and any(term in query_text for term in relation_terms)
    )


def _is_synthesis_evidence_query(query: str) -> bool:
    query_text = f" {normalize_for_search(query).strip()} "
    terms = [
        " synthesis ",
        " synthesize ",
        " synthesized ",
        " solvent ",
        " precursor ",
        " temperature ",
        " reaction time ",
        " procedure ",
        " yield ",
        " method ",
        " linker ",
        " ligand ",
    ]
    return any(term in query_text for term in terms)


def _synthesis_priority(fact: Fact) -> int:
    if fact.relation == "HAS_SYNTHESIS_EVIDENCE":
        return 2
    if fact.data_source == "MOF KG JSON" and fact.relation in {
        "KG_USES_METHOD",
        "KG_USES_METAL_PRECURSOR",
        "KG_USES_ORGANIC_PRECURSOR",
        "KG_USES_SOLVENT",
        "KG_CITED_IN",
    }:
        return 1
    return 0


def _synthesis_completeness(fact: Fact) -> int:
    if fact.relation != "HAS_SYNTHESIS_EVIDENCE":
        return 0
    text = normalize_for_search(f"{fact.value} {fact.evidence}")
    return sum(
        1
        for term in [
            "method",
            "metal precursor",
            "organic precursor",
            "linker",
            "solvent",
            "temperature",
            "reaction time",
            "operation",
            "yield",
            "doi",
        ]
        if term in text
    )


def _merge_sources(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    for source in [*left, *right]:
        if source and source not in merged:
            merged.append(source)
    return tuple(merged)


def _fact_matches_identifier(fact: Fact, identifiers: set[str]) -> bool:
    candidates = [fact.refcode or "", *fact.material_names]
    for candidate in candidates:
        normalized_candidate = normalize_for_search(candidate).strip()
        if not normalized_candidate:
            continue
        for identifier in identifiers:
            if identifier == normalized_candidate:
                return True
            if len(identifier) >= 5 and (identifier in normalized_candidate or normalized_candidate in identifier):
                return True
    return False
