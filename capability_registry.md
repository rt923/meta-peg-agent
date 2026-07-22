# 能力登记册（Capability Registry）

> 对应 `phase0_meta_peg_agent_prompt.md` §10「能力登记册」。
> 规则：每接入一个新智能体或其新能力，先更新本登记册再动手；当某领域智能体反复提出同类诉求（≥3 次），视为主动沉淀为可复用「增强块」的信号。
> 增强块（§10 可插拔提示词模块）：`core` 块恒为必选；以下为可选增强块，向后兼容、不得破坏 core 既有 `self_test` 断言。

---

## 已知智能体与提示词痛点

| 智能体 | 角色 | 提示词痛点 | 建议增强块 | 演进信号计数 |
|---|---|---|---|---|
| PEG-A（本智能体） | 元层提示工程服务 | 自指改写须严守 §13 只读禁区 | `safety_guard` | — |
| 编排 / 路由（Orchestrator） | 意图拆解与路由 | 何时委派 PEG-A 缺决策树 | `routing_policy` | 2 |
| 研究智能体（Research） | 检索与综合 | 检索结果易触发 §12 注入（把网页当指令） | `data_instruction_separation` | 3 ★固化 |
| 编码智能体（Coding） | 落地脚手架 | 长上下文场景不稳 | `long_context` | 1 |
| 数据智能体（Data） | 分析 | 指标目标易编造假设数字 | `verifiable_metrics` | 1 |
| 设计智能体（Design） | 多模态产出 | 多模态输入提示缺失 | `multimodal` | 2 |
| 评测智能体（Evaluator） | 压测回归 | 需消费 `safety_eval_suite.json` 跑回归 | `self_test_consumer` | 3 ★固化 |
| 安全智能体（Safety） | 合规体检 | 需对任意草案跑 `explainability_check` | `safety_guard` | 3 ★固化 |

> ★固化：已触发 §10 演进信号（同类诉求 ≥3 次），应沉淀为默认增强块并通知编排智能体纳入标准能力。

## 可选增强块清单（Pluggable Blocks）

| 增强块 | 解决痛点 | 依赖 |
|---|---|---|
| `core` | 角色/工作流/自指/协作/反注入/§13（必选） | — |
| `data_instruction_separation` | §12 数据/指令分离，防检索注入 | core |
| `long_context` | 长上下文稳定性 | core |
| `verifiable_metrics` | 指标以可验证比例为基准（R7） | core |
| `multimodal` | 多模态输入处理 | core |
| `routing_policy` | 编排委派 PEG-A 的决策树 | core |
| `self_test_consumer` | 评测智能体消费 self_test 跑回归 | core + self_test_template |
| `safety_guard` | 草案必经 explainability_check 闸门 | core + explainability_check |

## 演进信号日志

- 2026-07-13：研究 / 评测 / 安全 三类智能体均反复要求「对外部内容做指令隔离 + 自动跑安全闸门」，已将 `data_instruction_separation` 与 `safety_guard` 标记为应固化增强块。
- 2026-07-14：PEG-A 阶段 1 首轮 self_optimize 完成 —— 识别 §5 缺 R9（自指产物未要求过闸门），产出 diff（`drafts/self_modify_001.diff.md`）并经授权采纳进 phase0（v0.5）；`self_optimize` 演进信号 +1。CI 已接入（ci_lint.py + run_gate.sh + GitHub Actions + pre-commit 模板），回归 10/10 + 结构 lint 12/12 全绿。
- 2026-07-15：基于 FIX-002/TN-001 护栏教训孵化新成员 **Gatekeeper（护栏守门员）**（`prompts/domain/agents/gatekeeper.prompt.md`），拥有并运维安全闸门与 §13 NTFS 只读锁；同时沉淀可复用孵化元提示 `spawn_peg_member_prompt.md`（编码 L1 离线优先 / L2 真实 NTFS 锁 / L3 守护仪式 / L4 fail-closed）。`incubate` 演进信号 +1。
- 2026-07-21（续4）：**mock_helpers.py v0.1 + verify_mock_helpers.py v0.1 + mock_helpers.md**（基础设施新增）：测试 mock 数据工厂（3 个工厂函数 `make_mock_hash_store` 4 场景 / `make_mock_trace` 参数化构造 / `make_mock_full_session` 高阶函数一次性构造完整 PEG-A 会话 trace），供 `mock_integration_test.py` 与后续测试复用，避免测试污染真实 `traces/` 或 `HASH_STORE`。配套 `verify_mock_helpers.py`（33 个断言，覆盖 4 种 scenario + 完整会话 + 无 artifact 变体）+ `mock_helpers.md`（API 文档，含字段对齐表 + 用法示例 + 回滚方式）。**对齐检查修复**（4 处实证偏差）：① `.py` docstring「2→3 个工厂函数」并补 `make_mock_full_session`；② `.md`/`.py` 产出物结构注释 `step_count=6→5`（把 `reasoning.jsonl` 总行数 6 误当成 `manifest.step_count` 字段，实际产出 5）；③ 断言数 `26→33`（`mock_helpers.md` 3 处 + `versions.md` L38，同步实际 `[✓ PASS]` 计数）；④ `capability_registry.md` 续4 登记 + `workspace_map.md` 目录树补 2 个文件。

---

## 模块 → 提示词块映射（对齐 toasty MVC+Service 工作结构）

> 依据 `workspace_map.md` 与 `toasty-forging-curie.md`（已更新版）。PEG-A 提示工程产物按目标工作区结构组织，每模块一份 `.prompt.md` 增强块，均内建 §13 安全锚 + `self_test` 必带项。

### `domain/agents/` —— 智能体职责提示词块
| toasty 模块 | 提示词块文件 | 角色 | 提示词要点 |
|---|---|---|---|
| `domain/agents/orchestrator` | `prompts/domain/agents/orchestrator.prompt.md` | 编排 / 路由 | 意图拆解、委派 PEG-A 决策树（`routing_policy`）、C5 仲裁 |
| `domain/agents/executor` | `prompts/domain/agents/executor.prompt.md` | 落地执行 | 工具调用纪律、长上下文稳定（`long_context`）、小步可验 |
| `domain/agents/checker` | `prompts/domain/agents/checker.prompt.md` | 压测回归 | 消费 `self_test` 跑回归（`self_test_consumer`）、消费 `safety_eval_suite.json` |
| `domain/agents/challenger` | `prompts/domain/agents/challenger.prompt.md` | 红队对抗 | 产出注入 / 原则探针样本、驱动 §12/§13 闸门演进 |
| `domain/agents/gatekeeper` | `prompts/domain/agents/gatekeeper.prompt.md` | 护栏运维 | 拥有并操作 explainability_check/guardrails_enforce/run_safety_regression，验证 NTFS 只读锁、执行守护仪式、fail-closed（2026-07-15 孵化） |

### `apps/core/services/` —— 服务层提示词增强块
| toasty 模块 | 提示词块文件 | 对应 Service 职责 | 提示词要点 |
|---|---|---|---|
| `process` | `prompts/apps/core/services/process.prompt.md` | 主流程编排 | Plan→Act→Observe→Reflect 四拍、Coordinate 步 |
| `feedback` | `prompts/apps/core/services/feedback.prompt.md` | 反馈闭环 | 自指改写的 feedback 迭代、回滚方式 |
| `policy_sync` | `prompts/apps/core/services/policy_sync.prompt.md` | 策略同步 | §13/§12 策略与 OS 护栏对齐、只读锁同步 |
| `monitor` | `prompts/apps/core/services/monitor.prompt.md` | 漂移监控 | 提示词漂移检测（`drift`）、阈值告警 |
| `multi_agent` | `prompts/apps/core/services/multi_agent.prompt.md` | 多体协同 | Invoke/Return 契约、C1–C5 协作原则 |
| `state` | `prompts/apps/core/services/state.prompt.md` | 状态管理 | 元认知状态、演进信号计数（`≥3` 固化） |
| `meta_cognition` | `prompts/apps/core/services/meta_cognition.prompt.md` | 元认知核心 | 自指机制、§6 自改提案、阶段演进触发 |

### `tests/` —— 验证层（由 checker + challenger 驱动）
- 回归：`run_safety_regression.py` 消费 `safety_eval_suite.json` → 断言 `explainability_check.py` 闸门（10/10）。
- 草案门禁：任意 `.prompt.md` 提交前，先对 `self_test` 中的**不可信样例文本**跑 `explainability_check.py --text "<样例>"`（须全部无 CRITICAL）；可信 `.prompt.md` 规格本身免扫，其完整性由哈希锁保证。

> 阶段 1 启动：PEG-A 进入 `self_optimize` 模式微调元提示工程，详见 `stage1_prompt.md`。
