from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.retrievers.base import RetrievalResult
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever
from app.stores import Fact


def test_hybrid_retriever_keeps_simple_rag_path_working_with_empty_graph():
    store = KnowledgeStore(get_settings().open_source_data_dir)
    retriever = HybridRetriever([KeywordRetriever(store), NoResultGraphRetriever()])

    results = retriever.search("What is the BET surface area of UTSA-67?", limit=3)

    assert results
    assert any("BET Surface Area" in result.fact.relation for result in results)


def test_hybrid_retriever_keeps_shared_neighbor_queries_focused_on_kg_results():
    seed = make_fact("RAPXEN", "MOF KG JSON", "KG_USES_SOLVENT", "CH3OH")
    related = make_fact("RAPXIR", "MOF KG JSON", "KG_USES_SOLVENT", "CH3OH")
    unrelated = make_fact("XENMIO", "MOF-ChemUnity water_stability_chemunity_v0.1.0.csv", "HAS_PROPERTY: Water Stability", "Stable")
    retriever = HybridRetriever(
        [
            StaticRetriever([RetrievalResult(fact=seed, score=100.0), RetrievalResult(fact=unrelated, score=90.0)]),
            StaticRetriever([RetrievalResult(fact=related, score=80.0)]),
        ]
    )

    results = retriever.search("What other MOFs use the same solvent as RAPXEN?", limit=5)

    assert [result.fact.refcode for result in results] == ["RAPXIR"]


def test_hybrid_retriever_prioritizes_synthesis_documents_for_synthesis_intent():
    synthesis = make_fact("YEXLAR", "MOF KG synthesis evidence", "HAS_SYNTHESIS_EVIDENCE", "method: Conventional solvothermal")
    kg_solvent = make_fact("YEXLAR", "MOF KG JSON", "KG_USES_SOLVENT", "DMF")
    retriever = HybridRetriever(
        [
            StaticRetriever([RetrievalResult(fact=kg_solvent, score=80.0)]),
            StaticRetriever([RetrievalResult(fact=synthesis, score=60.0)]),
        ]
    )

    results = retriever.search("What synthesis evidence is available for YEXLAR?", limit=2)

    assert [result.fact.relation for result in results] == ["HAS_SYNTHESIS_EVIDENCE", "KG_USES_SOLVENT"]


def test_hybrid_retriever_filters_vector_noise_for_explicit_entity_queries():
    seed = make_fact("RAPXEN", "MOF KG synthesis evidence", "HAS_SYNTHESIS_EVIDENCE", "solvent: CH3OH")
    neighbor = make_fact("RAPXIR", "MOF KG synthesis evidence", "HAS_SYNTHESIS_EVIDENCE", "solvent: CH3OH")
    retriever = HybridRetriever(
        [
            StaticRetriever([RetrievalResult(fact=neighbor, score=99.0)]),
            StaticRetriever([RetrievalResult(fact=seed, score=40.0)]),
        ]
    )

    results = retriever.search("What solvent is used in RAPXEN?", limit=5)

    assert [result.fact.refcode for result in results] == ["RAPXEN"]


def test_hybrid_retriever_prioritizes_complete_synthesis_evidence():
    variant = make_fact("YEXLAR", "MOF KG synthesis evidence", "HAS_SYNTHESIS_EVIDENCE", "metal precursor: Cu(NO3)2")
    complete = make_fact(
        "YEXLAR",
        "MOF KG synthesis evidence",
        "HAS_SYNTHESIS_EVIDENCE",
        "method: Conventional solvothermal; solvent: DMF; temperature: 433.15 K; reaction time: 72.0 h; operation: heat; yield: 58 %",
    )
    retriever = HybridRetriever(
        [
            StaticRetriever([RetrievalResult(fact=variant, score=90.0)]),
            StaticRetriever([RetrievalResult(fact=complete, score=50.0)]),
        ]
    )

    results = retriever.search("What synthesis evidence is available for YEXLAR?", limit=2)

    assert results[0].fact.value.startswith("method: Conventional solvothermal")


class StaticRetriever:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results

    def search(self, query: str, limit: int = 6) -> list[RetrievalResult]:
        return self.results[:limit]


def make_fact(refcode: str, data_source: str, relation: str, value: str) -> Fact:
    return Fact(
        id=f"test-{refcode}-{relation}",
        refcode=refcode,
        material_names=(refcode,),
        relation=relation,
        value=value,
        evidence=f"{refcode} evidence",
        doi=None,
        data_source=data_source,
        path=f"Material({refcode}) -> {relation.removeprefix('KG_')} -> {value}",
        search_text=f"{refcode} {relation} {value}".lower(),
    )
