# 语义化版本登记册（Version Registry）

> 对应 `phase0_meta_peg_agent_prompt.md` §10「版本与弃用」。
> 每次提示词结构变更带语义化版本；被新块取代的旧块标记 `deprecated` 并保留过渡期，避免下游智能体断链。
> 阶段 2 将启用自动版本管理与回滚。

---

## PEG-A 自身提示词

| 版本 | 日期 | 变更 | 状态 |
|---|---|---|---|
| v0.1 | 2026-07-13 | 阶段 0 种子提示词（§1–§8）：角色/语气/工作流/工具/规则/自指/场景/IO | archived |
| v0.2 | 2026-07-13 | 新增 §9 多智能体协作、§10 演进预留、§11 被调用场景与时机 | archived |
| v0.3 | 2026-07-13 | 新增 §12 反注入、§13 最底层安全原则 | current |
| v0.4 | 2026-07-13 | 配套产物（os_guardrails / explainability_check / safety_eval / stage1_tool_schema / self_test_template / ARCHITECTURE_BRIEF） | archived |
| v0.5 | 2026-07-14 | **阶段 1 首轮 self_optimize 落地**：§5 新增 R9（自指产物须过 explainability_check 闸门）；diff 见 `drafts/self_modify_001.diff.md` | current |

## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| explainability_check.py | v0.2 | 2026-07-13 | v0.1 漏报 5/10 → 修正正则后 10/10 |
| safety_eval_suite.json | v0.1 | 2026-07-13 | 10 条红队用例 |
| run_safety_regression.py | v0.1 | 2026-07-13 | in-repo CI，10/10 才合入 |
| guardrails_enforce.py | v0.1 | 2026-07-13 | §13 只读锁 + 哈希校验 |
| capability_registry.md | v0.1 | 2026-07-13 | 能力登记册初版 |
| drafts/PEG-2026-07-13-001.md | v0.1 | 2026-07-13 | 首个带 self_test 的范例草案 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| `get_detector()` 等全局单例工厂（参考 toasty-forging-curie.md 重构范式） | — | `create_*` 工厂 + 依赖注入 | 待阶段 2 |
