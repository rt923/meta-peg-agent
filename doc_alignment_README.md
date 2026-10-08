# doc_alignment — 15 件套产物全览

> 基于 doc_alignment 增强块 v0.1（★固化，2026-07-22）
> 本 README 解释 15 个文件之间的层级关系、流转逻辑和构建顺序。

---

## 产物全景图

```
                        ┌─────────────────────────────────┐
                        │  doc_alignment.prompt.md (L0)   │ ← 根：所有规则源头
                        │  D1–D6 规则 + §12/§13 + self_test│
                        └──────────┬──────────────────────┘
                  ┌────────────────┼──────────────────┐
                  ▼                ▼                    ▼
    ┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐
    │  结构化导出 (L1) │  │ 规则速查 (L1) │  │  接入指南 (L1)       │
    │  json            │  │ quickref     │  │  onboarding          │
    └────────┬─────────┘  └──────────────┘  └──────────┬───────────┘
             │                                ┌────────┼──────────┐
             │                                ▼        ▼          ▼
             │                    ┌──────────────┐ ┌────────┐ ┌──────────────┐
             │                    │ TROUBLESHOOT  │ │windows │ │migration     │
             │                    │ × 3 (L2)     │ │_demo   │ │_checklist    │
             │                    └──────────────┘ └────────┘ └──────────────┘
             │
    ┌────────┴─────────┐
    │  验证工具链 (L2)  │
    │  validate.py     │──→ ci.yml ──→ CI/CD 流水线
    │  test_rules.py   │──→ ci.yml
    └────────┬─────────┘
             │
    ┌────────┴─────────┐
    │  CI/CD 层 (L3)   │
    │  ci_timing_report│
    │  ci_timing.json  │
    └──────────────────┘

    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    所有产物 ─ → versions.md / workspace_map.md / capability_registry.md (L4 登记册)
```

---

## 分层详解

### L0: 核心增强块（1 个文件）

| 文件 | 角色 | 内容 |
|---|---|---|
| `prompts/.../doc_alignment.prompt.md` | **根节点** | D1–D6 六条规则定义、§12 反注入、§13 安全锚、7 条 self_test |

**依赖**: 无（L0 是自包含的，不依赖任何其他文件）

**被依赖**: 所有 L1 文件均从此派生

---

### L1: 文档产出物（3 个文件）

| 文件 | 从 L0 转化方式 | 用途 |
|---|---|---|
| `doc_alignment.json` | 结构化导出（JSON 格式） | 供外部工具通过 API 加载规则 |
| `doc_alignment_quickref.md` | 规则速查提取 | 六条规则一句话速查 + 偏差分级表 |
| `doc_alignment_onboarding.md` | 接入流程转化 | 5 步新项目接入流程 + 踩坑表 |

**依赖**: 均直接读取 `doc_alignment.prompt.md`

**被依赖**: 
- `json` → `validate.py`, `test_rules.py`, `ci_timing_report.py`, `migration_checklist.md`
- `onboarding` → `TROUBLESHOOTING.md`, `windows_demo.md`

---

### L2: 踩坑文档链（3 个文件）

| 文件 | 从 L1 转化方式 | 用途 |
|---|---|---|
| `TROUBLESHOOTING.md` | 从 `onboarding.md` 第五节独立提取 | 8 条踩坑详解（症状 + 根因 + 解法） |
| `TROUBLESHOOTING_table.md` | 从 `TROUBLESHOOTING.md` 表格化 | Confluence/Notion 表格版 |
| `TROUBLESHOOTING_raw_tables.md` | 从 `TROUBLESHOOTING.md` 去装饰 | 纯 Markdown 源码（直接粘贴） |

**依赖**: `TROUBLESHOOTING.md` ← `onboarding.md`

**链式关系**: `TROUBLESHOOTING.md` → `table.md` → `raw_tables.md`（不可逆：去装饰后丢失标题和注释）

---

### L2: 演示/迁移文档（2 个文件）

| 文件 | 从 L1 转化方式 | 用途 |
|---|---|---|
| `doc_alignment_windows_demo.md` | `onboarding.md` + `TROUBLESHOOTING.md` 场景模拟 | Windows 环境完整接入演示（18 项检查点） |
| `doc_alignment_migration_checklist.md` | 从 `doc_alignment.json` 规则驱动 | 旧项目迁移评估清单（37 项检查 × 6 维度） |

**依赖**: 
- `windows_demo.md` ← `onboarding.md` + `TROUBLESHOOTING.md`
- `migration_checklist.md` ← `doc_alignment.json`（读 D1–D6 规则生成清单）

---

### L2: 验证工具链（2 个文件）

| 文件 | 读什么 | 做什么 |
|---|---|---|
| `validate_doc_alignment_json.py` | 读取 `doc_alignment.json` | 11 项结构完整性校验（exit_code 0/1） |
| `test_doc_alignment_rules.py` | 读取 `doc_alignment.json` | 38 个 Pytest 用例覆盖 D1–D6 全场景 |

**依赖**: 均直接读取 `doc_alignment.json`

**被依赖**: 
- `validate.py` ← `ci_timing_report.py`（import） + `ci.yml`（called by）
- `test_rules.py` ← `ci.yml`（called by）

---

### L3: CI/CD 层（2 个文件）

| 文件 | 关系 | 触发条件 |
|---|---|---|
| `ci_timing_report.py` | import `validate.py` + 读 `doc_alignment.json` | 手动运行 |
| `.github/workflows/doc_alignment_ci.yml` | 调用 `validate.py` + `test_rules.py` | push/PR 触及相关文件 |

**依赖**: 
- `ci_timing_report.py` ← `validate_doc_alignment_json.py`（import） + `doc_alignment.json`（读）
- `ci.yml` ← `validate_doc_alignment_json.py`（called by） + `test_doc_alignment_rules.py`（called by）

**产出**: `ci_timing_report.py` → `ci_timing_report.json`（机器可读耗时数据）

---

### L4: 登记册（3 个文件）

| 文件 | 角色 | 登记内容 |
|---|---|---|
| `versions.md` | 版本登记册 | 所有 15 个文件的版本号、日期、变更摘要 |
| `workspace_map.md` | 工作区映射 | 所有文件的目录树位置 + 注释 |
| `capability_registry.md` | 能力登记册 | 已知智能体表 + 增强块清单 + 演进信号日志 |

**依赖**: 所有 L0–L3 文件以虚线「登记」关系指向 L4

**交叉引用** (D4): `versions.md` ↔ `workspace_map.md` ↔ `capability_registry.md` 三向对齐

---

## 构建顺序（拓扑排序）

修改某文件时，需按此顺序重新构建下游文件：

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

## 数据流方向

```
实线 →  : 读/derive（数据从源流向目标）
虚线 →  : 登记（元数据写入登记册）
 import  : Python 模块导入
called by: CI/CD 调用
```

| 流向 | 示例 |
|---|---|
| 读/derive | `prompt.md` → `json` → `validate.py` |
| 登记 | `json` ⇢ `versions.md` |
| import | `validate.py` ← `ci_timing_report.py` |
| called by | `validate.py` ← `ci.yml` |

---

## 快速导航

| 我想... | 看这个文件 |
|---|---|
| 了解规则 | `doc_alignment_quickref.md` |
| 接入新项目 | `doc_alignment_onboarding.md` |
| 迁移旧项目 | `doc_alignment_migration_checklist.md` |
| 排查问题 | `TROUBLESHOOTING.md` |
| 集成外部工具 | `doc_alignment.json` |
| 验证 JSON | `python validate_doc_alignment_json.py` |
| 跑测试 | `pytest test_doc_alignment_rules.py -v` |
| 看架构图 | `doc_alignment_architecture.md`（复制 Mermaid 到 mermaid.live） |
| 看 CI 状态 | `.github/workflows/doc_alignment_ci.yml` |

---

> 版本: v0.1 (2026-07-22) | 增强块状态: ★固化 | R9 闸门: 0 CRITICAL