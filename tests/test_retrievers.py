from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.retrievers import HybridRetriever, KeywordRetriever, NoResultGraphRetriever


def test_hybrid_retriever_keeps_simple_rag_path_working_with_empty_graph():
    store = KnowledgeStore(get_settings().open_source_data_dir)
    retriever = HybridRetriever([KeywordRetriever(store), NoResultGraphRetriever()])

    results = retriever.search("What is the BET surface area of UTSA-67?", limit=3)

    assert results
    assert any("BET Surface Area" in result.fact.relation for result in results)
