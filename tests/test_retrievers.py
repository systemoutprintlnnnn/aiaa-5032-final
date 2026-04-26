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
