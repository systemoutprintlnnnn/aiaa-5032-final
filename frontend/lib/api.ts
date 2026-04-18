export type ApiSource = {
  id: string;
  title: string;
  doi?: string | null;
  refcode?: string | null;
  evidence: string;
  data_source?: string | null;
  license?: string | null;
};

export type KgFact = {
  path: string;
  relation: string;
  value: string;
  source_id: string;
};

export type QueryResponse = {
  query: string;
  mode: string;
  answer: string;
  sources: ApiSource[];
  kg_facts: KgFact[];
  retrieved_count: number;
};

export type RagStatus = {
  retrieval_mode: string;
  vector_store_enabled: boolean;
  llm_enabled: boolean;
  api_key_configured: boolean;
  embedding_provider: string;
  embedding_model: string;
  qdrant_collection: string;
  llm_provider: string;
  llm_model: string;
};

type Fetcher = typeof fetch;

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export async function queryMof(
  question: string,
  topK = 6,
  fetcher: Fetcher = fetch,
): Promise<QueryResponse> {
  const response = await fetcher(`${getApiBaseUrl()}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!response.ok) {
    throw new Error(`Query failed with HTTP ${response.status}`);
  }

  return response.json() as Promise<QueryResponse>;
}

export async function getRagStatus(fetcher: Fetcher = fetch): Promise<RagStatus> {
  const response = await fetcher(`${getApiBaseUrl()}/api/rag/status`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Status check failed with HTTP ${response.status}`);
  }

  return response.json() as Promise<RagStatus>;
}

export type StreamMeta = {
  type: "meta";
  query: string;
  mode: string;
  sources: ApiSource[];
  kg_facts: KgFact[];
  retrieved_count: number;
};

export type StreamToken = { type: "token"; text: string };
export type StreamDone = { type: "done"; mode: string; answer: string };
export type StreamError = { type: "error"; message: string };
export type StreamEvent = StreamMeta | StreamToken | StreamDone | StreamError;

export async function streamQueryMof(
  question: string,
  topK: number,
  onEvent: (event: StreamEvent) => void,
  options: { signal?: AbortSignal; fetcher?: Fetcher } = {},
): Promise<void> {
  const { signal, fetcher = fetch } = options;
  const response = await fetcher(`${getApiBaseUrl()}/api/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed with HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex !== -1) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      if (line) {
        onEvent(JSON.parse(line) as StreamEvent);
      }
      newlineIndex = buffer.indexOf("\n");
    }
  }

  const tail = buffer.trim();
  if (tail) {
    onEvent(JSON.parse(tail) as StreamEvent);
  }
}
