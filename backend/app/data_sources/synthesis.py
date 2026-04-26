from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SynthesisEvidenceRecord:
    row_index: int
    refcode: str
    names: tuple[str, ...]
    value: str
    evidence: str
    doi: str | None
    source: str | None


def load_synthesis_evidence_records(path: Path) -> list[SynthesisEvidenceRecord]:
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []

    records: list[SynthesisEvidenceRecord] = []
    for idx, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        record = _row_to_record(idx, row)
        if record is not None:
            records.append(record)
    return records


def _row_to_record(idx: int, row: dict[str, Any]) -> SynthesisEvidenceRecord | None:
    refcode = _clean_text(row.get("identifier")).upper()
    if not refcode:
        return None

    material_name = _clean_text(row.get("name"))
    csd_name = _clean_text(row.get("csd_chemical_name"))
    names = tuple(dict.fromkeys(name for name in [material_name, csd_name] if name))

    method = _clean_text(row.get("method"))
    metal = _format_precursors(row.get("M_precursor"))
    organic = _format_precursors(row.get("O_precursor"))
    solvent = _format_precursors(row.get("S_precursor"))
    temperature = _clean_text(row.get("temperature"))
    reaction_time = _clean_text(row.get("time"))
    operation = _format_operations(row.get("operation"))
    yield_value = _clean_text(row.get("Yield"))
    doi = _clean_text(row.get("doi")) or None
    source = _clean_text(row.get("source")) or None

    value_parts = []
    for label, value in [
        ("method", method),
        ("metal precursor", metal),
        ("organic precursor/linker", organic),
        ("solvent", solvent),
        ("temperature", temperature),
        ("reaction time", reaction_time),
        ("yield", yield_value),
    ]:
        if value:
            value_parts.append(f"{label}: {value}")

    evidence_parts = [f"Synthesis record for {refcode}."]
    if material_name:
        evidence_parts.append(f"Material name: {material_name}.")
    for label, value in [
        ("Method", method),
        ("Metal precursor", metal),
        ("Organic precursor/linker", organic),
        ("Solvent", solvent),
        ("Temperature", temperature),
        ("Reaction time", reaction_time),
        ("Operation", operation),
        ("Yield", yield_value),
        ("DOI", doi or ""),
        ("Source", source or ""),
    ]:
        if value:
            evidence_parts.append(f"{label}: {value}.")

    value = "; ".join(value_parts)
    evidence = " ".join(evidence_parts)
    if not value and evidence == f"Synthesis record for {refcode}.":
        return None

    return SynthesisEvidenceRecord(
        row_index=idx,
        refcode=refcode,
        names=names,
        value=value or "Synthesis evidence available",
        evidence=evidence,
        doi=doi,
        source=source,
    )


def _format_precursors(value: Any) -> str:
    if not isinstance(value, list):
        return ""

    parts: list[str] = []
    for item in value:
        if isinstance(item, dict):
            name = _clean_text(item.get("name"))
            details = []
            for key in ["composition", "formula", "smiles"]:
                detail = _clean_text(item.get(key))
                if detail:
                    details.append(f"{key}: {detail}")
            if name and details:
                parts.append(f"{name} ({'; '.join(details)})")
            elif name:
                parts.append(name)
            elif details:
                parts.append("; ".join(details))
        else:
            text = _clean_text(item)
            if text:
                parts.append(text)
    return "; ".join(parts)


def _format_operations(value: Any) -> str:
    if not isinstance(value, list):
        return ""

    parts: list[str] = []
    for item in value:
        if isinstance(item, dict):
            name = _clean_text(item.get("name")) or "operation"
            temperature = _clean_text(item.get("Temperature") or item.get("temperature"))
            time = _clean_text(item.get("Time") or item.get("time"))
            text = name
            if temperature:
                text += f" at {temperature}"
            if time:
                text += f" for {time}"
            parts.append(text)
        else:
            text = _clean_text(item)
            if text:
                parts.append(text)
    return "; ".join(parts)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()
