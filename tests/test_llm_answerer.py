from app.answerers.llm import OpenAILLMAnswerer, _format_evidence
from app.stores import Fact


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

    settings = get_settings()
    store = KnowledgeStore(settings.open_source_data_dir, synthesis_data_path=settings.resolved_kg_synthesis_path)
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


def test_llm_evidence_format_includes_source_doi_and_path():
    fact = Fact(
        id="synthesis-YEXLAR-0",
        refcode="YEXLAR",
        material_names=("{[(CH3)2NH2][Zn(FDA)(BTZ)2]}n",),
        relation="HAS_SYNTHESIS_EVIDENCE",
        value="method: Conventional solvothermal",
        evidence="Operation: heat at 160 °C for 3 days. DOI: 10.1021/acs.cgd.8b00344. Source: KAIST.",
        doi="10.1021/acs.cgd.8b00344",
        data_source="MOF KG synthesis evidence",
        path="Material(YEXLAR) -> HAS_SYNTHESIS_EVIDENCE -> SynthesisRecord:36",
        search_text="yexlar synthesis",
    )

    evidence = _format_evidence([(fact, 10.0)])

    assert "source=MOF KG synthesis evidence" in evidence
    assert "doi=10.1021/acs.cgd.8b00344" in evidence
    assert "path=Material(YEXLAR) -> HAS_SYNTHESIS_EVIDENCE -> SynthesisRecord:36" in evidence
    assert "Operation: heat at 160 °C for 3 days" in evidence
