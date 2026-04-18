import { describe, expect, it } from "vitest";
import { toQueryViewModel } from "./presentation";
import type { QueryResponse } from "./api";

const response: QueryResponse = {
  query: "What is the BET surface area of UTSA-67?",
  mode: "hybrid_rag",
  answer: "UTSA-67 has a BET surface area of 1137 m2 g-1 [S1].",
  retrieved_count: 2,
  sources: [
    {
      id: "S1",
      title: "MOF-ChemUnity demo.json (CUVVOG)",
      doi: "10.1039/C5CC08210B",
      refcode: "CUVVOG",
      evidence:
        "The Brunauer-Emmett-Teller surface area was estimated to be 1137 m2 g-1.",
      data_source: "MOF-ChemUnity demo.json",
      license: "MOF-ChemUnity data: CC BY-NC 4.0; code: MIT",
    },
  ],
  kg_facts: [
    {
      path: "Material(CUVVOG) -> HAS_EXPERIMENTAL_PROPERTY -> BET Surface Area",
      relation: "HAS_EXPERIMENTAL_PROPERTY: BET Surface Area",
      value: "1137 m2 g-1",
      source_id: "S1",
    },
  ],
};

describe("toQueryViewModel", () => {
  it("keeps answer, retrieval mode, source metadata, and graph facts ready for display", () => {
    const viewModel = toQueryViewModel(response);

    expect(viewModel.modeLabel).toBe("Hybrid RAG");
    expect(viewModel.retrievedLabel).toBe("2 retrieved");
    expect(viewModel.answer).toContain("1137 m2 g-1");
    expect(viewModel.sources[0]?.metadata).toContain("DOI 10.1039/C5CC08210B");
    expect(viewModel.sources[0]?.metadata).toContain("CSD CUVVOG");
    expect(viewModel.facts[0]?.path).toContain("Material(CUVVOG)");
  });

  it("uses stable empty-state labels when no evidence is returned", () => {
    const viewModel = toQueryViewModel({
      ...response,
      mode: "insufficient_evidence",
      answer: "Insufficient evidence.",
      retrieved_count: 0,
      sources: [],
      kg_facts: [],
    });

    expect(viewModel.modeLabel).toBe("Insufficient evidence");
    expect(viewModel.retrievedLabel).toBe("0 retrieved");
    expect(viewModel.sources).toEqual([]);
    expect(viewModel.facts).toEqual([]);
  });
});
