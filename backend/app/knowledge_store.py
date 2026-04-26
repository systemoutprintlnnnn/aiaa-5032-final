from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from app.data_sources.synthesis import SynthesisEvidenceRecord, load_synthesis_evidence_records
from app.stores import Document, Fact


OPEN_SOURCE_LICENSE = "MOF-ChemUnity data: CC BY-NC 4.0; code: MIT"
KG_RUNTIME_LICENSE_NOTICE = "Team/course-provided MOF KG data; no explicit public license supplied."
KG_SYNTHESIS_DATA_SOURCE = "MOF KG synthesis evidence"


class KnowledgeStore:
    """In-memory seed-data store backed by public MOF-ChemUnity sample data."""

    def __init__(self, data_dir: Path, synthesis_data_path: Path | None = None) -> None:
        self.data_dir = data_dir
        self.synthesis_data_path = synthesis_data_path
        self.facts: list[Fact] = []
        self.documents: list[Document] = []
        self.material_count = 0
        self.synthesis_evidence_count = 0
        self._load()

    def _load(self) -> None:
        demo_path = self.data_dir / "demo.json"
        water_path = self.data_dir / "water_stability_chemunity_v0.1.0.csv"
        names_path = self.data_dir / "mof_names_and_csd_codes.csv"

        if demo_path.exists():
            self._load_demo(demo_path)
        if water_path.exists():
            self._load_water_stability(water_path)
        if names_path.exists():
            self._load_names(names_path)
        if self.synthesis_data_path is not None:
            self._load_synthesis_evidence(self.synthesis_data_path)

    def _load_demo(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.material_count += len(data)

        for item in data:
            refcode = clean_text(item.get("refcode")) or None
            names = tuple(clean_text(name) for name in item.get("names", []) if clean_text(name))
            references = item.get("references") or []
            default_doi = references[0] if references else None

            if refcode or names:
                value = ", ".join(names) if names else "No names available"
                self._add_fact(
                    refcode=refcode,
                    names=names,
                    relation="HAS_NAME",
                    value=value,
                    evidence=f"{refcode or 'This material'} is associated with names: {value}.",
                    doi=default_doi,
                    data_source="MOF-ChemUnity demo.json",
                    path=f"Material({refcode}) -> HAS_NAME -> Name",
                )

            for prop in item.get("experimental_properties", []):
                self._add_property_fact(refcode, names, prop, "HAS_EXPERIMENTAL_PROPERTY", "MOF-ChemUnity demo.json", default_doi)

            for prop in item.get("computational_properties", []):
                prop_name = clean_text(prop.get("name"))
                if not prop_name or not is_useful_computational_property(prop_name):
                    continue
                self._add_property_fact(refcode, names, prop, "HAS_COMPUTATIONAL_PROPERTY", "MOF-ChemUnity demo.json", default_doi)

            synthesis = item.get("synthesis")
            if isinstance(synthesis, dict):
                self._add_synthesis_fact(refcode, names, synthesis, default_doi)

            for app in item.get("applications", []):
                app_name = clean_text(app.get("name"))
                recommendation = clean_text(app.get("recommendation"))
                justification = clean_text(app.get("justification"))
                if not app_name and not recommendation:
                    continue
                value = recommendation or app_name
                evidence = justification or recommendation or app_name
                self._add_fact(
                    refcode=refcode,
                    names=names,
                    relation="HAS_APPLICATION",
                    value=value,
                    evidence=evidence,
                    doi=clean_text(app.get("reference")) or default_doi,
                    data_source="MOF-ChemUnity demo.json",
                    path=f"Material({refcode}) -> HAS_APPLICATION -> Application",
                )

    def _load_water_stability(self, path: Path) -> None:
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                refcode = clean_text(row.get("Ref Code")) or None
                names = tuple(split_names(row.get("MOF Name")))
                value = clean_text(row.get("Value"))
                summary = clean_text(row.get("Summary"))
                condition = clean_text(row.get("Condition"))
                if not value and not summary:
                    continue
                evidence = summary or f"Water stability is reported as {value}."
                if condition:
                    evidence = f"{evidence} Condition: {condition}."
                self._add_fact(
                    refcode=refcode,
                    names=names,
                    relation="HAS_PROPERTY: Water Stability",
                    value=value or "Water stability reported",
                    evidence=evidence,
                    doi=clean_text(row.get("Reference")),
                    data_source="MOF-ChemUnity water_stability_chemunity_v0.1.0.csv",
                    path=f"Material({refcode}) -> HAS_PROPERTY -> Water Stability",
                )

    def _load_names(self, path: Path) -> None:
        with path.open(newline="", encoding="utf-8") as fh:
            for idx, row in enumerate(csv.DictReader(fh)):
                refcode = clean_text(row.get("Ref Code")) or None
                names = tuple(split_names(row.get("MOF Name")))
                if not refcode or not names:
                    continue
                self._add_fact(
                    refcode=refcode,
                    names=names,
                    relation="HAS_NAME",
                    value=", ".join(names),
                    evidence=f"{refcode} is associated with names/coreferences: {', '.join(names)}.",
                    doi=clean_text(row.get("Reference")),
                    data_source="MOF-ChemUnity MOF_names_and_CSD_codes.csv",
                    path=f"Material({refcode}) -> HAS_NAME -> Name",
                    fact_id=f"names-{idx}",
                )

    def _add_property_fact(
        self,
        refcode: str | None,
        names: tuple[str, ...],
        prop: dict[str, Any],
        relation: str,
        data_source: str,
        default_doi: str | None,
    ) -> None:
        name = clean_text(prop.get("name"))
        raw_value = prop.get("value")
        value = clean_text(str(raw_value)) if raw_value is not None else ""
        units = clean_text(prop.get("units"))
        summary = clean_text(prop.get("summary"))
        justification = clean_text(prop.get("justification"))
        if not name or not value:
            return

        value_with_units = f"{value} {units}".strip() if units and units.lower() != "none" else value
        evidence = justification or summary or f"{name}: {value_with_units}"
        self._add_fact(
            refcode=refcode,
            names=names,
            relation=f"{relation}: {name}",
            value=value_with_units,
            evidence=evidence,
            doi=clean_text(prop.get("reference")) or default_doi,
            data_source=data_source,
            path=f"Material({refcode}) -> {relation} -> {name}",
        )

    def _add_synthesis_fact(self, refcode: str | None, names: tuple[str, ...], synthesis: dict[str, Any], default_doi: str | None) -> None:
        procedure = clean_text(synthesis.get("procedure"))
        justification = clean_text(synthesis.get("justification"))
        if not procedure and not justification:
            return

        parts = []
        for key, label in [
            ("metal_precursor", "metal precursor"),
            ("linker", "linker"),
            ("solvent", "solvent"),
            ("temperature", "temperature"),
            ("reaction_time", "reaction time"),
            ("conditions", "conditions"),
        ]:
            value = clean_text(synthesis.get(key))
            if value and value.lower() not in {"not provided", "not specified"}:
                parts.append(f"{label}: {value}")

        value = "; ".join(parts) if parts else "Synthesis procedure available"
        evidence = procedure or justification
        self._add_fact(
            refcode=refcode,
            names=names,
            relation="HAS_SYNTHESIS",
            value=value,
            evidence=evidence,
            doi=clean_text(synthesis.get("reference")) or default_doi,
            data_source="MOF-ChemUnity demo.json",
            path=f"Material({refcode}) -> HAS_SYNTHESIS -> Synthesis",
        )

    def _load_synthesis_evidence(self, path: Path) -> None:
        for record in load_synthesis_evidence_records(path):
            self._add_synthesis_evidence_fact(record)
            self.synthesis_evidence_count += 1

    def _add_synthesis_evidence_fact(self, record: SynthesisEvidenceRecord) -> None:
        search_text = " ".join([record.refcode, *record.names, "HAS_SYNTHESIS_EVIDENCE", record.value, record.evidence, record.doi or ""])
        fact = Fact(
            id=f"kg-synthesis-{record.row_index}",
            refcode=record.refcode,
            material_names=record.names,
            relation="HAS_SYNTHESIS_EVIDENCE",
            value=record.value,
            evidence=record.evidence,
            doi=record.doi,
            data_source=KG_SYNTHESIS_DATA_SOURCE,
            path=f"Material({record.refcode}) -> HAS_SYNTHESIS_EVIDENCE -> SynthesisRecord:{record.row_index}",
            search_text=normalize_for_search(search_text),
        )
        self.facts.append(fact)
        self.documents.append(
            Document(
                id=f"doc-{fact.id}",
                text=f"{record.refcode}. {fact.relation}: {fact.value}. Evidence: {fact.evidence}",
                refcode=fact.refcode,
                material_names=fact.material_names,
                relation=fact.relation,
                source=fact.data_source,
                doi=fact.doi,
                license=KG_RUNTIME_LICENSE_NOTICE,
                fact_id=fact.id,
            )
        )

    def _add_fact(
        self,
        *,
        refcode: str | None,
        names: tuple[str, ...],
        relation: str,
        value: str,
        evidence: str,
        doi: str | None,
        data_source: str,
        path: str,
        fact_id: str | None = None,
        license: str = OPEN_SOURCE_LICENSE,
    ) -> None:
        fact_id = fact_id or f"fact-{len(self.facts)}"
        text = " ".join([refcode or "", *names, relation, value, evidence, doi or ""])
        fact = Fact(
            id=fact_id,
            refcode=refcode,
            material_names=names,
            relation=relation,
            value=value,
            evidence=evidence,
            doi=doi,
            data_source=data_source,
            path=path,
            search_text=normalize_for_search(text),
        )
        self.facts.append(fact)
        self.documents.append(
            Document(
                id=f"doc-{fact.id}",
                text=f"{fact.relation}: {fact.value}. Evidence: {fact.evidence}",
                refcode=fact.refcode,
                material_names=fact.material_names,
                relation=fact.relation,
                source=fact.data_source,
                doi=fact.doi,
                license=license,
                fact_id=fact.id,
            )
        )

    def search(self, query: str, limit: int = 6) -> list[tuple[Fact, float]]:
        query_text = normalize_for_search(query)
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return []
        explicit_identifiers = extract_explicit_identifiers(query)
        if explicit_identifiers and not self._has_known_identifier(explicit_identifiers):
            return []

        scored: list[tuple[Fact, float]] = []
        has_explicit_entity = False
        for fact in self.facts:
            fact_tokens = set(tokenize(fact.search_text))
            if not fact_tokens:
                continue

            score = 0.0
            entity_match = False
            for token in query_tokens:
                if token in fact_tokens:
                    score += 1.0
                elif len(token) > 3 and token in fact.search_text:
                    score += 0.5

            if fact.refcode and fact.refcode.lower() in query_text:
                score += 5.0
                entity_match = True
            for name in fact.material_names:
                normalized_name = normalize_for_search(name).strip()
                if is_specific_name(normalized_name) and normalized_name in query_text:
                    score += 5.0
                    entity_match = True

            score += relation_bonus(query_text, fact.relation)

            if score > 0:
                has_explicit_entity = has_explicit_entity or entity_match
                scored.append((fact, score + (20.0 if entity_match else 0.0)))

        if has_explicit_entity:
            scored = [
                (fact, score)
                for fact, score in scored
                if (fact.refcode and fact.refcode.lower() in query_text)
                or any(is_specific_name(normalize_for_search(name).strip()) and normalize_for_search(name).strip() in query_text for name in fact.material_names)
            ]

        desired_relations = infer_desired_relations(query_text)
        if desired_relations:
            focused = [(fact, score) for fact, score in scored if relation_matches(fact.relation, desired_relations)]
            if focused:
                scored = focused

        scored.sort(key=lambda item: item[1], reverse=True)
        return dedupe(scored, limit)

    def _has_known_identifier(self, identifiers: set[str]) -> bool:
        for fact in self.facts:
            candidates = [fact.refcode or "", *fact.material_names]
            for candidate in candidates:
                normalized_candidate = normalize_for_search(candidate).strip()
                if not normalized_candidate:
                    continue
                for identifier in identifiers:
                    if identifier == normalized_candidate:
                        return True
                    if len(identifier) >= 5 and is_specific_name(identifier) and identifier in normalized_candidate:
                        return True
        return False


def dedupe(scored: list[tuple[Fact, float]], limit: int) -> list[tuple[Fact, float]]:
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


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def split_names(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    return [part.strip() for part in text.split("<|>") if part.strip()]


def normalize_for_search(text: str) -> str:
    return re.sub(r"[^a-z0-9α-ωåÅ°₂₃₄₅₆₇₈₉()+./-]+", " ", text.lower())


def tokenize(text: str) -> list[str]:
    stopwords = {
        "the", "is", "are", "a", "an", "of", "for", "to", "in", "on", "with",
        "what", "which", "show", "tell", "me", "about", "does", "do", "and",
        "mof", "material",
    }
    return [token for token in text.split() if len(token) > 1 and token not in stopwords]


def extract_explicit_identifiers(raw_query: str) -> set[str]:
    identifiers: set[str] = set()
    generic = {"CSD", "MOF", "BET"}
    for candidate in re.findall(r"[A-Za-z0-9][A-Za-z0-9_()/-]{3,}", raw_query):
        if candidate.upper() in generic:
            continue
        has_digit = any(char.isdigit() for char in candidate)
        has_structural_marker = any(char in candidate for char in "_-()/")
        is_refcode_like = candidate.isupper() and len(candidate) >= 5
        if has_structural_marker or (has_digit and any(char.isalpha() for char in candidate)) or is_refcode_like:
            normalized = normalize_for_search(candidate).strip()
            if normalized:
                identifiers.add(normalized)
    return identifiers


def is_specific_name(name: str) -> bool:
    if not name:
        return False
    if len(name) < 4:
        return False
    generic = {"compound", "complex", "material"}
    return name not in generic


def relation_bonus(query_text: str, relation: str) -> float:
    relation_text = relation.lower()
    bonus = 0.0
    if any(word in query_text for word in ["water", "stable", "stability", "soluble"]) and "water stability" in relation_text:
        bonus += 4.0
    synthesis_terms = [
        "synthesis",
        "synthesize",
        "solvent",
        "temperature",
        "precursor",
        "procedure",
        "yield",
        "reaction time",
        "method",
        "linker",
        "ligand",
    ]
    if any(word in query_text for word in synthesis_terms) and "synthesis" in relation_text:
        bonus += 4.0
    if any(word in query_text for word in ["name", "alias", "coreference", "called"]) and "has_name" in relation_text:
        bonus += 3.0
    if any(word in query_text for word in ["surface", "bet"]) and "surface area" in relation_text:
        bonus += 4.0
    if "pore volume" in query_text and "pore volume" in relation_text:
        bonus += 4.0
    if "pore diameter" in query_text and "pore diameter" in relation_text:
        bonus += 4.0
    if "uptake" in query_text and "uptake" in relation_text:
        bonus += 3.0
    return bonus


def infer_desired_relations(query_text: str) -> set[str]:
    desired: set[str] = set()
    if any(word in query_text for word in ["water", "stable", "stability", "soluble"]):
        desired.add("water stability")
    if any(
        word in query_text
        for word in ["synthesis", "synthesize", "solvent", "temperature", "precursor", "conditions", "procedure", "yield", "reaction time", "method", "linker", "ligand"]
    ):
        desired.add("synthesis")
    if any(word in query_text for word in ["name", "alias", "coreference", "called", "associated"]):
        desired.add("name")
    if any(word in query_text for word in ["surface", "bet"]):
        desired.add("surface area")
    if "pore volume" in query_text:
        desired.add("pore volume")
    if "pore diameter" in query_text:
        desired.add("pore diameter")
    if "uptake" in query_text:
        desired.add("uptake")
    return desired


def relation_matches(relation: str, desired_relations: set[str]) -> bool:
    relation_text = relation.lower()
    for desired in desired_relations:
        if desired == "name" and "has_name" in relation_text:
            return True
        if desired == "synthesis" and "synthesis" in relation_text:
            return True
        if desired in relation_text:
            return True
    return False


def is_useful_computational_property(name: str) -> bool:
    lowered = name.lower()
    useful_terms = [
        "doi",
        "journal",
        "metal types",
        "molecular formula",
        "crystal system",
        "density",
        "surface area",
        "pore",
        "uptake",
        "logkh",
        "largest included sphere",
        "largest free sphere",
        "space group",
        "cellv",
    ]
    return any(term in lowered for term in useful_terms)
