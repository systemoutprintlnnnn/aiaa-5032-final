from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    refcode: str | None
    material_names: tuple[str, ...]
    relation: str
    source: str
    doi: str | None
    license: str | None
    fact_id: str


@dataclass(frozen=True)
class Fact:
    id: str
    refcode: str | None
    material_names: tuple[str, ...]
    relation: str
    value: str
    evidence: str
    doi: str | None
    data_source: str
    path: str
    search_text: str
