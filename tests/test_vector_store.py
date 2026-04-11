from app.rag.chunks import EvidenceChunk
from app.rag.vector_store import QdrantVectorStore, VectorHit


def test_vector_hit_keeps_payload_and_score():
    hit = VectorHit(id="fact-1", score=0.9, payload={"fact_id": "fact-1"})

    assert hit.id == "fact-1"
    assert hit.score == 0.9
    assert hit.payload["fact_id"] == "fact-1"


class FakeQdrantClient:
    def __init__(self):
        self.points = []

    def get_collections(self):
        class Collections:
            collections = []

        return Collections()

    def create_collection(self, **kwargs):
        pass

    def upsert(self, collection_name, points):
        self.points.extend(points)


def test_qdrant_vector_store_offsets_point_ids_for_batched_upserts():
    client = FakeQdrantClient()
    store = QdrantVectorStore(url="http://qdrant", collection="mof", dimensions=3, client=client)
    chunk = EvidenceChunk(id="fact-7", text="evidence", payload={"fact_id": "fact-7"})

    store.upsert_chunks([chunk], [[0.1, 0.2, 0.3]], start_index=128)

    assert client.points[0].id == 128
    assert client.points[0].payload["chunk_id"] == "fact-7"
