"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  getApiBaseUrl,
  getRagStatus,
  streamQueryMof,
} from "../lib/api";
import type {
  ApiSource,
  KgFact,
  QueryResponse,
  RagStatus,
  StreamEvent,
} from "../lib/api";
import { toQueryViewModel } from "../lib/presentation";

const exampleQuestions = [
  "What is the BET surface area of UTSA-67?",
  "Is UTSA-67 water stable?",
  "What synthesis evidence is available for CUVVOG?",
];

type StreamingState = {
  mode: string;
  sources: ApiSource[];
  kg_facts: KgFact[];
  retrieved_count: number;
  answer: string;
  done: boolean;
};

export function MofWorkbench() {
  const [question, setQuestion] = useState(exampleQuestions[0]);
  const [streaming, setStreaming] = useState<StreamingState | null>(null);
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const resultRef = useRef<HTMLElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const viewModel = useMemo(() => {
    if (!streaming) return null;
    const snapshot: QueryResponse = {
      query: question,
      mode: streaming.mode,
      answer: streaming.answer,
      sources: streaming.sources,
      kg_facts: streaming.kg_facts,
      retrieved_count: streaming.retrieved_count,
    };
    return toQueryViewModel(snapshot);
  }, [streaming, question]);

  useEffect(() => {
    textareaRef.current?.focus();
    textareaRef.current?.select();
  }, []);

  useEffect(() => {
    let isActive = true;
    getRagStatus()
      .then((nextStatus) => {
        if (isActive) {
          setStatus(nextStatus);
          setStatusError(null);
        }
      })
      .catch((nextError: unknown) => {
        if (isActive) {
          setStatus(null);
          setStatusError(toErrorMessage(nextError));
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runQuery(question);
  }

  async function runQuery(nextQuestion: string) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) {
      setError("Please enter a question first.");
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);
    setStreaming({
      mode: "streaming",
      sources: [],
      kg_facts: [],
      retrieved_count: 0,
      answer: "",
      done: false,
    });

    requestAnimationFrame(() => {
      resultRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });

    try {
      await streamQueryMof(
        trimmed,
        6,
        (nextEvent: StreamEvent) => {
          setStreaming((prev) => reduceStream(prev, nextEvent));
          if (nextEvent.type === "error") {
            setError(nextEvent.message);
          }
        },
        { signal: controller.signal },
      );
    } catch (nextError) {
      if ((nextError as { name?: string })?.name === "AbortError") {
        return;
      }
      setStreaming(null);
      setError(toErrorMessage(nextError));
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      setIsLoading(false);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      void runQuery(question);
    }
  }

  const isStreaming = streaming !== null && !streaming.done && isLoading;
  const hasResult = viewModel !== null;

  const pillLabel = statusError
    ? "Backend offline"
    : status
      ? status.llm_enabled
        ? `${status.retrieval_mode} · ${status.llm_model}`
        : `${status.retrieval_mode} · deterministic`
      : "Connecting…";

  const runtimeFooter = status
    ? [
        `retrieval=${status.retrieval_mode}`,
        `embedding=${status.embedding_model}`,
        `engine=${status.llm_enabled ? status.llm_model : "deterministic"}`,
        `collection=${status.qdrant_collection}`,
      ].join("  ·  ")
    : statusError ?? "Probing backend…";

  return (
    <main className="app">
      <header className="app-header">
        <h1 className="brand">
          <span>MOF Workbench</span>
          <span className="brand__tag">evidence-backed Q&amp;A</span>
        </h1>
        <span
          className={`status-pill${statusError ? " is-offline" : ""}`}
          title={getApiBaseUrl()}
        >
          <span className="status-pill__dot" aria-hidden />
          {pillLabel}
        </span>
      </header>

      <div className="layout">
        <div className="main-col">
          <section className="ask" aria-label="Ask a question">
            <div className="ask__label">
              <h2>Ask a question about a MOF</h2>
              <span className="ask__hint">⌘ + Enter to send</span>
            </div>

            <form className="ask__card" onSubmit={handleSubmit}>
              <textarea
                ref={textareaRef}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                rows={3}
                placeholder="e.g. What is the BET surface area of UTSA-67?"
                spellCheck={false}
              />
              <div className="ask__actions">
                <span className="ask__hint-inline">top_k = 6</span>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="btn-primary__spinner" aria-hidden />
                      <span>Answering…</span>
                    </>
                  ) : (
                    <>
                      <span>Ask</span>
                      <span aria-hidden>→</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            <div className="examples">
              <span className="examples__label">Try</span>
              {exampleQuestions.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="chip"
                  onClick={() => {
                    setQuestion(example);
                    textareaRef.current?.focus();
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </section>

          {(hasResult || error) && (
            <section className="result" ref={resultRef} aria-label="Answer">
              {error ? (
                <div className="error-card" role="alert">
                  <strong>Request failed</strong>
                  {error}
                </div>
              ) : null}

              {viewModel ? (
                <>
                  <div className="result__head">
                    <span className="mode-badge">{viewModel.modeLabel}</span>
                    {isStreaming ? (
                      <span className="live-indicator">
                        <span className="live-indicator__dot" aria-hidden />
                        streaming
                      </span>
                    ) : null}
                    <span className="result__meta">
                      {viewModel.retrievedLabel}
                    </span>
                  </div>

                  <article
                    className={`answer-card${isStreaming ? " is-streaming" : ""}`}
                  >
                    {viewModel.answer ? (
                      <p className="answer-text">
                        {viewModel.answer}
                        {isStreaming ? (
                          <span className="stream-cursor" aria-hidden />
                        ) : null}
                      </p>
                    ) : (
                      <p className="answer-placeholder">
                        <span className="stream-cursor" aria-hidden />
                        Retrieving evidence and composing the answer…
                      </p>
                    )}
                  </article>

                  {viewModel.facts.length > 0 ? (
                    <details className="details-block">
                      <summary>
                        <span>Related facts</span>
                        <span className="details-count">
                          {viewModel.facts.length}
                        </span>
                      </summary>
                      <div className="details-body">
                        <ul className="facts-list">
                          {viewModel.facts.map((fact) => (
                            <li
                              className="fact-item"
                              key={`${fact.source_id}-${fact.path}`}
                            >
                              <span className="path">
                                {fact.path.replace(/->/g, "→")}
                              </span>
                              <p className="rel">{fact.relation}</p>
                              <p className="val">
                                <strong>{fact.value}</strong>
                                <span className="cite">
                                  ({fact.source_id})
                                </span>
                              </p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  ) : null}
                </>
              ) : null}
            </section>
          )}
        </div>

        <aside className="side-col" aria-label="Sources">
          {viewModel && viewModel.sources.length > 0 ? (
            <section className="side-panel">
              <header className="side-panel__head">
                <span>Sources</span>
                <span className="side-panel__count">
                  {viewModel.sources.length}
                </span>
              </header>
              <div className="side-panel__body">
                <ol className="sources-list">
                  {viewModel.sources.map((source) => (
                    <li className="source-item" key={source.id}>
                      <span className="source-badge">{source.id}</span>
                      <div>
                        <h3>{source.title}</h3>
                        <p className="meta">{source.metadata}</p>
                        <p className="evidence">{source.evidence}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </section>
          ) : (
            <div className="side-empty">
              <h3>Sources</h3>
              <p>
                Citations and evidence passages will appear here as soon as
                you ask a question.
              </p>
            </div>
          )}
        </aside>
      </div>

      <footer className="app-footer">{runtimeFooter}</footer>
    </main>
  );
}

function reduceStream(
  prev: StreamingState | null,
  event: StreamEvent,
): StreamingState | null {
  const base: StreamingState = prev ?? {
    mode: "streaming",
    sources: [],
    kg_facts: [],
    retrieved_count: 0,
    answer: "",
    done: false,
  };

  switch (event.type) {
    case "meta":
      return {
        ...base,
        mode: event.mode,
        sources: event.sources,
        kg_facts: event.kg_facts,
        retrieved_count: event.retrieved_count,
      };
    case "token":
      return { ...base, answer: base.answer + event.text };
    case "done":
      return {
        ...base,
        mode: event.mode,
        answer: event.answer || base.answer,
        done: true,
      };
    case "error":
      return { ...base, done: true };
    default:
      return base;
  }
}

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
