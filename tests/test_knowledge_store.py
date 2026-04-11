from app.config import get_settings
from app.knowledge_store import KnowledgeStore


def test_store_loads_facts_and_documents():
    store = KnowledgeStore(get_settings().open_source_data_dir)

    assert store.material_count == 100
    assert len(store.facts) > 0
    assert len(store.documents) == len(store.facts)


def test_store_search_returns_bet_surface_area_evidence():
    store = KnowledgeStore(get_settings().open_source_data_dir)

    results = store.search("What is the BET surface area of UTSA-67?", limit=3)

    assert results
    assert any("BET Surface Area" in fact.relation for fact, _score in results)
    assert any("1137" in fact.value for fact, _score in results)
