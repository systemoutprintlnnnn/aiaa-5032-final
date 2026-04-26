import json

from app.config import Settings
from app.data_sources.synthesis import load_synthesis_evidence_records
from app.knowledge_store import KnowledgeStore
from app.retrievers import KeywordRetriever


def test_synthesis_loader_formats_complete_record(tmp_path):
    path = tmp_path / "synthesis.json"
    path.write_text(
        json.dumps(
            [
                {
                    "identifier": "YEXLAR",
                    "name": "{[(CH3)2NH2][Zn(FDA)(BTZ)2]}n",
                    "method": "Conventional solvothermal",
                    "M_precursor": [{"name": "Zn(NO3)2⋅6H2O", "composition": "0.0297 g,0.1 mmol"}],
                    "O_precursor": [{"name": "H2FDA"}, {"name": "HBTZ"}],
                    "S_precursor": [{"name": "DMF", "composition": "3 mL"}, {"name": "C2H5OH", "composition": "1 mL"}],
                    "temperature": "433.15 K",
                    "time": "72.0 h",
                    "operation": [{"name": "heat", "Temperature": "160 °C", "Time": "3 days"}, {"name": "dry"}],
                    "Yield": "58 %",
                    "doi": "10.1021/acs.cgd.8b00344",
                    "source": "KAIST",
                }
            ]
        ),
        encoding="utf-8",
    )

    records = load_synthesis_evidence_records(path)

    assert len(records) == 1
    record = records[0]
    assert record.refcode == "YEXLAR"
    assert record.row_index == 0
    assert record.doi == "10.1021/acs.cgd.8b00344"
    assert "Conventional solvothermal" in record.evidence
    assert "Zn(NO3)2⋅6H2O" in record.evidence
    assert "H2FDA" in record.evidence
    assert "DMF" in record.evidence
    assert "433.15 K" in record.evidence
    assert "72.0 h" in record.evidence
    assert "heat at 160 °C for 3 days" in record.evidence
    assert "58 %" in record.evidence


def test_knowledge_store_keeps_synthesis_variants_as_separate_records(tmp_path):
    data_dir = tmp_path / "open_source"
    data_dir.mkdir()
    synthesis_path = tmp_path / "synthesis.json"
    synthesis_path.write_text(
        json.dumps(
            [
                {"identifier": "YEXLAR", "name": "base", "method": "Conventional solvothermal", "doi": "10.1/base"},
                {"identifier": "YEXLAR", "name": "variant", "M_precursor": [{"name": "Ni(NO3)2"}], "doi": "10.1/variant"},
            ]
        ),
        encoding="utf-8",
    )

    store = KnowledgeStore(data_dir, synthesis_data_path=synthesis_path)

    yexlar_facts = [fact for fact in store.facts if fact.refcode == "YEXLAR"]
    assert len(yexlar_facts) == 2
    assert {fact.path for fact in yexlar_facts} == {
        "Material(YEXLAR) -> HAS_SYNTHESIS_EVIDENCE -> SynthesisRecord:0",
        "Material(YEXLAR) -> HAS_SYNTHESIS_EVIDENCE -> SynthesisRecord:1",
    }
    assert {fact.doi for fact in yexlar_facts} == {"10.1/base", "10.1/variant"}


def test_keyword_retriever_prioritizes_synthesis_evidence_for_yexlar():
    settings = Settings()
    store = KnowledgeStore(settings.open_source_data_dir, synthesis_data_path=settings.resolved_kg_synthesis_path)
    retriever = KeywordRetriever(store)

    results = retriever.search("What synthesis evidence is available for YEXLAR?", limit=5)

    assert results
    assert results[0].fact.relation == "HAS_SYNTHESIS_EVIDENCE"
    assert results[0].fact.refcode == "YEXLAR"
    assert "Conventional solvothermal" in results[0].fact.evidence
    assert "10.1021/acs.cgd.8b00344" in results[0].fact.evidence
