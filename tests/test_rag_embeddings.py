from app.rag.embeddings import OpenAIEmbeddingProvider


class FakeEmbeddingClient:
    class Embeddings:
        def create(self, model, input):
            class Item:
                embedding = [0.1, 0.2, 0.3]

            class Response:
                data = [Item() for _ in input]

            return Response()

    embeddings = Embeddings()


def test_openai_embedding_provider_embeds_texts_with_client():
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", client=FakeEmbeddingClient())

    vectors = provider.embed_texts(["a", "b"])

    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]


def test_openai_embedding_provider_embeds_query():
    provider = OpenAIEmbeddingProvider(model="fake-model", api_key="test-key", client=FakeEmbeddingClient())

    vector = provider.embed_query("hello")

    assert vector == [0.1, 0.2, 0.3]
