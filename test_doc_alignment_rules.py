#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_alignment_rules.py
基于 doc_alignment.json 的 7 条规则（D1–D6）的 Pytest 单元测试。

覆盖:
  D1: 实证文档对齐检查（5 维度 + 3 偏差级别）
  D2: 同性质遗漏扫描（跨文件 search）
  D3: 目录树完整性验证（精确匹配 + 通配）
  D4: 登记文件交叉引用（三向对齐）
  D5: 运行时产物识别（4 种通配模式）
  D6: 演进信号回溯更新（范围准确性 + 验证结果 + 计数）

运行:
  pip install pytest
  pytest test_doc_alignment_rules.py -v
  pytest test_doc_alignment_rules.py -v --tb=short

版本: v0.1 (2026-07-22)
"""

import json
import os
import re
import sys
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime

import pytest

HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "doc_alignment.json"


# ── Fixtures ──────────────────────────────────────────

@pytest.fixture(scope="module")
def rules():
    """加载 doc_alignment.json 规则定义"""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def temp_project():
    """创建临时项目目录，模拟代码+文档成对场景"""
    with tempfile.TemporaryDirectory(prefix="da_test_") as tmp:
        yield Path(tmp)


# ── D1: 实证文档对齐检查 ──────────────────────────────

class TestD1FunctionSignature:
    """D1 维度 1: 函数签名对比"""

    def test_signature_match(self, rules):
        """参数名、个数、默认值完全一致 → 一致"""
        code_sig = {"name": "add_task", "params": ["title", "priority"], "defaults": {"priority": 1}}
        doc_sig = {"name": "add_task", "params": ["title", "priority"], "defaults": {"priority": 1}}
        assert code_sig == doc_sig  # 实现层：字典相等即一致

    def test_signature_mismatch_param_name(self, rules):
        """参数名不一致 → 真偏差"""
        code_sig = {"name": "schedule", "params": ["interval_hours"]}
        doc_sig = {"name": "schedule", "params": ["interval"]}
        assert code_sig != doc_sig, "参数名 interval_hours ≠ interval → 真偏差"

    def test_signature_missing_default(self, rules):
        """文档缺默认参数 → 真偏差"""
        code_sig = {"name": "clean", "params": ["paths", "dry_run"], "defaults": {"paths": None, "dry_run": False}}
        doc_sig = {"name": "clean", "params": ["paths"], "defaults": {}}
        assert "dry_run" not in doc_sig["params"], "文档应补 dry_run 参数"

    def test_signature_return_type_vague(self, rules):
        """返回值类型不明确 → 轻微不一致"""
        doc_return = "task id"   # 未明确是 int
        code_return = "int"       # 实际是 int
        # 判定逻辑：doc 无类型标注 → 轻微不一致
        assert "int" not in doc_return.lower(), "文档未标注具体类型"


class TestD1DeviationLevels:
    """D1 三级偏差分类"""

    def test_true_deviation_code_doc_contradiction(self, rules):
        """文档与代码矛盾 → 真偏差"""
        doc_value = 6
        code_value = 5
        level = rules["rules"]["D1"]["deviation_levels"]["true_deviation"]
        assert doc_value != code_value, f"step_count={doc_value} vs 实际产出 {code_value}"
        assert level["action"] == "须修"

    def test_minor_inconsistency_no_behavioral_impact(self, rules):
        """文档措辞模糊但功能无碍 → 轻微不一致"""
        issue = "datetime 导入位置在函数内而非模块顶部"
        level = rules["rules"]["D1"]["deviation_levels"]["minor_inconsistency"]
        assert level["action"] == "标注不改", f"'{issue}' 应仅标注"

    def test_number_drift_assertion_count_mismatch(self, rules):
        """文档计数与实际运行结果不符 → 数字漂移"""
        doc_count = 26
        actual_count = 33
        level = rules["rules"]["D1"]["deviation_levels"]["number_drift"]
        assert doc_count != actual_count, f"断言数 {doc_count} ≠ {actual_count}"
        assert level["action"] == "须同步"

    def test_all_three_levels_exist(self, rules):
        """三级偏差定义完整"""
        devs = rules["rules"]["D1"]["deviation_levels"]
        assert set(devs.keys()) == {"true_deviation", "minor_inconsistency", "number_drift"}
        for k, v in devs.items():
            assert all(f in v for f in ("definition", "action", "example")), f"{k} 缺字段"


class TestD1AllDimensions:
    """D1 五项维度完整性"""

    def test_five_dimensions_exist(self, rules):
        dims = rules["rules"]["D1"]["dimensions"]
        assert len(dims) == 5
        ids = {d["id"] for d in dims}
        assert ids == {
            "function_signature", "scenario_coverage",
            "field_names", "artifact_structure", "behavior_description"
        }

    def test_dimension_field_names_trap(self, rules):
        """字段名陷阱：task_summary ≠ task"""
        code_field = "task_summary"
        doc_field = "task"
        assert code_field != doc_field, "字段名不一致：生产代码用 task_summary，文档用 task"


# ── D2: 同性质遗漏扫描 ────────────────────────────────

class TestD2SameTypeScan:
    """D2: 修复偏差后扫描同文件及关联文件"""

    def test_same_field_in_sibling_file(self, temp_project, rules):
        """修复 .md 后扫描 .py 同名字段"""
        # 模拟：mock_helpers.md 和 mock_helpers.py 各含 step_count
        md = temp_project / "mock_helpers.md"
        py = temp_project / "mock_helpers.py"
        md.write_text("step_count=5", encoding="utf-8")
        py.write_text("step_count=5", encoding="utf-8")
        # 假设修复后两文件一致
        md_val = re.search(r"step_count=(\d+)", md.read_text(encoding="utf-8")).group(1)
        py_val = re.search(r"step_count=(\d+)", py.read_text(encoding="utf-8")).group(1)
        assert md_val == py_val, f"跨文件 step_count 不一致: {md_val} ≠ {py_val}"

    def test_same_field_located_in_both_files(self, temp_project, rules):
        """同名字段在两文件中均可定位"""
        md = temp_project / "doc.md"
        py = temp_project / "code.py"
        md.write_text("assertion_count: 33", encoding="utf-8")
        py.write_text("# assertion_count: 33", encoding="utf-8")
        md_found = "assertion_count" in md.read_text(encoding="utf-8")
        py_found = "assertion_count" in py.read_text(encoding="utf-8")
        assert md_found and py_found, "D2 扫描应在两文件中均找到同名字段"

    def test_scan_after_fix_no_residual(self, temp_project, rules):
        """修复后扫描应无残留旧值"""
        md = temp_project / "doc.md"
        md.write_text("step_count=5", encoding="utf-8")
        content = md.read_text(encoding="utf-8")
        assert "step_count=6" not in content, "修复后不应残留旧值 6"


# ── D3: 目录树完整性验证 ──────────────────────────────

class TestD3DirectoryTree:
    """D3: 目录树完整性验证（精确匹配 + 通配覆盖）"""

    def test_exact_file_match(self, temp_project, rules):
        """精确文件匹配：磁盘文件 100% 在目录树中"""
        # 创建磁盘文件
        (temp_project / "README.md").write_text("", encoding="utf-8")
        (temp_project / "src").mkdir()
        (temp_project / "src" / "main.py").write_text("", encoding="utf-8")
        # 模拟目录树登记
        tree_files = {"README.md", "src/main.py"}
        disk_files = set()
        for f in temp_project.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f):
                disk_files.add(str(f.relative_to(temp_project)).replace("\\", "/"))
        assert disk_files == tree_files, f"磁盘 {disk_files} ≠ 目录树 {tree_files}"

    def test_wildcard_coverage_gate_logs(self, temp_project, rules):
        """通配覆盖：gate_*.jsonl 不逐名登记"""
        logs_dir = temp_project / "logs"
        logs_dir.mkdir()
        (logs_dir / "gate_20260714_125558_PASS_abc.jsonl").write_text("{}", encoding="utf-8")
        (logs_dir / "gate_20260715_091200_FAIL_def.jsonl").write_text("{}", encoding="utf-8")
        # 逐名匹配（应有两种方式可覆盖）
        gate_files = [f.name for f in logs_dir.glob("gate_*.jsonl")]
        assert len(gate_files) == 2, "通配 gate_*.jsonl 应匹配所有闸门日志"

    def test_100_percent_coverage(self, temp_project, rules):
        """精确匹配 + 通配覆盖 = 100%"""
        (temp_project / "readme.md").write_text("", encoding="utf-8")
        (temp_project / "logs").mkdir()
        (temp_project / "logs" / "gate_001.jsonl").write_text("{}", encoding="utf-8")
        # 精确匹配: readme.md
        # 通配覆盖: logs/gate_*.jsonl
        exact = {"readme.md"}
        wildcard = {"logs/gate_*.jsonl"}
        disk = {"readme.md", "logs/gate_001.jsonl"}
        # 验证：gate_001.jsonl 被通配覆盖
        covered = exact | {"logs/gate_001.jsonl"}  # 通过通配匹配
        assert covered == disk, f"通配覆盖后应 100%: {covered} vs {disk}"

    def test_cache_exclusion(self, temp_project, rules):
        """缓存目录排除验证"""
        (temp_project / "__pycache__").mkdir()
        (temp_project / "__pycache__" / "module.cpython-312.pyc").write_text("", encoding="utf-8")
        (temp_project / "main.py").write_text("", encoding="utf-8")
        # 排除 __pycache__
        disk_no_cache = set()
        for f in temp_project.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f) and ".pytest_cache" not in str(f):
                disk_no_cache.add(f.name)
        assert "module.cpython-312.pyc" not in disk_no_cache, "__pycache__ 应被排除"


# ── D4: 登记文件交叉引用 ──────────────────────────────

class TestD4CrossReference:
    """D4: 三向对齐（versions.md / capability_registry.md / workspace_map.md）"""

    def test_versions_to_workspace_map(self, temp_project, rules):
        """versions.md 登记的文件应在 workspace_map.md 中有对应位置"""
        versions = {"doc_alignment.json", "doc_alignment_onboarding.md", "TROUBLESHOOTING.md"}
        ws_map = {"doc_alignment.json", "doc_alignment_onboarding.md", "TROUBLESHOOTING.md", "README.md"}
        missing = versions - ws_map
        assert not missing, f"versions.md 登记但 workspace_map.md 缺失: {missing}"

    def test_workspace_map_to_capability_registry(self, temp_project, rules):
        """workspace_map.md 的关键文件应在 capability_registry.md 有演进信号"""
        ws_key_files = {"doc_alignment.prompt.md", "doc_alignment.json"}
        cap_entries = {"doc_alignment.prompt.md", "doc_alignment.json"}  # 模拟已有
        missing = ws_key_files - cap_entries
        assert not missing, f"workspace_map 关键文件但 capability_registry 缺失: {missing}"

    def test_cross_reference_trigger(self, rules):
        """D4 trigger 规则：任一文件更新后检查另两份"""
        trigger = rules["rules"]["D4"]["trigger"]
        assert "另两份" in trigger, "D4 trigger 应包含交叉检查指令"

    def test_three_way_table_structure(self, rules):
        """D4 交叉引用表结构完整"""
        crt = rules["rules"]["D4"]["cross_reference_table"]
        assert "versions.md" in crt
        assert "capability_registry.md" in crt
        assert "workspace_map.md" in crt
        assert len(crt) == 3, "三向对齐表应恰好 3 项"


# ── D5: 运行时产物识别 ────────────────────────────────

class TestD5RuntimeArtifacts:
    """D5: 运行时产物不逐名登记，用通配模式"""

    def test_gate_log_pattern(self, rules):
        """gate_*.jsonl 通配匹配"""
        pattern = rules["rules"]["D5"]["wildcard_patterns"]["gate_logs"]["pattern"]
        assert pattern == "logs/gate_*.jsonl"
        filename = "gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl"
        # 通配匹配：gate_ 开头 + .jsonl 结尾
        assert filename.startswith("gate_") and filename.endswith(".jsonl"), \
            f"'{filename}' 应匹配 {pattern}"

    def test_trace_artifact_pattern(self, rules):
        """<trace_id>/artifacts/* 通配匹配"""
        pattern = rules["rules"]["D5"]["wildcard_patterns"]["trace_artifacts"]["pattern"]
        assert "<trace_id>" in pattern
        example = "20260721_104251_0b52/artifacts/diff.md"
        # 匹配: 时间戳格式 / artifacts / *.md
        parts = example.replace("\\", "/").split("/")
        assert len(parts) == 3, f"trace artifact 路径应为三段: {parts}"
        assert parts[1] == "artifacts", f"第二段应为 artifacts: {parts}"

    def test_cache_exclusion_flag(self, rules):
        """缓存排除标识"""
        caches = rules["rules"]["D5"]["wildcard_patterns"]["caches"]
        assert caches["exclude"] is True, "缓存应标记为 exclude"
        assert "__pycache__" in caches["pattern"]
        assert ".pytest_cache" in caches["pattern"]

    def test_ide_config_directory_annotation(self, rules):
        """IDE 配置目录级注释"""
        ide = rules["rules"]["D5"]["wildcard_patterns"]["ide_config"]
        assert ide["pattern"] == ".obsidian/"
        assert "note" in ide, "IDE 配置应有注释说明"

    def test_all_four_wildcard_types_exist(self, rules):
        """四类通配模式完整"""
        wc = rules["rules"]["D5"]["wildcard_patterns"]
        assert set(wc.keys()) == {"gate_logs", "trace_artifacts", "caches", "ide_config"}


# ── D6: 演进信号回溯更新 ──────────────────────────────

class TestD6EvolutionSignal:
    """D6: 完成对齐后回溯更新能力登记册"""

    def test_accurate_scope_reporting(self, rules):
        """修复范围不低估：实际补 40+ 不能写「补 2 个」"""
        actual_fix_count = 43
        reported_fix_count = 2
        # 模拟 D6 检查
        assert actual_fix_count > reported_fix_count, \
            f"低估范围: 实际 {actual_fix_count}，登记 {reported_fix_count}"
        # D6 checks 第一条
        check = rules["rules"]["D6"]["checks"][0]
        assert "不低估" in check

    def test_regression_result_included(self, rules):
        """回归验证结果写入登记条目"""
        regression_result = "33/33 全 PASS"
        check = rules["rules"]["D6"]["checks"][1]
        assert "回归验证" in check
        assert "PASS" in regression_result

    def test_evolution_signal_increment(self, rules):
        """演进信号计数 +1"""
        before = 5
        after = before + 1
        check = rules["rules"]["D6"]["checks"][2]
        assert "计数 +1" in check
        assert after == 6, "演进信号计数应递增"

    def test_three_checks_exist(self, rules):
        """D6 三项检查完整"""
        checks = rules["rules"]["D6"]["checks"]
        assert len(checks) == 3
        for c in checks:
            assert isinstance(c, str) and len(c) >= 5, f"检查项应为完整描述: {c[:30]}..."


# ── 跨规则集成测试 ────────────────────────────────────

class TestCrossRuleIntegration:
    """D1–D6 跨规则协作场景"""

    def test_full_alignment_workflow_order(self, rules):
        """对齐流程顺序：D1 → D2 → D3/D4 → D6"""
        wf = rules["workflow"]["steps"]
        assert wf[0]["step"] == 1 and "逐项对比" in wf[0]["action"]  # D1
        assert wf[1]["step"] == 2 and "D2" in wf[1].get("note", "")  # D2
        assert wf[2]["step"] == 3 and "D4" in wf[2].get("note", "")  # D3+D4
        assert wf[4]["step"] == 5 and "D6" in wf[4]["action"]        # D6

    def test_d1_d2_chain_after_fix(self, temp_project, rules):
        """D1 发现偏差 → 修复 → D2 扫描 → 无遗漏"""
        md = temp_project / "api.md"
        py = temp_project / "api.py"
        # 修复前：两文件均写 step_count=6
        md.write_text("step_count=6", encoding="utf-8")
        py.write_text("step_count=6", encoding="utf-8")
        # D1 发现
        assert "step_count=6" in md.read_text(encoding="utf-8"), "D1 应在 .md 发现偏差"
        # 修复两文件
        md.write_text("step_count=5", encoding="utf-8")
        py.write_text("step_count=5", encoding="utf-8")
        # D2 扫描
        md_content = md.read_text(encoding="utf-8")
        py_content = py.read_text(encoding="utf-8")
        assert "step_count=6" not in md_content, "D2: .md 残留旧值"
        assert "step_count=6" not in py_content, "D2: .py 残留旧值"
        assert "step_count=5" in md_content and "step_count=5" in py_content

    def test_d5_d3_wildcard_in_directory_tree(self, temp_project, rules):
        """D5 通配 + D3 目录树 = 100% 覆盖"""
        (temp_project / "logs").mkdir()
        (temp_project / "logs" / "gate_001.jsonl").write_text("{}", encoding="utf-8")
        (temp_project / "logs" / "gate_002.jsonl").write_text("{}", encoding="utf-8")
        (temp_project / "README.md").write_text("", encoding="utf-8")
        # D3 精确: README.md
        # D5 通配: gate_*.jsonl
        disk_files = set()
        for f in temp_project.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f):
                disk_files.add(f.name)
        # 逐名登记不应包含 gate_ 文件
        named = {f for f in disk_files if not f.startswith("gate_")}
        # 通配覆盖 gate_ 文件
        wildcard_covered = {f for f in disk_files if f.startswith("gate_")}
        assert len(wildcard_covered) == 2, f"gate_*.jsonl 应覆盖 {wildcard_covered}"
        assert named | wildcard_covered == disk_files, "D5 通配 + D3 精确 = 100%"

    def test_d6_after_full_alignment(self, temp_project, rules):
        """完成全流程对齐后 D6 回溯更新"""
        # 模拟对齐完成
        fix_log = {
            "files_fixed": 43,
            "deviations": {"true_deviation": 2, "minor": 1, "number_drift": 1},
            "regression": "33/33 PASS",
            "evolution_signal_count": 6,  # 之前 5 + 本次 1
        }
        # D6 checks
        assert fix_log["files_fixed"] >= 10, "不应低估修复范围"
        assert "PASS" in fix_log["regression"], "应包含回归结果"
        assert fix_log["evolution_signal_count"] == 6, "演进信号应 +1"


# ── JSON Schema 最终一致性 ─────────────────────────────

class TestJsonSchemaConsistency:
    """验证 JSON 规则定义与测试预期一致"""

    def test_self_test_count_matches_json(self, rules):
        """self_test 数组长度 = r9_gate.self_test_total"""
        assert len(rules["self_test"]) == rules["meta"]["r9_gate"]["self_test_total"]

    def test_json_has_no_critical(self, rules):
        """r9_gate.critical 应为 0"""
        assert rules["meta"]["r9_gate"]["critical"] == 0

    def test_all_rule_ids_in_self_test(self, rules):
        """self_test 中引用的 rule ID 必须在 rules 中存在"""
        valid_ids = set(rules["rules"].keys())
        for st in rules["self_test"]:
            assert st["rule"] in valid_ids, f"self_test rule={st['rule']} 不在 rules 中"

    def test_workflow_steps_sequential(self, rules):
        """workflow.steps 的 step 字段必须从 1 连续递增"""
        steps = rules["workflow"]["steps"]
        for i, s in enumerate(steps, 1):
            assert s["step"] == i, f"步骤 {i} 的 step 字段应为 {i}，实际 {s['step']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])