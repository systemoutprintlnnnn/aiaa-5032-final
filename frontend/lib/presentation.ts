import type { ApiSource, KgFact, QueryResponse } from "./api";

export type SourceViewModel = ApiSource & {
  metadata: string;
  retrievalTags: string[];
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
    retrievalTags: toRetrievalTags(source.retrieval_sources),
    metadata: metadata.length > 0 ? metadata.join(" | ") : "No source metadata",
  };
}

function toRetrievalTags(sources: string[] | null | undefined): string[] {
  const labels: Record<string, string> = {
    embedding: "Embedding",
    keyword: "Keyword",
    kg: "KG",
  };
  const tags: string[] = [];
  for (const source of sources ?? []) {
    const label = labels[source] ?? humanizeMode(source);
    if (label && !tags.includes(label)) {
      tags.push(label);
    }
  }
  return tags.length > 0 ? tags : ["Unknown"];
}

function humanizeMode(mode: string): string {
  return mode
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
