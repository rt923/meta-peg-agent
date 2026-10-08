#!/usr/bin/env python3
"""
verify_mock_helpers.py
验证 make_mock_hash_store + make_mock_full_session 是否正常工作

按用法示例构造 mock 数据，跑断言验证：
  1. make_mock_hash_store: 4 种 scenario 都能正确写入
  2. make_mock_full_session: 完整 PEG-A 会话 trace 三件套齐全
"""
import sys
import os
import json
import tempfile
import hashlib
import shutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mock_helpers import make_mock_hash_store, make_mock_full_session


def section(title):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def assert_true(cond, msg):
    status = "✓ PASS" if cond else "✗ FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        raise AssertionError(msg)


def verify_make_mock_hash_store():
    section("验证 1: make_mock_hash_store 4 种 scenario")
    tmp = tempfile.mkdtemp(prefix="verify_hs_")
    try:
        # scenario: no_field（旧产物）
        p1 = os.path.join(tmp, "no_field.json")
        make_mock_hash_store(p1, "no_field")
        with open(p1, encoding="utf-8") as f:
            s1 = json.load(f)
        assert_true("guardrail_token_hash" not in s1, "no_field: 无 guardrail_token_hash 字段")
        assert_true(s1.get("file_hash") == "a" * 64, "no_field: file_hash 正确")

        # scenario: null_field
        p2 = os.path.join(tmp, "null_field.json")
        make_mock_hash_store(p2, "null_field")
        with open(p2, encoding="utf-8") as f:
            s2 = json.load(f)
        assert_true("guardrail_token_hash" in s2, "null_field: 字段存在")
        assert_true(s2.get("guardrail_token_hash") is None, "null_field: 值为 None")

        # scenario: valid_hash
        p3 = os.path.join(tmp, "valid_hash.json")
        make_mock_hash_store(p3, "valid_hash")
        with open(p3, encoding="utf-8") as f:
            s3 = json.load(f)
        expected_hash = hashlib.sha256(b"mock-token-123").hexdigest()
        assert_true(s3.get("guardrail_token_hash") == expected_hash, "valid_hash: 哈希值正确")

        # scenario: corrupt（非 JSON 内容）
        p4 = os.path.join(tmp, "corrupt.json")
        make_mock_hash_store(p4, "corrupt")
        with open(p4, encoding="utf-8") as f:
            raw = f.read()
        assert_true(raw == "not a valid json {{{", "corrupt: 写入非 JSON 字符串")
        try:
            json.loads(raw)
            assert_true(False, "corrupt: 应解析失败但成功了")
        except json.JSONDecodeError:
            assert_true(True, "corrupt: JSON 解析失败（符合预期）")

        # scenario: 未知值应抛 ValueError
        try:
            make_mock_hash_store(os.path.join(tmp, "x.json"), "unknown_scenario")
            assert_true(False, "未知 scenario 应抛 ValueError")
        except ValueError as e:
            assert_true("未知 scenario" in str(e), "未知 scenario 抛 ValueError 含中文提示")

        print(f"\n  4/4 scenario 验证通过")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify_make_mock_full_session():
    section("验证 2: make_mock_full_session 完整 PEG-A 会话")
    tmp = tempfile.mkdtemp(prefix="verify_session_")
    traces_root = os.path.join(tmp, "traces")
    os.makedirs(traces_root)
    try:
        # 调用高阶函数（按用法示例）
        result = make_mock_full_session(
            traces_root=traces_root,
            trace_id="20260721_100000_full",  # 固定 ID 便于断言
            task="验证 mock_helpers",
            status="completed",
            include_artifact=True,
            artifact_content="# 自定义 artifact\n内容\n",
        )

        # 验证返回值结构
        assert_true(isinstance(result, dict), "返回 dict")
        assert_true("trace_dir" in result, "返回值含 trace_dir")
        assert_true("trace_id" in result, "返回值含 trace_id")
        assert_true("reasoning_path" in result, "返回值含 reasoning_path")
        assert_true("manifest_path" in result, "返回值含 manifest_path")
        assert_true("artifact_path" in result, "返回值含 artifact_path")
        assert_true(result["trace_id"] == "20260721_100000_full", "trace_id 正确")

        # 验证 trace_dir 存在
        assert_true(os.path.isdir(result["trace_dir"]), "trace_dir 目录存在")

        # 验证 reasoning.jsonl: 6 行（trace_start + 5 拍）
        with open(result["reasoning_path"], encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        assert_true(len(lines) == 6, f"reasoning.jsonl 行数=6（实际={len(lines)}）")

        # 验证 reasoning.jsonl 第一行是 trace_start
        first = json.loads(lines[0])
        assert_true(first.get("event") == "trace_start", "第一行 event=trace_start")

        # 验证 reasoning.jsonl 后续 5 行 phase 是 Plan/Act/Observe/Reflect/Coordinate
        phases = [json.loads(l).get("phase") for l in lines[1:]]
        expected_phases = ["Plan", "Act", "Observe", "Reflect", "Coordinate"]
        assert_true(phases == expected_phases, f"5 拍 phase 顺序正确（实际={phases}）")

        # 验证 manifest.json
        with open(result["manifest_path"], encoding="utf-8") as f:
            manifest = json.load(f)
        assert_true(manifest.get("status") == "completed", "manifest status=completed")
        assert_true(manifest.get("step_count") == 5, f"manifest step_count=5（实际={manifest.get('step_count')}）")
        assert_true(manifest.get("task_summary") == "验证 mock_helpers", "manifest task_summary 正确")
        assert_true(len(manifest.get("artifacts", [])) == 1, "manifest 含 1 个 artifact")

        # 验证 artifact 文件存在 + 内容正确
        assert_true(os.path.exists(result["artifact_path"]), "artifact 文件存在")
        with open(result["artifact_path"], encoding="utf-8") as f:
            art_content = f.read()
        assert_true(art_content == "# 自定义 artifact\n内容\n", "artifact 内容是自定义的")

        # 验证 manifest 中 artifact 路径已更新为 full-art
        art_entry = manifest["artifacts"][0]
        assert_true(art_entry["id"] == "20260721_100000_full-full-art", "artifact id 已重命名")
        assert_true(art_entry["path"] == "artifacts/20260721_100000_full-full-art.md", "artifact path 已更新")

        # 验证 build_historical_index 能扫描到
        import importlib
        if "build_historical_index" in sys.modules:
            importlib.reload(sys.modules["build_historical_index"])
        import build_historical_index as bhi
        md, count = bhi.scan_future_traces(traces_root)
        assert_true(count == 1, f"build_historical_index 扫到 1 条 trace（实际={count}）")
        assert_true("20260721_100000_full" in md, "索引页含 trace_id")
        assert_true("验证 mock_helpers" in md, "索引页含 task_summary")

        print(f"\n  完整 PEG-A 会话 trace 验证通过")
        print(f"  trace_dir: {result['trace_dir']}")
        print(f"  trace_id:  {result['trace_id']}")
        print(f"  reasoning.jsonl: 6 行（1 trace_start + 5 拍）")
        print(f"  manifest.json: status=completed, 1 artifact")
        print(f"  artifact: 20260721_100000_full-full-art.md（自定义内容）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify_no_artifact_variant():
    section("验证 3: make_mock_full_session（无 artifact 变体）")
    tmp = tempfile.mkdtemp(prefix="verify_noart_")
    traces_root = os.path.join(tmp, "traces")
    os.makedirs(traces_root)
    try:
        result = make_mock_full_session(
            traces_root=traces_root,
            task="无 artifact 测试",
            include_artifact=False,
        )
        assert_true(result["artifact_path"] is None, "include_artifact=False 时 artifact_path=None")
        assert_true(os.path.isdir(result["trace_dir"]), "trace_dir 仍创建")

        with open(result["manifest_path"], encoding="utf-8") as f:
            manifest = json.load(f)
        assert_true(len(manifest.get("artifacts", [])) == 0, "manifest artifacts 为空列表")

        print(f"\n  无 artifact 变体验证通过")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("# mock_helpers.py 验证脚本")
    print("# 验证 make_mock_hash_store + make_mock_full_session")
    print("#" * 60)

    verify_make_mock_hash_store()
    verify_make_mock_full_session()
    verify_no_artifact_variant()

    print("\n" + "=" * 60)
    print("全部验证通过 ✓")
    print("=" * 60)
