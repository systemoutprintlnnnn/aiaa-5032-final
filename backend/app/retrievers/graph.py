from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from app.knowledge_store import (
    clean_text,
    extract_explicit_identifiers,
    is_specific_name,
    normalize_for_search,
    tokenize,
)
from app.retrievers.base import RetrievalResult
from app.stores import Fact

KG_DATA_SOURCE = "MOF KG JSON"


class KGGraphRetriever:
    """Local JSON graph retriever for KG Builder exports."""

    def __init__(self, graph_path: Path) -> None:
        self.graph_path = graph_path
        self.facts: list[Fact] = []
        self.fact_count = 0
        self.is_loaded = False
        self.load_error: str | None = None
        self._facts_by_subject: dict[str, list[Fact]] = defaultdict(list)
        self._facts_by_target: dict[str, list[Fact]] = defaultdict(list)
        self._known_identifiers: set[str] = set()
        self._subject_names: dict[str, tuple[str, ...]] = {}
        self._load()

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        if not self.facts:
            return []

        query_text = normalize_for_search(query)
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return []

        explicit_identifiers = extract_explicit_identifiers(query)
        if explicit_identifiers and not self._has_known_identifier(explicit_identifiers):
            return []

        desired_rel_types = _desired_relation_types(query_text)
        if _is_unsupported_property_query(query_text) and not desired_rel_types:
            return []

        shared_results = self._shared_neighbor_results(query_text, desired_rel_types, limit)
        if shared_results:
            return [RetrievalResult(fact=fact, score=score, retrieval_sources=("kg",)) for fact, score in self._dedupe(shared_results, limit)]

        scored: list[tuple[Fact, float]] = []
        for fact in self.facts:
            score = self._score_fact(fact, query_text, query_tokens, desired_rel_types)
            if score > 0:
                scored.append((fact, score))

        if desired_rel_types:
            focused = [(fact, score) for fact, score in scored if _fact_rel_type(fact) in desired_rel_types]
            if focused:
                scored = focused

        scored.sort(key=lambda item: item[1], reverse=True)
        return [RetrievalResult(fact=fact, score=score, retrieval_sources=("kg",)) for fact, score in self._dedupe(scored, limit)]

    def _load(self) -> None:
        if not self.graph_path.exists():
            return

        try:
            raw = json.loads(self.graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.load_error = str(exc)
            return

        nodes: dict[str, dict[str, Any]] = raw.get("nodes", {})
        relationships: list[dict[str, Any]] = raw.get("relationships", [])
        self._subject_names = _build_subject_names(nodes, relationships)
        self._known_identifiers = _build_known_identifiers(nodes, self._subject_names)

        for idx, rel in enumerate(relationships):
            from_id = clean_text(rel.get("from"))
            to_id = clean_text(rel.get("to"))
            rel_type = clean_text(rel.get("type"))
            if not from_id.startswith("MOF:") or not to_id or not rel_type:
                continue

            source_node = nodes.get(from_id, {})
            target_node = nodes.get(to_id, {})
            fact = self._relationship_to_fact(idx, from_id, to_id, rel_type, rel, source_node, target_node)
            if fact is None:
                continue
            self.facts.append(fact)
            self._facts_by_subject[from_id].append(fact)
            self._facts_by_target[to_id].append(fact)

        self.fact_count = len(self.facts)
        self.is_loaded = self.fact_count > 0

    def _relationship_to_fact(
        self,
        idx: int,
        from_id: str,
        to_id: str,
        rel_type: str,
        rel: dict[str, Any],
        source_node: dict[str, Any],
        target_node: dict[str, Any],
    ) -> Fact | None:
        source_attrs = source_node.get("attributes", {})
        target_attrs = target_node.get("attributes", {})
        refcode = clean_text(source_attrs.get("refcode")) or from_id.removeprefix("MOF:")
        names = self._subject_names.get(from_id, ())
        relation = _human_relation(rel_type)
        value = _target_value(target_attrs, to_id)
        if not value:
            return None

        evidence_parts = [f"{names[0] if names else refcode} has KG relation {rel_type} to {value}."]
        rel_attrs = rel.get("attributes") or {}
        evidence = clean_text(rel_attrs.get("evidence")) or clean_text(target_attrs.get("evidence"))
        condition = clean_text(target_attrs.get("condition"))
        formula = clean_text(target_attrs.get("formula"))
        smiles = clean_text(target_attrs.get("smiles"))
        if evidence:
            evidence_parts.append(evidence)
        if condition:
            evidence_parts.append(f"Condition: {condition}.")
        if formula:
            evidence_parts.append(f"Formula: {formula}.")
        if smiles:
            evidence_parts.append(f"SMILES: {smiles}.")

        search_text = " ".join([refcode, *names, relation, rel_type, value, " ".join(evidence_parts), to_id])
        return Fact(
            id=f"kg-{idx}",
            refcode=refcode,
            material_names=names,
            relation=relation,
            value=value,
            evidence=" ".join(evidence_parts),
            doi=value if rel_type == "CITED_IN" else None,
            data_source=KG_DATA_SOURCE,
            path=f"Material({refcode}) -> {rel_type} -> {to_id}",
            search_text=normalize_for_search(search_text),
        )

    def _score_fact(self, fact: Fact, query_text: str, query_tokens: list[str], desired_rel_types: set[str]) -> float:
        score = 0.0
        fact_tokens = set(tokenize(fact.search_text))
        for token in query_tokens:
            if token in fact_tokens:
                score += 1.0
            elif len(token) > 3 and token in fact.search_text:
                score += 0.5

        if fact.refcode and normalize_for_search(fact.refcode).strip() in query_text:
            score += 30.0
        for name in fact.material_names:
            normalized_name = normalize_for_search(name).strip()
            if _is_distinct_name(normalized_name) and normalized_name in query_text:
                score += 25.0

        rel_type = _fact_rel_type(fact)
        if rel_type in desired_rel_types:
            score += 12.0
        elif desired_rel_types:
            score -= 4.0
        return max(score, 0.0)

    def _has_known_identifier(self, identifiers: set[str]) -> bool:
        for identifier in identifiers:
            if identifier in self._known_identifiers:
                return True
            if len(identifier) >= 5 and any(identifier in known for known in self._known_identifiers):
                return True
        return False

    def _shared_neighbor_results(self, query_text: str, desired_rel_types: set[str], limit: int) -> list[tuple[Fact, float]]:
        if not any(term in query_text for term in ["same", "other", "share", "shared", "also use", "common"]):
            return []

        seed_subjects = [
            subject
            for subject, names in self._subject_names.items()
            if _subject_matches_query(subject, names, query_text)
        ]
        if not seed_subjects:
            return []

        shareable_rel_types = desired_rel_types & {"USES_METAL_PRECURSOR", "USES_ORGANIC_PRECURSOR", "USES_SOLVENT", "USES_METHOD", "CITED_IN"}
        if not shareable_rel_types:
            shareable_rel_types = {"USES_METAL_PRECURSOR", "USES_ORGANIC_PRECURSOR", "USES_SOLVENT", "USES_METHOD", "CITED_IN"}

        expanded: list[tuple[Fact, float]] = []
        seed_refcodes = {subject.removeprefix("MOF:") for subject in seed_subjects}
        for subject in seed_subjects[:3]:
            for seed_fact in self._facts_by_subject.get(subject, []):
                rel_type = _fact_rel_type(seed_fact)
                if rel_type not in shareable_rel_types:
                    continue
                target_id = seed_fact.path.rsplit(" -> ", 1)[-1]
                for related in self._facts_by_target.get(target_id, []):
                    if related.refcode in seed_refcodes:
                        continue
                    expanded.append(
                        (
                            _with_shared_neighbor_evidence(related, seed_fact, rel_type),
                            40.0 + (8.0 if rel_type in desired_rel_types else 0.0),
                        )
                    )
                    if len(expanded) >= limit:
                        return expanded
        return expanded

    @staticmethod
    def _dedupe(scored: list[tuple[Fact, float]], limit: int) -> list[tuple[Fact, float]]:
        seen: set[tuple[str | None, str, str]] = set()
        results: list[tuple[Fact, float]] = []
        for fact, score in scored:
            key = (fact.refcode, fact.relation, fact.value)
            if key in seen:
                continue
            seen.add(key)
            results.append((fact, score))
            if len(results) >= limit:
                break
        return results


class NoResultGraphRetriever:
    """Compatibility fallback used when KG is disabled, missing, or invalid."""

    fact_count = 0
    is_loaded = False
    load_error: str | None = None

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        return []


def _build_subject_names(nodes: dict[str, dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    names_by_subject: dict[str, list[str]] = defaultdict(list)
    for node_id, node in nodes.items():
        if not node_id.startswith("MOF:"):
            continue
        attrs = node.get("attributes", {})
        for value in [attrs.get("display_name"), attrs.get("chemical_name")]:
            text = clean_text(value)
            if text:
                names_by_subject[node_id].append(text)

    for rel in relationships:
        if clean_text(rel.get("type")) != "HAS_NAME":
            continue
        from_id = clean_text(rel.get("from"))
        to_id = clean_text(rel.get("to"))
        target = nodes.get(to_id, {})
        name = clean_text(target.get("attributes", {}).get("name"))
        if from_id.startswith("MOF:") and name:
            names_by_subject[from_id].append(name)

    return {subject: tuple(dict.fromkeys(names)) for subject, names in names_by_subject.items()}


def _build_known_identifiers(nodes: dict[str, dict[str, Any]], subject_names: dict[str, tuple[str, ...]]) -> set[str]:
    identifiers: set[str] = set()
    for node_id, node in nodes.items():
        if not node_id.startswith("MOF:"):
            continue
        refcode = clean_text(node.get("attributes", {}).get("refcode")) or node_id.removeprefix("MOF:")
        normalized_refcode = normalize_for_search(refcode).strip()
        if normalized_refcode:
            identifiers.add(normalized_refcode)
        for name in subject_names.get(node_id, ()):
            normalized_name = normalize_for_search(name).strip()
            if normalized_name:
                identifiers.add(normalized_name)
    return identifiers


def _human_relation(rel_type: str) -> str:
    mapping = {
        "HAS_STABILITY": "KG_HAS_STABILITY: Water Stability",
        "USES_METAL_PRECURSOR": "KG_USES_METAL_PRECURSOR",
        "USES_ORGANIC_PRECURSOR": "KG_USES_ORGANIC_PRECURSOR",
        "USES_SOLVENT": "KG_USES_SOLVENT",
        "USES_METHOD": "KG_USES_METHOD",
        "HAS_NAME": "KG_HAS_NAME",
        "CITED_IN": "KG_CITED_IN",
    }
    return mapping.get(rel_type, f"KG_{rel_type}")


def _with_shared_neighbor_evidence(related: Fact, seed: Fact, rel_type: str) -> Fact:
    seed_subject = seed.refcode or (seed.material_names[0] if seed.material_names else "the seed MOF")
    related_subject = related.refcode or (related.material_names[0] if related.material_names else "this MOF")
    evidence = (
        f"{related.evidence} Shared-neighbor context: {seed_subject} and {related_subject} "
        f"both have KG relation {rel_type} to {related.value}."
    )
    return replace(related, evidence=evidence)


def _target_value(attrs: dict[str, Any], node_id: str) -> str:
    for key in ["value", "name", "doi", "display_name", "refcode"]:
        value = clean_text(attrs.get(key))
        if value:
            return value
    if ":" in node_id:
        return clean_text(node_id.rsplit(":", 1)[-1])
    return clean_text(node_id)


def _desired_relation_types(query_text: str) -> set[str]:
    desired: set[str] = set()
    if any(word in query_text for word in ["water", "stable", "stability", "soluble"]):
        desired.add("HAS_STABILITY")
    if any(word in query_text for word in ["name", "alias", "coreference", "called", "associated", "csd", "ref code", "refcode"]):
        desired.add("HAS_NAME")
    if any(word in query_text for word in ["method", "synthesis method", "solvothermal"]):
        desired.add("USES_METHOD")
    if "metal precursor" in query_text:
        desired.add("USES_METAL_PRECURSOR")
    if any(word in query_text for word in ["organic precursor", "linker", "ligand"]):
        desired.add("USES_ORGANIC_PRECURSOR")
    if "solvent" in query_text:
        desired.add("USES_SOLVENT")
    if any(word in query_text for word in ["doi", "source", "paper", "reference"]):
        desired.add("CITED_IN")
    return desired


def _is_unsupported_property_query(query_text: str) -> bool:
    return any(word in query_text for word in ["surface", "bet", "pore", "uptake", "conductivity"])


def _fact_rel_type(fact: Fact) -> str:
    parts = fact.path.split(" -> ")
    return parts[1] if len(parts) >= 3 else fact.relation.removeprefix("KG_")


def _subject_matches_query(subject: str, names: tuple[str, ...], query_text: str) -> bool:
    refcode = normalize_for_search(subject.removeprefix("MOF:")).strip()
    if refcode and refcode in query_text:
        return True
    for name in names:
        normalized_name = normalize_for_search(name).strip()
        if _is_distinct_name(normalized_name) and normalized_name in query_text:
            return True
    return False


def _is_distinct_name(normalized_name: str) -> bool:
    if not is_specific_name(normalized_name):
        return False
    generic_query_words = {"common", "mof", "mofs", "other", "same", "shared", "material"}
    name_tokens = set(normalized_name.split())
    return bool(name_tokens - generic_query_words)
