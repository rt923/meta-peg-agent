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
├── mock_helpers.py              # 测试 mock 数据工厂（3 个工厂函数，2026-07-21 基础设施新增）
├── mock_helpers.md              # mock_helpers.py API 文档（2026-07-21 基础设施新增）
├── doc_alignment_quickref.md     # doc_alignment 快速参考（六条规则速查 + 偏差分级 + 工作流 + self_test 状态，2026-07-22 固化）
├── doc_alignment.json           # doc_alignment 增强块 JSON 导出（结构化，供外部工具集成，2026-07-22）
├── doc_alignment_onboarding.md  # doc_alignment 新项目快速接入指南（前置检查 / 5 步流程 / 踩坑表，2026-07-22）
├── TROUBLESHOOTING.md           # doc_alignment 常见踩坑独立文档（8 条坑 + 快速诊断流程图，2026-07-22）
├── TROUBLESHOOTING_table.md     # TROUBLESHOOTING 8 条踩坑表格格式（Confluence/Notion 可直接复制粘贴，2026-07-22）
├── validate_doc_alignment_json.py # doc_alignment.json 外部工具加载兼容性校验（11 项检查，2026-07-22）
├── doc_alignment_windows_demo.md  # doc_alignment Windows 环境新项目接入演示（18 项检查点清单，2026-07-22）
├── test_doc_alignment_rules.py    # D1–D6 Pytest 单元测试（38 用例，13 测试类，2026-07-22）
├── TROUBLESHOOTING_raw_tables.md  # TROUBLESHOOTING 3 张表纯 Markdown 源码（Confluence/Notion 直接粘贴，2026-07-22）
├── ci_timing_report.py           # CI/CD 模拟运行报告（11 项微基准 + 耗时分布 + 瓶颈分析，2026-07-22）
├── doc_alignment_migration_checklist.md  # 旧项目迁移评估清单（37 项检查 × 6 维度 + 优先级矩阵，2026-07-22）
├── doc_alignment_architecture.md  # 15 件套产物架构图（3 张 Mermaid 流程图：依赖/分层/数据流，2026-07-22）
├── doc_alignment_README.md     # 15 件套产物全览 README（分层详解 L0–L4 + 构建顺序 + 快速导航，2026-07-28）
│   ├── src/doc_alignment_validator/
│   │   ├── __init__.py
│   │   ├── validate.py
│   │   └── data/doc_alignment.json
│   ├── setup.py
│   ├── pyproject.toml
│   ├── README.md
│   └── dist/doc_alignment_validator-0.1.0-py3-none-any.whl
├── migration_scanner.py        # 旧项目迁移自动扫描器（37 项检查 D1–D6 + Markdown/JSON 报告，2026-07-28）
├── render_mermaid.py           # Mermaid → PNG 渲染器（3 种方案：mmdc/playwright/mermaid_ink，2026-07-28）
│   └── workflows/
│       └── doc_alignment_ci.yml   # CI/CD 流水线（push/PR → 11 项校验 + R9 闸门 + 回归，2026-07-22）
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
│   │           ├── meta_cognition.prompt.md
│   │           └── doc_alignment.prompt.md   # 服务层：文档对齐检查（D1 实证对比 / D2 同性质扫描 / D3 目录树验证 / D4 交叉引用 / D5 运行时产物 / D6 回溯更新）
│   └── tests/                    # 对齐 toasty tests/
│       └── test_prompts.prompt.md
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
| `apps/core/services/doc_alignment_service.py` | `prompts/apps/core/services/doc_alignment.prompt.md` | 文档对齐检查 |

## 四、使用约定

- **incubate**：编排智能体新建子智能体 → PEG-A 在 `prompts/domain/agents/` 生成种子块。
- **design / refactor**：领域/服务智能体提示词卡点 → PEG-A 在对应路径产 diff。
- **self_optimize（阶段1）**：PEG-A 审视 `bootstrap_prompt.md` + `phase0_meta_peg_agent_prompt.md`，产出元提示工程改进 diff（见 `stage1_prompt.md`）。
- 每个块变更须登记 `versions.md` 与 `capability_registry.md`，并经回归 CI。

<!-- 自动补登 (2026-07-28) -->
├── .gitignore  # 自动补登: .gitignore
├── ARCHITECTURE_BRIEF.md  # 自动补登: ARCHITECTURE_BRIEF.md
├── 歡迎.md  # 自动补登: TRAE/歡迎.md
├── build_historical_index.py  # 自动补登: build_historical_index.py
├── ci_lint.py  # 自动补登: ci_lint.py
├── ci_timing_report.json  # 自动补登: ci_timing_report.json
├── demo_peg_collaboration.py  # 自动补登: demo_peg_collaboration.py
├── QUICKSTART.md  # 自动补登: doc_alignment_validator/QUICKSTART.md
├── README.md  # 自动补登: doc_alignment_validator/README.md
├── pyproject.toml  # 自动补登: doc_alignment_validator/pyproject.toml
├── setup.py  # 自动补登: doc_alignment_validator/setup.py
├── validate.py  # 自动补登: doc_alignment_validator/src/doc_alignment_validator/validate.py
├── validate.py  # 自动补登: doc_alignment_validator/validate.py
├── apply_unlock_hash_check.py  # 自动补登: drafts/_v0_6_apply_scripts/apply_unlock_hash_check.py
├── apply_v0_5_to_v0_6.py  # 自动补登: drafts/_v0_6_apply_scripts/apply_v0_5_to_v0_6.py
├── finalize_v0_6.py  # 自动补登: drafts/_v0_6_apply_scripts/finalize_v0_6.py
├── fix_cap_reg.py  # 自动补登: drafts/_v0_6_apply_scripts/fix_cap_reg.py
├── run_peg_a_e2e_demo.py  # 自动补登: drafts/_v0_6_apply_scripts/run_peg_a_e2e_demo.py
├── update_reg_v0_3.py  # 自动补登: drafts/_v0_6_apply_scripts/update_reg_v0_3.py
├── update_registries_v0_6.py  # 自动补登: drafts/_v0_6_apply_scripts/update_registries_v0_6.py
├── verify_v0_6_applied.py  # 自动补登: drafts/_v0_6_apply_scripts/verify_v0_6_applied.py
├── self_modify_001.diff.md  # 自动补登: drafts/self_modify_001.diff.md
├── self_modify_002.diff.md  # 自动补登: drafts/self_modify_002.diff.md
├── self_modify_003.diff.md  # 自动补登: drafts/self_modify_003.diff.md
├── FIX-002-guardrails-readonly-windows.md  # 自动补登: fix_reports/FIX-002-guardrails-readonly-windows.md
├── fix_versions_refs.py  # 自动补登: fix_versions_refs.py
├── guardrails_enforce.v0.2.bak.py  # 自动补登: guardrails_enforce.v0.2.bak.py
├── pre-commit  # 自动补登: hooks/pre-commit
├── install_mermaid_renderer.py  # 自动补登: install_mermaid_renderer.py
├── gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl  # 自动补登: logs/gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl
├── gate_20260714_125600_08_REJECT_4f81d002a00e1274.jsonl  # 自动补登: logs/gate_20260714_125600_08_REJECT_4f81d002a00e1274.jsonl
├── gate_20260714_130852_03_REJECT_5d7cdda0a9e59a27.jsonl  # 自动补登: logs/gate_20260714_130852_03_REJECT_5d7cdda0a9e59a27.jsonl
├── migration_scan_report.json  # 自动补登: migration_scan_report.json
├── migration_scan_report.md  # 自动补登: migration_scan_report.md
├── mock_integration_test.py  # 自动补登: mock_integration_test.py
├── peg_guard_prompt.md  # 自动补登: peg_guard_prompt.md
├── peg_team_overview.md  # 自动补登: peg_team_overview.md
├── peg_trace.py  # 自动补登: peg_trace.py
├── phase0_meta_peg_agent_prompt.md.guardrail.json  # 自动补登: phase0_meta_peg_agent_prompt.md.guardrail.json
├── phase0_meta_peg_agent_prompt_full.md  # 自动补登: phase0_meta_peg_agent_prompt_full.md
├── doc_alignment.prompt.md  # 自动补登: prompts/apps/core/services/doc_alignment.prompt.md
├── feedback.prompt.md  # 自动补登: prompts/apps/core/services/feedback.prompt.md
├── meta_cognition.prompt.md  # 自动补登: prompts/apps/core/services/meta_cognition.prompt.md
├── monitor.prompt.md  # 自动补登: prompts/apps/core/services/monitor.prompt.md
├── multi_agent.prompt.md  # 自动补登: prompts/apps/core/services/multi_agent.prompt.md
├── policy_sync.prompt.md  # 自动补登: prompts/apps/core/services/policy_sync.prompt.md
├── process.prompt.md  # 自动补登: prompts/apps/core/services/process.prompt.md
├── state.prompt.md  # 自动补登: prompts/apps/core/services/state.prompt.md
├── challenger.prompt.md  # 自动补登: prompts/domain/agents/challenger.prompt.md
├── checker.prompt.md  # 自动补登: prompts/domain/agents/checker.prompt.md
├── executor.prompt.md  # 自动补登: prompts/domain/agents/executor.prompt.md
├── gatekeeper.prompt.md  # 自动补登: prompts/domain/agents/gatekeeper.prompt.md
├── orchestrator.prompt.md  # 自动补登: prompts/domain/agents/orchestrator.prompt.md
├── run_gate.sh  # 自动补登: run_gate.sh
├── run_tests.ps1  # 自动补登: run_tests.ps1
├── stage1_team_prompt.md  # 自动补登: stage1_team_prompt.md
├── TN-001-llm-readonly-fix.md  # 自动补登: tech_notes/TN-001-llm-readonly-fix.md
├── test_guardrails_readonly.py  # 自动补登: test_guardrails_readonly.py
├── test_integration_live.py  # 自动补登: test_integration_live.py
├── test_llm_config_switch.py  # 自动补登: test_llm_config_switch.py
├── test_peg_a_v0_6_flow.py  # 自动补登: test_peg_a_v0_6_flow.py
├── test_peg_trace.py  # 自动补登: test_peg_trace.py
├── test_r9_runtime.py  # 自动补登: test_r9_runtime.py
├── test_readonly_windows.py  # 自动补登: test_readonly_windows.py
├── test_unlock_hash_check.py  # 自动补登: test_unlock_hash_check.py
├── 20260721_104251_0b52-e2e-demo-script.md  # 自动补登: traces/20260721_104251_0b52/artifacts/20260721_104251_0b52-e2e-demo-script.md
├── manifest.json  # 自动补登: traces/20260721_104251_0b52/manifest.json
├── reasoning.jsonl  # 自动补登: traces/20260721_104251_0b52/reasoning.jsonl
├── 20260721_104525_0b52-e2e-demo-script.md  # 自动补登: traces/20260721_104525_0b52/artifacts/20260721_104525_0b52-e2e-demo-script.md
├── manifest.json  # 自动补登: traces/20260721_104525_0b52/manifest.json
├── reasoning.jsonl  # 自动补登: traces/20260721_104525_0b52/reasoning.jsonl
├── _historical_index.md  # 自动补登: traces/_historical_index.md
├── verify_mock_helpers.py  # 自动补登: verify_mock_helpers.py

<!-- 自动补登 (2026-08-04) -->
├── auto_register_versions.py  # 自动补登: auto_register_versions.py