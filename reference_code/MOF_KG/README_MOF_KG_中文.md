# 面向 MOF 材料的三类知识图谱项目

> 当前状态：本目录是项目/课程提供的 KG 源数据目录。后端运行时会读取 `3.MOF-Synthesis.json` 作为合成 evidence 文档；离线 KG builder 会从本目录三个源文件生成 `backend/data/kg/mof_kg.json`，再由后端 `KGGraphRetriever` 读取。本文档描述数据设计背景，不代表还有未完成的当前开发任务。

本项目围绕金属有机框架材料（MOF, Metal-Organic Framework）构建三类任务导向型知识图谱，目标是提升大语言模型在 **MOF 性能判断、晶体数据库检索、合成路径问答** 等任务中的准确率与可解释性。

当前项目包含以下三类知识图谱：

1. **MOF 水稳定性知识图谱**  
   面向 MOF 材料水稳定性及相关证据构建的知识图谱，用于提高大语言模型对 MOF 水稳定性性能的判断准确率。

2. **MOF–CSD 标签映射知识图谱**  
   面向 MOF 材料名称、别名与 CSD 晶体数据库标签对应关系构建的知识图谱，用于提升大语言模型在晶体数据库中的检索能力。

3. **MOF 合成路径知识图谱**  
   面向 MOF 原始合成记录构建的知识图谱，用于提高大语言模型对 MOF 合成路径、反应条件与前驱体信息问答的准确率。

---

## 项目目标

本项目的核心目标是构建一套结构化的 MOF 知识资源，为以下任务提供支持：

- 面向 MOF 领域的 RAG 检索增强系统；
- 面向大语言模型的结构化知识支撑层；
- 面向性能、标签映射与合成路径的专业问答系统。

与仅依赖非结构化文本不同，本项目将 MOF 相关知识组织为可计算、可检索、可追溯的图结构，从而提升下游模型回答的准确性、稳定性与可解释性。

---

## 三类知识图谱概览

### 1. MOF 水稳定性知识图谱

该知识图谱围绕 MOF 材料的水稳定性表现构建。

#### 目标
用于提升大语言模型在以下问题上的判断能力：

- 某种 MOF 是否具有水稳定性？
- 哪些 MOF 适用于潮湿或水环境？
- 某个稳定性结论的证据来源是什么？

#### 数据来源
该知识图谱基于 **CSV 文件形式的三元组数据** 构建。

#### 典型知识表示
典型三元组模式如下：

```text
MOF -> HAS_WATER_STABILITY -> 稳定/不稳定
MOF -> HAS_STABILITY_EVIDENCE -> 证据文本
MOF -> HAS_SOURCE -> DOI/文献来源
```

#### 作用
该图谱可以帮助大语言模型：

- 更准确地判断 MOF 水稳定性；
- 基于结构化证据生成回答；
- 降低稳定性问答中的幻觉问题。

---

### 2. MOF–CSD 标签映射知识图谱

该知识图谱围绕 MOF 材料与剑桥晶体数据库（CSD, Cambridge Structural Database）标签之间的对应关系构建。

#### 目标
用于提升大语言模型在晶体数据库检索、材料名称归一化和实体对齐方面的能力。

典型问题包括：

- 某个 MOF 对应的 CSD Refcode 是什么？
- 某些材料名称是否指向同一个晶体条目？
- 文本中的 MOF 名称如何映射到数据库中的标准标签？

#### 数据来源
该知识图谱同样基于 **CSV 文件形式的三元组数据** 构建。

#### 典型知识表示
典型三元组模式如下：

```text
MOF_Name -> MAPS_TO_CSD -> CSD_Refcode
MOF -> HAS_ALIAS -> MOF_Name
MOF -> HAS_CSD_LABEL -> CSD_Refcode
CSD_Refcode -> HAS_SOURCE -> DOI/文献来源
```

#### 作用
该图谱可以帮助大语言模型：

- 更准确地完成晶体数据库检索；
- 对 MOF 名称、别名和标签进行统一映射；
- 提高数据库实体链接和检索的准确率。

---

### 3. MOF 合成路径知识图谱

该知识图谱围绕 MOF 材料的合成过程与实验条件构建。

#### 目标
用于提升大语言模型在以下问题上的问答能力：

- 某种 MOF 是如何合成的？
- 使用了哪些金属前驱体和有机前驱体？
- 反应温度、反应时间、操作步骤是什么？
- 合成方法和产率如何？

#### 数据来源
该知识图谱基于 **原始合成记录结构 `3.MOF-Synthesis.json`** 构建。

#### 原始记录结构
`3.MOF-Synthesis.json` 中常见的顶层字段包括：

- `identifier`
- `name`
- `doi`
- `method`
- `M_precursor`
- `O_precursor`
- `S_precursor`
- `operation`
- `temperature`
- `time`
- `Yield`
- `source`

#### 典型知识表示
典型图谱关系可设计为：

```text
MOF -> HAS_SYNTHESIS_METHOD -> 合成方法
MOF -> USES_METAL_PRECURSOR -> 金属前驱体
MOF -> USES_ORGANIC_PRECURSOR -> 有机前驱体
MOF -> USES_STRUCTURE_DIRECTING_COMPONENT -> 结构导向组分
MOF -> HAS_OPERATION -> 操作步骤
MOF -> HAS_TEMPERATURE -> 反应温度
MOF -> HAS_REACTION_TIME -> 反应时间
MOF -> HAS_YIELD -> 产率
MOF -> HAS_SOURCE -> DOI/文献来源
```

#### 作用
该图谱可以帮助大语言模型：

- 更准确地回答 MOF 合成相关问题；
- 检索结构化的合成流程信息；
- 支持前驱体、条件和方法层面的推理与问答。

---

## 数据类型说明

本项目目前使用两类主要数据格式：

### 1. CSV 三元组数据
用于：

- MOF 水稳定性知识图谱
- MOF–CSD 标签映射知识图谱

该类数据通常已经整理为结构化三元组，可直接转换为图谱中的边关系。

常见格式为：

```text
subject, relation, object
```

或者：

```text
start_node, relationship, end_node
```

---

### 2. JSON 结构化记录
用于：

- MOF 合成路径知识图谱

这类数据在原始状态下不是简单三元组，而是包含多个字段的结构化记录，需要进一步转换为图谱中的节点、关系和属性。

---

## 图谱构建思路

三类知识图谱虽然来源不同、粒度不同，但都可以围绕 **MOF 材料实体** 进行统一建模。

### 当前后端实际关系类型

当前 `tools/kg_builder` 导出的 `backend/data/kg/mof_kg.json` 使用以下主要关系类型，并由后端 `KGGraphRetriever` 映射为可展示的 KG facts：

```text
MOF -> HAS_STABILITY -> Stability
MOF -> HAS_NAME -> Name
MOF -> USES_METAL_PRECURSOR -> Precursor
MOF -> USES_ORGANIC_PRECURSOR -> Precursor
MOF -> USES_SOLVENT -> Precursor
MOF -> USES_METHOD -> Method
MOF -> CITED_IN -> DOI
```

后端还会把 `3.MOF-Synthesis.json` 的每一行加载为 `HAS_SYNTHESIS_EVIDENCE` 文档事实，用于合成问答。

### 统一核心实体
三类图谱共享的核心节点为：

- **MOF 材料实体**

### 一体化整合思路
统一后的图谱可以按如下方式组织：

```text
MOF
 ├── HAS_WATER_STABILITY -> 稳定性标签
 ├── HAS_CSD_LABEL -> CSD Refcode
 ├── HAS_ALIAS -> MOF 名称
 ├── HAS_SYNTHESIS_METHOD -> 合成方法
 ├── USES_METAL_PRECURSOR -> 金属前驱体
 ├── USES_ORGANIC_PRECURSOR -> 有机前驱体
 ├── HAS_TEMPERATURE -> 温度
 ├── HAS_REACTION_TIME -> 时间
 └── HAS_SOURCE -> DOI / 文献来源
```

这种组织方式既适合图数据库存储，也适合与向量检索结合，形成图增强的 RAG 系统。

---

## 典型应用场景

### 1. MOF 性能问答
例如：

- UiO-66 是否具有水稳定性？
- 哪些 MOF 更适合在水环境中应用？

### 2. CSD 数据库检索
例如：

- HKUST-1 对应的 CSD Refcode 是什么？
- 某个材料名称是否有多个数据库别名？

### 3. MOF 合成问答
例如：

- 某个 MOF 的合成方法是什么？
- 它使用了哪些前驱体？
- 合成温度和反应时间分别是多少？

### 4. 图增强 RAG
三类图谱还可作为：

- 结构化检索层；
- 大模型的知识支撑层；
- 带证据的问答信息源。

---

## 对大语言模型的预期提升

引入这三类知识图谱后，预期可以从以下三个方面提升大语言模型性能：

### 1. 提高性能判断能力
水稳定性知识图谱可提升模型对 MOF 水稳定性和相关性能问题的判断准确率。

### 2. 提高实体对齐与数据库检索能力
MOF–CSD 标签映射知识图谱可提升模型对材料名称、别名与晶体数据库标签之间的匹配能力。

### 3. 提高合成过程问答能力
MOF 合成路径知识图谱可提升模型对合成流程、前驱体、反应条件等问题的回答准确率。

---

## 可选扩展方向

如果项目重新打开，可以在以下方向上继续扩展；这些不是当前提交的待办：

- 将三类图谱进一步整合为统一的 MOF 综合知识图谱；
- 增加 DOI、证据句子、文献片段等来源节点；
- 打通性能、标签映射与合成路径之间的联系；
- 将图谱检索与向量检索结合，构建混合式 MOF RAG 系统；
- 从 MOF 扩展到 COF、HOF 及更广泛的框架材料体系。

---

## 总结

本项目围绕 MOF 领域构建三类互补的知识图谱：

- **MOF 水稳定性知识图谱**：提升模型对水稳定性性能判断的准确率；
- **MOF–CSD 标签映射知识图谱**：提升模型在晶体数据库中的检索与实体匹配能力；
- **MOF 合成路径知识图谱**：提升模型对 MOF 合成路径和反应条件问答的准确率。

三类图谱分别面向 **性能判断、数据库检索、合成问答** 三个关键任务，为后续构建专业化 MOF RAG 系统和图增强问答系统提供结构化知识基础。
