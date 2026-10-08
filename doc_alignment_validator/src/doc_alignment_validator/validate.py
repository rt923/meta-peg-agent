#!/usr/bin/env python3
"""
validate.py — doc_alignment.json 11 项完整性校验引擎。

从 validate_doc_alignment_json.py 提取，改为可 import 的模块形式。
"""

import json
import os
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_JSON = PACKAGE_DIR / "data" / "doc_alignment.json"

REQUIRED_TOP_KEYS = [
    "meta", "role", "rules", "workflow", "self_test", "security", "related_files"
]
REQUIRED_META_KEYS = [
    "name", "version", "date", "type", "dependency", "status",
    "evolution_signal_source", "r9_gate"
]
REQUIRED_RULE_IDS = ["D1", "D2", "D3", "D4", "D5", "D6"]
REQUIRED_D1_DIMENSIONS = [
    "function_signature", "scenario_coverage", "field_names",
    "artifact_structure", "behavior_description"
]
REQUIRED_D1_DEVIATION_LEVELS = [
    "true_deviation", "minor_inconsistency", "number_drift"
]
REQUIRED_D5_WILDCARD_KEYS = [
    "gate_logs", "trace_artifacts", "caches", "ide_config"
]
REQUIRED_SELF_TEST_KEYS = ["id", "rule", "name", "input", "expected"]
REQUIRED_SECURITY_KEYS = ["section_12", "section_13"]
VALID_RULE_IDS = {"D1", "D2", "D3", "D4", "D5", "D6"}


def get_json_path():
    """返回随包分发的 doc_alignment.json 绝对路径"""
    return DEFAULT_JSON


def fail(msg):
    raise AssertionError(msg)


def check_json_syntax(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        fail(f"JSON 语法错误: {e}")
    except FileNotFoundError:
        fail(f"文件不存在: {path}")


def check_top_level_keys(data):
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            fail(f"顶层缺字段: {key}")


def check_meta(data):
    meta = data["meta"]
    for key in REQUIRED_META_KEYS:
        if key not in meta:
            fail(f"meta 缺字段: {key}")
    assert isinstance(meta["name"], str), "meta.name 应为 str"
    assert isinstance(meta["version"], str), "meta.version 应为 str"
    assert isinstance(meta["date"], str), "meta.date 应为 str"
    assert isinstance(meta["type"], str), "meta.type 应为 str"
    assert isinstance(meta["dependency"], str), "meta.dependency 应为 str"
    assert isinstance(meta["status"], str), "meta.status 应为 str"
    assert isinstance(meta["evolution_signal_source"], str)
    r9 = meta["r9_gate"]
    assert isinstance(r9, dict), "meta.r9_gate 应为 dict"
    assert isinstance(r9["self_test_total"], int)
    assert isinstance(r9["critical"], int)
    assert isinstance(r9["status"], str)
    assert r9["critical"] == 0, f"r9_gate.critical 应为 0，实际 {r9['critical']}"


def check_role(data):
    role = data["role"]
    assert isinstance(role, dict), "role 应为 dict"
    for key in ("identity", "responsibility"):
        if key not in role:
            fail(f"role 缺字段: {key}")
        assert isinstance(role[key], str), f"role.{key} 应为 str"


def check_rules(data):
    rules = data["rules"]
    assert isinstance(rules, dict), "rules 应为 dict"
    for rid in REQUIRED_RULE_IDS:
        if rid not in rules:
            fail(f"rules 缺规则: {rid}")
    d1 = rules["D1"]
    assert isinstance(d1, dict), "D1 应为 dict"
    for key in ("name", "description", "dimensions", "deviation_levels"):
        if key not in d1:
            fail(f"D1 缺字段: {key}")
    dims = d1["dimensions"]
    assert isinstance(dims, list) and len(dims) == 5
    for dim in dims:
        for key in ("id", "label", "detail"):
            if key not in dim:
                fail(f"D1.dimensions 项缺字段: {key}")
    dim_ids = {d["id"] for d in dims}
    assert dim_ids == set(REQUIRED_D1_DIMENSIONS)
    devs = d1["deviation_levels"]
    assert isinstance(devs, dict)
    for key in REQUIRED_D1_DEVIATION_LEVELS:
        if key not in devs:
            fail(f"D1.deviation_levels 缺: {key}")
        for sub in ("definition", "action", "example"):
            if sub not in devs[key]:
                fail(f"D1.deviation_levels.{key} 缺: {sub}")
    for rid in ("D2", "D3", "D4", "D6"):
        r = rules[rid]
        for key in ("name", "description"):
            if key not in r:
                fail(f"{rid} 缺字段: {key}")
    d5 = rules["D5"]
    wc = d5.get("wildcard_patterns", {})
    assert isinstance(wc, dict)
    for key in REQUIRED_D5_WILDCARD_KEYS:
        if key not in wc:
            fail(f"D5.wildcard_patterns 缺: {key}")
        assert "pattern" in wc[key], f"D5.wildcard_patterns.{key} 缺 pattern"


def check_workflow(data):
    wf = data["workflow"]
    assert isinstance(wf, dict)
    steps = wf.get("steps", [])
    assert isinstance(steps, list) and len(steps) == 5
    for i, s in enumerate(steps, 1):
        assert s.get("step") == i
        assert "action" in s


def check_self_test(data):
    st = data["self_test"]
    assert isinstance(st, list) and len(st) == 7
    for i, item in enumerate(st, 1):
        for key in REQUIRED_SELF_TEST_KEYS:
            if key not in item:
                fail(f"self_test[{i-1}] 缺字段: {key}")
        assert item["id"] == i
        if item["rule"] not in VALID_RULE_IDS:
            fail(f"self_test[{i-1}].rule 无效: {item['rule']}")


def check_security(data):
    sec = data["security"]
    assert isinstance(sec, dict)
    for key in REQUIRED_SECURITY_KEYS:
        if key not in sec:
            fail(f"security 缺字段: {key}")
        for sub in ("title", "content"):
            if sub not in sec[key]:
                fail(f"security.{key} 缺: {sub}")


def check_related_files(data):
    rf = data["related_files"]
    assert isinstance(rf, dict)
    # 检查自引用
    if "json_export" not in rf:
        fail("related_files 缺少 json_export 自引用")
    # 磁盘存在性检查：仅在源 repo 环境下执行（安装包中跳过）
    for key, rel_path in rf.items():
        assert isinstance(rel_path, str)
    # 尝试定位源 repo 根目录（向上查找 meta_peg_agent/）
    repo_root = PACKAGE_DIR
    for _ in range(5):
        if (repo_root / "versions.md").exists():
            break
        repo_root = repo_root.parent
    if (repo_root / "versions.md").exists():
        # 在源 repo 中，检查文件存在性
        for key, rel_path in rf.items():
            fname = rel_path.split("(")[0].strip().split("/")[-1]
            if fname.endswith((".md", ".json")) and "/" not in rel_path.split("(")[0].strip():
                if not (repo_root / fname).exists():
                    fail(f"related_files.{key} → {fname} 在磁盘上不存在 (repo_root={repo_root})")


def check_null_values(data, path=""):
    if isinstance(data, dict):
        for k, v in data.items():
            if v is None:
                fail(f"字段 {path}.{k} 值为 None")
            check_null_values(v, f"{path}.{k}" if path else k)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            if v is None:
                fail(f"字段 {path}[{i}] 值为 None")
            check_null_values(v, f"{path}[{i}]")


def check_array_emptiness(data):
    if not data["rules"]["D1"]["dimensions"]:
        fail("D1.dimensions 为空数组")
    if not data["self_test"]:
        fail("self_test 为空数组")
    if not data["workflow"]["steps"]:
        fail("workflow.steps 为空数组")


def validate(json_path=None):
    if json_path is None:
        json_path = DEFAULT_JSON
    print(f"加载 JSON: {json_path}")
    data = check_json_syntax(str(json_path))
    print("  [✓] 1. JSON 语法合法")
    check_top_level_keys(data)
    print("  [✓] 2. 顶层字段完整 (7/7)")
    check_meta(data)
    print("  [✓] 3. meta 字段完整 + 类型正确")
    check_role(data)
    print("  [✓] 4. role 字段完整")
    check_rules(data)
    print("  [✓] 5. D1–D6 规则结构完整 (5 维度 + 3 偏差 + 4 通配)")
    check_workflow(data)
    print("  [✓] 6. workflow 五步完整 (step 1–5)")
    check_self_test(data)
    print("  [✓] 7. self_test 7 条完整 (rule 引用有效)")
    check_security(data)
    print("  [✓] 8. security §12/§13 完整")
    check_related_files(data)
    print("  [✓] 9. related_files 路径一致性")
    check_null_values(data)
    print("  [✓] 10. 空值校验通过 (0 null)")
    check_array_emptiness(data)
    print("  [✓] 11. 数组非空校验通过")
    print(f"\n{'='*50}")
    print("全部校验通过 ✅ — 外部工具可安全加载")
    return True


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="doc_alignment JSON 校验")
    p.add_argument("--json-path", default=str(DEFAULT_JSON))
    args = p.parse_args()
    try:
        validate(args.json_path)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 校验失败: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """entry_points 入口"""
    import argparse
    p = argparse.ArgumentParser(description="doc_alignment JSON 校验")
    p.add_argument("--json-path", default=str(DEFAULT_JSON))
    args = p.parse_args()
    try:
        validate(args.json_path)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 校验失败: {e}", file=sys.stderr)
        sys.exit(1)