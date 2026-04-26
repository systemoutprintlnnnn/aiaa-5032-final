"""Node and relationship schemas for MOF Knowledge Graph"""
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class PrecursorType(str, Enum):
    """Precursor type enumeration"""
    METAL = "metal"
    ORGANIC = "organic"
    SOLVENT = "solvent"


class RelationshipType(str, Enum):
    """Relationship type enumeration"""
    HAS_STABILITY = "HAS_STABILITY"
    USES_METAL_PRECURSOR = "USES_METAL_PRECURSOR"
    USES_ORGANIC_PRECURSOR = "USES_ORGANIC_PRECURSOR"
    USES_SOLVENT = "USES_SOLVENT"
    USES_METHOD = "USES_METHOD"
    HAS_NAME = "HAS_NAME"
    CITED_IN = "CITED_IN"


# Node models
class MOFNode(BaseModel):
    """MOF core node"""
    refcode: str = Field(..., description="CSD reference code")
    display_name: Optional[str] = Field(None, description="Primary display name")
    chemical_name: Optional[str] = Field(None, description="Chemical name")

    @property
    def node_id(self) -> str:
        return f"MOF:{self.refcode}"

    class Config:
        frozen = True


class StabilityNode(BaseModel):
    """Water stability classification node (shared)"""
    value: str = Field(..., description="Stable or Unstable")
    evidence: Optional[str] = Field(None, description="Evidence text")
    condition: Optional[str] = Field(None, description="Experimental condition")

    @property
    def node_id(self) -> str:
        return f"Stability:{self.value}"

    class Config:
        frozen = True


class MethodNode(BaseModel):
    """Synthesis method node (shared)"""
    name: str = Field(..., description="Method name")

    @property
    def node_id(self) -> str:
        return f"Method:{self.name}"

    class Config:
        frozen = True


class PrecursorNode(BaseModel):
    """Precursor node (shared)"""
    name: str = Field(..., description="Precursor name")
    formula: Optional[str] = Field(None, description="Chemical formula")
    smiles: Optional[str] = Field(None, description="SMILES string")
    precursor_type: PrecursorType = Field(..., description="Type: metal/organic/solvent")

    @property
    def node_id(self) -> str:
        return f"Precursor:{self.precursor_type.value}:{self.normalized_name()}"

    def normalized_name(self) -> str:
        """Return normalized name for matching"""
        return self.name.lower().strip()

    class Config:
        frozen = True


class DOINode(BaseModel):
    """DOI reference node (shared)"""
    doi: str = Field(..., description="DOI identifier")

    @property
    def node_id(self) -> str:
        return f"DOI:{self.doi}"

    class Config:
        frozen = True


class NameNode(BaseModel):
    """MOF name/alias node"""
    name: str = Field(..., description="Name or alias")
    is_primary: bool = Field(False, description="Is primary name")

    @property
    def node_id(self) -> str:
        return f"Name:{self.name}"

    class Config:
        frozen = True


# Relationship model
class Relationship(BaseModel):
    """Relationship between two nodes"""
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    relation_type: RelationshipType = Field(..., description="Relationship type")

    @property
    def node_id(self) -> str:
        return f"{self.from_node}->{self.relation_type.value}->{self.to_node}"

    class Config:
        frozen = True


# Graph data structure for export
class GraphData(BaseModel):
    """Complete graph data structure"""
    nodes: dict[str, dict] = Field(default_factory=dict)
    relationships: list[dict] = Field(default_factory=list)

    def add_node(self, node_id: str, node_type: str, attributes: dict) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = {"type": node_type, "attributes": attributes}

    def add_relationship(self, from_node: str, to_node: str, relation_type: RelationshipType | str, attributes: Optional[dict] = None) -> None:
        # Handle both enum and string
        if isinstance(relation_type, str):
            rel_type_str = relation_type
        else:
            rel_type_str = relation_type.value

        rel = {
            "from": from_node,
            "to": to_node,
            "type": rel_type_str,
        }
        if attributes:
            rel["attributes"] = attributes
        self.relationships.append(rel)

    class Config:
        arbitrary_types_allowed = True