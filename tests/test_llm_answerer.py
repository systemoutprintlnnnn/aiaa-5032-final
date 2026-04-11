from app.answerers.llm import OpenAILLMAnswerer


class FakeResponse:
    output_text = "UTSA-67 has a reported BET surface area of 1137 m2 g-1 [S1]."


class FakeResponses:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    responses = FakeResponses()


def test_llm_answerer_refuses_without_evidence():
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=FakeClient())

    response = answerer.answer("question", [])

    assert response.mode == "insufficient_evidence"
    assert response.sources == []


def test_llm_answerer_uses_evidence_when_matches_exist():
    from app.config import get_settings
    from app.knowledge_store import KnowledgeStore

    store = KnowledgeStore(get_settings().open_source_data_dir)
    fact = store.search("What is the BET surface area of UTSA-67?", limit=1)[0][0]
    answerer = OpenAILLMAnswerer(model="fake-model", api_key="test-key", client=FakeClient())

    response = answerer.answer("What is the BET surface area of UTSA-67?", [(fact, 1.0)])

    assert "1137" in response.answer
    assert response.sources
    assert response.kg_facts
