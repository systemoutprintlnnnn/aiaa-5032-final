import json

from app.retrievers.graph import KGGraphRetriever, NoResultGraphRetriever


def write_graph(path):
    graph = {
        "nodes": {
            "MOF:UNABAN": {
                "type": "MOF",
                "attributes": {"refcode": "UNABAN", "display_name": "Zn(LTP)2"},
            },
            "MOF:OTHER1": {
                "type": "MOF",
                "attributes": {"refcode": "OTHER1", "display_name": "Other MOF"},
            },
            "Stability:Stable": {
                "type": "Stability",
                "attributes": {"value": "Stable", "evidence": "Stable in water."},
            },
            "Name:Zn(LTP)2": {
                "type": "Name",
                "attributes": {"name": "Zn(LTP)2", "is_primary": True},
            },
            "Method:Conventional solvothermal": {
                "type": "Method",
                "attributes": {"name": "Conventional solvothermal"},
            },
            "Precursor:solvent:water": {
                "type": "Precursor",
                "attributes": {"name": "water", "precursor_type": "solvent"},
            },
            "Precursor:metal:zn(no3)2": {
                "type": "Precursor",
                "attributes": {"name": "Zn(NO3)2", "precursor_type": "metal"},
            },
            "DOI:10.0000/example": {
                "type": "DOI",
                "attributes": {"doi": "10.0000/example"},
            },
        },
        "relationships": [
            {"from": "MOF:UNABAN", "to": "Stability:Stable", "type": "HAS_STABILITY"},
            {"from": "MOF:UNABAN", "to": "Name:Zn(LTP)2", "type": "HAS_NAME"},
            {"from": "MOF:UNABAN", "to": "Method:Conventional solvothermal", "type": "USES_METHOD"},
            {"from": "MOF:UNABAN", "to": "Precursor:solvent:water", "type": "USES_SOLVENT"},
            {"from": "MOF:UNABAN", "to": "Precursor:metal:Zn(NO3)2", "type": "USES_METAL_PRECURSOR"},
            {"from": "MOF:UNABAN", "to": "DOI:10.0000/example", "type": "CITED_IN"},
            {"from": "MOF:OTHER1", "to": "Precursor:solvent:water", "type": "USES_SOLVENT"},
        ],
        "metadata": {"node_count": 8, "relationship_count": 7},
    }
    path.write_text(json.dumps(graph), encoding="utf-8")


def test_no_result_graph_retriever_returns_empty_for_missing_kg():
    retriever = NoResultGraphRetriever()

    assert retriever.fact_count == 0
    assert retriever.search("What solvent is used in UNABAN?") == []


def test_kg_graph_retriever_treats_invalid_json_as_empty(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    graph_path.write_text("{not json", encoding="utf-8")

    retriever = KGGraphRetriever(graph_path)

    assert retriever.is_loaded is False
    assert retriever.fact_count == 0
    assert retriever.search("What solvent is used in UNABAN?") == []


def test_kg_graph_retriever_returns_solvent_fact_for_refcode(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    write_graph(graph_path)
    retriever = KGGraphRetriever(graph_path)

    results = retriever.search("What solvent is used in UNABAN?", limit=3)

    assert retriever.fact_count == 7
    assert results
    assert results[0].fact.refcode == "UNABAN"
    assert results[0].fact.relation == "KG_USES_SOLVENT"
    assert results[0].fact.value == "water"
    assert results[0].fact.path == "Material(UNABAN) -> USES_SOLVENT -> Precursor:solvent:water"


def test_kg_graph_retriever_returns_water_stability_fact(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    write_graph(graph_path)
    retriever = KGGraphRetriever(graph_path)

    results = retriever.search("What is the water stability of Zn(LTP)2?", limit=3)

    assert results
    assert results[0].fact.refcode == "UNABAN"
    assert results[0].fact.relation == "KG_HAS_STABILITY: Water Stability"
    assert results[0].fact.value == "Stable"


def test_kg_graph_retriever_returns_alias_fact(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    write_graph(graph_path)
    retriever = KGGraphRetriever(graph_path)

    results = retriever.search("What names are associated with CSD ref code UNABAN?", limit=3)

    assert results
    assert results[0].fact.relation == "KG_HAS_NAME"
    assert results[0].fact.value == "Zn(LTP)2"


def test_kg_graph_retriever_expands_shared_neighbor_without_seed_mof(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    write_graph(graph_path)
    retriever = KGGraphRetriever(graph_path)

    results = retriever.search("What other MOFs use the same solvent as UNABAN?", limit=5)

    assert results
    assert results[0].fact.refcode == "OTHER1"
    assert all(result.fact.refcode != "UNABAN" for result in results)


def test_kg_graph_retriever_returns_empty_for_unknown_explicit_identifier(tmp_path):
    graph_path = tmp_path / "mof_kg.json"
    write_graph(graph_path)
    retriever = KGGraphRetriever(graph_path)

    assert retriever.search("What solvent is used in NOT_A_REAL_MOF_123?", limit=3) == []
