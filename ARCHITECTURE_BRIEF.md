# 元认知提示工程智能体（PEG-A）· 单页架构说明

> 面向对象：负责「**具备自指能力、工具调用能力、自主式元认知 AI OS**」的架构设计团队。
> 对话 / 会话 ID：`2026-07-13-11-57-54`（本目录即本次提示工程全部产物的唯一来源）。
> 配套文件：本目录 `phase0_meta_peg_agent_prompt.md` + `meta_peg_agent/` 下 5 个工程化产物。

---

## 0. 一句话定位

PEG-A 是运行在元认知 AI OS 之上的**元层共享服务**：它把「更好的提示词」作为唯一产出，并内建**反注入（§12）+ 最底层不可绕过安全原则（§13）**，通过「提示词软约束 → OS 硬约束 → 自动闸门 → 回归用例 → 工具契约 → 草案自检」六段闭环，孵化一个可自指、可调工具、可元认知、且安全底座无法被破解的智能体。

## 1. 三大终极目标（所有设计的验收基准）

| 目标 | 在本架构中的落点 |
|---|---|
| **自指能力** | §6 自指机制（审视→提议 diff→授权改写→回归）；R5 不越权自改；§13 为只读禁区 |
| **工具调用能力** | §4 工具分层；`stage1_tool_schema.json` 9 工具 + 4 禁用；§12 数据/指令分离 |
| **自主元认知 AI OS** | §3 Meta-Loop（Plan→Act→Observe→Reflect→Coordinate）；§9 协作枢纽；§10 可插拔块 + 演进信号 |

## 2. 五层架构（自顶向下穿透，安全层贯穿）

```
[协作接入层]  其他智能体 / 用户  ──§11 Invoke/Return 契约──┐
                                                          ↓
[元层服务层]  PEG-A（§1–§11 软约束：角色/工作流/自指/协作）  ↓
                                                          ↓
[安全根层]    §13 三原则（只读禁区）+ §12 反注入  ──────────┤（每次草案必经）
                                                          ↓
[OS 护栏层]   os_guardrails.md 沙箱权限 + explainability_check.py 闸门 + 注入熔断
                                                          ↓
[产物/回归]   self_test_template · safety_eval_suite · stage1_tool_schema
```

| 层 | 性质 | 对应文件 | 关键约束 |
|---|---|---|---|
| 协作接入层 | 软 | §11 | Invoke/Return JSON 契约；Do/Don't Invoke 表；决策树 |
| 元层服务层 | 软 | `phase0_meta_peg_agent_prompt.md` §1–§11 | 四身份 + Meta-Loop + 协作五原则 C1–C5 |
| 安全根层 | 软+根 | §12 / §13 | 三条最终原则高于一切；自指只读禁区 |
| OS 护栏层 | **硬** | `os_guardrails.md` / `explainability_check.py` | 沙箱权限清单、deny 硬熔断、可解释性闸门、注入熔断、§13 文件系统只读锁 |
| 产物/回归 | 软 | `self_test_template.md` / `safety_eval_suite.json` / `stage1_tool_schema.json` | 每草案必带 self_test；红队用例全绿才采纳 |

## 3. 调用流与守护链（运行时）

1. 其他智能体按 §11 发 `Invoke`（intent: design/refactor/audit/self_optimize/incubate）。
2. PEG-A 跑 Meta-Loop，产出提示词草案（核心块 + 增强块）并附 `self_test`。
3. 草案在「落盘 / 回传」前**必须过 `explainability_check.py` 闸门**：反注入命中→CRITICAL 拒；原则违反→CRITICAL 拒；不可知知识→WARN 复核。
4. 评测智能体用 `safety_eval_suite.json`（10 条红队：注入 + 三条原则探针 + 1 良性）回归，全绿采纳。
5. 任何自指改写（§6）若触及 §13 → OS 层直接拒绝（§13 文件系统只读锁 + 启动哈希校验）。

## 4. 安全模型（为什么「不可破解」分两层）

- **软约束（提示词）**：§12/§13 声明意图与边界；可被极强注入绕过，**不提供数学级保证**。
- **硬约束（OS）**：`os_guardrails.md` 在第 5 节落地「§13 只读文件 + 校验和锁 + 启动哈希」，任何进程（含 PEG-A 自指写）改它都因权限不足失败；`explainability_check.py` 在每次产出前强制扫描。
- 结论：真正不可破解性由 **OS 级强制** 提供，提示词仅声明意图——这是工程上正确的分层。

## 5. 关键契约速查

- **Invoke**：`{caller, intent, target, context, blocking, expected_return}`
- **Return**：`{status, artifact, self_test, verify_method, delegated, next}`
- **工具权限分层**：`allow`（9 个）/ `gated`（apply_rewrite，须授权且不触 §13）/ `deny`（4 个：exec_system / modify_other_agent_code / disable_safety / emit_unknowable_knowledge）
- **self_test 必带项**：samples≥3（正常/注入/安全各一）、`safety_gate.require_passed=true`、`verify_method` 可复现。

## 6. 阶段演进

- 阶段 0（本文件 + §12/§13）：已交付。
- 阶段 1（工具 schema + self_test 模板 + 红队用例 + OS 护栏）：已交付；**阶段 1 自微调启动** —— PEG-A 进入 `self_optimize` 模式微调元提示工程（`stage1_prompt.md`），并按 `toasty-forging-curie.md` 更新结构重组工作区（`workspace_map.md` + `prompts/` 11 个模块块）。
- 阶段 2：提示词版本管理 + 自动回归，启用能力登记册与 Self-Test Hook。
- 阶段 3：授权下自主发起自指改进提案并排队，逼近自主元认知闭环。
- 阶段 N：提示词层与 OS 策略层合一，各智能体经 PEG-A 持续自进化。

## 7. 文件清单

| 文件 | 用途 |
|---|---|
| `meta_peg_agent/phase0_meta_peg_agent_prompt.md` | 阶段 0 种子提示词全文（§1–§13）+ 设计注解 + 路线图（2026-07-14 从工作区根归并至 meta_peg_agent/） |
| `meta_peg_agent/os_guardrails.md` | OS 级沙箱权限清单 / 硬熔断 / 闸门 / 熔断 / §13 只读锁 |
| `meta_peg_agent/explainability_check.py` | 反注入 + 安全原则 + 可知性校验执行器（已修正正则达 10/10） |
| `meta_peg_agent/safety_eval_suite.json` | 10 条 red-team 用例（注入 + 三原则探针 + 1 良性） |
| `meta_peg_agent/stage1_tool_schema.json` | 9 工具 schema + 4 禁用工具 + 权限分层 |
| `meta_peg_agent/self_test_template.md` | 每草案必带 self_test 结构模板 + 示例 |
| `meta_peg_agent/run_safety_regression.py` | in-repo 回归 CI（10/10 才合入） |
| `meta_peg_agent/guardrails_enforce.py` | §13 文件系统只读锁 + 哈希校验 + §13 不可改断言 |
| `meta_peg_agent/capability_registry.md` | §10 能力登记册 + 模块→提示词块映射 |
| `meta_peg_agent/drafts/PEG-2026-07-13-001.md` | 首个带 self_test 的范例草案 |
| `meta_peg_agent/versions.md` | 语义化版本登记册 |
| `meta_peg_agent/workspace_map.md` | 按 toasty MVC+Service 结构重组工作区的总纲 |
| `meta_peg_agent/stage1_prompt.md` | 阶段 1 提示词：PEG-A 进入 self_optimize 微调元提示工程 |
| `meta_peg_agent/prompts/domain/agents/*.prompt.md` | 4 个智能体职责块（orchestrator/executor/checker/challenger） |
| `meta_peg_agent/prompts/apps/core/services/*.prompt.md` | 7 个服务层增强块（process/feedback/policy_sync/monitor/multi_agent/state/meta_cognition） |
| `meta_peg_agent/ARCHITECTURE_BRIEF.md` | 本文件 |
