# doc_alignment 15 件套产物架构图

> 基于 doc_alignment 增强块 v0.1（★固化，2026-07-22）
> 渲染方式：复制下方 Mermaid 代码到 [Mermaid Live Editor](https://mermaid.live) 或 VS Code 的 Mermaid 预览插件。

---

## 完整依赖关系图

```mermaid
flowchart TD
    %% ═══════════════════════════════════════════
    %% 根节点：核心增强块
    %% ═══════════════════════════════════════════
    ROOT["📄 doc_alignment.prompt.md<br/>完整增强块<br/>（D1–D6 规则 + §12/§13 + self_test）"]
    style ROOT fill:#1a1a2e,stroke:#e94560,color:#fff,stroke-width:3px

    %% ═══════════════════════════════════════════
    %% 第一层：二级派生（结构化导出 + 速查）
    %% ═══════════════════════════════════════════
    JSON["📦 doc_alignment.json<br/>结构化 JSON 导出<br/>（外部工具集成）"]
    QUICK["📋 doc_alignment_quickref.md<br/>六条规则速查<br/>（偏差分级 + 工作流）"]
    ONBOARD["🚀 doc_alignment_onboarding.md<br/>新项目接入指南<br/>（5 步流程 + 踩坑表）"]
    style JSON fill:#16213e,stroke:#0f3460,color:#e0e0e0
    style QUICK fill:#16213e,stroke:#0f3460,color:#e0e0e0
    style ONBOARD fill:#16213e,stroke:#0f3460,color:#e0e0e0

    ROOT -->|"结构化导出"| JSON
    ROOT -->|"规则速查提取"| QUICK
    ROOT -->|"接入流程转化"| ONBOARD

    %% ═══════════════════════════════════════════
    %% 第二层：踩坑文档链（接入指南 → 踩坑详细 → 表格 → 纯表格）
    %% ═══════════════════════════════════════════
    TROUBLE["🐛 TROUBLESHOOTING.md<br/>8 条踩坑详解<br/>（症状 + 根因 + 解法）"]
    TROUBLE_TBL["📊 TROUBLESHOOTING_table.md<br/>表格版<br/>（速查表 + 诊断流程）"]
    TROUBLE_RAW["📝 TROUBLESHOOTING_raw_tables.md<br/>纯 Markdown 源码<br/>（直接粘贴）"]
    style TROUBLE fill:#0f3460,stroke:#533483,color:#e0e0e0
    style TROUBLE_TBL fill:#0f3460,stroke:#533483,color:#e0e0e0
    style TROUBLE_RAW fill:#0f3460,stroke:#533483,color:#e0e0e0

    ONBOARD -->|"第五节独立提取"| TROUBLE
    TROUBLE -->|"表格化"| TROUBLE_TBL
    TROUBLE -->|"去装饰纯源码"| TROUBLE_RAW

    %% ═══════════════════════════════════════════
    %% 第三层：演示文档（接入指南 + 踩坑 → Windows 场景）
    %% ═══════════════════════════════════════════
    WIN_DEMO["🪟 doc_alignment_windows_demo.md<br/>Windows 环境完整演示<br/>（18 项检查点 + win-utils 模拟）"]
    MIGRATE["✅ doc_alignment_migration_checklist.md<br/>旧项目迁移评估清单<br/>（37 项检查 × 6 维度）"]
    style WIN_DEMO fill:#0f3460,stroke:#533483,color:#e0e0e0
    style MIGRATE fill:#0f3460,stroke:#533483,color:#e0e0e0

    ONBOARD -->|"Windows 场景模拟"| WIN_DEMO
    TROUBLE -->|"系统级坑引用"| WIN_DEMO
    JSON -->|"D1–D6 规则驱动"| MIGRATE

    %% ═══════════════════════════════════════════
    %% 第四层：验证工具链（JSON → 校验脚本 → 单元测试）
    %% ═══════════════════════════════════════════
    VALIDATE["🔍 validate_doc_alignment_json.py<br/>JSON 加载校验<br/>（11 项检查）"]
    TEST["🧪 test_doc_alignment_rules.py<br/>Pytest 单元测试<br/>（38 用例 × 13 类）"]
    style VALIDATE fill:#1b4332,stroke:#2d6a4f,color:#e0e0e0
    style TEST fill:#1b4332,stroke:#2d6a4f,color:#e0e0e0

    JSON -->|"读取并校验结构"| VALIDATE
    JSON -->|"读取规则定义"| TEST

    %% ═══════════════════════════════════════════
    %% 第五层：CI/CD 层（流水线 + 耗时报告）
    %% ═══════════════════════════════════════════
    CI["⚙️ .github/workflows/doc_alignment_ci.yml<br/>CI/CD 流水线<br/>（push/PR → 校验 + 闸门 + 回归）"]
    TIMING_PY["⏱️ ci_timing_report.py<br/>CI/CD 耗时报告生成器<br/>（11 项微基准 + 瓶颈分析）"]
    TIMING_JSON["📈 ci_timing_report.json<br/>耗时报告数据<br/>（机器可读）"]
    style CI fill:#2d6a4f,stroke:#40916c,color:#e0e0e0
    style TIMING_PY fill:#2d6a4f,stroke:#40916c,color:#e0e0e0
    style TIMING_JSON fill:#2d6a4f,stroke:#40916c,color:#e0e0e0

    VALIDATE -->|"被 CI 调用"| CI
    TEST -->|"被 CI 调用"| CI
    VALIDATE -->|"import 并逐项计时"| TIMING_PY
    JSON -->|"读取数据"| TIMING_PY
    TIMING_PY -->|"生成"| TIMING_JSON

    %% ═══════════════════════════════════════════
    %% 第六层：登记册（所有产物最终汇聚）
    %% ═══════════════════════════════════════════
    REGISTRY["📚 capability_registry.md<br/>能力登记册<br/>（4 处登记：已知智能体 / 增强块清单 / 演进信号 × 2）"]
    VERSIONS["📅 versions.md<br/>版本登记册<br/>（15 条 doc_alignment 条目）"]
    WS_MAP["🗺️ workspace_map.md<br/>工作区映射<br/>（19 行 doc_alignment 目录树）"]
    style REGISTRY fill:#533483,stroke:#7b2ff7,color:#e0e0e0
    style VERSIONS fill:#533483,stroke:#7b2ff7,color:#e0e0e0
    style WS_MAP fill:#533483,stroke:#7b2ff7,color:#e0e0e0

    ROOT -.->|"登记"| REGISTRY
    JSON -.->|"登记"| VERSIONS
    ONBOARD -.->|"登记"| VERSIONS
    TROUBLE -.->|"登记"| VERSIONS
    VALIDATE -.->|"登记"| VERSIONS
    TEST -.->|"登记"| VERSIONS
    CI -.->|"登记"| VERSIONS
    MIGRATE -.->|"登记"| VERSIONS
    VERSIONS -.->|"D4 交叉引用"| WS_MAP
    VERSIONS -.->|"D4 交叉引用"| REGISTRY
    WS_MAP -.->|"D4 交叉引用"| REGISTRY

    %% ═══════════════════════════════════════════
    %% 图例
    %% ═══════════════════════════════════════════
    subgraph LEGEND["图例"]
        L1["核心增强块"]:::legendCore
        L2["文档产出物"]:::legendDoc
        L3["工具/脚本"]:::legendTool
        L4["CI/CD 层"]:::legendCI
        L5["登记册"]:::legendReg
    end
    classDef legendCore fill:#1a1a2e,stroke:#e94560,color:#fff
    classDef legendDoc fill:#16213e,stroke:#0f3460,color:#e0e0e0
    classDef legendTool fill:#1b4332,stroke:#2d6a4f,color:#e0e0e0
    classDef legendCI fill:#2d6a4f,stroke:#40916c,color:#e0e0e0
    classDef legendReg fill:#533483,stroke:#7b2ff7,color:#e0e0e0
```

---

## 分层架构视图

```mermaid
flowchart LR
    subgraph L0["L0: 核心增强块"]
        A["doc_alignment.prompt.md"]
    end

    subgraph L1["L1: 文档产出物"]
        B["json / quickref / onboarding"]
        C["TROUBLESHOOTING × 3"]
        D["windows_demo / migration"]
    end

    subgraph L2["L2: 验证工具"]
        E["validate_doc_alignment_json.py"]
        F["test_doc_alignment_rules.py"]
    end

    subgraph L3["L3: CI/CD"]
        G["doc_alignment_ci.yml"]
        H["ci_timing_report.py → .json"]
    end

    subgraph L4["L4: 登记册"]
        I["capability_registry.md"]
        J["versions.md"]
        K["workspace_map.md"]
    end

    L0 --> L1
    L0 --> L2
    L2 --> L3
    L1 -.-> L4
    L2 -.-> L4
    L3 -.-> L4
```

---

## 数据流向图（读/写/引用）

```mermaid
flowchart LR
    subgraph 数据源
        PROMPT["prompt.md<br/>（D1–D6 规则）"]
    end

    subgraph 文档产出
        JSON_D["json"]
        QUICK_D["quickref"]
        ONBOARD_D["onboarding"]
        TROUBLE_D["TROUBLESHOOTING × 3"]
        DEMO_D["windows_demo"]
        MIG_D["migration"]
    end

    subgraph 工具层
        VAL_D["validate.py"]
        TEST_D["test_rules.py"]
        TIMING_D["timing_report.py"]
    end

    subgraph 登记层
        REG_D["capability_registry"]
        VER_D["versions"]
        WSM_D["workspace_map"]
    end

    PROMPT -->|"read: 规则定义"| JSON_D
    PROMPT -->|"read: 提取速查"| QUICK_D
    PROMPT -->|"read: 转化流程"| ONBOARD_D
    ONBOARD_D -->|"read: 第五节"| TROUBLE_D
    ONBOARD_D -->|"read: 场景模拟"| DEMO_D
    JSON_D -->|"read: 规则驱动"| MIG_D
    JSON_D -->|"read: 结构校验"| VAL_D
    JSON_D -->|"read: 规则定义"| TEST_D
    JSON_D -->|"read: 数据源"| TIMING_D
    VAL_D -->|"import"| TIMING_D
    VAL_D -->|"called by"| GITHUB["ci.yml"]
    TEST_D -->|"called by"| GITHUB

    JSON_D -.->|"write: 登记"| VER_D
    ONBOARD_D -.->|"write: 登记"| VER_D
    VAL_D -.->|"write: 登记"| VER_D
    VER_D -.->|"D4: 交叉引用"| REG_D
    VER_D -.->|"D4: 交叉引用"| WSM_D
```

---

## 产物拓扑排序（构建顺序）

```
1.  doc_alignment.prompt.md          ← 根，所有规则源头
2.  doc_alignment.json               ← 从 1 结构化导出
3.  doc_alignment_quickref.md        ← 从 1 提取速查
4.  doc_alignment_onboarding.md      ← 从 1 转化流程
5.  TROUBLESHOOTING.md               ← 从 4 第五节独立
6.  TROUBLESHOOTING_table.md         ← 从 5 表格化
7.  TROUBLESHOOTING_raw_tables.md    ← 从 5 去装饰
8.  doc_alignment_windows_demo.md    ← 从 4+5 场景模拟
9.  doc_alignment_migration_checklist.md ← 从 2 规则驱动
10. validate_doc_alignment_json.py   ← 从 2 读取校验
11. test_doc_alignment_rules.py      ← 从 2 读取规则
12. ci_timing_report.py              ← 从 10 import + 从 2 读取
13. ci_timing_report.json            ← 从 12 生成
14. .github/workflows/doc_alignment_ci.yml ← 调用 10+11
15. capability_registry.md           ← 从 1-14 登记
    versions.md                      ← 从 1-14 登记
    workspace_map.md                 ← 从 1-14 登记
```

---

> 复制上方 Mermaid 代码到 [mermaid.live](https://mermaid.live) 即可渲染交互式图表。