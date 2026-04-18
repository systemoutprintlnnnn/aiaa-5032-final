import type { ApiSource, KgFact, QueryResponse } from "./api";

export type SourceViewModel = ApiSource & {
  metadata: string;
};

export type FactViewModel = KgFact;

export type QueryViewModel = {
  answer: string;
  modeLabel: string;
  retrievedLabel: string;
  sources: SourceViewModel[];
  facts: FactViewModel[];
};

const modeLabels: Record<string, string> = {
  hard_fact_lookup: "Hard fact lookup",
  hybrid_rag: "Hybrid RAG",
  insufficient_evidence: "Insufficient evidence",
};

export function toQueryViewModel(response: QueryResponse): QueryViewModel {
  return {
    answer: response.answer,
    modeLabel: modeLabels[response.mode] ?? humanizeMode(response.mode),
    retrievedLabel: `${response.retrieved_count} retrieved`,
    sources: response.sources.map(toSourceViewModel),
    facts: response.kg_facts,
  };
}

function toSourceViewModel(source: ApiSource): SourceViewModel {
  const metadata = [
    source.doi ? `DOI ${source.doi}` : null,
    source.refcode ? `CSD ${source.refcode}` : null,
    source.data_source,
    source.license,
  ].filter(Boolean);

  return {
    ...source,
    metadata: metadata.length > 0 ? metadata.join(" | ") : "No source metadata",
  };
}

function humanizeMode(mode: string): string {
  return mode
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
