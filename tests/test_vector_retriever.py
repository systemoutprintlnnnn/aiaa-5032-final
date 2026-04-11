from app.config import get_settings
from app.knowledge_store import KnowledgeStore
from app.rag.vector_store import VectorHit
from app.retrievers.vector import VectorRetriever


class FakeEmbeddingProvider:
    def embed_query(self, query):
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self, fact_id):
        self.fact_id = fact_id

    def search(self, query_vector, limit):
        return [VectorHit(id="point-1", score=0.9, payload={"fact_id": self.fact_id})]


def test_vector_retriever_maps_vector_hit_to_retrieval_result():
    store = KnowledgeStore(get_settings().open_source_data_dir)
    fact = store.facts[0]
    retriever = VectorRetriever(
        store=store,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(fact.id),
    )

    results = retriever.search("query", limit=1)

    assert len(results) == 1
    assert results[0].fact.id == fact.id
    assert results[0].score == 0.9
