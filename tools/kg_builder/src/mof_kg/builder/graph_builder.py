"""Graph builder using NetworkX"""
from typing import Optional
import networkx as nx

from mof_kg.config import Config, get_config
from mof_kg.models.schema import (
    MOFNode,
    StabilityNode,
    MethodNode,
    PrecursorNode,
    DOINode,
    NameNode,
    GraphData,
)
from mof_kg.extractors import (
    WaterStabilityExtractor,
    NameMappingExtractor,
    SynthesisExtractor,
)


class GraphBuilder:
    """Build MOF Knowledge Graph with shared nodes"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.graph = nx.DiGraph()
        self.stats = {
            "mof_nodes": 0,
            "stability_nodes": 0,
            "precursor_nodes": 0,
            "method_nodes": 0,
            "doi_nodes": 0,
            "name_nodes": 0,
            "relationships": 0,
        }

    def build(self) -> GraphData:
        """Build the complete knowledge graph

        Returns:
            GraphData containing all nodes and relationships
        """
        data = GraphData()

        # Extract from all three data sources
        self._extract_water_stability(data)
        self._extract_name_mapping(data)
        self._extract_synthesis(data)

        return data

    def _extract_water_stability(self, data: GraphData) -> None:
        """Extract and add water stability data"""
        extractor = WaterStabilityExtractor(self.config.water_stability_path)
        mofs, stabilities, dois, relations = extractor.extract_nodes_and_relations()

        # Add MOF nodes
        for mof in mofs:
            data.add_node(mof.node_id, "MOF", mof.model_dump())
            self.stats["mof_nodes"] += 1

        # Add Stability nodes (shared)
        for stability in stabilities:
            data.add_node(stability.node_id, "Stability", stability.model_dump())
            self.stats["stability_nodes"] += 1

        # Add DOI nodes (shared)
        for doi in dois:
            data.add_node(doi.node_id, "DOI", doi.model_dump())
            self.stats["doi_nodes"] += 1

        # Add relationships
        for from_id, to_id, rel_type, evidence in relations:
            attrs = {"evidence": evidence} if evidence else None
            data.add_relationship(from_id, to_id, rel_type, attrs)
            self.stats["relationships"] += 1

    def _extract_name_mapping(self, data: GraphData) -> None:
        """Extract and add name mapping data"""
        extractor = NameMappingExtractor(self.config.name_mapping_path)
        mofs, names, relations = extractor.extract_nodes_and_relations()

        # Add MOF nodes (skip if already exists)
        for mof in mofs:
            if mof.node_id not in data.nodes:
                data.add_node(mof.node_id, "MOF", mof.model_dump())
                self.stats["mof_nodes"] += 1

        # Add Name nodes
        for name in names:
            data.add_node(name.node_id, "Name", name.model_dump())
            self.stats["name_nodes"] += 1

        # Add relationships
        for from_id, to_id, rel_type in relations:
            data.add_relationship(from_id, to_id, rel_type)
            self.stats["relationships"] += 1

    def _extract_synthesis(self, data: GraphData) -> None:
        """Extract and add synthesis data"""
        extractor = SynthesisExtractor(self.config.synthesis_path)
        mofs, precursors, methods, dois, relations, mof_attrs = extractor.extract_nodes_and_relations()

        # Add MOF nodes (skip if already exists)
        for mof in mofs:
            if mof.node_id not in data.nodes:
                # Add synthesis attributes
                attrs = mof.model_dump()
                refcode = mof.refcode
                if refcode in mof_attrs:
                    attrs.update(mof_attrs[refcode])
                data.add_node(mof.node_id, "MOF", attrs)
                self.stats["mof_nodes"] += 1
            else:
                # Update existing MOF with synthesis attributes
                refcode = mof.refcode
                if refcode in mof_attrs:
                    existing = data.nodes[mof.node_id]
                    existing["attributes"].update(mof_attrs[refcode])

        # Add Precursor nodes (shared)
        for precursor in precursors:
            data.add_node(precursor.node_id, "Precursor", precursor.model_dump())
            self.stats["precursor_nodes"] += 1

        # Add Method nodes (shared)
        for method in methods:
            data.add_node(method.node_id, "Method", method.model_dump())
            self.stats["method_nodes"] += 1

        # Add DOI nodes (shared, skip if already exists)
        for doi in dois:
            if doi.node_id not in data.nodes:
                data.add_node(doi.node_id, "DOI", doi.model_dump())
                self.stats["doi_nodes"] += 1

        # Add relationships
        for from_id, to_id, rel_type in relations:
            data.add_relationship(from_id, to_id, rel_type)
            self.stats["relationships"] += 1

    def get_stats(self) -> dict:
        """Return graph statistics"""
        return self.stats

    def get_networkx_graph(self, data: GraphData) -> nx.DiGraph:
        """Convert GraphData to NetworkX DiGraph"""
        G = nx.DiGraph()

        # Add nodes
        for node_id, node_data in data.nodes.items():
            G.add_node(node_id, **node_data)

        # Add edges
        for rel in data.relationships:
            G.add_edge(
                rel["from"],
                rel["to"],
                type=rel["type"],
                **rel.get("attributes", {}),
            )

        return G

    def find_mofs_using_precursor(self, data: GraphData, precursor_name: str) -> list[str]:
        """Find all MOFs using a specific precursor

        Args:
            data: GraphData object
            precursor_name: Name of the precursor to search for

        Returns:
            List of MOF node IDs
        """
        # Find precursor node(s) matching the name
        precursor_ids = []
        for node_id, node_data in data.nodes.items():
            if node_data["type"] == "Precursor":
                if node_data["attributes"].get("name", "").lower() == precursor_name.lower():
                    precursor_ids.append(node_id)

        # Find MOFs connected to these precursors
        mof_ids = set()
        for rel in data.relationships:
            if rel["to"] in precursor_ids and rel["from"].startswith("MOF:"):
                mof_ids.add(rel["from"])

        return list(mof_ids)

    def find_shared_precursors(self, data: GraphData) -> dict[str, list[str]]:
        """Find precursors shared by multiple MOFs

        Returns:
            Dict mapping precursor_id → list of MOF ids
        """
        precursor_to_mofs: dict[str, list[str]] = {}

        for rel in data.relationships:
            if rel["to"].startswith("Precursor:") and rel["from"].startswith("MOF:"):
                precursor_id = rel["to"]
                mof_id = rel["from"]
                if precursor_id not in precursor_to_mofs:
                    precursor_to_mofs[precursor_id] = []
                precursor_to_mofs[precursor_id].append(mof_id)

        # Filter to only shared precursors (used by > 1 MOF)
        return {k: v for k, v in precursor_to_mofs.items() if len(v) > 1}