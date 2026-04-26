> 归档说明：本文是 KG + RAG 创新方向的历史设计备忘，不是当前项目的待办清单。当前已完成代码和运行方式以 `docs/PLAN.md`、`docs/ARCHITECTURE.md`、`docs/API_CONTRACT.md` 和根目录 `README.md` 为准。

二、创新点分析
2.1 KG + RAG 结合的创新方向

┌─────────────────────────────────────────────────────────────────┐
│                    创新点矩阵                                    │
└─────────────────────────────────────────────────────────────────┘

          ┌─────────────────────────────────────┐
          │RAG Pipeline                         │
          │                                     │
          ▼                                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│Retrieval│   │   Reranking    │   │  Generation    │
│                 │   │                 │   │                 │
│创新点 1: │   │创新点 2:         │   │创新点 3:        │
│Graph-Guided    │   │Graph-Reranker│   │KG-Enhanced      │
│Entity Retrieval│   │                 │   │Prompt           │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │创新点 4:         │
                      │Query Decomposition│
                      │(KG-guided)       │
                      └─────────────────┘
创新点 1: Graph-Guided Entity Retrieval
问题： 传统向量检索对实体名称不敏感

方案： 用 KG 实体节点指导检索


┌─────────────────────────────────────────────────────────────────┐
│          传统 RAG vs Graph-Guided Retrieval                      │
└─────────────────────────────────────────────────────────────────┘

传统 RAG:
用户问题 → Embedding → 向量检索 → 返回相似文档
问题: "UTSA-67 的前驱体" 可能检索不到 "CUVVOG"(refcode)

Graph-Guided:
用户问题 → NER 识别实体 → KG 查询实体节点 → 扩展检索
         "UTSA-67" → KG: 找到 MOF:CUVVOG → 检索时加入 "CUVVOG"
具体实现：


class GraphGuidedRetriever:
    def retrieve(self, query: str) -> list[Document]:
        # Step 1: 实体识别
        entities = self.ner.extract(query)  # ["UTSA-67"]
        
        # Step 2: KG 实体链接
        kg_entities = self.kg.lookup(entities)  # MOF:CUVVOG
        
        # Step 3: 图扩展 (1-hop)
        neighbors = self.kg.get_neighbors(kg_entities)
        # → Precursor: Zn(NO₃)₂, Method: solvothermal...
        
        # Step 4: 增强查询
        expanded_query = query + " " + " ".join(neighbor_terms)
        
        # Step 5: 向量检索
        return self.vector_store.search(expanded_query)
贡献点：

实体链接精度提升
查询扩展基于结构化知识
解决别名/同义词问题
创新点 2: Graph-Based Reranking
问题： 向量检索结果可能不相关，需要重排序

方案： 用 KG 关系计算相关性分数


┌─────────────────────────────────────────────────────────────────┐
│                Graph-Based Reranking                             │
└─────────────────────────────────────────────────────────────────┘

检索结果:
  Doc1: "UTSA-67 uses Zn(NO₃)₂ as metal precursor..."
  Doc2: "MOF-5 is synthesized at 150°C..."
  Doc3: "Cu-based MOFs have good stability..."

问题: "UTSA-67 用了什么金属前驱体？"

Graph Reranking:
  1. 从 KG 找到 UTSA-67 的真实前驱体: Zn(NO₃)₂
  2. 计算每个 Doc 与 KG 事实的重叠度
     - Doc1: 提到 UTSA-67 + Zn(NO₃)₂ → 高分
     - Doc2: 提到 MOF-5 (无关) → 低分
     - Doc3: 提到 Cu (错误金属) → 低分
  3. 重排序后 Doc1 排第一
贡献点：

基于结构化知识的重排序
减少幻觉文档的干扰
可解释性：用 KG 事实验证
创新点 3: KG-Enhanced Prompt Generation
问题： LLM 生成答案可能幻觉，缺乏证据

方案： 把 KG 结构化路径注入 Prompt


┌─────────────────────────────────────────────────────────────────┐
│            KG-Enhanced Prompt                                    │
└─────────────────────────────────────────────────────────────────┘

传统 Prompt:
──────────────────────────────────────────────────────────────────
Context: [检索到的文档片段]

Question: UTSA-67 的水稳定性如何？

Answer:

KG-Enhanced Prompt:
──────────────────────────────────────────────────────────────────
Context: [检索到的文档片段]

Knowledge Graph Facts:
  MOF:UTSA-67 (CUVVOG)
    ├── HAS_NAME → "UTSA-67"
    ├── HAS_STABILITY → Stable
    │└── evidence: "The compound is stable in water..."
    └── USES_METAL_PRECURSOR → Zn(NO₃)₂

Question: UTSA-67 的水稳定性如何？

Answer based on the KG facts and context:
贡献点：

结构化证据减少幻觉
可追溯的知识来源
答案更准确
创新点 4: KG-Guided Query Decomposition
问题： 复杂问题需要多步推理

方案： 用 KG 结构引导问题分解


┌─────────────────────────────────────────────────────────────────┐
│          Query Decomposition Example                             │
└─────────────────────────────────────────────────────────────────┘

复杂问题:
"UTSA-67 用的前驱体还被哪些水稳定性好的 MOF 使用？"

KG-Guided Decomposition:
──────────────────────────────────────────────────────────────────
Step 1: 找 UTSA-67 的前驱体
        KG: MOF:UTSA-67 → USES_METAL_PRECURSOR → Zn(NO₃)₂

Step 2: 找用 Zn(NO₃)₂ 的其他 MOF
        KG: Precursor:Zn(NO₃)₂ ← USES_METAL_PRECURSOR ← MOF列表

Step 3: 过滤水稳定性好的
        KG: MOF列表 → HAS_STABILITY → Stable

Answer: [MOF-5, MOF-177, ...]
贡献点：

自动问题分解
基于 KG 结构的推理路径
可解释的推理过程
创新点 5: Entity Normalization for RAG
问题： 同一实体有多种表述

方案： KG 中的实体归一化


┌─────────────────────────────────────────────────────────────────┐
│              Entity Normalization                                │
└─────────────────────────────────────────────────────────────────┘

问题: "water" 在数据中有多种表述:
  - H2O
  - water  
  - aqueous solution
  - distilled water
  - deionized water

KG 归一化:
  所有这些 → 映射到同一个 Precursor 节点

效果:
  查询 "H2O" → 能检索到所有用 "water" 的 MOF
贡献点：

解决同义词问题
提高召回率
领域特定的归一化规则


三、推荐的创新组合
方案 A: 轻量创新（适合快速验证）

Baseline: Vector RAG + Hybrid Retrieval
──────────────────────────────────────────────────────────────────
创新点:
1. Graph-Guided Entity Retrieval (实体链接 + 查询扩展)
2. KG-Enhanced Prompt (注入结构化事实)

工作量: 中等
创新程度: 够发表
方案 B: 完整创新（适合深入研究）

Baseline: Vector RAG + Hybrid Retrieval
──────────────────────────────────────────────────────────────────
创新点:
1. Graph-Guided Entity Retrieval
2. Graph-Based Reranking
3. KG-Enhanced Prompt
4. Entity Normalization

工作量: 较大
创新程度: 较高
