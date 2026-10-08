#!/usr/bin/env python3
"""
test_auto_register_versions.py
单元测试：验证 auto_register_versions.py 的核心补登逻辑稳定性。

覆盖:
  - is_runtime_artifact() — 运行时产物过滤
  - is_source_file() — 合法源文件白名单
  - parse_versions_md() — 工程化产物表解析
  - find_unregistered() — 差异检测
  - get_file_description() — 备注生成
  - generate_entries() — 表格行生成
  - apply_registration() — 插入逻辑

用法:
  python test_auto_register_versions.py

版本: v0.1 (2026-08-04)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 将脚本所在目录加入 sys.path 以导入 auto_register_versions
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from auto_register_versions import (
    is_runtime_artifact,
    is_source_file,
    parse_versions_md,
    find_unregistered,
    get_file_description,
    generate_entries,
    apply_registration,
    EXCLUDE_RUNTIME_PATTERNS,
    EXCLUDE_SELF,
    SOURCE_EXTENSIONS,
)


class TestIsRuntimeArtifact(unittest.TestCase):
    """运行时产物过滤测试"""

    def test_logs_gate_excluded(self):
        self.assertTrue(is_runtime_artifact("logs/gate_20260714_125558.jsonl"))
        self.assertTrue(is_runtime_artifact("logs/gate_20260714_125600_08_REJECT.jsonl"))

    def test_traces_runtime_excluded(self):
        self.assertTrue(is_runtime_artifact("traces/20260721_104251/manifest.json"))
        self.assertTrue(is_runtime_artifact("traces/20260721_104251/reasoning.jsonl"))
        self.assertTrue(is_runtime_artifact("traces/20260721_104251/artifacts/demo.md"))

    def test_traces_historical_index_preserved(self):
        """traces/_historical_index.md 是文档，不应被排除"""
        self.assertFalse(is_runtime_artifact("traces/_historical_index.md"))

    def test_normal_source_not_excluded(self):
        self.assertFalse(is_runtime_artifact("fix_versions_refs.py"))
        self.assertFalse(is_runtime_artifact("versions.md"))
        self.assertFalse(is_runtime_artifact("drafts/self_modify_001.diff.md"))
        self.assertFalse(is_runtime_artifact("prompts/domain/agents/orchestrator.prompt.md"))


class TestIsSourceFile(unittest.TestCase):
    """合法源文件过滤测试"""

    def test_python_files(self):
        self.assertTrue(is_source_file("fix_versions_refs.py"))
        self.assertTrue(is_source_file("test_peg_trace.py"))
        self.assertTrue(is_source_file("ci_lint.py"))

    def test_markdown_files(self):
        self.assertTrue(is_source_file("README.md"))
        self.assertTrue(is_source_file("ARCHITECTURE_BRIEF.md"))
        self.assertTrue(is_source_file("drafts/self_modify_001.diff.md"))

    def test_json_files(self):
        self.assertTrue(is_source_file("migration_scan_report.json"))
        self.assertTrue(is_source_file("stage1_tool_schema.json"))
        self.assertTrue(is_source_file("logs/gate_20260714.jsonl"))

    def test_config_files(self):
        self.assertTrue(is_source_file("pyproject.toml"))
        self.assertTrue(is_source_file(".gitignore"))
        self.assertTrue(is_source_file("hooks/pre-commit"))

    def test_shell_scripts(self):
        self.assertTrue(is_source_file("run_gate.sh"))
        self.assertTrue(is_source_file("run_tests.ps1"))

    def test_non_source_excluded(self):
        self.assertFalse(is_source_file("image.png"))
        self.assertFalse(is_source_file("video.mp4"))
        self.assertFalse(is_source_file("binary.exe"))
        self.assertFalse(is_source_file("data.csv"))

    def test_git_internal_excluded(self):
        """AUTO_MERGE, HEAD 等 .git 内部文件不应被当作源文件"""
        self.assertFalse(is_source_file("AUTO_MERGE"))
        self.assertFalse(is_source_file("HEAD"))
        self.assertFalse(is_source_file("index"))
        self.assertFalse(is_source_file("config"))


class TestParseVersionsMd(unittest.TestCase):
    """versions.md 表解析测试"""

    def setUp(self):
        self.sample = """# 语义化版本登记册

## PEG-A 自身提示词

| 版本 | 日期 | 变更 | 状态 |
|---|---|---|---|
| v0.1 | 2026-07-13 | 阶段 0 种子提示词 | archived |
| v0.6 | 2026-07-21 | peg_trace.py 接入主流程 | current |

## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| explainability_check.py | v0.2 | 2026-07-13 | 安全闸门 |
| guardrails_enforce.py | v0.3 | 2026-07-21 | 只读锁 |
| peg_trace.py | v0.1 | 2026-07-16 | trace 基础设施 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| get_detector() | — | create_* 工厂 | 待阶段 2 |
"""

    def test_parse_only_engineering_table(self):
        entries = parse_versions_md(self.sample)
        self.assertEqual(len(entries), 3, "应只解析工程化产物表（3 条）")

    def test_excludes_version_numbers(self):
        entries = parse_versions_md(self.sample)
        self.assertNotIn("v0.1", entries, "v0.1 是版本号，不应被解析")
        self.assertNotIn("v0.6", entries, "v0.6 是版本号，不应被解析")

    def test_excludes_deprecation_items(self):
        entries = parse_versions_md(self.sample)
        self.assertNotIn("get_detector()", entries, "弃用项不应被解析")
        for e in entries:
            self.assertNotIn("create_*", e, "弃用表的替代列不应被解析")

    def test_includes_expected_files(self):
        entries = parse_versions_md(self.sample)
        self.assertIn("explainability_check.py", entries)
        self.assertIn("guardrails_enforce.py", entries)
        self.assertIn("peg_trace.py", entries)

    def test_empty_table(self):
        text = """## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
"""
        entries = parse_versions_md(text)
        self.assertEqual(len(entries), 0, "空表应返回 0 条")

    def test_no_engineering_table(self):
        text = """# 只有版本表

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-07-13 | init |
"""
        entries = parse_versions_md(text)
        self.assertEqual(len(entries), 0, "无工程化产物表应返回 0 条")


class TestFindUnregistered(unittest.TestCase):
    """差异检测测试"""

    def test_all_registered(self):
        disk = {"a.py", "b.md", "c.json"}
        registered = {"a.py", "b.md", "c.json"}
        result = find_unregistered(disk, registered)
        self.assertEqual(len(result), 0, "全部已登记应返回空")

    def test_some_unregistered(self):
        disk = {"a.py", "b.md", "c.json", "d.py"}
        registered = {"a.py", "b.md"}
        result = find_unregistered(disk, registered)
        self.assertEqual(len(result), 2)
        self.assertIn("c.json", result)
        self.assertIn("d.py", result)

    def test_excludes_self_references(self):
        disk = {"a.py", "versions.md", "workspace_map.md"}
        registered = {"a.py"}
        result = find_unregistered(disk, registered)
        # a.py 已登记，versions.md/workspace_map.md 是自引用 → 全部排除
        self.assertEqual(len(result), 0, "a.py 已登记，自引用应被排除")

    def test_excludes_runtime_artifacts(self):
        disk = {"a.py", "logs/gate_20260714.jsonl", "traces/20260721/manifest.json"}
        registered = {"a.py"}
        result = find_unregistered(disk, registered)
        # a.py 已登记，logs/traces 是运行时产物 → 全部排除
        self.assertEqual(len(result), 0, "a.py 已登记，运行时产物应被排除")

    def test_excludes_non_source(self):
        disk = {"a.py", "image.png", "video.mp4"}
        registered = {"a.py"}
        result = find_unregistered(disk, registered)
        # a.py 已登记，png/mp4 非源文件 → 全部排除
        self.assertEqual(len(result), 0, "a.py 已登记，非源文件应被排除")

    def test_non_source_not_registered(self):
        """非源文件即使未登记也不应出现在结果中"""
        disk = {"image.png", "video.mp4"}
        registered = set()
        result = find_unregistered(disk, registered)
        self.assertEqual(len(result), 0, "非源文件不应出现在未登记列表中")

    def test_source_not_registered_appears(self):
        """未登记的合法源文件应出现在结果中"""
        disk = {"new_feature.py"}
        registered = set()
        result = find_unregistered(disk, registered)
        self.assertEqual(result, ["new_feature.py"])

    def test_basename_match(self):
        """测试 basename 兜底匹配（兼容旧格式）"""
        disk = {"drafts/my_draft.md"}
        registered = {"my_draft.md"}  # 只有 basename 登记
        result = find_unregistered(disk, registered)
        self.assertEqual(len(result), 0, "basename 匹配应视为已登记")

    def test_full_path_match(self):
        disk = {"drafts/my_draft.md"}
        registered = {"drafts/my_draft.md"}  # 完整路径登记
        result = find_unregistered(disk, registered)
        self.assertEqual(len(result), 0, "完整路径匹配应视为已登记")


class TestGetFileDescription(unittest.TestCase):
    """备注生成测试"""

    def test_gitignore(self):
        self.assertEqual(get_file_description(".gitignore"), "VCS 忽略规则")

    def test_pre_commit(self):
        self.assertEqual(get_file_description("hooks/pre-commit"), "Git pre-commit hook")

    def test_test_file(self):
        desc = get_file_description("test_guardrails_readonly.py")
        self.assertIn("测试", desc)
        self.assertIn("guardrails readonly", desc)

    def test_draft_self_modify(self):
        desc = get_file_description("drafts/self_modify_001.diff.md")
        self.assertIn("自修改", desc)

    def test_v0_6_script(self):
        desc = get_file_description("drafts/_v0_6_apply_scripts/apply_unlock_hash_check.py")
        self.assertIn("v0.6", desc)

    def test_fix_report(self):
        desc = get_file_description("fix_reports/FIX-002-guardrails-readonly-windows.md")
        self.assertEqual(desc, "修复报告")

    def test_tech_note(self):
        desc = get_file_description("tech_notes/TN-001-llm-readonly-fix.md")
        self.assertEqual(desc, "技术笔记")

    def test_domain_agent(self):
        desc = get_file_description("prompts/domain/agents/orchestrator.prompt.md")
        self.assertIn("领域智能体", desc)
        self.assertIn("orchestrator", desc)

    def test_core_service(self):
        desc = get_file_description("prompts/apps/core/services/feedback.prompt.md")
        self.assertIn("核心服务", desc)
        self.assertIn("feedback", desc)

    def test_doc_alignment_validator_pyproject(self):
        desc = get_file_description("doc_alignment_validator/pyproject.toml")
        self.assertEqual(desc, "pip 包构建配置")

    def test_doc_alignment_validator_setup(self):
        desc = get_file_description("doc_alignment_validator/setup.py")
        self.assertEqual(desc, "pip 包安装脚本")

    def test_doc_alignment_validator_validate(self):
        desc = get_file_description("doc_alignment_validator/validate.py")
        self.assertEqual(desc, "包入口：11 项校验引擎")

    def test_doc_alignment_validator_src(self):
        desc = get_file_description("doc_alignment_validator/src/doc_alignment_validator/validate.py")
        self.assertIn("pip 包", desc)

    def test_traces_historical(self):
        desc = get_file_description("traces/_historical_index.md")
        self.assertIn("历史", desc)

    def test_unknown_fallback(self):
        desc = get_file_description("some_unknown_script.py")
        self.assertEqual(desc, "源文件")


class TestGenerateEntries(unittest.TestCase):
    """表格行生成测试"""

    def test_single_entry(self):
        entries = generate_entries(["fix_versions_refs.py"], "2026-08-04")
        self.assertEqual(len(entries), 1)
        expected = "| fix_versions_refs.py | v0.1 | 2026-08-04 | 基础设施新增：登记册一致性自动修复工具 |"
        self.assertEqual(entries[0], expected)

    def test_multiple_entries(self):
        unregistered = ["a.py", "b.md"]
        entries = generate_entries(unregistered, "2026-08-04")
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].startswith("| a.py |"))
        self.assertTrue(entries[1].startswith("| b.md |"))

    def test_custom_date(self):
        entries = generate_entries(["test.py"], "2025-01-15")
        self.assertIn("2025-01-15", entries[0])


class TestApplyRegistration(unittest.TestCase):
    """插入逻辑测试"""

    def setUp(self):
        self.sample = """## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| explainability_check.py | v0.2 | 2026-07-13 | 安全闸门 |
| guardrails_enforce.py | v0.3 | 2026-07-21 | 只读锁 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| old_func | v0.1 | new_func | 阶段 2 |
"""

    def test_insert_before_deprecation(self):
        new_entries = ["| peg_trace.py | v0.1 | 2026-08-04 | trace 基础设施 |"]
        result = apply_registration(self.sample, new_entries)

        # 新条目应在弃用记录之前
        self.assertIn("peg_trace.py", result)
        self.assertIn("## 弃用记录", result)
        idx_peg = result.index("peg_trace.py")
        idx_dep = result.index("## 弃用记录")
        self.assertLess(idx_peg, idx_dep, "新条目应在弃用记录之前")

    def test_preserves_existing_entries(self):
        new_entries = ["| peg_trace.py | v0.1 | 2026-08-04 | trace |"]
        result = apply_registration(self.sample, new_entries)
        self.assertIn("explainability_check.py", result)
        self.assertIn("guardrails_enforce.py", result)

    def test_multiple_new_entries(self):
        new_entries = [
            "| a.py | v0.1 | 2026-08-04 | test a |",
            "| b.md | v0.1 | 2026-08-04 | test b |",
        ]
        result = apply_registration(self.sample, new_entries)
        self.assertIn("a.py", result)
        self.assertIn("b.md", result)


class TestIntegration(unittest.TestCase):
    """集成测试：端到端补登流程"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

        # 创建模拟 versions.md
        self.versions = self.tmp / "versions.md"
        self.versions.write_text("""## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| existing.py | v0.1 | 2026-07-13 | 已存在 |

## 弃用记录

| 项 | 弃用版本 | 替代 |
|---|---|---|
| old | v0.1 | new |
""", encoding="utf-8")

        # 创建模拟源文件
        (self.tmp / "existing.py").write_text("# existing")
        (self.tmp / "new_file.py").write_text("# new")
        (self.tmp / "new_doc.md").write_text("# doc")
        (self.tmp / "logs").mkdir()
        (self.tmp / "logs" / "gate_20260714.jsonl").write_text("{}")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_end_to_end_find_and_register(self):
        """E2E: 扫描 → 找未登记 → 补登 → 验证"""
        # 1. 扫描磁盘
        from auto_register_versions import list_disk_files
        disk = list_disk_files(self.tmp)
        self.assertIn("existing.py", disk)
        self.assertIn("new_file.py", disk)
        self.assertIn("new_doc.md", disk)
        # logs 是运行时产物，但 list_disk_files 不排除运行时产物
        # 排除在 find_unregistered 阶段完成

        # 2. 解析已登记
        ver_text = self.versions.read_text(encoding="utf-8")
        registered = parse_versions_md(ver_text)
        self.assertIn("existing.py", registered)

        # 3. 找未登记（排除运行时产物）
        unreg = find_unregistered(disk, registered)
        self.assertIn("new_file.py", unreg)
        self.assertIn("new_doc.md", unreg)
        self.assertNotIn("logs/gate_20260714.jsonl", unreg,
                         "运行时产物不应出现在未登记列表中")

        # 4. 生成条目
        entries = generate_entries(unreg, "2026-08-04")
        self.assertEqual(len(entries), 2)

        # 5. 插入
        new_content = apply_registration(self.versions, entries)
        self.versions.write_text(new_content, encoding="utf-8")

        # 6. 验证：重新解析应包含新文件
        ver_text2 = self.versions.read_text(encoding="utf-8")
        registered2 = parse_versions_md(ver_text2)
        self.assertIn("new_file.py", registered2)
        self.assertIn("new_doc.md", registered2)
        self.assertIn("existing.py", registered2)

        # 7. 验证：再次扫描应无未登记
        unreg2 = find_unregistered(disk, registered2)
        self.assertEqual(len(unreg2), 0, "补登后应无遗漏")


if __name__ == "__main__":
    unittest.main(verbosity=2)