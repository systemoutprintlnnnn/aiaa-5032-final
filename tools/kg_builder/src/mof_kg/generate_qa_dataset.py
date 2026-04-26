"""Generate evaluation QA pairs from MOF Knowledge Graph (English version)"""
import json
import random
from pathlib import Path
from typing import Any
from collections import defaultdict

from mof_kg.config import get_config
from mof_kg.builder import GraphBuilder


class QADatasetGenerator:
    """Generate QA pairs from Knowledge Graph"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("Loading Knowledge Graph...")
        config = get_config()
        self.builder = GraphBuilder(config)
        self.data = self.builder.build()
        self.stats = self.builder.get_stats()

        self._build_indices()

        print(f"KG loaded: {len(self.data.nodes)} nodes, {len(self.data.relationships)} edges")

    def _build_indices(self):
        """Build indices for efficient querying"""
        self.mofs = {}
        self.mof_names = {}
        self.mof_to_precursors = defaultdict(list)
        self.mof_to_method = {}
        self.mof_to_doi = {}
        self.mof_to_stability = {}

        self.precursors = {}
        self.precursor_to_mofs = defaultdict(list)

        self.methods = {}
        self.method_to_mofs = defaultdict(list)

        self.dois = {}
        self.doi_to_mofs = defaultdict(list)

        self.stability_mofs = {"Stable": [], "Unstable": []}
        self.mof_to_names = defaultdict(list)

        for node_id, node_data in self.data.nodes.items():
            node_type = node_data["type"]
            attrs = node_data["attributes"]

            if node_type == "MOF":
                self.mofs[node_id] = node_data
                display_name = attrs.get("display_name")
                if display_name:
                    self.mof_names[display_name.lower()] = node_id
                refcode = attrs.get("refcode")
                if refcode:
                    self.mof_names[refcode.lower()] = node_id

            elif node_type == "Precursor":
                self.precursors[node_id] = node_data

            elif node_type == "Method":
                self.methods[node_id] = node_data

            elif node_type == "DOI":
                self.dois[node_id] = node_data

        for rel in self.data.relationships:
            from_node = rel["from"]
            to_node = rel["to"]
            rel_type = rel["type"]

            if rel_type == "USES_METAL_PRECURSOR":
                self.precursor_to_mofs[to_node].append(from_node)
                self.mof_to_precursors[from_node].append((to_node, "metal"))
            elif rel_type == "USES_ORGANIC_PRECURSOR":
                self.precursor_to_mofs[to_node].append(from_node)
                self.mof_to_precursors[from_node].append((to_node, "organic"))
            elif rel_type == "USES_SOLVENT":
                self.precursor_to_mofs[to_node].append(from_node)
                self.mof_to_precursors[from_node].append((to_node, "solvent"))
            elif rel_type == "USES_METHOD":
                self.method_to_mofs[to_node].append(from_node)
                self.mof_to_method[from_node] = to_node
            elif rel_type == "CITED_IN":
                self.doi_to_mofs[to_node].append(from_node)
                self.mof_to_doi[from_node] = to_node
            elif rel_type == "HAS_STABILITY":
                if "Stable" in to_node:
                    self.stability_mofs["Stable"].append(from_node)
                    self.mof_to_stability[from_node] = "Stable"
                elif "Unstable" in to_node:
                    self.stability_mofs["Unstable"].append(from_node)
                    self.mof_to_stability[from_node] = "Unstable"
            elif rel_type == "HAS_NAME":
                name_data = self.data.nodes.get(to_node, {})
                name = name_data.get("attributes", {}).get("name", "")
                if name:
                    self.mof_to_names[from_node].append(name)

    def _get_mof_name(self, mof_id: str) -> str:
        mof_data = self.mofs.get(mof_id, {})
        attrs = mof_data.get("attributes", {})
        return attrs.get("display_name") or attrs.get("refcode", mof_id)

    def generate_type_a(self, count: int = 100) -> list[dict]:
        """Type A: Simple Retrieval - Single MOF property queries"""
        qa_pairs = []

        mof_list = list(self.mofs.keys())
        random.shuffle(mof_list)

        generated = 0
        for mof_id in mof_list:
            if generated >= count:
                break

            mof_name = self._get_mof_name(mof_id)

            # Stability
            if mof_id in self.mof_to_stability:
                stability = self.mof_to_stability[mof_id]
                qa_pairs.append({
                    "id": f"A-{generated+1:04d}",
                    "type": "simple_retrieval",
                    "question": f"What is the water stability of {mof_name}?",
                    "answer": f"The water stability of {mof_name} is {stability}.",
                    "evidence": f"Stability: {stability}",
                    "mof_id": mof_id,
                    "mof_name": mof_name,
                })
                generated += 1

            if generated >= count:
                break

            # Method
            if mof_id in self.mof_to_method:
                method_id = self.mof_to_method[mof_id]
                method_data = self.methods.get(method_id, {})
                method_name = method_data.get("attributes", {}).get("name", "Unknown")
                qa_pairs.append({
                    "id": f"A-{generated+1:04d}",
                    "type": "simple_retrieval",
                    "question": f"What is the synthesis method of {mof_name}?",
                    "answer": f"{mof_name} is synthesized using the {method_name} method.",
                    "evidence": f"Synthesis method: {method_name}",
                    "mof_id": mof_id,
                    "mof_name": mof_name,
                })
                generated += 1

            if generated >= count:
                break

            # Metal precursor
            precursors = self.mof_to_precursors.get(mof_id, [])
            metal_precursors = [p for p, t in precursors if t == "metal"]
            if metal_precursors:
                precursor_id = metal_precursors[0]
                precursor_data = self.precursors.get(precursor_id, {})
                precursor_name = precursor_data.get("attributes", {}).get("name", "Unknown")
                qa_pairs.append({
                    "id": f"A-{generated+1:04d}",
                    "type": "simple_retrieval",
                    "question": f"What metal precursor is used in {mof_name}?",
                    "answer": f"{mof_name} uses {precursor_name} as the metal precursor.",
                    "evidence": f"Metal precursor: {precursor_name}",
                    "mof_id": mof_id,
                    "mof_name": mof_name,
                })
                generated += 1

            if generated >= count:
                break

            # Solvent
            solvent_precursors = [p for p, t in precursors if t == "solvent"]
            if solvent_precursors:
                precursor_id = solvent_precursors[0]
                precursor_data = self.precursors.get(precursor_id, {})
                precursor_name = precursor_data.get("attributes", {}).get("name", "Unknown")
                qa_pairs.append({
                    "id": f"A-{generated+1:04d}",
                    "type": "simple_retrieval",
                    "question": f"What solvent is used in the synthesis of {mof_name}?",
                    "answer": f"{mof_name} uses {precursor_name} as the solvent.",
                    "evidence": f"Solvent: {precursor_name}",
                    "mof_id": mof_id,
                    "mof_name": mof_name,
                })
                generated += 1

        print(f"Generated {len(qa_pairs)} Type A (Simple Retrieval) QA pairs")
        return qa_pairs[:count]

    def generate_type_b(self, count: int = 100) -> list[dict]:
        """Type B: Entity Linking - Alias/synonym queries"""
        qa_pairs = []

        mofs_with_aliases = [(mof_id, names) for mof_id, names in self.mof_to_names.items() if len(names) >= 2]
        random.shuffle(mofs_with_aliases)

        generated = 0
        for mof_id, names in mofs_with_aliases:
            if generated >= count:
                break

            mof_data = self.mofs.get(mof_id, {})
            attrs = mof_data.get("attributes", {})
            refcode = attrs.get("refcode", "")
            names_list = list(names)

            if len(names_list) < 2:
                continue

            # Q: CSD code
            if refcode:
                qa_pairs.append({
                    "id": f"B-{generated+1:04d}",
                    "type": "entity_linking",
                    "question": f"What is the CSD code of {names_list[0]}?",
                    "answer": refcode,
                    "evidence": f"CSD Refcode: {refcode}",
                    "mof_id": mof_id,
                    "mof_name": names_list[0],
                    "refcode": refcode,
                    "aliases": names_list,
                })
                generated += 1

            if generated >= count:
                break

            # Q: Same MOF?
            if len(names_list) >= 2:
                qa_pairs.append({
                    "id": f"B-{generated+1:04d}",
                    "type": "entity_linking",
                    "question": f"Are {names_list[0]} and {names_list[1]} the same MOF?",
                    "answer": f"Yes, they are the same MOF with CSD code {refcode}.",
                    "evidence": f"Both names correspond to CSD code: {refcode}",
                    "mof_id": mof_id,
                    "mof_name": names_list[0],
                    "refcode": refcode,
                    "aliases": names_list,
                })
                generated += 1

            if generated >= count:
                break

            # Q: Aliases
            qa_pairs.append({
                "id": f"B-{generated+1:04d}",
                "type": "entity_linking",
                "question": f"What are the other names or aliases of {names_list[0]}?",
                "answer": ", ".join(names_list[1:]) if len(names_list) > 1 else "No other aliases",
                "evidence": f"All aliases: {', '.join(names_list)}",
                "mof_id": mof_id,
                "mof_name": names_list[0],
                "refcode": refcode,
                "aliases": names_list,
            })
            generated += 1

        print(f"Generated {len(qa_pairs)} Type B (Entity Linking) QA pairs")
        return qa_pairs[:count]

    def generate_type_c(self, count: int = 100) -> list[dict]:
        """Type C: Cross-Entity Query - Cross-MOF association queries"""
        qa_pairs = []

        generated = 0

        # Pattern 1: Same precursor
        for precursor_id, mof_ids in list(self.precursor_to_mofs.items())[:500]:
            if generated >= count:
                break

            if len(mof_ids) < 2:
                continue

            precursor_data = self.precursors.get(precursor_id, {})
            precursor_attrs = precursor_data.get("attributes", {})
            precursor_name = precursor_attrs.get("name", "")
            precursor_type = precursor_attrs.get("precursor_type", "")

            if not precursor_name:
                continue

            first_mof_name = self._get_mof_name(mof_ids[0])
            other_mofs = [self._get_mof_name(m) for m in mof_ids[1:6]]

            if precursor_type == "metal":
                question = f"What other MOFs use the same metal precursor as {first_mof_name}?"
                answer = f"MOFs using the same metal precursor ({precursor_name}): {', '.join(other_mofs)}"
            elif precursor_type == "organic":
                question = f"What other MOFs use the same organic precursor as {first_mof_name}?"
                answer = f"MOFs using the same organic precursor ({precursor_name}): {', '.join(other_mofs)}"
            elif precursor_type == "solvent":
                question = f"What other MOFs use the same solvent as {first_mof_name}?"
                answer = f"MOFs using the same solvent ({precursor_name}): {', '.join(other_mofs)}"
            else:
                continue

            qa_pairs.append({
                "id": f"C-{generated+1:04d}",
                "type": "cross_entity_query",
                "question": question,
                "answer": answer,
                "evidence": f"Shared {precursor_type} precursor: {precursor_name}",
                "mof_id": mof_ids[0],
                "mof_name": first_mof_name,
                "related_mofs": other_mofs,
                "shared_resource": precursor_name,
                "resource_type": precursor_type,
            })
            generated += 1

        # Pattern 2: Same method
        for method_id, mof_ids in list(self.method_to_mofs.items())[:200]:
            if generated >= count:
                break

            if len(mof_ids) < 2:
                continue

            method_data = self.methods.get(method_id, {})
            method_name = method_data.get("attributes", {}).get("name", "")

            if not method_name or method_name == "Unknown":
                continue

            first_mof_name = self._get_mof_name(mof_ids[0])
            other_mofs = [self._get_mof_name(m) for m in mof_ids[1:6]]

            question = f"What other MOFs use the same synthesis method as {first_mof_name}?"
            answer = f"MOFs using the same synthesis method ({method_name}): {', '.join(other_mofs)}"

            qa_pairs.append({
                "id": f"C-{generated+1:04d}",
                "type": "cross_entity_query",
                "question": question,
                "answer": answer,
                "evidence": f"Shared method: {method_name}",
                "mof_id": mof_ids[0],
                "mof_name": first_mof_name,
                "related_mofs": other_mofs,
                "shared_resource": method_name,
                "resource_type": "method",
            })
            generated += 1

        # Pattern 3: Same DOI
        for doi_id, mof_ids in list(self.doi_to_mofs.items())[:200]:
            if generated >= count:
                break

            if len(mof_ids) < 2:
                continue

            doi_data = self.dois.get(doi_id, {})
            doi = doi_data.get("attributes", {}).get("doi", "")

            first_mof_name = self._get_mof_name(mof_ids[0])
            other_mofs = [self._get_mof_name(m) for m in mof_ids[1:6]]

            question = f"What other MOFs are from the same paper as {first_mof_name}?"
            answer = f"MOFs from the same paper (DOI: {doi}): {', '.join(other_mofs)}"

            qa_pairs.append({
                "id": f"C-{generated+1:04d}",
                "type": "cross_entity_query",
                "question": question,
                "answer": answer,
                "evidence": f"Shared DOI: {doi}",
                "mof_id": mof_ids[0],
                "mof_name": first_mof_name,
                "related_mofs": other_mofs,
                "shared_resource": doi,
                "resource_type": "doi",
            })
            generated += 1

        print(f"Generated {len(qa_pairs)} Type C (Cross-Entity Query) QA pairs")
        return qa_pairs[:count]

    def generate_type_d(self, count: int = 100) -> list[dict]:
        """Type D: Multi-hop Reasoning - Multi-step reasoning queries"""
        qa_pairs = []

        generated = 0

        # Pattern 1: MOF -> Precursor -> other MOFs with stability
        for precursor_id, mof_ids in self.precursor_to_mofs.items():
            if generated >= count:
                break

            if len(mof_ids) < 3:
                continue

            precursor_data = self.precursors.get(precursor_id, {})
            precursor_attrs = precursor_data.get("attributes", {})
            precursor_name = precursor_attrs.get("name", "")
            precursor_type = precursor_attrs.get("precursor_type", "")

            if precursor_type != "metal" or not precursor_name:
                continue

            stable_mofs = []
            unstable_mofs = []
            for mof_id in mof_ids:
                mof_name = self._get_mof_name(mof_id)
                if mof_id in self.mof_to_stability:
                    if self.mof_to_stability[mof_id] == "Stable":
                        stable_mofs.append(mof_name)
                    else:
                        unstable_mofs.append(mof_name)

            if len(stable_mofs) >= 1 and len(unstable_mofs) >= 1:
                first_mof_name = stable_mofs[0] if stable_mofs else self._get_mof_name(mof_ids[0])
                other_stable = stable_mofs[1:4] if len(stable_mofs) > 1 else []

                if other_stable:
                    question = f"What other water-stable MOFs use the same metal precursor as {first_mof_name}?"
                    answer = f"The metal precursor {precursor_name} is also used by: {', '.join(other_stable)}"

                    qa_pairs.append({
                        "id": f"D-{generated+1:04d}",
                        "type": "multi_hop_reasoning",
                        "question": question,
                        "answer": answer,
                        "evidence": f"Precursor: {precursor_name}, Stability: Stable",
                        "mof_name": first_mof_name,
                        "precursor": precursor_name,
                        "stable_related_mofs": other_stable,
                        "hop_type": "MOF->Precursor->MOF->Stability",
                    })
                    generated += 1

        # Pattern 2: Method -> MOFs -> stability distribution
        for method_id, mof_ids in self.method_to_mofs.items():
            if generated >= count:
                break

            if len(mof_ids) < 3:
                continue

            method_data = self.methods.get(method_id, {})
            method_name = method_data.get("attributes", {}).get("name", "")

            if not method_name or method_name == "Unknown":
                continue

            stable_count = sum(1 for m in mof_ids if m in self.mof_to_stability and self.mof_to_stability[m] == "Stable")
            unstable_count = sum(1 for m in mof_ids if m in self.mof_to_stability and self.mof_to_stability[m] == "Unstable")

            if stable_count > 0 and unstable_count > 0:
                question = f"What is the water stability distribution for MOFs synthesized using the {method_name} method?"
                answer = f"Among MOFs synthesized using {method_name}: {stable_count} are water-stable, {unstable_count} are water-unstable."

                qa_pairs.append({
                    "id": f"D-{generated+1:04d}",
                    "type": "multi_hop_reasoning",
                    "question": question,
                    "answer": answer,
                    "evidence": f"Method: {method_name}, Stable: {stable_count}, Unstable: {unstable_count}",
                    "method": method_name,
                    "stable_count": stable_count,
                    "unstable_count": unstable_count,
                    "hop_type": "Method->MOF->Stability",
                })
                generated += 1

        # Pattern 3: DOI -> MOFs -> common precursor
        for doi_id, mof_ids in self.doi_to_mofs.items():
            if generated >= count:
                break

            if len(mof_ids) < 2:
                continue

            precursor_counts = defaultdict(int)
            for mof_id in mof_ids:
                for precursor_id, _ in self.mof_to_precursors.get(mof_id, []):
                    precursor_counts[precursor_id] += 1

            common_precursors = [(pid, cnt) for pid, cnt in precursor_counts.items() if cnt >= 2]
            if common_precursors:
                precursor_id, cnt = common_precursors[0]
                precursor_name = self.precursors.get(precursor_id, {}).get("attributes", {}).get("name", "")

                mof_names = [self._get_mof_name(m) for m in mof_ids[:3]]

                question = f"What do {mof_names[0]} and {mof_names[1]} (from the same paper) have in common?"
                answer = f"They both use {precursor_name} as a precursor."

                qa_pairs.append({
                    "id": f"D-{generated+1:04d}",
                    "type": "multi_hop_reasoning",
                    "question": question,
                    "answer": answer,
                    "evidence": f"Common precursor: {precursor_name}",
                    "mof_names": mof_names,
                    "common_precursor": precursor_name,
                    "hop_type": "DOI->MOF->Precursor",
                })
                generated += 1

        print(f"Generated {len(qa_pairs)} Type D (Multi-hop Reasoning) QA pairs")
        return qa_pairs[:count]

    def generate_type_e(self, count: int = 100) -> list[dict]:
        """Type E: Filtering Query - Multi-condition filtering queries"""
        qa_pairs = []

        generated = 0

        # Pattern 1: Precursor + Stability filter
        for precursor_id, mof_ids in self.precursor_to_mofs.items():
            if generated >= count:
                break

            if len(mof_ids) < 2:
                continue

            precursor_data = self.precursors.get(precursor_id, {})
            precursor_attrs = precursor_data.get("attributes", {})
            precursor_name = precursor_attrs.get("name", "")
            precursor_type = precursor_attrs.get("precursor_type", "")

            if not precursor_name:
                continue

            stable_mofs = []
            unstable_mofs = []
            for mof_id in mof_ids:
                mof_name = self._get_mof_name(mof_id)
                if mof_id in self.mof_to_stability:
                    if self.mof_to_stability[mof_id] == "Stable":
                        stable_mofs.append(mof_name)
                    else:
                        unstable_mofs.append(mof_name)

            if stable_mofs:
                metal_name = precursor_name.split("(")[0] if "(" in precursor_name else precursor_name

                question = f"What MOFs use {metal_name} precursor and are water-stable?"
                answer = f"Water-stable MOFs using {metal_name} precursor: {', '.join(stable_mofs[:5])}"

                qa_pairs.append({
                    "id": f"E-{generated+1:04d}",
                    "type": "filtering_query",
                    "question": question,
                    "answer": answer,
                    "evidence": f"Precursor: {precursor_name}, Stability: Stable",
                    "filters": ["precursor", "stability"],
                    "precursor": precursor_name,
                    "stability_filter": "Stable",
                    "result_count": len(stable_mofs),
                })
                generated += 1

            if generated >= count:
                break

            if unstable_mofs:
                metal_name = precursor_name.split("(")[0] if "(" in precursor_name else precursor_name

                question = f"What MOFs use {metal_name} precursor and are water-unstable?"
                answer = f"Water-unstable MOFs using {metal_name} precursor: {', '.join(unstable_mofs[:5])}"

                qa_pairs.append({
                    "id": f"E-{generated+1:04d}",
                    "type": "filtering_query",
                    "question": question,
                    "answer": answer,
                    "evidence": f"Precursor: {precursor_name}, Stability: Unstable",
                    "filters": ["precursor", "stability"],
                    "precursor": precursor_name,
                    "stability_filter": "Unstable",
                    "result_count": len(unstable_mofs),
                })
                generated += 1

        # Pattern 2: Method + Stability filter
        for method_id, mof_ids in self.method_to_mofs.items():
            if generated >= count:
                break

            if len(mof_ids) < 3:
                continue

            method_data = self.methods.get(method_id, {})
            method_name = method_data.get("attributes", {}).get("name", "")

            if not method_name or method_name == "Unknown":
                continue

            stable_mofs = []
            for mof_id in mof_ids:
                if mof_id in self.mof_to_stability and self.mof_to_stability[mof_id] == "Stable":
                    stable_mofs.append(self._get_mof_name(mof_id))

            if len(stable_mofs) >= 2:
                question = f"What MOFs synthesized using {method_name} method are water-stable?"
                answer = f"Water-stable MOFs using {method_name}: {', '.join(stable_mofs[:5])}"

                qa_pairs.append({
                    "id": f"E-{generated+1:04d}",
                    "type": "filtering_query",
                    "question": question,
                    "answer": answer,
                    "evidence": f"Method: {method_name}, Stability: Stable",
                    "filters": ["method", "stability"],
                    "method": method_name,
                    "stability_filter": "Stable",
                    "result_count": len(stable_mofs),
                })
                generated += 1

        print(f"Generated {len(qa_pairs)} Type E (Filtering Query) QA pairs")
        return qa_pairs[:count]

    def generate_all(self, count_per_type: int = 100) -> dict[str, list[dict]]:
        """Generate all QA pairs"""
        print("\n=== Generating QA Pairs ===\n")

        all_qa = {
            "type_a_simple_retrieval": self.generate_type_a(count_per_type),
            "type_b_entity_linking": self.generate_type_b(count_per_type),
            "type_c_cross_entity": self.generate_type_c(count_per_type),
            "type_d_multi_hop": self.generate_type_d(count_per_type),
            "type_e_filtering": self.generate_type_e(count_per_type),
        }

        return all_qa

    def save(self, qa_pairs: dict[str, list[dict]], filename: str = "qa_evaluation_dataset_en.json"):
        """Save QA pairs to JSON file"""
        output_path = self.output_dir / filename

        output = {
            "metadata": {
                "total_qa_pairs": sum(len(pairs) for pairs in qa_pairs.values()),
                "language": "English",
                "types": {
                    "type_a_simple_retrieval": {"count": len(qa_pairs["type_a_simple_retrieval"]), "description": "Single MOF property queries"},
                    "type_b_entity_linking": {"count": len(qa_pairs["type_b_entity_linking"]), "description": "Alias/synonym queries"},
                    "type_c_cross_entity": {"count": len(qa_pairs["type_c_cross_entity"]), "description": "Cross-MOF association queries"},
                    "type_d_multi_hop": {"count": len(qa_pairs["type_d_multi_hop"]), "description": "Multi-hop reasoning queries"},
                    "type_e_filtering": {"count": len(qa_pairs["type_e_filtering"]), "description": "Multi-condition filtering queries"},
                },
            },
            "qa_pairs": qa_pairs,
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\nSaved {output['metadata']['total_qa_pairs']} QA pairs to {output_path}")
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate QA evaluation dataset from MOF KG")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of QA pairs per type (default: 100)")
    parser.add_argument("--output", "-o", type=str, default="qa_evaluation_dataset_en.json", help="Output filename")

    args = parser.parse_args()

    config = get_config()
    generator = QADatasetGenerator(config.dataset_output_dir)
    qa_pairs = generator.generate_all(count_per_type=args.count)
    generator.save(qa_pairs, filename=args.output)


if __name__ == "__main__":
    main()
