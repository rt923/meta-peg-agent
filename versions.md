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
| v0.5 | 2026-07-14 | **阶段 1 首轮 self_optimize 落地**：§5 新增 R9（自指产物须过 explainability_check 闸门）；diff 见 `drafts/self_modify_001.diff.md` | archived |
| v0.6 | 2026-07-21 | **peg_trace.py 接入主流程**：§3 末尾追加 Meta-Loop trace 持久化说明；§4 末尾追加 trace 持久化类；§11.4.1 新增 Return 前 save_artifact 步骤；diff 见 `drafts/self_modify_002.diff.md`，R9 闸门准入（passed:true, 0 alerts, 0 CRITICAL）；已应用（11606→12623 字节）+ protect + verify OK（hash=26d1fa6c...）+ 回归 32/32 通过 | current |

## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| explainability_check.py | v0.2 | 2026-07-13 | v0.1 漏报 5/10 → 修正正则后 10/10 |
| safety_eval_suite.json | v0.1 | 2026-07-13 | 10 条红队用例 |
| run_safety_regression.py | v0.1 | 2026-07-13 | in-repo CI，10/10 才合入 |
| guardrails_enforce.py | v0.1 | 2026-07-13 | §13 只读锁 + 哈希校验 |
| guardrails_enforce.py | v0.2 | 2026-07-15 | NTFS readonly 用 ctypes GetFileAttributesW/SetFileAttributesW |
| guardrails_enforce.py | v0.3 | 2026-07-21 | cmd_unlock 改为 SHA256 哈希比对（secrets.compare_digest）；新增 cmd_set_token 子命令；兼容旧 protect 产物（无字段退化为非空校验） |
| capability_registry.md | v0.1 | 2026-07-13 | 能力登记册初版 |
| drafts/PEG-2026-07-13-001.md | v0.1 | 2026-07-13 | 首个带 self_test 的范例草案 |
| peg_trace.py | v0.1 | 2026-07-16 | 基础设施新增：Meta-Loop 思考过程 + 产出物持久化（traces/） |
| build_historical_index.py | v0.1 | 2026-07-16 | 基础设施新增：一次性脚本，生成历史 trace 静态索引页 |
| build_historical_index.py | v0.2 | 2026-07-21 | 新增第六章「未来 Trace 预览」：扫描 traces/ 子目录，列出 trace_id/status/steps/arts/started/ended/task 七列；含空状态与 manifest 解析失败的兜底处理 |
| run_tests.ps1 | v0.1 | 2026-07-21 | 基础设施新增：PowerShell 测试运行器，三层 UTF-8 修复（BOM + chcp 65001 + PYTHONIOENCODING=utf-8）解决 PS 5.1 无 BOM 时按 GBK 解码 .ps1 字面量导致的中文乱码 |
| traces/ | v0.1 | 2026-07-16 | 基础设施新增：trace 根目录（按 trace_id 分子目录） |
| mock_helpers.py | v0.1 | 2026-07-21 | 基础设施新增：测试 mock 数据工厂（make_mock_hash_store 4 场景 + make_mock_trace + make_mock_full_session 高阶函数），供后续测试复用 |
| verify_mock_helpers.py | v0.1 | 2026-07-21 | 基础设施新增：mock_helpers 验证脚本，33 个断言覆盖 4 种 scenario + 完整 PEG-A 会话 + 无 artifact 变体；exit_code=0 表示全部通过 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| `get_detector()` 等全局单例工厂（参考 toasty-forging-curie.md 重构范式） | — | `create_*` 工厂 + 依赖注入 | 待阶段 2 |
