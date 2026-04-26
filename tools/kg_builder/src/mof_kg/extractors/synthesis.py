"""Synthesis data extractor"""
import json
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

from mof_kg.models.schema import (
    MOFNode,
    MethodNode,
    PrecursorNode,
    DOINode,
    PrecursorType,
    RelationshipType,
)


@dataclass
class SynthesisRecord:
    """Raw synthesis record from JSON"""
    identifier: str  # CSD refcode
    name: str | None
    doi: str | None
    method: str | None
    metal_precursors: list[dict]
    organic_precursors: list[dict]
    solvent_precursors: list[dict]
    temperature: str | None
    time: str | None
    yield_value: str | None


class SynthesisExtractor:
    """Extract MOF, Precursor, Method, DOI nodes from synthesis JSON"""

    def __init__(self, path: Path):
        self.path = path

    def extract(self) -> Iterator[SynthesisRecord]:
        """Parse JSON and yield raw records"""
        with self.path.open(encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            identifier = item.get("identifier", "").strip()
            if not identifier:
                continue

            yield SynthesisRecord(
                identifier=identifier,
                name=item.get("name"),
                doi=item.get("doi"),
                method=item.get("method"),
                metal_precursors=item.get("M_precursor", []),
                organic_precursors=item.get("O_precursor", []),
                solvent_precursors=item.get("S_precursor", []),
                temperature=item.get("temperature"),
                time=item.get("time"),
                yield_value=item.get("Yield"),
            )

    def extract_precursor_info(self, precursor_dict: dict) -> tuple[str, str | None, str | None]:
        """Extract name, formula, smiles from precursor dict"""
        name = precursor_dict.get("name", "").strip()
        formula = precursor_dict.get("formula")
        smiles = precursor_dict.get("smiles")

        if formula:
            formula = formula.strip()
        if smiles:
            smiles = smiles.strip()

        return name, formula, smiles

    def extract_nodes_and_relations(self) -> tuple[
        list[MOFNode],
        list[PrecursorNode],
        list[MethodNode],
        list[DOINode],
        list[tuple[str, str, str]],
        dict[str, dict],  # MOF attributes (temperature, time, yield)
    ]:
        """Extract all nodes and relationships from synthesis data

        Returns:
            - List of MOF nodes
            - List of Precursor nodes (metal, organic, solvent)
            - List of Method nodes
            - List of DOI nodes
            - List of (mof_id, target_id, relation_type) tuples
            - Dict of MOF attributes (temperature, time, yield)
        """
        mof_nodes: list[MOFNode] = []
        precursor_nodes: list[PrecursorNode] = []
        method_nodes: list[MethodNode] = []
        doi_nodes: list[DOINode] = []
        relations: list[tuple[str, str, str]] = []
        mof_attributes: dict[str, dict] = {}

        seen_mofs: set[str] = set()
        seen_precursors: set[str] = set()  # Key: type:name
        seen_methods: set[str] = set()
        seen_dois: set[str] = set()

        for record in self.extract():
            mof_id = f"MOF:{record.identifier}"

            # Create MOF node
            if record.identifier not in seen_mofs:
                mof_nodes.append(MOFNode(
                    refcode=record.identifier,
                    display_name=record.name,
                    chemical_name=record.name,
                ))
                seen_mofs.add(record.identifier)

            # Store MOF attributes (temperature, time, yield)
            mof_attributes[record.identifier] = {
                "temperature": record.temperature,
                "time": record.time,
                "yield": record.yield_value,
            }

            # Create Method node (shared)
            if record.method:
                method_key = record.method
                if method_key not in seen_methods:
                    method_nodes.append(MethodNode(name=method_key))
                    seen_methods.add(method_key)
                relations.append((
                    mof_id,
                    f"Method:{method_key}",
                    RelationshipType.USES_METHOD.value,
                ))

            # Create DOI node (shared)
            if record.doi:
                if record.doi not in seen_dois:
                    doi_nodes.append(DOINode(doi=record.doi))
                    seen_dois.add(record.doi)
                relations.append((
                    mof_id,
                    f"DOI:{record.doi}",
                    RelationshipType.CITED_IN.value,
                ))

            # Create Precursor nodes (metal)
            for p in record.metal_precursors:
                name, formula, smiles = self.extract_precursor_info(p)
                if name:
                    precursor_key = f"metal:{name}"
                    if precursor_key not in seen_precursors:
                        precursor_nodes.append(PrecursorNode(
                            name=name,
                            formula=formula,
                            smiles=smiles,
                            precursor_type=PrecursorType.METAL,
                        ))
                        seen_precursors.add(precursor_key)
                    relations.append((
                        mof_id,
                        f"Precursor:metal:{name}",
                        RelationshipType.USES_METAL_PRECURSOR.value,
                    ))

            # Create Precursor nodes (organic)
            for p in record.organic_precursors:
                name, formula, smiles = self.extract_precursor_info(p)
                if name:
                    precursor_key = f"organic:{name}"
                    if precursor_key not in seen_precursors:
                        precursor_nodes.append(PrecursorNode(
                            name=name,
                            formula=formula,
                            smiles=smiles,
                            precursor_type=PrecursorType.ORGANIC,
                        ))
                        seen_precursors.add(precursor_key)
                    relations.append((
                        mof_id,
                        f"Precursor:organic:{name}",
                        RelationshipType.USES_ORGANIC_PRECURSOR.value,
                    ))

            # Create Precursor nodes (solvent)
            for p in record.solvent_precursors:
                name, formula, smiles = self.extract_precursor_info(p)
                if name:
                    precursor_key = f"solvent:{name}"
                    if precursor_key not in seen_precursors:
                        precursor_nodes.append(PrecursorNode(
                            name=name,
                            formula=formula,
                            smiles=smiles,
                            precursor_type=PrecursorType.SOLVENT,
                        ))
                        seen_precursors.add(precursor_key)
                    relations.append((
                        mof_id,
                        f"Precursor:solvent:{name}",
                        RelationshipType.USES_SOLVENT.value,
                    ))

        return mof_nodes, precursor_nodes, method_nodes, doi_nodes, relations, mof_attributes