# MOF Literature Assistant - Paper-Informed Implementation Plan

## Reframed Goal

AIAA 5032 课程项目不应该只是一个普通的 MOF QA chatbot，而应该做成一个小规模、可展示、可评测的 **citation-grounded MOF literature assistant**：

- 用 RAG 读取项目文献并生成有引用的科学回答。
- 用 KG 把 MOF、别名、性质、应用、合成、证据和论文来源连起来。
- 用 dual-track retrieval 区分硬事实和软知识：硬事实走 KG/Text-to-Cypher，软知识走向量检索。
- 用 rerank、self-feedback 和 citation verification 降低科学问答里的幻觉。
- 用一个小型 benchmark 展示：纯 LLM < vector RAG < graph-enhanced RAG。

这相当于课程项目范围内的迷你版 OpenScholar + KG-FM + MOF-ChemUnity，而不是复刻它们的超大规模数据工程。

## PDF Reading Notes

| Paper | Project takeaway |
|---|---|
| `MOF-ChemUnity: Literature-Informed Large Language Models for Metal-Organic Framework Research` | 核心启发是 material-centric KG。MOF 名称和 coreference 需要先消歧并连接到一个材料实体；每条 property/application/synthesis fact 都要保留证据句和来源。graph-enhanced RAG 的价值在于多跳查询、结构-性质解释、推荐和可信引用。 |
| `Construction of a knowledge graph for framework material enabled by large language models and its application` | 可借鉴低成本 KG 构建路径：文献 metadata/abstract -> LLM 结构化 JSON -> Neo4j；问答时先把自然语言转 Cypher，再执行查询，最后让 LLM 基于 KG 结果回答。该论文还说明 KG 对 BUT-55 这类名称不显式出现的问题很有帮助。 |
| `Synthesizing scientific literature with retrieval-augmented language models` | OpenScholar 的关键不是“多塞上下文”，而是大规模检索、reranker、自反馈迭代和引用校验。课程项目不做 45M papers，但要迁移三个思想：top-N rerank、一次 self-feedback retrieval loop、claim-level citation verification。 |

## PPT Reading Notes

The reference files are now under `References/`.

| Deck | Project takeaway |
|---|---|
| `AIAA 5032 -mid pre- lcy.pptx` | 项目叙事是：MOFs 获得 2025 Nobel Prize in Chemistry 背景加持，应用覆盖 energy storage、gas capture、catalysis、drug delivery、sensing 等；核心问题是 MOF 材料数量多、命名复杂、通用 LLM 缺乏领域知识，因此需要 KG-enhanced RAG。数据来源应包括结构化数据库、文献抽取和高通量计算数据。评测要覆盖 property-specific QA 和 descriptive knowledge generation。 |
| `AIAA 5032 - Midterm Presentation - Group12 - Approch Part.pptx` | 明确提出 dual-track hybrid retrieval：Graph Query 用 Text-to-Cypher 回答 hard facts，例如 surface area 等精确数值，目标是减少 hallucination；Vector Search 回答 soft knowledge，例如描述性上下文和 synthesis mechanisms；最后做 Graph-Text Fusion。 |

## Scope Decisions

1. 不复刻 100,000 篇论文级别的 KG，也不复刻 45M paper 的 OpenScholar datastore。
2. 首先用 `References/` 下的 PDF/PPTX 和后续团队提供的 MOF 文献做 seed corpus。
3. KG 队友若未完成 Neo4j，也要有可运行的 `StubGraphRetriever` 或小样例 Neo4j graph，保证主系统和展示不被阻塞。
4. 不强依赖 CSD/CoRE MOF/QMOF 访问权限；schema 预留 `csd_ref`、formula、metal、linker、descriptor 等字段，后续可接。
5. 评价标准从“回答看起来不错”改为“答案正确、引用可追溯、KG 关系解释清楚”。
6. 第一版展示优先支持两类问题：property-specific QA 和 descriptive/synthesis knowledge generation。

## Updated Architecture

```text
References / seed docs
  -> ingest parser
  -> chunks with title / DOI / page / section metadata
  -> embeddings in Qdrant
  -> LLM fact extraction JSON
  -> normalized facts
  -> Neo4j or sample graph

User query
  -> planner / router
  -> hard-fact KG retrieval by template Cypher or generated read-only Cypher
  -> soft-knowledge vector retrieval
  -> reranker for retrieved chunks
  -> fusion of chunks + graph facts + evidence
  -> draft answer
  -> optional self-feedback retrieval loop
  -> citation verification
  -> final answer + source cards + graph paths
```

## Technical Stack

| Component | Choice |
|---|---|
| Frontend | Next.js 14+ App Router, Tailwind, react-markdown |
| Backend | FastAPI, Pydantic, LangChain-compatible adapters where useful |
| LLM | Zhipu AI GLM family via config; router can use cheaper model |
| Embedding | Zhipu AI embedding-3 or another configured embedding provider |
| Vector DB | Qdrant Cloud or local Qdrant |
| Reranker | Prefer BGE reranker / cross-encoder if easy; fallback to LLM rerank |
| KG | Neo4j through a `KGRetriever` interface; stub/sample graph as fallback |
| Evaluation | Python evaluation script with curated questions and manual labels |

## Data And KG Schema

Core nodes:

- `Material`: canonical MOF/material entity, with optional formula, metal, linker, CSD reference.
- `Name`: aliases and paper-specific names such as HKUST-1, Cu-BTC, MOF-199, compound labels.
- `Publication`: title, DOI, year, venue, local file.
- `Evidence`: exact evidence text, page, section, confidence, extraction method.
- `Property`: water stability, thermal stability, uptake, surface area, band gap, etc.
- `Application`: gas separation, carbon capture, sensing, catalysis, drug delivery, etc.
- `Synthesis`: precursors, solvent, temperature, time, method, product material.
- `Dataset` / `Descriptor`: optional future nodes for CoRE MOF, QMOF, pore descriptors, RAC descriptors.

Relationships:

- `(Material)-[:HAS_NAME]->(Name)`
- `(Material)-[:REPORTED_IN]->(Publication)`
- `(Material)-[:HAS_PROPERTY {confidence, extracted_by}]->(Property)`
- `(Material)-[:HAS_APPLICATION {confidence}]->(Application)`
- `(Material)-[:HAS_SYNTHESIS]->(Synthesis)`
- `(Property)-[:SUPPORTED_BY]->(Evidence)-[:FROM]->(Publication)`
- `(Application)-[:SUPPORTED_BY]->(Evidence)-[:FROM]->(Publication)`
- `(Synthesis)-[:SUPPORTED_BY]->(Evidence)-[:FROM]->(Publication)`
- `(Material)-[:SIMILAR_TO {method}]->(Material)` as an optional recommendation edge.

Important rule: do not flatten contradictions. If two papers report different stability labels or synthesis conditions, keep both as separate evidence-backed facts.

## Ingestion Plan

1. Parse PDFs into text with page metadata. Use `pdftotext` for a first pass; consider PyMuPDF or Marker if section/page fidelity becomes important.
2. Parse PPTX files with `markitdown` and keep slide number metadata. PPTs are useful for project narrative, baseline categories, and demo requirements.
3. Chunk text into 256-400 word chunks with title, file name, page/slide, section, and DOI metadata where available.
4. Embed chunks and write them to Qdrant.
5. Run LLM extraction per document or per high-value section to produce structured JSON:
   - materials and aliases
   - property facts
   - application facts
   - synthesis facts
   - evidence sentences
   - publication metadata
6. Add table/figure extraction as an extension point for semi-structured PDF evidence. For the first deliverable, manually curate high-value table/figure facts if automatic extraction is unreliable.
7. Validate with Pydantic before graph import.
8. Normalize property/application names using a small curated dictionary.
9. Import validated facts into Neo4j or a local sample graph.

## Retrieval And Generation Plan

1. `router.py` classifies the query:
   - hard factual lookup
   - multi-paper synthesis
   - material/property relation
   - property-specific QA
   - descriptive/synthesis generation
   - application/recommendation
   - unsupported/unknown
2. Hard factual lookup and property-specific QA trigger KG retrieval first when relevant entities/properties are detected.
3. Descriptive/synthesis generation triggers vector retrieval first, because mechanisms and narrative context usually live in prose.
4. Vector retrieval gets a broad candidate set, e.g. top 30 chunks.
5. Reranker selects top 8-12 chunks and caps per-document passages to avoid one PDF dominating.
6. KG retrieval runs in two modes:
   - template Cypher for common tasks, such as property lookup, application lookup, synthesis lookup, publication summary
   - optional LLM-generated Cypher constrained by schema, read-only operations, and a result limit
7. Fusion formats evidence as numbered sources with exact snippets and graph paths.
8. Generator answers only from supplied evidence. If the evidence does not support a claim, it must say so.
9. Citation verifier checks whether each factual sentence has a supporting source. Unsupported claims are revised or marked as not supported.
10. Optional OpenScholar-style self-feedback loop:
   - generate draft
   - ask the model what is missing or weakly supported
   - issue one more retrieval query
   - revise final answer

## Frontend Plan

The frontend should showcase the scientific-assistant idea, not just a chat box.

Main UI:

- Query input and streamed answer.
- Inline citations in the answer.
- Source cards with title, page, evidence snippet, and score.
- KG facts panel showing graph path, e.g. `Material -> HAS_PROPERTY -> Water stability -> SUPPORTED_BY -> Publication`.
- A toggle for `Vector RAG` vs `Graph-enhanced RAG` for demos and ablation.
- A warning state for unsupported answers: “No sufficient evidence found in the provided corpus.”

Good demo detail: show why the system trusts an answer. The source/evidence panel is more important than visual polish.

## Evaluation Plan

Build a 20-30 question test set from the provided PDFs and team-selected MOF examples.

Question categories:

- factual retrieval: exact facts from one paper
- multi-paper synthesis: compare MOF-ChemUnity, KG-FM, and OpenScholar ideas
- relation/graph query: material -> property/application/source
- property-specific QA: water solubility/stability, thermal conductivity, surface area, gas uptake
- descriptive generation: synthesis methods, synthesis mechanisms, application rationale
- recommendation/explanation: literature-backed criteria for a MOF application
- negative or trick questions: answer should say insufficient evidence

Compare four modes:

| Mode | Purpose |
|---|---|
| LLM only | hallucination baseline |
| Vector RAG | normal retrieval baseline |
| Vector RAG + rerank + citation verifier | OpenScholar-inspired baseline |
| Vector + KG + rerank + citation verifier | final proposed system |

Metrics:

- manual correctness
- citation precision / claim support rate
- retrieval hit rate
- number of unsupported claims
- latency
- relevance, coverage, organization, and usefulness for longer synthesis answers
- qualitative trustworthiness notes

The report should include a small ablation table. Even 10 carefully chosen questions are better than no evaluation.

## Demo Ideas

1. **Name ambiguity demo**: show why aliases/coreferences matter, using examples like HKUST-1 / Cu-BTC / MOF-199 or paper-specific compound labels if present in the seed corpus.
2. **Abstract-only KG limitation demo**: ask what KG-FM can and cannot know if it extracts mostly from abstracts; contrast with full-text/evidence-backed graph extraction.
3. **BUT-55 style demo**: show KG retrieval succeeding when the exact material name is not obvious in a text snippet, if the sample graph contains this fact.
4. **Water stability evidence demo**: ask for stability and require the system to show the evidence sentence rather than just a stable/unstable label.
5. **Literature synthesis demo**: ask “What should a trustworthy MOF literature assistant do differently from a vanilla LLM?” and cite all three PDFs.
6. **Ablation demo**: show the same question answered by vanilla LLM, vector RAG, and graph-enhanced RAG.
7. **Hard fact vs soft knowledge demo**: ask for a precise property value and then for a synthesis mechanism; show that the first leans on KG/Text-to-Cypher and the second leans on vector retrieval.

## Development Phases

### Phase 0: Reading And Planning

- Read all project PDFs and PPTX decks.
- Extract paper- and presentation-informed requirements.
- Replace the original engineering-only plan with this research-aligned plan.

### Phase 1: Backend Skeleton And Data Contracts

- Create FastAPI backend structure.
- Add `config.py`, `models.py`, health endpoint, CORS.
- Define source, citation, evidence, KG fact, and query response schemas first.
- Add `.env.example`.

Validation:

- `GET /api/health` works.
- Pydantic models can serialize a mock answer with citations and KG facts.

### Phase 2: PDF Ingestion And Vector RAG

- Implement PDF/PPTX loader, chunker, metadata extraction, embedding, Qdrant upsert.
- Implement vector retriever and a basic generator.
- Answer questions with inline source IDs and source cards.

Validation:

- A query over the provided references returns relevant chunks.
- The answer cites real source IDs from the retrieved context.

### Phase 3: Rerank And Citation Verification

- Add reranker adapter.
- Add per-document cap and top-N configuration.
- Add citation verification pass.
- Add unsupported-claim handling.

Validation:

- Compare retrieval quality before/after rerank on 5-10 curated queries.
- The system refuses or qualifies answers when sources are weak.

### Phase 4: KG Interface And Sample Graph

- Implement `kg/base.py`, `kg/stub.py`, and `kg/__init__.py`.
- Define Neo4j-compatible schema.
- Add sample extracted facts from the PDFs.
- Implement template Cypher queries for material property, application, synthesis, and publication evidence.

Validation:

- The system can answer at least one relation question using the graph path.
- It still works with `KG_ENABLED=false`.

### Phase 5: Graph-Enhanced RAG Fusion

- Combine vector chunks and KG facts in a single prompt.
- Surface graph facts separately in the response.
- Add an optional one-step self-feedback retrieval loop for synthesis queries.

Validation:

- Relation-heavy questions improve with KG enabled.
- Final answer contains citations and graph evidence, not generic statements.

### Phase 6: Frontend Demo

- Build the main Next.js page.
- Stream answer text.
- Show source cards and KG fact panel.
- Add baseline/enhanced mode toggle for presentation.

Validation:

- End-to-end query works from browser to backend.
- Sources and graph paths are visible and understandable.

### Phase 7: Evaluation And Final Report

- Build 20-30 curated questions.
- Run modes A-D and collect results.
- Produce a small table and 2-3 qualitative examples.
- Write final narrative around paper inspirations:
  - OpenScholar: rerank/self-feedback/citation verification
  - KG-FM: LLM-to-JSON-to-Neo4j and Cypher-based retrieval
  - MOF-ChemUnity: material-centric KG, evidence preservation, entity resolution

## Risks And Mitigations

| Risk | Mitigation |
|---|---|
| KG teammate is delayed | Keep `StubGraphRetriever` and build a small sample graph from extracted facts. |
| PDF extraction is noisy | Start with `pdftotext`, keep page metadata, manually curate a few high-value facts, and validate JSON with Pydantic. |
| LLM hallucinated citations | Strict evidence-only prompt plus citation verification and unsupported-claim handling. |
| Scope grows too large | Do not implement full CSD matching, huge corpus ingestion, or full recommendation ML unless the core demo is finished. |
| Reranker setup takes too long | Use LLM rerank fallback or simple metadata/keyword scoring, but keep the rerank interface. |
| API cost / rate limits | Cache extraction and generation results; use cheaper model for routing and extraction tests. |

## Immediate Next Steps

1. Implement backend schemas around `Source`, `Evidence`, `Citation`, `KGFact`, and streamed query events.
2. Implement reference ingestion for the provided PDFs/PPTX and index them into Qdrant.
3. Build baseline vector RAG with inline citations.
4. Add rerank + citation verification before spending too much time on frontend styling.
5. Build a tiny sample KG from 10-20 extracted facts so graph-enhanced behavior can be demonstrated even before full team KG integration.
