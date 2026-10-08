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
| prompts/apps/core/services/doc_alignment.prompt.md | v0.1 | 2026-07-22 | 基础设施新增：D1–D6 文档对齐方法论增强块（实证对比 / 同性质扫描 / 目录树验证 / 交叉引用 / 运行时产物 / 回溯更新），R9 闸门 7/7 通过 |
| doc_alignment_quickref.md | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment 独立快速参考文档（六条规则速查表 + 偏差分级 + 工作流 + 三向对齐 + 通配模式 + self_test 验证状态），供后续智能体引用 |
| doc_alignment.json | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment 增强块结构化 JSON 导出（meta/role/rules/workflow/self_test/security/related_files），供外部工具集成 |
| doc_alignment_onboarding.md | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment 新项目快速接入指南（前置检查 / 5 步最小可行流程 / 持续对齐清单 / 通配速查 / 踩坑表 / PEG-A 集成方案） |
| TROUBLESHOOTING.md | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment 常见踩坑独立文档（8 条坑 + 症状 + 根因 + 解法 + 快速诊断流程图），含 Windows 路径分隔符 / PS 5.1 乱码 / JSON 编码三大系统级坑 |
| TROUBLESHOOTING_table.md | v0.1 | 2026-07-22 | 基础设施新增：TROUBLESHOOTING 8 条踩坑 Confluence/Notion 表格格式（速查表 + 诊断流程 + 编码检查清单 + 路径分隔符对照表），可直接复制粘贴 |
| validate_doc_alignment_json.py | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment.json 外部工具加载兼容性校验脚本（11 项检查：语法/顶层字段/meta 类型/role/D1 5 维度+3 偏差/D2–D6 结构/workflow 5 步/self_test 7 条/security §12§13/related_files 路径一致性/空值校验/数组非空），exit_code=0 表示全部通过 |
| doc_alignment_windows_demo.md | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment Windows 环境新项目接入完整演示（win-utils 模拟项目：前置检查 / 首次对齐 6 步 / 关键检查点清单 18 项 / Windows 特有 5 项），含编码修复 + 偏差清单 + D4 补登记示例 |
| .github/workflows/doc_alignment_ci.yml | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment CI/CD 流水线（push/PR 触发 → 11 项 JSON 结构校验 + R9 闸门 self_test 7/7 + 回归测试），确保每次提交自动运行 |
| test_doc_alignment_rules.py | v0.1 | 2026-07-22 | 基础设施新增：D1–D6 Pytest 单元测试（38 用例，13 测试类，覆盖 5 维度 + 3 偏差 + 4 通配 + 跨规则集成 + JSON Schema 一致性），38/38 全 PASS |
| TROUBLESHOOTING_raw_tables.md | v0.1 | 2026-07-22 | 基础设施新增：TROUBLESHOOTING 3 张表纯 Markdown 源码（无标题/注释/代码块包装），可直接复制粘贴到 Confluence/Notion/飞书 |
| ci_timing_report.py | v0.1 | 2026-07-22 | 基础设施新增：CI/CD 模拟运行报告（11 项独立微基准 + 耗时分布 + 瓶颈分析 + JSON 报告），含隐藏警告扫描 |
| doc_alignment_migration_checklist.md | v0.1 | 2026-07-22 | 基础设施新增：旧项目迁移评估清单（37 项检查 × 6 维度 + 优先级矩阵 + 两步迁移路径），逐项打勾 |
| doc_alignment_architecture.md | v0.1 | 2026-07-22 | 基础设施新增：doc_alignment 15 件套产物架构图（3 张 Mermaid 流程图：完整依赖关系 / 分层架构 / 数据流向 + 拓扑排序），可渲染到 mermaid.live |
| doc_alignment_validator/ | v0.1.0 | 2026-07-28 | 基础设施新增：pip 可安装包（doc_alignment.json + 11 项校验引擎），pip install 后 `from doc_alignment_validator import validate; validate()` 即可使用，已构建 wheel 并验证 11/11 通过 |
| migration_scanner.py | v0.1 | 2026-07-28 | 基础设施新增：基于 doc_alignment_migration_checklist.md 的自动扫描器（37 项检查 D1–D6），输出 Markdown + JSON 报告，meta_peg_agent 自扫 7/37 自动通过 |
| render_mermaid.py | v0.1 | 2026-07-28 | 基础设施新增：Mermaid → PNG 渲染器（3 种方案：mmdc / playwright / mermaid_ink），支持从 Markdown 自动提取 Mermaid 代码块 |
| doc_alignment_README.md | v0.1 | 2026-07-28 | 基础设施新增：doc_alignment 15 件套产物全览 README（分层详解 L0–L4 + 构建顺序 + 数据流方向 + 快速导航） |

| .gitignore | v0.1 | 2026-08-04 | 基础设施新增：VCS 忽略规则 |
| ARCHITECTURE_BRIEF.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 架构简报 |
| TRAE/歡迎.md | v0.1 | 2026-08-04 | 基础设施新增：TRAE IDE 欢迎文档 |
| auto_register_versions.py | v0.1 | 2026-08-04 | 基础设施新增：源文件 |
| bootstrap_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：引导提示词 |
| ci_lint.py | v0.1 | 2026-08-04 | 基础设施新增：CI 代码检查脚本 |
| ci_timing_report.json | v0.1 | 2026-08-04 | 基础设施新增：CI 耗时报告 |
| demo_peg_collaboration.py | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 多智能体协作演示 |
| doc_alignment_validator/QUICKSTART.md | v0.1 | 2026-08-04 | 基础设施新增：doc_alignment_validator 包文件 |
| doc_alignment_validator/README.md | v0.1 | 2026-08-04 | 基础设施新增：doc_alignment_validator 包文件 |
| doc_alignment_validator/pyproject.toml | v0.1 | 2026-08-04 | 基础设施新增：pip 包构建配置 |
| doc_alignment_validator/setup.py | v0.1 | 2026-08-04 | 基础设施新增：pip 包安装脚本 |
| doc_alignment_validator/src/doc_alignment_validator/validate.py | v0.1 | 2026-08-04 | 基础设施新增：包入口：11 项校验引擎 |
| doc_alignment_validator/validate.py | v0.1 | 2026-08-04 | 基础设施新增：包入口：11 项校验引擎 |
| drafts/_v0_6_apply_scripts/apply_unlock_hash_check.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/apply_v0_5_to_v0_6.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/finalize_v0_6.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/fix_cap_reg.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/run_peg_a_e2e_demo.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/update_reg_v0_3.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/update_registries_v0_6.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/_v0_6_apply_scripts/verify_v0_6_applied.py | v0.1 | 2026-08-04 | 基础设施新增：v0.6 升级脚本 |
| drafts/self_modify_001.diff.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 自修改 diff 草案 |
| drafts/self_modify_002.diff.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 自修改 diff 草案 |
| drafts/self_modify_003.diff.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 自修改 diff 草案 |
| fix_reports/FIX-002-guardrails-readonly-windows.md | v0.1 | 2026-08-04 | 基础设施新增：修复报告 |
| fix_versions_refs.py | v0.1 | 2026-08-04 | 基础设施新增：登记册一致性自动修复工具 |
| guardrails_enforce.v0.2.bak.py | v0.1 | 2026-08-04 | 基础设施新增：guardrails_enforce v0.2 备份 |
| hooks/pre-commit | v0.1 | 2026-08-04 | 基础设施新增：Git pre-commit hook |
| install_mermaid_renderer.py | v0.1 | 2026-08-04 | 基础设施新增：Mermaid 渲染器一键安装脚本 |
| migration_scan_report.json | v0.1 | 2026-08-04 | 基础设施新增：迁移扫描 JSON 报告 |
| migration_scan_report.md | v0.1 | 2026-08-04 | 基础设施新增：迁移扫描 Markdown 报告 |
| mock_helpers.md | v0.1 | 2026-08-04 | 基础设施新增：mock_helpers 文档 |
| mock_integration_test.py | v0.1 | 2026-08-04 | 基础设施新增：集成测试 |
| os_guardrails.md | v0.1 | 2026-08-04 | 基础设施新增：OS 护栏文档 |
| peg_guard_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：PEG 护栏提示词 |
| peg_team_overview.md | v0.1 | 2026-08-04 | 基础设施新增：PEG 团队概览 |
| phase0_meta_peg_agent_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 主提示词 |
| phase0_meta_peg_agent_prompt.md.guardrail.json | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 主提示词护栏 JSON |
| phase0_meta_peg_agent_prompt_full.md | v0.1 | 2026-08-04 | 基础设施新增：PEG-A 主提示词完整版 |
| prompts/apps/core/services/feedback.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：feedback |
| prompts/apps/core/services/meta_cognition.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：meta_cognition |
| prompts/apps/core/services/monitor.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：monitor |
| prompts/apps/core/services/multi_agent.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：multi_agent |
| prompts/apps/core/services/policy_sync.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：policy_sync |
| prompts/apps/core/services/process.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：process |
| prompts/apps/core/services/state.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：核心服务提示词：state |
| prompts/domain/agents/challenger.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：领域智能体提示词：challenger |
| prompts/domain/agents/checker.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：领域智能体提示词：checker |
| prompts/domain/agents/executor.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：领域智能体提示词：executor |
| prompts/domain/agents/gatekeeper.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：领域智能体提示词：gatekeeper |
| prompts/domain/agents/orchestrator.prompt.md | v0.1 | 2026-08-04 | 基础设施新增：领域智能体提示词：orchestrator |
| run_gate.sh | v0.1 | 2026-08-04 | 基础设施新增：gate 运行脚本（Shell） |
| self_test_template.md | v0.1 | 2026-08-04 | 基础设施新增：测试：self template.md |
| spawn_peg_member_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：PEG 成员孵化提示词 |
| stage1_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：阶段 1 提示词 |
| stage1_team_prompt.md | v0.1 | 2026-08-04 | 基础设施新增：阶段 1 团队提示词 |
| stage1_tool_schema.json | v0.1 | 2026-08-04 | 基础设施新增：阶段 1 工具 Schema |
| tech_notes/TN-001-llm-readonly-fix.md | v0.1 | 2026-08-04 | 基础设施新增：技术笔记 |
| test_guardrails_readonly.py | v0.1 | 2026-08-04 | 基础设施新增：测试：guardrails readonly |
| test_integration_live.py | v0.1 | 2026-08-04 | 基础设施新增：测试：integration live |
| test_llm_config_switch.py | v0.1 | 2026-08-04 | 基础设施新增：测试：llm config switch |
| test_peg_a_v0_6_flow.py | v0.1 | 2026-08-04 | 基础设施新增：测试：peg a v0 6 flow |
| test_peg_trace.py | v0.1 | 2026-08-04 | 基础设施新增：测试：peg trace |
| test_r9_runtime.py | v0.1 | 2026-08-04 | 基础设施新增：测试：r9 runtime |
| test_readonly_windows.py | v0.1 | 2026-08-04 | 基础设施新增：测试：readonly windows |
| test_unlock_hash_check.py | v0.1 | 2026-08-04 | 基础设施新增：测试：unlock hash check |
| traces/_historical_index.md | v0.1 | 2026-08-04 | 基础设施新增：历史 trace 静态索引页 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| `get_detector()` 等全局单例工厂（参考 toasty-forging-curie.md 重构范式） | — | `create_*` 工厂 + 依赖注入 | 待阶段 2 |