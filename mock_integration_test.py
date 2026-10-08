#!/usr/bin/env python3
"""
mock_integration_test.py
为 4 个目标构造 mock 数据并本地运行测试:
  1. cmd_unlock 哈希比对（guardrails_enforce.py v0.3）
  2. peg_trace 主流程（Tracer.start/log/save_artifact/end）
  3. build_historical_index 第六章扫描
  4. test_peg_trace.py 关键测试类

mock 数据由 mock_helpers.py 提供（可复用）
"""
import sys
import os
import json
import shutil
import tempfile
import unittest
import subprocess
import hashlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 从 mock_helpers 导入可复用的 mock 工厂函数
from mock_helpers import make_mock_hash_store, make_mock_trace


class TestCmdUnlockHashCheckMock(unittest.TestCase):
    """目标 1: cmd_unlock 哈希比对 mock 测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="mock_unlock_")
        self.old_hs = None
        self.old_pf = None
        import guardrails_enforce as ge
        self.ge = ge
        self.old_hs = ge.HASH_STORE
        self.old_pf = ge.PROTECTED_FILE
        self.mock_pf = os.path.join(self.tmpdir, "phase0.md")
        with open(self.mock_pf, "w", encoding="utf-8") as f:
            f.write("# mock\n## §13 ...")
        ge.PROTECTED_FILE = self.mock_pf
        ge.HASH_STORE = self.mock_pf + ".guardrail.json"

    def tearDown(self):
        self.ge.HASH_STORE = self.old_hs
        self.ge.PROTECTED_FILE = self.old_pf
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("GUARDRAIL_TOKEN", None)
        os.environ.pop("GUARDRAIL_TOKEN_CURRENT", None)

    def test_mock_no_field_fallback(self):
        """mock 旧产物（无 guardrail_token_hash）→ 退化为非空校验"""
        make_mock_hash_store(self.ge.HASH_STORE, "no_field")
        os.environ["GUARDRAIL_TOKEN"] = "any-placeholder"
        rc = self.ge.cmd_unlock(self.mock_pf)
        self.assertEqual(rc, 0)

    def test_mock_null_field_fallback(self):
        """mock null 字段 → 退化为非空校验"""
        make_mock_hash_store(self.ge.HASH_STORE, "null_field")
        os.environ["GUARDRAIL_TOKEN"] = "any-placeholder"
        rc = self.ge.cmd_unlock(self.mock_pf)
        self.assertEqual(rc, 0)

    def test_mock_valid_hash_match(self):
        """mock 有效哈希 + 匹配 token → 通过"""
        make_mock_hash_store(self.ge.HASH_STORE, "valid_hash")
        os.environ["GUARDRAIL_TOKEN"] = "mock-token-123"
        rc = self.ge.cmd_unlock(self.mock_pf)
        self.assertEqual(rc, 0)

    def test_mock_valid_hash_mismatch(self):
        """mock 有效哈希 + 不匹配 token → exit 2"""
        make_mock_hash_store(self.ge.HASH_STORE, "valid_hash")
        os.environ["GUARDRAIL_TOKEN"] = "wrong-token"
        rc = self.ge.cmd_unlock(self.mock_pf)
        self.assertEqual(rc, 2)

    def test_mock_empty_token_rejected(self):
        """mock 有效哈希 + 空 token → exit 2"""
        make_mock_hash_store(self.ge.HASH_STORE, "valid_hash")
        os.environ.pop("GUARDRAIL_TOKEN", None)
        rc = self.ge.cmd_unlock(self.mock_pf)
        self.assertEqual(rc, 2)


class TestPegTraceMainFlowMock(unittest.TestCase):
    """目标 2: peg_trace 主流程 mock 测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="mock_peg_trace_")
        import peg_trace
        self.peg_trace = peg_trace
        self.old_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        self.peg_trace.TRACES_ROOT = self.old_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_mock_full_session(self):
        """mock 完整 PEG-A 会话: 5 拍 + artifact + end"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock 完整会话")
        for p in ["Plan", "Act", "Observe", "Reflect", "Coordinate"]:
            tracer.log(phase=p, action=f"{p} 动作", evidence=[f"{p} 证据"], next_step=f"{p} 下一步")
        tracer.save_artifact(artifact_id="mock-art", content="# mock\n", artifact_type="tech_note")
        tracer.end(status="completed")

        # 验证三件套
        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        manifest_path = os.path.join(tracer.trace_dir, "manifest.json")
        self.assertTrue(os.path.exists(reasoning_path))
        self.assertTrue(os.path.exists(manifest_path))
        with open(reasoning_path, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 6)  # trace_start + 5 拍
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(len(manifest["artifacts"]), 1)

    def test_mock_evidence_no_masking(self):
        """mock evidence 含 token 值应原样保留"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock 不脱敏")
        tracer.log(phase="Plan", action="注入 token", evidence=["GUARDRAIL_TOKEN=mock-secret-xyz"], next_step="act")
        tracer.end(status="completed")

        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        with open(reasoning_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("mock-secret-xyz", content)
        self.assertNotIn("[REDACTED]", content)


class TestBuildHistoricalIndexMock(unittest.TestCase):
    """目标 3: build_historical_index 第六章 mock 测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="mock_hist_idx_")
        self.traces_root = os.path.join(self.tmpdir, "traces")
        os.makedirs(self.traces_root)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_mock_ch6_empty_traces(self):
        """mock traces/ 为空目录 → 第六章显示 trace 数 0"""
        sys.path.insert(0, HERE)
        try:
            import importlib
            if "build_historical_index" in sys.modules:
                importlib.reload(sys.modules["build_historical_index"])
            import build_historical_index as bhi
            md, count = bhi.scan_future_traces(self.traces_root)
            self.assertEqual(count, 0)
        except ImportError:
            self.skipTest("build_historical_index 不可导入")

    def test_mock_ch6_completed_trace(self):
        """mock 1 条 completed trace → 第六章列出"""
        make_mock_trace(self.traces_root, "20260721_100000_mock", "completed", 6, 1, "mock 任务")
        sys.path.insert(0, HERE)
        try:
            import importlib
            if "build_historical_index" in sys.modules:
                importlib.reload(sys.modules["build_historical_index"])
            import build_historical_index as bhi
            md, count = bhi.scan_future_traces(self.traces_root)
            self.assertEqual(count, 1)
            self.assertIn("completed", md)
            self.assertIn("20260721_100000_mock", md)
        except ImportError:
            self.skipTest("build_historical_index 不可导入")

    def test_mock_ch6_broken_manifest(self):
        """mock manifest 损坏 → 第六章标记解析失败"""
        make_mock_trace(self.traces_root, "20260721_100100_brok", "completed", 6, 1, "mock", manifest_broken=True)
        sys.path.insert(0, HERE)
        try:
            import importlib
            if "build_historical_index" in sys.modules:
                importlib.reload(sys.modules["build_historical_index"])
            import build_historical_index as bhi
            md, count = bhi.scan_future_traces(self.traces_root)
            self.assertEqual(count, 1)
            # 损坏 manifest 应标记解析失败
            self.assertIn("解析失败", md)
        except ImportError:
            self.skipTest("build_historical_index 不可导入")

    def test_mock_ch6_mixed_statuses(self):
        """mock 3 条 trace 含 completed/aborted/broken → 第六章全列出"""
        make_mock_trace(self.traces_root, "20260721_100200_a", "completed", 6, 2, "任务A")
        make_mock_trace(self.traces_root, "20260721_100201_b", "aborted", 3, 0, "任务B")
        make_mock_trace(self.traces_root, "20260721_100202_c", "completed", 5, 1, "任务C", manifest_broken=True)
        sys.path.insert(0, HERE)
        try:
            import importlib
            if "build_historical_index" in sys.modules:
                importlib.reload(sys.modules["build_historical_index"])
            import build_historical_index as bhi
            md, count = bhi.scan_future_traces(self.traces_root)
            self.assertEqual(count, 3)
            self.assertIn("任务A", md)
            self.assertIn("任务B", md)
            self.assertIn("aborted", md)
        except ImportError:
            self.skipTest("build_historical_index 不可导入")


class TestTestPegTraceSegmentMock(unittest.TestCase):
    """目标 4: test_peg_trace.py 关键测试类用 mock 数据再跑一次"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="mock_test_peg_")
        import peg_trace
        self.peg_trace = peg_trace
        self.old_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        self.peg_trace.TRACES_ROOT = self.old_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_mock_tracer_start_creates_dir(self):
        """mock: Tracer.start 应创建 trace 目录"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock start")
        self.assertTrue(os.path.isdir(tracer.trace_dir))
        self.assertTrue(tracer.trace_id)

    def test_mock_log_appends_to_reasoning(self):
        """mock: log 应追加到 reasoning.jsonl"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock log")
        before = 0
        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        if os.path.exists(reasoning_path):
            with open(reasoning_path, encoding="utf-8") as f:
                before = sum(1 for l in f if l.strip())
        tracer.log(phase="Plan", action="mock", evidence=[], next_step="n")
        with open(reasoning_path, encoding="utf-8") as f:
            after = sum(1 for l in f if l.strip())
        self.assertEqual(after, before + 1)

    def test_mock_save_artifact_writes_file(self):
        """mock: save_artifact 应写入文件"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock art")
        result = tracer.save_artifact(artifact_id="mock-a", content="mock content", artifact_type="diff")
        self.assertTrue(result[0])
        self.assertTrue(os.path.exists(result[0]))
        with open(result[0], encoding="utf-8") as f:
            self.assertEqual(f.read(), "mock content")

    def test_mock_end_writes_manifest(self):
        """mock: end 应写 manifest.json"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock end")
        tracer.end(status="completed")
        manifest_path = os.path.join(tracer.trace_dir, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["status"], "completed")

    def test_mock_invalid_phase_rejected(self):
        """mock: 非法 phase 应被拒绝"""
        tracer = self.peg_trace.Tracer.start(task_summary="mock invalid")
        result = tracer.log(phase="InvalidPhase", action="x", evidence=[], next_step="y")
        self.assertFalse(result)


if __name__ == "__main__":
    print("=" * 70)
    print("Mock 集成测试: cmd_unlock + peg_trace + build_historical_index + test_peg_trace")
    print("=" * 70)
    unittest.main(verbosity=2)
