from app.rag.embeddings import OpenAIEmbeddingProvider


class FakeEmbeddingClient:
    def __init__(self):
        self.last_request = None
        self.embeddings = self.Embeddings(self)

    class Embeddings:
        def __init__(self, parent):
            self.parent = parent

        def create(self, **kwargs):
            self.parent.last_request = kwargs

            class Item:
                embedding = [0.1, 0.2, 0.3]

            class Response:
                data = [Item() for _ in kwargs["input"]]

            return Response()


def test_openai_embedding_provider_embeds_texts_with_client():
    client = FakeEmbeddingClient()
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", dimensions=2048, client=client)

    vectors = provider.embed_texts(["a", "b"])

    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert client.last_request == {"model": "fake-model", "input": ["a", "b"], "dimensions": 2048}


def test_openai_embedding_provider_embeds_query():
    client = FakeEmbeddingClient()
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", client=client)

    vector = provider.embed_query("hello")

    assert vector == [0.1, 0.2, 0.3]
