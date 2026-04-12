from app.answerers.llm import OpenAILLMAnswerer


class FakeResponse:
    class Choice:
        class Message:
            content = "UTSA-67 has a reported BET surface area of 1137 m2 g-1 [S1]."

        message = Message()

    choices = [Choice()]


class FakeCompletions:
    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return FakeResponse()


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def test_llm_answerer_refuses_without_evidence():
    client = FakeClient()
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=client)

    response = answerer.answer("question", [])

    assert response.mode == "insufficient_evidence"
    assert response.sources == []
    assert client.chat.completions.last_request is None


def test_llm_answerer_uses_evidence_when_matches_exist():
    from app.config import get_settings
    from app.knowledge_store import KnowledgeStore

    store = KnowledgeStore(get_settings().open_source_data_dir)
    fact = store.search("What is the BET surface area of UTSA-67?", limit=1)[0][0]
    client = FakeClient()
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=client)

    response = answerer.answer("What is the BET surface area of UTSA-67?", [(fact, 1.0)])

    assert "1137" in response.answer
    assert response.sources
    assert response.kg_facts
    assert client.chat.completions.last_request["model"] == "fake-model"
    assert client.chat.completions.last_request["messages"][0]["role"] == "system"
    assert client.chat.completions.last_request["messages"][1]["role"] == "user"
