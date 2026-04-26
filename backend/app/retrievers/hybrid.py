from __future__ import annotations

from app.knowledge_store import extract_explicit_identifiers, normalize_for_search
from app.retrievers.base import RetrievalResult, Retriever
from app.stores import Fact


class HybridRetriever:
    """Merge simple RAG retrieval with optional KG retrieval."""

    def __init__(self, retrievers: list[Retriever]) -> None:
        self.retrievers = retrievers

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        merged: list[RetrievalResult] = []
        seen: set[tuple[str | None, str, str]] = set()

        for retriever in self.retrievers:
            for result in retriever.search(query, limit=limit):
                key = (result.fact.refcode, result.fact.relation, result.fact.value)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(result)

        merged.sort(key=lambda item: item.score, reverse=True)

        if _is_shared_neighbor_query(query):
            seed_identifiers = extract_explicit_identifiers(query)
            if seed_identifiers:
                merged = [result for result in merged if not _fact_matches_identifier(result.fact, seed_identifiers)]
            kg_results = [result for result in merged if result.fact.data_source == "MOF KG JSON"]
            if kg_results:
                merged = kg_results

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
