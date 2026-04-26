# MOF Knowledge Graph Builder

构建以 MOF 为中心的知识图谱，支持共享节点设计。

## 目录结构

```text
tools/kg_builder/
├── README.md                  # 本文件
├── pyproject.toml             # Python 项目配置
├── requirements.txt           # 依赖
├── src/mof_kg/
│   ├── __init__.py
│   ├── config.py              # 配置（数据路径等）
│   ├── cli.py                 # 命令行工具入口
│   ├── generate_qa_dataset.py # QA 数据集生成
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema.py          # 节点和关系模型定义
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── water_stability.py  # 水稳定性数据提取
│   │   ├── name_mapping.py     # 名称映射数据提取
│   │   └── synthesis.py        # 合成数据提取
│   ├── normalizer/
│   │   ├── __init__.py
│   │   └── precursor.py        # 前驱体名称归一化
│   └── builder/
│       ├── __init__.py
│       ├── graph_builder.py    # 图构建主逻辑
│       └── exporters.py        # 导出器 (JSON/Cypher/GraphML)
├── ../../backend/data/kg/      # 当前配置的输出目录
│   ├── mof_kg.json             # JSON 格式，后端直接读取
│   ├── mof_kg.cypher           # Neo4j Cypher 脚本
│   ├── mof_kg.graphml          # GraphML 格式（可视化）
│   └── dataset/                # 评估数据集和统计信息
│       ├── qa_evaluation_dataset_en.json  # QA 评估数据集
│       └── kg_statistics.json  # KG 统计信息
```

## 当前仓库内使用

```bash
cd /Users/tjzhou/Desktop/AIWorkspace/homework/aiaa-5032-final
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli --help
```

如需以 editable package 形式安装：

```bash
cd /Users/tjzhou/Desktop/AIWorkspace/homework/aiaa-5032-final/tools/kg_builder
pip install -e .
```

## 命令行使用

### 查看帮助

```bash
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli --help
```

### 构建 KG

```bash
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli build
```

输出示例：
```
Building MOF Knowledge Graph...

=== Graph Statistics ===
  mof_nodes: 27,961
  stability_nodes: 2
  precursor_nodes: 22,501
  method_nodes: 5
  doi_nodes: 13,760
  name_nodes: 18,316
  relationships: 218,662

Shared precursors: 6,783
Top 5 most shared precursors:
  H2O: used by 3,738 MOFs
  water: used by 3,146 MOFs
  ...
```

### 查看统计信息

```bash
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli stats
```

### 导出 KG

```bash
# 导出所有格式
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format all

# 只导出 JSON
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format json

# 只导出 Cypher（用于 Neo4j）
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format cypher

# 只导出 GraphML（用于 Gephi/Cytoscape 可视化）
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli export --format graphml
```

### 查询 KG

```bash
# 查找使用特定前驱体的 MOF
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli query --precursor "water"
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.cli query --precursor "Zn(NO3)2⋅6H2O"
```

---

## KG 设计说明

### 设计原则

1. **MOF 为中心节点**：每个 MOF 是图中的核心节点（0-hop）
2. **特性为 1-hop 邻居**：所有 MOF 的特性（名称、稳定性、前驱体等）都是直接连接的 1-hop 邻居
3. **共享节点设计**：前驱体、方法、DOI 等节点被多个 MOF 共享，实现 MOF 之间的间接连接

### 节点类型

| 节点类型 | 说明 | 是否共享 | 属性 |
|----------|------|---------|------|
| MOF | 核心节点 | 否 | refcode, display_name, temperature, time, yield |
| Stability | 水稳定性 | 是 | value (Stable/Unstable), evidence, condition |
| Precursor | 前驱体 | 是 | name, formula, smiles, precursor_type |
| Method | 合成方法 | 是 | name |
| DOI | 文献来源 | 是 | doi |
| Name | 名称/别名 | 否 | name, is_primary |

### 关系类型

| 关系 | 说明 | 方向 |
|------|------|------|
| HAS_STABILITY | 水稳定性 | MOF → Stability |
| USES_METAL_PRECURSOR | 金属前驱体 | MOF → Precursor |
| USES_ORGANIC_PRECURSOR | 有机配体 | MOF → Precursor |
| USES_SOLVENT | 溶剂 | MOF → Precursor |
| USES_METHOD | 合成方法 | MOF → Method |
| HAS_NAME | 名称/别名 | MOF → Name |
| CITED_IN | 文献来源 | MOF → DOI |

### 图结构示意

```
                    Precursor: Zn(NO₃)₂ (共享节点)
                    /                       \
                   /                         \
                  ▼                           ▼
           MOF: UTSA-67                  MOF: MOF-5
                 │                              │
                 ▼                              ▼
          Stability: Stable             Stability: Stable

→ 两个 MOF 通过共享的前驱体节点间接连接
```

---

## 数据来源

KG 从以下三个数据文件构建（位于仓库根目录的 `reference_code/MOF_KG/`）：

| 文件 | 记录数 | 用途 |
|------|--------|------|
| `1.water_stability_chemunity_v0.1.0.csv` | 1,803 | 水稳定性信息 |
| `2.MOF_names_and_CSD_codes.csv` | 15,143 | 名称-标签映射 |
| `3.MOF-Synthesis.json` | 28,989 | 合成路径信息 |

---

## 输出文件说明

| 文件 | 格式 | 用途 |
|------|------|------|
| `backend/data/kg/mof_kg.json` | JSON | 供 RAG 系统直接读取 |
| `backend/data/kg/mof_kg.cypher` | Cypher | 导入 Neo4j 图数据库 |
| `backend/data/kg/mof_kg.graphml` | GraphML | 用 Gephi/Cytoscape 可视化 |
| `backend/data/kg/dataset/kg_statistics.json` | JSON | KG 统计信息摘要 |

---

## Python API 使用

```python
from mof_kg.config import get_config
from mof_kg.builder import GraphBuilder, JSONExporter

# 获取配置
config = get_config()

# 构建 KG
builder = GraphBuilder(config)
data = builder.build()

# 获取统计
stats = builder.get_stats()
print(stats)

# 查找使用特定前驱体的 MOF
mofs = builder.find_mofs_using_precursor(data, "water")
print(f"Found {len(mofs)} MOFs using water")

# 查找共享的前驱体
shared = builder.find_shared_precursors(data)
print(f"Shared precursors: {len(shared)}")

# 导出到 JSON
exporter = JSONExporter(config.kg_output_dir / "mof_kg.json")
exporter.export(data)
```

---

## 导入 Neo4j

1. 启动 Neo4j 数据库
2. 在 Neo4j Browser 中打开 `backend/data/kg/mof_kg.cypher`
3. 执行脚本（或使用 `cypher-shell` 命令行工具）

```bash
# 使用 cypher-shell 导入
cypher-shell -u neo4j -p password < backend/data/kg/mof_kg.cypher
```

---

## 可视化

使用 GraphML 文件在 Gephi 或 Cytoscape 中可视化：

1. 打开 Gephi
2. File → Open → 选择 `backend/data/kg/mof_kg.graphml`
3. 使用布局算法（如 ForceAtlas2）进行可视化

---

## 当前 KG 统计（构建时）

```
节点统计:
  MOF 节点:        27,961
  稳定性节点:      2 (Stable, Unstable)
  前驱体节点:      22,501
    - 金属前驱体:   6,825
    - 有机配体:     12,582
    - 溶剂:         3,094
  方法节点:        5
  DOI 节点:        13,760
  名称节点:        18,316
  
关系统计:
  总关系数:        218,662
  总节点数:        82,545

共享节点统计:
  共享前驱体数:    6,783 (被多个 MOF 使用)
  
Top 5 最共享的前驱体:
  H2O:              3,738 MOFs
  water:            3,146 MOFs
  NaOH:             1,947 MOFs
  DMF:              1,877 MOFs
  aqueous solution: 1,776 MOFs
```

---

## 生成评估数据集

### 生成 QA Pairs

```bash
# 生成 500 个 QA pairs (每种类型 100 个)
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.generate_qa_dataset --count 100

# 指定输出文件名
PYTHONPATH=tools/kg_builder/src python3 -m mof_kg.generate_qa_dataset --count 100 --output my_dataset.json
```

### 数据集类型

| 类型 | 数量 | 描述 |
|------|------|------|
| Type A: Simple Retrieval | 100 | 单 MOF 属性查询 |
| Type B: Entity Linking | 100 | 别名/同义词查询 |
| Type C: Cross-Entity | 100 | 跨 MOF 关联查询 |
| Type D: Multi-hop Reasoning | 100 | 多跳推理查询 |
| Type E: Filtering | 100 | 多条件过滤查询 |

### 数据集说明

生成的数据集默认写入 `backend/data/kg/dataset/`。

## 文件路径参考

| 路径 | 说明 |
|------|------|
| `reference_code/MOF_KG/` | 源数据目录 |
| `backend/data/kg/` | 当前配置的 KG 输出目录 |
| `backend/data/kg/mof_kg.json` | 后端运行时 KG 数据 (JSON) |
| `backend/data/kg/mof_kg.cypher` | KG 数据 (Neo4j Cypher) |
| `backend/data/kg/dataset/` | 评估数据集和统计信息输出目录 |
| `tools/kg_builder/src/mof_kg/` | 源代码目录 |
