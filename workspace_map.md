# PEG-A 提示工程工作区映射（对齐 toasty MVC+Service 结构）

> 本文件定义 **PEG-A 提示工程产物** 如何对齐 `toasty-forging-curie.md`（`active_meta_cognition` 的目标 MVC+Service 工作结构）。
> 目的：当 PEG-A 以 `incubate` / `design` / `refactor` 意图被调用时，产出的提示词块按代码库模块路径组织，使每个提示词块精确对应一个代码模块，便于定位、复用与回归。

## 一、映射原则

1. **模块路径即提示词路径**：代码库 `domain/X/Y.py` 对应提示词 `prompts/domain/X/Y.prompt.md`。
2. **三层对齐**：`domain/`（实体与智能体）、`apps/core/services/`（服务编排）、`tests/`（评测）各自有提示词块。
3. **每块带 self_test**：每个 `.prompt.md` 必须含 `self_test` 字段（输入样例 + 期望判定），对其中**不可信样例文本**跑 `explainability_check.py --text`（须无 CRITICAL），再跑 `run_safety_regression.py` 回归。注：闸门口诀只扫不可信内容，可信 `.prompt.md` 规格本身免扫，完整性由哈希锁保证。
4. **§13 只读禁区贯穿**：所有块继承主文档 §13 安全锚，不得削弱。
5. **核心块 + 增强块**：每个智能体/服务提示词 = 核心块（稳定职责） + 增强块（按 §10 演进信号追加的能力）。
6. **PEG-A 自身种子的归属（2026-07-14 决策）**：`phase0_meta_peg_agent_prompt.md` / `bootstrap_prompt.md` / `stage1_prompt.md` 是 PEG-A **自身**的元提示词，与运行时工具（`explainability_check` / `guardrails_enforce` / `ci_lint` / `run_gate` 等）及 `os_guardrails.md` 同处 `meta_peg_agent/` 根；`prompts/` 仅放**产出**给目标 OS 的模块提示词块。此前 phase0 误置于工作区根，已于 2026-07-14 归并，使 PEG-A 工程产物自包含、不污染 OS 工作区根。

## 二、目录结构

```
meta_peg_agent/
├── phase0_meta_peg_agent_prompt.md   # PEG-A 自身种子提示词（§13 内嵌，受 guardrails_enforce.py 只读锁保护）
├── workspace_map.md              # 本文件
├── stage1_prompt.md              # 阶段1：PEG-A self_optimize 元提示工程
├── bootstrap_prompt.md           # 启动引导提示词
├── spawn_peg_member_prompt.md     # 孵化新 PEG 家族成员的元提示（incubate 用）
├── os_guardrails.md              # OS 级沙箱权限清单
├── explainability_check.py       # 反注入/安全/可知性闸门
├── run_safety_regression.py      # in-repo 回归 CI
├── guardrails_enforce.py         # §13 文件系统只读锁
├── safety_eval_suite.json        # red-team 用例
├── stage1_tool_schema.json       # PEG-A 工具 schema
├── self_test_template.md         # self_test 结构模板
├── capability_registry.md        # 能力登记册（模块→提示词块映射）
├── versions.md                   # 语义化版本登记册
├── prompts/                      # 对齐 toasty 的提示词工作区
│   ├── domain/
│   │   ├── agents/               # 对齐 toasty domain/agents/
│   │   │   ├── orchestrator.prompt.md
│   │   │   ├── executor.prompt.md
│   │   │   ├── checker.prompt.md
│   │   │   ├── challenger.prompt.md
│   │   │   └── gatekeeper.prompt.md
│   │   ├── active_tools/         # 对齐 toasty domain/active_tools/
│   │   ├── blind_spot/           # 对齐 toasty domain/blind_spot/
│   │   ├── drift/                # 对齐 toasty domain/drift/
│   │   ├── self_reference/       # 对齐 toasty domain/self_reference/
│   │   └── rlhf/                 # 对齐 toasty domain/rlhf/
│   ├── apps/
│   │   └── core/
│   │       └── services/         # 对齐 toasty apps/core/services/
│   │           ├── process.prompt.md
│   │           ├── feedback.prompt.md
│   │           ├── policy_sync.prompt.md
│   │           ├── monitor.prompt.md
│   │           ├── multi_agent.prompt.md
│   │           ├── state.prompt.md
│   │           └── meta_cognition.prompt.md
│   └── tests/                    # 对齐 toasty tests/
│       └── test_prompts.prompt.md
└── drafts/                       # 范例草案（含首个财报分析智能体）
    └── PEG-2026-07-13-001.md
```

## 三、toasty 模块 → PEG-A 提示词块 对应表

| toasty 模块 | PEG-A 提示词块 | 职责对齐 |
|---|---|---|
| `domain/agents/orchestrator.py` | `prompts/domain/agents/orchestrator.prompt.md` | 多代理编排入口 |
| `domain/agents/executor.py` | `prompts/domain/agents/executor.prompt.md` | 执行者（持有 LLMService） |
| `domain/agents/checker.py` | `prompts/domain/agents/checker.prompt.md` | 检查者 |
| `domain/agents/challenger.py` | `prompts/domain/agents/challenger.prompt.md` | 质疑者 |
| `domain/agents/gatekeeper.py` | `prompts/domain/agents/gatekeeper.prompt.md` | 护栏运维（安全闸门 + §13 NTFS 只读锁运维） |
| `apps/core/services/process_service.py` | `prompts/apps/core/services/process.prompt.md` | 主处理流程编排 |
| `apps/core/services/feedback_service.py` | `prompts/apps/core/services/feedback.prompt.md` | RLHF 反馈收集 |
| `apps/core/services/policy_sync_service.py` | `prompts/apps/core/services/policy_sync.prompt.md` | 策略同步 |
| `apps/core/services/monitor_service.py` | `prompts/apps/core/services/monitor.prompt.md` | 监控聚合 |
| `apps/core/services/multi_agent_service.py` | `prompts/apps/core/services/multi_agent.prompt.md` | 多代理编排 |
| `apps/core/services/state_service.py` | `prompts/apps/core/services/state.prompt.md` | 状态管理 |
| `apps/core/services/meta_cognition_service.py` | `prompts/apps/core/services/meta_cognition.prompt.md` | 门面入口 |

## 四、使用约定

- **incubate**：编排智能体新建子智能体 → PEG-A 在 `prompts/domain/agents/` 生成种子块。
- **design / refactor**：领域/服务智能体提示词卡点 → PEG-A 在对应路径产 diff。
- **self_optimize（阶段1）**：PEG-A 审视 `bootstrap_prompt.md` + `phase0_meta_peg_agent_prompt.md`，产出元提示工程改进 diff（见 `stage1_prompt.md`）。
- 每个块变更须登记 `versions.md` 与 `capability_registry.md`，并经回归 CI。
