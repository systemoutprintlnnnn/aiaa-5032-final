"""CLI tool for MOF Knowledge Graph Builder"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from mof_kg.config import get_config
from mof_kg.builder import GraphBuilder, JSONExporter, CypherExporter, GraphMLExporter


def cmd_build(args):
    """Build the knowledge graph"""
    print("Building MOF Knowledge Graph...")

    config = get_config()
    builder = GraphBuilder(config)

    # Build the graph
    data = builder.build()

    # Print statistics
    stats = builder.get_stats()
    print("\n=== Graph Statistics ===")
    for key, value in stats.items():
        print(f"  {key}: {value:,}")

    # Show shared precursor statistics
    shared = builder.find_shared_precursors(data)
    print(f"\nShared precursors: {len(shared)}")
    if shared:
        top_shared = sorted(shared.items(), key=lambda x: -len(x[1]))[:5]
        print("Top 5 most shared precursors:")
        for precursor_id, mofs in top_shared:
            # Safely get precursor name
            node_data = data.nodes.get(precursor_id)
            precursor_name = node_data["attributes"].get("name", "unknown") if node_data else precursor_id
            print(f"  {precursor_name}: used by {len(mofs)} MOFs")

    return data, stats


def cmd_export(args):
    """Export the knowledge graph"""
    # Build first
    config = get_config()
    builder = GraphBuilder(config)
    data = builder.build()

    config.kg_output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []

    if args.format in ["json", "all"]:
        json_path = config.kg_output_dir / "mof_kg.json"
        exporter = JSONExporter(json_path)
        exporter.export(data)
        print(f"Exported JSON to: {json_path}")
        exported_files.append(json_path)

    if args.format in ["cypher", "all"]:
        cypher_path = config.kg_output_dir / "mof_kg.cypher"
        exporter = CypherExporter(cypher_path)
        exporter.export(data)
        print(f"Exported Cypher to: {cypher_path}")
        exported_files.append(cypher_path)

    if args.format in ["graphml", "all"]:
        graphml_path = config.kg_output_dir / "mof_kg.graphml"
        exporter = GraphMLExporter(graphml_path)
        exporter.export(data)
        print(f"Exported GraphML to: {graphml_path}")
        exported_files.append(graphml_path)

    # Also export statistics
    _export_statistics(config, builder, data)

    return exported_files


def _export_statistics(config, builder, data):
    """Export KG statistics to JSON file"""
    stats = builder.get_stats()
    shared_precursors = builder.find_shared_precursors(data)

    # Count precursors by type
    precursor_types = {"metal": 0, "organic": 0, "solvent": 0}
    for node_id, node_data in data.nodes.items():
        if node_data["type"] == "Precursor":
            ptype = node_data["attributes"].get("precursor_type", "unknown")
            if ptype in precursor_types:
                precursor_types[ptype] += 1

    # Top shared precursors
    top_shared = sorted(shared_precursors.items(), key=lambda x: -len(x[1]))[:20]
    top_shared_info = []
    for precursor_id, mofs in top_shared:
        node_data = data.nodes.get(precursor_id)
        precursor_name = node_data["attributes"].get("name", "unknown") if node_data else precursor_id
        top_shared_info.append({
            "name": precursor_name,
            "node_id": precursor_id,
            "mof_count": len(mofs),
        })

    # Stability distribution
    stability_dist = {"Stable": 0, "Unstable": 0}
    for rel in data.relationships:
        if rel["type"] == "HAS_STABILITY":
            if "Stable" in rel["to"]:
                stability_dist["Stable"] += 1
            elif "Unstable" in rel["to"]:
                stability_dist["Unstable"] += 1

    # Build statistics object
    statistics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_sources": [
                "1.water_stability_chemunity_v0.1.0.csv",
                "2.MOF_names_and_CSD_codes.csv",
                "3.MOF-Synthesis.json",
            ],
        },
        "node_statistics": {
            "total_nodes": sum(v for k, v in stats.items() if k.endswith('_nodes')),
            "by_type": {
                "mof": stats['mof_nodes'],
                "stability": stats['stability_nodes'],
                "precursor": stats['precursor_nodes'],
                "method": stats['method_nodes'],
                "doi": stats['doi_nodes'],
                "name": stats['name_nodes'],
            },
            "precursor_breakdown": precursor_types,
        },
        "relationship_statistics": {
            "total_relationships": stats['relationships'],
        },
        "shared_node_statistics": {
            "shared_precursors_count": len(shared_precursors),
            "top_20_shared_precursors": top_shared_info,
        },
        "stability_distribution": stability_dist,
    }

    # Write to file (dataset directory)
    output_path = config.dataset_output_dir / "kg_statistics.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(statistics, f, ensure_ascii=False, indent=2)

    print(f"Exported statistics to: {output_path}")
    return statistics


def cmd_stats(args):
    """Show graph statistics"""
    config = get_config()
    builder = GraphBuilder(config)
    data = builder.build()

    stats = builder.get_stats()

    print("\n=== MOF Knowledge Graph Statistics ===\n")
    print("Node counts:")
    print(f"  MOF nodes:        {stats['mof_nodes']:,}")
    print(f"  Stability nodes:  {stats['stability_nodes']:,}")
    print(f"  Precursor nodes:  {stats['precursor_nodes']:,}")
    print(f"  Method nodes:     {stats['method_nodes']:,}")
    print(f"  DOI nodes:        {stats['doi_nodes']:,}")
    print(f"  Name nodes:       {stats['name_nodes']:,}")
    print(f"\nTotal nodes:       {sum(v for k, v in stats.items() if k.endswith('_nodes')):,}")
    print(f"Total relationships: {stats['relationships']:,}")

    # Shared nodes analysis
    print("\n=== Shared Nodes Analysis ===")
    shared_precursors = builder.find_shared_precursors(data)
    print(f"Shared precursors: {len(shared_precursors)}")

    # Count MOFs per precursor type
    precursor_types = {"metal": 0, "organic": 0, "solvent": 0}
    for node_id, node_data in data.nodes.items():
        if node_data["type"] == "Precursor":
            ptype = node_data["attributes"].get("precursor_type", "unknown")
            if ptype in precursor_types:
                precursor_types[ptype] += 1

    print("\nPrecursor breakdown:")
    for ptype, count in precursor_types.items():
        print(f"  {ptype}: {count:,}")

    # Show top 10 shared precursors
    print("\n=== Top 10 Shared Precursors ===")
    top_shared = sorted(shared_precursors.items(), key=lambda x: -len(x[1]))[:10]
    for precursor_id, mofs in top_shared:
        node_data = data.nodes.get(precursor_id)
        precursor_name = node_data["attributes"].get("name", "unknown") if node_data else precursor_id
        print(f"  {precursor_name}: used by {len(mofs)} MOFs")


def cmd_stats_export(args):
    """Export statistics to JSON file"""
    config = get_config()
    builder = GraphBuilder(config)
    data = builder.build()

    statistics = _export_statistics(config, builder, data)

    print("\n=== Exported Statistics Summary ===")
    print(f"Total nodes: {statistics['node_statistics']['total_nodes']:,}")
    print(f"Total relationships: {statistics['relationship_statistics']['total_relationships']:,}")
    print(f"Shared precursors: {statistics['shared_node_statistics']['shared_precursors_count']:,}")


def cmd_query(args):
    """Query the knowledge graph"""
    config = get_config()
    builder = GraphBuilder(config)
    data = builder.build()

    if args.precursor:
        # Find MOFs using a specific precursor
        mofs = builder.find_mofs_using_precursor(data, args.precursor)
        print(f"\nMOFs using '{args.precursor}': {len(mofs)}")
        for mof_id in mofs[:20]:  # Show first 20
            mof_data = data.nodes.get(mof_id, {})
            name = mof_data.get("attributes", {}).get("display_name", "unknown")
            print(f"  {mof_id}: {name}")
        if len(mofs) > 20:
            print(f"  ... and {len(mofs) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        description="MOF Knowledge Graph Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # build command
    parser_build = subparsers.add_parser("build", help="Build the knowledge graph")

    # export command
    parser_export = subparsers.add_parser("export", help="Export the knowledge graph")
    parser_export.add_argument(
        "--format", "-f",
        choices=["json", "cypher", "graphml", "all"],
        default="all",
        help="Export format (default: all)",
    )

    # stats command
    parser_stats = subparsers.add_parser("stats", help="Show graph statistics")

    # stats-export command
    parser_stats_export = subparsers.add_parser("stats-export", help="Export statistics to JSON file")

    # query command
    parser_query = subparsers.add_parser("query", help="Query the knowledge graph")
    parser_query.add_argument(
        "--precursor", "-p",
        help="Find MOFs using this precursor",
    )

    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "stats-export":
        cmd_stats_export(args)
    elif args.command == "query":
        cmd_query(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()