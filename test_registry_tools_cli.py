#!/usr/bin/env python3
"""
test_registry_tools_cli.py
registry_tools pip 包 CLI 命令全覆盖单元测试。

覆盖 registry-check (fix_versions_refs) 和 registry-register (auto_register_versions)
的所有 CLI 输入输出场景，包括：
  - 正常扫描（干净/脏工作区）
  - 修复模式（--fix / --apply）
  - 错误处理（文件缺失/无效目标）
  - 边界情况（空目录/全部已登记/大量文件）
  - 输出格式（中文标记/emoji/计数）

用法:
  python test_registry_tools_cli.py

版本: v0.1 (2026-08-04)
"""

import os
import re
import sys
import tempfile
import unittest
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# 确保可以导入 registry_tools
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "registry_tools" / "src"))

from registry_tools.fix_versions_refs import (
    main as fix_main,
    parse_workspace_map,
    parse_versions_md,
    list_disk_files,
    find_phantom_entries,
    find_missing_files,
    fix_workspace_map,
)
from registry_tools.auto_register_versions import (
    main as register_main,
    find_unregistered,
    generate_entries,
    apply_registration,
)


# ── 辅助函数 ──────────────────────────────────────────

def make_fixture_dir(tmp: Path, *, with_workspace=True, with_versions=True,
                     source_files=None, phantom_in_tree=None):
    """创建测试用的模拟项目目录

    Args:
        tmp: 临时目录 Path
        with_workspace: 是否创建 workspace_map.md
        with_versions: 是否创建 versions.md
        source_files: 要创建的源文件列表，如 ["a.py", "sub/b.md"]
        phantom_in_tree: 目录树中登记但磁盘不存在的文件列表
    """
    if source_files is None:
        source_files = []
    if phantom_in_tree is None:
        phantom_in_tree = []

    # 创建源文件
    for f in source_files:
        full = tmp / f
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(f"# {f}", encoding="utf-8")

    # 创建 workspace_map.md
    if with_workspace:
        tree_lines = ["```", "meta_peg_agent/"]
        for f in sorted(source_files):
            basename = os.path.basename(f)
            tree_lines.append(f"├── {basename}  # 源文件")
        for p in phantom_in_tree:
            tree_lines.append(f"├── {p}  # 虚假条目")
        tree_lines.append("```")
        (tmp / "workspace_map.md").write_text("\n".join(tree_lines), encoding="utf-8")

    # 创建 versions.md
    if with_versions:
        ver_lines = [
            "## 工程化产物",
            "",
            "| 文件 | 版本 | 日期 | 备注 |",
            "|---|---|---|---|",
        ]
        for f in sorted(source_files):
            ver_lines.append(f"| {f} | v0.1 | 2026-07-13 | 测试 |")
        ver_lines.extend([
            "",
            "## 弃用记录",
            "",
            "| 项 | 弃用版本 | 替代 | 过渡期 |",
            "|---|---|---|---|",
            "| old_func | v0.1 | new_func | 阶段 2 |",
        ])
        (tmp / "versions.md").write_text("\n".join(ver_lines), encoding="utf-8")


def run_cli_main(main_func, argv):
    """运行 CLI main 函数并捕获输出和退出码"""
    stdout = StringIO()
    exit_code = 0
    with patch.object(sys, "argv", argv), patch("sys.stdout", stdout), \
         patch("sys.exit", side_effect=SystemExit) as mock_exit:
        try:
            main_func()
        except SystemExit as e:
            exit_code = e.code if isinstance(e.code, int) else 1
    return stdout.getvalue(), exit_code


# ═════════════════════════════════════════════════════════
# registry-check (fix_versions_refs) CLI 测试
# ═════════════════════════════════════════════════════════

class TestRegistryCheckDryRun(unittest.TestCase):
    """registry-check --dry-run 输入输出场景"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_clean_workspace_zero_issues(self):
        """干净工作区：3.4=0, 3.5=0, 登记不存在=0"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md", "c.json"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("✅ 扫描完成", out)
        self.assertIn("3.4 虚假条目", out)
        self.assertIn("3.5 遗漏文件", out)
        self.assertIn("目录树条目: 3", out)
        self.assertIn("versions.md 条目: 3", out)
        # 磁盘文件数 = 3 源文件 + versions.md + workspace_map.md = 5
        self.assertIn("磁盘文件数:", out)

    def test_dirty_workspace_phantom_entries(self):
        """脏工作区：有虚假条目"""
        make_fixture_dir(self.tmp, source_files=["a.py"],
                         phantom_in_tree=["ghost.py"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("3.4 虚假条目", out)
        self.assertIn("✅ 扫描完成", out)

    def test_dirty_workspace_missing_files(self):
        """脏工作区：有遗漏文件"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"],
                         with_workspace=True)
        # workspace_map 只登记了 a.py（b.md 未登记）
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── a.py\n```\n", encoding="utf-8"
        )

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("3.5 遗漏文件", out)
        self.assertIn("✅ 扫描完成", out)

    def test_output_contains_header_info(self):
        """输出包含扫描目标路径信息"""
        make_fixture_dir(self.tmp, source_files=["a.py"])

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("🔍 扫描目标:", out)
        self.assertIn("workspace_map.md:", out)
        self.assertIn("versions.md:", out)

    def test_versions_md_reference_check(self):
        """versions.md 引用检查输出"""
        make_fixture_dir(self.tmp, source_files=["a.py"])

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("versions.md 引用检查:", out)
        self.assertIn("登记但磁盘不存在:", out)
        self.assertIn("磁盘存在但未登记:", out)

    def test_default_target_cwd(self):
        """默认 --target 使用当前工作目录（含已存在的文件）"""
        # 构造 fixture 目录模拟真实项目环境
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("✅ 扫描完成", out)

    def test_phantom_entry_truncation(self):
        """虚假条目超过 10 个时显示截断提示"""
        phantoms = [f"ghost_{i}.py" for i in range(15)]
        make_fixture_dir(self.tmp, source_files=["a.py"],
                         phantom_in_tree=phantoms)

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("还有 5 条", out)

    def test_missing_file_truncation(self):
        """遗漏文件超过 15 个时显示截断提示"""
        files = [f"file_{i}.py" for i in range(20)]
        make_fixture_dir(self.tmp, source_files=files)
        # workspace_map 只登记 3 个
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── file_0.py\n├── file_1.py\n├── file_2.py\n```\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        missing_count = len(find_missing_files(
            parse_workspace_map((self.tmp / "workspace_map.md").read_text(encoding="utf-8")),
            list_disk_files(self.tmp), self.tmp
        ))
        if missing_count > 15:
            self.assertIn("还有", out)

    def test_empty_directory(self):
        """空目录：无文件，目录树为空"""
        make_fixture_dir(self.tmp, source_files=[])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("目录树条目: 0", out)
        # 磁盘文件数 = 0 源文件 + versions.md + workspace_map.md = 2
        self.assertIn("磁盘文件数:", out)


class TestRegistryCheckFix(unittest.TestCase):
    """registry-check --fix 修复模式"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_fix_removes_phantom_entries(self):
        """--fix 移除虚假条目"""
        make_fixture_dir(self.tmp, source_files=["a.py"],
                         phantom_in_tree=["ghost.py"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])

        self.assertEqual(code, 0)
        self.assertIn("✅ workspace_map.md 已修复", out)
        self.assertIn("移除 1 虚假", out)

        # 验证：修复后不应再有 ghost.py
        ws_text = (self.tmp / "workspace_map.md").read_text(encoding="utf-8")
        self.assertNotIn("ghost.py", ws_text)

    def test_fix_adds_missing_files(self):
        """--fix 添加遗漏文件"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"])
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── a.py\n```\n", encoding="utf-8"
        )

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])

        self.assertEqual(code, 0)
        self.assertIn("✅ workspace_map.md 已修复", out)
        self.assertIn("添加", out)

        # 验证：修复后应包含 b.md
        ws_text = (self.tmp / "workspace_map.md").read_text(encoding="utf-8")
        self.assertIn("b.md", ws_text)

    def test_fix_preserves_existing_content(self):
        """--fix 保留已有内容"""
        make_fixture_dir(self.tmp, source_files=["a.py"],
                         phantom_in_tree=["ghost.py"])

        run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])

        ws_text = (self.tmp / "workspace_map.md").read_text(encoding="utf-8")
        self.assertIn("a.py", ws_text, "已有文件应保留")
        self.assertIn("meta_peg_agent/", ws_text, "目录结构应保留")

    def test_fix_idempotent(self):
        """--fix 幂等：运行两次结果相同"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"],
                         phantom_in_tree=["ghost.py"])
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── a.py\n├── ghost.py\n```\n",
            encoding="utf-8"
        )

        # 第一次修复
        run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])
        after_first = (self.tmp / "workspace_map.md").read_text(encoding="utf-8")

        # 第二次修复（应无变化）
        run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])
        after_second = (self.tmp / "workspace_map.md").read_text(encoding="utf-8")

        self.assertEqual(after_first, after_second, "两次 --fix 结果应相同")


class TestRegistryCheckErrors(unittest.TestCase):
    """registry-check 错误处理"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_workspace_map(self):
        """缺少 workspace_map.md 时退出码=1"""
        make_fixture_dir(self.tmp, with_workspace=False, with_versions=True,
                         source_files=["a.py"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 1)
        self.assertIn("❌ workspace_map.md 不存在", out)

    def test_missing_versions_md(self):
        """缺少 versions.md 时退出码=1"""
        make_fixture_dir(self.tmp, with_workspace=True, with_versions=False,
                         source_files=["a.py"])

        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 1)
        self.assertIn("❌ versions.md 不存在", out)

    def test_nonexistent_target(self):
        """目标目录不存在时异常"""
        out, code = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", "/nonexistent/path/xyz",
        ])

        self.assertEqual(code, 1)


# ═════════════════════════════════════════════════════════
# registry-register (auto_register_versions) CLI 测试
# ═════════════════════════════════════════════════════════

class TestRegistryRegisterDryRun(unittest.TestCase):
    """registry-register --dry-run 输入输出场景"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_all_registered_no_output(self):
        """全部已登记：输出 '全部已登记，无需补登'"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"])

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("全部已登记", out)

    def test_some_unregistered(self):
        """有未登记文件：列出文件"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md", "c.json"])
        # versions.md 只登记 a.py, b.md
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n"
            "| b.md | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("待补登文件", out)
        self.assertIn("c.json", out)
        self.assertIn("➕", out)

    def test_output_header_info(self):
        """输出包含标题和统计信息"""
        make_fixture_dir(self.tmp, source_files=["a.py"])

        out, _ = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("🔍 扫描目标:", out)
        self.assertIn("versions.md:", out)
        self.assertIn("磁盘文件数:", out)
        self.assertIn("已登记条目:", out)

    def test_runtime_artifacts_excluded(self):
        """运行时产物不出现在待补登列表中"""
        make_fixture_dir(self.tmp, source_files=["a.py", "logs/gate_20260714.jsonl"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("全部已登记", out, "运行时产物应被排除，不应出现在待补登中")

    def test_non_source_excluded(self):
        """非源文件不出现在待补登列表中"""
        make_fixture_dir(self.tmp, source_files=["a.py", "image.png"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("全部已登记", out, "非源文件应被排除")

    def test_empty_directory(self):
        """空目录"""
        make_fixture_dir(self.tmp, source_files=[])

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 0)
        self.assertIn("全部已登记", out)

    def test_hint_to_apply(self):
        """提示用户运行 --apply"""
        files = [f"file_{i}.py" for i in range(3)]
        make_fixture_dir(self.tmp, source_files=files)
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("--apply", out)


class TestRegistryRegisterApply(unittest.TestCase):
    """registry-register --apply 补登模式"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_apply_registers_files(self):
        """--apply 将未登记文件写入 versions.md"""
        make_fixture_dir(self.tmp, source_files=["a.py", "new_feature.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])

        self.assertEqual(code, 0)
        self.assertIn("✅ 已补登", out)
        self.assertIn("new_feature.py", out)

        # 验证文件已写入
        ver_text = (self.tmp / "versions.md").read_text(encoding="utf-8")
        self.assertIn("new_feature.py", ver_text)

    def test_apply_preserves_existing(self):
        """--apply 保留已有条目"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])

        ver_text = (self.tmp / "versions.md").read_text(encoding="utf-8")
        self.assertIn("a.py", ver_text, "已有条目应保留")
        self.assertIn("弃用记录", ver_text, "弃用记录表应保留")

    def test_apply_idempotent(self):
        """--apply 幂等：运行两次不重复插入"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        # 第一次补登
        run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])
        after_first = (self.tmp / "versions.md").read_text(encoding="utf-8")

        # 第二次补登（应无变化，因为 b.py 已登记）
        run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])
        after_second = (self.tmp / "versions.md").read_text(encoding="utf-8")

        self.assertEqual(after_first, after_second, "两次 --apply 结果应相同")

    def test_apply_custom_date(self):
        """--apply --date 使用自定义日期"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
            "--date", "2025-01-15",
        ])

        self.assertEqual(code, 0)
        self.assertIn("2025-01-15", out)

        ver_text = (self.tmp / "versions.md").read_text(encoding="utf-8")
        self.assertIn("2025-01-15", ver_text)

    def test_apply_no_new_files(self):
        """--apply 无新文件时的输出"""
        make_fixture_dir(self.tmp, source_files=["a.py"])
        # versions.md 已包含 a.py

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])

        self.assertEqual(code, 0)
        self.assertIn("全部已登记", out)

    def test_apply_entries_before_deprecation(self):
        """--apply 插入的条目在弃用记录之前"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])

        ver_text = (self.tmp / "versions.md").read_text(encoding="utf-8")
        idx_b = ver_text.index("b.py")
        idx_dep = ver_text.index("## 弃用记录")
        self.assertLess(idx_b, idx_dep, "b.py 应在弃用记录之前")


class TestRegistryRegisterErrors(unittest.TestCase):
    """registry-register 错误处理"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_versions_md(self):
        """缺少 versions.md 时退出码=1"""
        make_fixture_dir(self.tmp, with_versions=False, source_files=["a.py"])

        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertEqual(code, 1)
        self.assertIn("❌ versions.md 不存在", out)

    def test_nonexistent_target(self):
        """目标目录不存在"""
        out, code = run_cli_main(register_main, [
            "auto_register_versions", "--target", "/nonexistent/path/xyz",
        ])

        self.assertEqual(code, 1)


# ═════════════════════════════════════════════════════════
# 跨命令集成测试
# ═════════════════════════════════════════════════════════

class TestCrossCommandIntegration(unittest.TestCase):
    """跨命令集成测试：check → fix → register 完整工作流"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_full_workflow(self):
        """完整工作流：check → fix → register → check（验证归零）"""
        # 1. 创建脏工作区：有虚假条目 + 遗漏文件 + 未登记文件
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md", "c.json"],
                         phantom_in_tree=["ghost.py"])
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── a.py\n├── ghost.py\n```\n",
            encoding="utf-8"
        )
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | 测试 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        # 2. check: 确认有差异
        out1, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])
        self.assertIn("3.4 虚假条目", out1)
        self.assertIn("3.5 遗漏文件", out1)

        # 3. fix: 修复 workspace_map.md
        out2, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])
        self.assertIn("✅ workspace_map.md 已修复", out2)

        # 4. register: 补登 versions.md
        out3, _ = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--apply",
        ])
        self.assertIn("✅ 已补登", out3)

        # 5. check: 验证归零
        out4, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])
        self.assertIn("3.4 虚假条目", out4)

        # 6. register: 验证全部已登记
        out5, _ = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])
        self.assertIn("全部已登记", out5)

    def test_basename_registration_flow(self):
        """basename 匹配：versions.md 用 basename 登记，check 不误报"""
        make_fixture_dir(self.tmp, source_files=["subdir/a.py"])
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| a.py | v0.1 | 2026-07-13 | basename 登记 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        # basename 匹配应不报 missing
        self.assertIn("登记但磁盘不存在: 0", out)

    def test_directory_entry_in_versions_md(self):
        """versions.md 中目录项（以 / 结尾）检查磁盘目录存在性"""
        (self.tmp / "subdir").mkdir()
        (self.tmp / "subdir" / "a.py").write_text("# a", encoding="utf-8")
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── subdir/\n```\n", encoding="utf-8"
        )
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n"
            "| subdir/ | v0.1 | 2026-07-13 | 目录 |\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("登记但磁盘不存在: 0", out,
                      "磁盘上存在的目录不应被误报为缺失")


# ═════════════════════════════════════════════════════════
# 输出格式验证
# ═════════════════════════════════════════════════════════

class TestOutputFormat(unittest.TestCase):
    """输出格式和标记验证"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_check_output_uses_correct_markers(self):
        """registry-check 输出使用正确的标记"""
        make_fixture_dir(self.tmp, source_files=["a.py"])

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--dry-run",
        ])

        # 验证关键标记
        self.assertIn("🔍", out, "应有扫描标记")
        self.assertIn("✅", out, "应有完成标记")
        self.assertIn("──", out, "应有分隔线")
        self.assertIn("3.4", out, "应有 3.4 检查项")
        self.assertIn("3.5", out, "应有 3.5 检查项")

    def test_register_output_uses_correct_markers(self):
        """registry-register 输出使用正确的标记"""
        files = [f"f_{i}.py" for i in range(3)]
        make_fixture_dir(self.tmp, source_files=files)
        (self.tmp / "versions.md").write_text(
            "## 工程化产物\n\n| 文件 | 版本 | 日期 | 备注 |\n|---|---|---|---|\n\n"
            "## 弃用记录\n\n| 项 | 弃用版本 | 替代 |\n|---|---|---|\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(register_main, [
            "auto_register_versions", "--target", str(self.tmp), "--dry-run",
        ])

        self.assertIn("🔍", out, "应有扫描标记")
        self.assertIn("➕", out, "应有新增标记")
        self.assertIn("--apply", out, "应有提示")

    def test_fix_output_has_fix_summary(self):
        """registry-check --fix 输出包含修复摘要"""
        make_fixture_dir(self.tmp, source_files=["a.py", "b.md"],
                         phantom_in_tree=["ghost.py"])
        (self.tmp / "workspace_map.md").write_text(
            "```\nmeta_peg_agent/\n├── a.py\n├── ghost.py\n```\n",
            encoding="utf-8"
        )

        out, _ = run_cli_main(fix_main, [
            "fix_versions_refs", "--target", str(self.tmp), "--fix",
        ])

        self.assertIn("移除", out, "应有移除计数")
        self.assertIn("添加", out, "应有添加计数")


if __name__ == "__main__":
    unittest.main(verbosity=2)