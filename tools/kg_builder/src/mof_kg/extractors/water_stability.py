"""Water stability data extractor"""
import csv
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

from mof_kg.models.schema import MOFNode, StabilityNode, DOINode, RelationshipType


@dataclass
class WaterStabilityRecord:
    """Raw water stability record from CSV"""
    mof_name: str
    refcode: str
    value: str
    condition: str | None
    summary: str | None
    doi: str | None


class WaterStabilityExtractor:
    """Extract MOF, Stability, and DOI nodes from water stability CSV"""

    def __init__(self, path: Path):
        self.path = path

    def extract(self) -> Iterator[WaterStabilityRecord]:
        """Parse CSV and yield raw records"""
        with self.path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse MOF names (may contain <|> separator for multiple names)
                mof_name = row.get("MOF Name", "").strip()
                refcode = row.get("Ref Code", "").strip()
                value = row.get("Value", "").strip()
                condition = row.get("Condition", "").strip() or None
                summary = row.get("Summary", "").strip() or None
                doi = row.get("Reference", "").strip() or None

                if refcode and value:
                    yield WaterStabilityRecord(
                        mof_name=mof_name,
                        refcode=refcode,
                        value=value,
                        condition=condition,
                        summary=summary,
                        doi=doi,
                    )

    def get_primary_name(self, mof_name: str) -> str:
        """Extract primary name from <|> separated names"""
        if "<|>" in mof_name:
            parts = mof_name.split("<|>")
            # Prefer named MOF (like "UTSA-67") over generic names
            for part in parts:
                part = part.strip()
                # Skip generic names like "compound 1", "complex 3"
                if not any(g in part.lower() for g in ["compound", "complex"]):
                    if len(part) > 2:
                        return part
            # Fall back to first part
            return parts[0].strip()
        return mof_name

    def extract_nodes_and_relations(self) -> tuple[list[MOFNode], list[StabilityNode], list[DOINode], list[tuple[str, str, str, str | None]]]:
        """Extract all nodes and relationships from water stability data

        Returns:
            - List of MOF nodes
            - List of Stability nodes
            - List of DOI nodes
            - List of (mof_id, stability_id, relation_type, evidence) tuples
        """
        mof_nodes: list[MOFNode] = []
        stability_nodes: list[StabilityNode] = []
        doi_nodes: list[DOINode] = []
        relations: list[tuple[str, str, str, str | None]] = []

        seen_mofs: set[str] = set()
        seen_stabilities: set[str] = set()
        seen_dois: set[str] = set()

        for record in self.extract():
            # Create MOF node
            if record.refcode not in seen_mofs:
                primary_name = self.get_primary_name(record.mof_name)
                mof_nodes.append(MOFNode(
                    refcode=record.refcode,
                    display_name=primary_name,
                ))
                seen_mofs.add(record.refcode)

            # Create Stability node (shared by MOFs with same stability)
            stability_key = f"{record.value}"
            if stability_key not in seen_stabilities:
                stability_nodes.append(StabilityNode(
                    value=record.value,
                    evidence=record.summary,
                    condition=record.condition,
                ))
                seen_stabilities.add(stability_key)

            # Create DOI node (shared)
            if record.doi and record.doi not in seen_dois:
                doi_nodes.append(DOINode(doi=record.doi))
                seen_dois.add(record.doi)

            # Create relationship
            mof_id = f"MOF:{record.refcode}"
            stability_id = f"Stability:{record.value}"
            relations.append((
                mof_id,
                stability_id,
                RelationshipType.HAS_STABILITY.value,
                record.summary,  # evidence as relation attribute
            ))

            # DOI relationship
            if record.doi:
                relations.append((
                    mof_id,
                    f"DOI:{record.doi}",
                    RelationshipType.CITED_IN.value,
                    None,
                ))

        return mof_nodes, stability_nodes, doi_nodes, relations