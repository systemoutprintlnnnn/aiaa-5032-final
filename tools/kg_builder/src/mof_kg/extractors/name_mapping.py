"""Name mapping data extractor"""
import csv
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

from mof_kg.models.schema import MOFNode, NameNode, DOINode, RelationshipType


@dataclass
class NameMappingRecord:
    """Raw name mapping record from CSV"""
    mof_names: list[str]  # Split by <|>
    refcode: str
    doi: str | None


class NameMappingExtractor:
    """Extract MOF, Name, and DOI nodes from name mapping CSV"""

    def __init__(self, path: Path):
        self.path = path

    def extract(self) -> Iterator[NameMappingRecord]:
        """Parse CSV and yield raw records"""
        with self.path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mof_name_raw = row.get("MOF Name", "").strip()
                refcode = row.get("Ref Code", "").strip()
                doi = row.get("Reference", "").strip() or None

                if refcode and mof_name_raw:
                    # Split names by <|>
                    names = [n.strip() for n in mof_name_raw.split("<|>") if n.strip()]
                    yield NameMappingRecord(
                        mof_names=names,
                        refcode=refcode,
                        doi=doi,
                    )

    def is_generic_name(self, name: str) -> bool:
        """Check if name is generic (like 'compound 1', 'complex 3')"""
        generic_patterns = ["compound", "complex", "material", "sample"]
        return any(p in name.lower() for p in generic_patterns)

    def select_primary_name(self, names: list[str]) -> str | None:
        """Select the most meaningful name as primary"""
        for name in names:
            if not self.is_generic_name(name) and len(name) > 2:
                return name
        # Fall back to first non-empty name
        for name in names:
            if len(name) > 2:
                return name
        return None

    def extract_nodes_and_relations(self) -> tuple[list[MOFNode], list[NameNode], list[tuple[str, str, str]]]:
        """Extract MOF nodes, Name nodes, and HAS_NAME relationships

        Returns:
            - List of MOF nodes
            - List of Name nodes
            - List of (mof_id, name_id, relation_type) tuples
        """
        mof_nodes: list[MOFNode] = []
        name_nodes: list[NameNode] = []
        relations: list[tuple[str, str, str]] = []

        seen_mofs: set[str] = set()
        seen_names: set[str] = set()

        for record in self.extract():
            primary_name = self.select_primary_name(record.mof_names)

            # Create MOF node
            if record.refcode not in seen_mofs:
                mof_nodes.append(MOFNode(
                    refcode=record.refcode,
                    display_name=primary_name,
                ))
                seen_mofs.add(record.refcode)

            mof_id = f"MOF:{record.refcode}"

            # Create Name nodes and relationships for each name
            for name in record.mof_names:
                if name not in seen_names:
                    is_primary = (name == primary_name)
                    name_nodes.append(NameNode(
                        name=name,
                        is_primary=is_primary,
                    ))
                    seen_names.add(name)

                name_id = f"Name:{name}"
                relations.append((
                    mof_id,
                    name_id,
                    RelationshipType.HAS_NAME.value,
                ))

        return mof_nodes, name_nodes, relations