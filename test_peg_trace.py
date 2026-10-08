#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
peg_trace.py 单元测试（unittest 风格，兼容 pytest）

覆盖:
  - Tracer.start() 创建目录 + 初始 trace_start 记录
  - log() 五拍阶段写入 + 非法 phase 拒绝
  - save_artifact() 原文写入不脱敏 + sha256 + manifest 登记
  - end() manifest 写盘 + 终态校验
  - 失败容错（目录不可写不抛异常）
  - CLI list/show/tail 子命令
  - 自指安全验证（防御性闸门扫描）

运行:
  python test_peg_trace.py              # unittest 直接跑
  python -m unittest test_peg_trace     # unittest 模块跑
  python -m pytest test_peg_trace.py    # pytest 兼容（如已装）

对应 peg_trace.py self_test 草案（PEG-2026-07-16-001）。
"""

import os
import sys
import io
import json
import shutil
import tempfile
import hashlib
import subprocess
import contextlib
from datetime import datetime

import unittest

# ---- Windows 控制台 UTF-8 修复 ----
# 根因: PowerShell 默认用 GBK 解码 stdout/stderr 字节流，导致 docstring 中文乱码。
# 此处显式 reconfigure stdout/stderr 为 UTF-8，确保跨平台一致输出。
# 注意: 仅修 Python 进程输出层；PowerShell 控制台若仍乱码，
#       请用 run_tests.ps1 包装脚本（会先 chcp 65001 切 UTF-8 代码页）。
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, io.UnsupportedOperation):
    pass  # 某些环境（重定向到文件）不支持 reconfigure，忽略

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import peg_trace


# ============================================================
# 辅助：临时重定向 TRACES_ROOT
# ============================================================

@contextlib.contextmanager
def temp_traces_root():
    """临时把 peg_trace.TRACES_ROOT 指向临时目录，避免污染真实 traces/。"""
    original = peg_trace.TRACES_ROOT
    tmp = tempfile.mkdtemp(prefix="peg_trace_test_")
    fake_root = os.path.join(tmp, "traces")
    os.makedirs(fake_root, exist_ok=True)
    peg_trace.TRACES_ROOT = fake_root
    try:
        yield fake_root
    finally:
        peg_trace.TRACES_ROOT = original
        shutil.rmtree(tmp, ignore_errors=True)


# ============================================================
# 1. Tracer.start()
# ============================================================

class TestTracerStart(unittest.TestCase):
    def test_start_creates_trace_dir(self):
        with temp_traces_root() as root:
            t = peg_trace.Tracer.start("测试任务")
            self.assertTrue(os.path.isdir(t.trace_dir))
            self.assertTrue(os.path.isdir(os.path.join(t.trace_dir, "artifacts")))

    def test_start_trace_id_format(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试任务")
            parts = t.trace_id.split("_")
            self.assertEqual(len(parts), 3, f"trace_id 应为三段: {t.trace_id}")
            self.assertEqual(len(parts[2]), 4, f"末段应为 4 字符哈希: {parts[2]}")

    def test_start_writes_initial_trace_start_log(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试任务")
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            self.assertGreaterEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["phase"], "Plan")
            self.assertEqual(entry["action"], "trace_start")
            self.assertEqual(entry["step"], 1)
            self.assertTrue(any("trace_id=" in e for e in entry["evidence"]))

    def test_start_sets_started_at(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试任务")
            self.assertIsNotNone(t.started_at)
            # 应是合法 ISO8601
            datetime.fromisoformat(t.started_at)


# ============================================================
# 2. log()
# ============================================================

class TestLog(unittest.TestCase):
    def test_log_valid_phases(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            initial = t.step
            for phase in ("Plan", "Act", "Observe", "Reflect", "Coordinate"):
                ok = t.log(phase=phase, action=f"测试 {phase}",
                           evidence=[f"{phase}_证据"], next_step="下一步")
                self.assertTrue(ok, f"{phase} 应写入成功")
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), initial + 5)

    def test_log_invalid_phase_rejected(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            before = t.step
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                ok = t.log(phase="Unknown_Phase", action="非法",
                           evidence=[], next_step="无")
            self.assertFalse(ok)
            self.assertEqual(t.step, before, "非法 phase 不应递增 step")
            self.assertIn("非法 phase", err_buf.getvalue())

    def test_log_step_increments(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            initial = t.step
            t.log("Act", "动作1", ["e1"], "n1")
            self.assertEqual(t.step, initial + 1)
            t.log("Observe", "观察1", ["e2"], "n2")
            self.assertEqual(t.step, initial + 2)

    def test_log_entry_structure(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            t.log("Act", "测试动作", ["证据1", "证据2"], "下一步")
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            last = json.loads(lines[-1])
            for key in ("ts", "trace_id", "step", "phase", "action",
                        "evidence", "next"):
                self.assertIn(key, last, f"记录缺字段: {key}")
            self.assertEqual(last["evidence"], ["证据1", "证据2"])
            self.assertEqual(last["next"], "下一步")

    def test_log_empty_evidence_allowed(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            ok = t.log("Plan", "无证据", [], "下一步")
            self.assertTrue(ok)
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            last = json.loads(lines[-1])
            self.assertEqual(last["evidence"], [])

    def test_log_none_evidence_normalized(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            ok = t.log("Plan", "None 证据", None, "下一步")
            self.assertTrue(ok)
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            last = json.loads(lines[-1])
            self.assertEqual(last["evidence"], [])


# ============================================================
# 3. save_artifact()
# ============================================================

class TestSaveArtifact(unittest.TestCase):
    def test_save_artifact_returns_path_and_sha(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            content = "diff --git a/file b/file\n+新增行\n"
            fpath, sha = t.save_artifact("diff-001", content, "diff")
            self.assertIsNotNone(fpath)
            self.assertTrue(os.path.isfile(fpath))
            self.assertEqual(sha,
                             hashlib.sha256(content.encode("utf-8")).hexdigest())

    def test_save_artifact_preserves_original_no_redaction(self):
        """token 值与敏感内容应原样写入，不脱敏。"""
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            content = "GUARDRAIL_TOKEN=abc123secret\n§13 不可被覆盖\n"
            fpath, _ = t.save_artifact("sensitive-001", content, "diff")
            with open(fpath, encoding="utf-8") as f:
                written = f.read()
            self.assertIn("abc123secret", written, "token 值应原样保留")
            self.assertIn("§13 不可被覆盖", written, "§13 断言应原样保留")

    def test_save_artifact_registers_to_manifest_memory(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            t.save_artifact("art-1", "内容", "tech_note")
            arts = t.list_artifacts()
            self.assertEqual(len(arts), 1)
            self.assertEqual(arts[0]["id"], "art-1")
            self.assertEqual(arts[0]["type"], "tech_note")
            self.assertIn("sha256", arts[0])
            self.assertEqual(arts[0]["size_bytes"],
                             len("内容".encode("utf-8")))

    def test_save_artifact_type_extensions(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            cases = [
                ("diff", "diff"),
                ("prompt_md", "md"),
                ("tech_note", "md"),
                ("verify_report", "json"),
                ("other", "txt"),
            ]
            for art_type, ext in cases:
                fpath, _ = t.save_artifact(f"art-{art_type}", "x", art_type)
                self.assertTrue(fpath.endswith(f".{ext}"),
                                f"{art_type} 应使用 .{ext}，实际: {fpath}")

    def test_save_artifact_invalid_type_falls_back(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                fpath, _ = t.save_artifact("bad-type", "x", "totally_invalid")
            self.assertTrue(fpath.endswith(".txt"))
            self.assertIn("非法 artifact_type", err_buf.getvalue())

    def test_save_artifact_origin_step_defaults_to_current(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            t.log("Act", "动作", [], "下一步")
            current_step = t.step
            t.save_artifact("art-default-step", "x", "diff")
            arts = t.list_artifacts()
            self.assertEqual(arts[-1]["origin_step"], current_step)

    def test_save_artifact_explicit_origin_step(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            t.save_artifact("art-explicit", "x", "diff", origin_step=42)
            arts = t.list_artifacts()
            self.assertEqual(arts[-1]["origin_step"], 42)

    def test_save_artifact_sha256_matches_content(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            content = "测试 sha256 一致性"
            _, sha = t.save_artifact("sha-test", content, "other")
            expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.assertEqual(sha, expected)


# ============================================================
# 4. end()
# ============================================================

class TestEnd(unittest.TestCase):
    def test_end_writes_manifest(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            path = t.end("completed")
            self.assertIsNotNone(path)
            self.assertTrue(os.path.isfile(path))
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            for key in ("trace_id", "task_summary", "started_at",
                        "ended_at", "status", "step_count", "artifacts"):
                self.assertIn(key, m, f"manifest 缺字段: {key}")
            self.assertEqual(m["status"], "completed")
            self.assertIsNotNone(m["ended_at"])
            datetime.fromisoformat(m["ended_at"])

    def test_end_invalid_status_falls_back(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                path = t.end("totally_invalid")
            self.assertIsNotNone(path)
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            self.assertEqual(m["status"], "aborted")
            self.assertIn("非法 status", err_buf.getvalue())

    def test_end_manifest_includes_artifacts(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            t.save_artifact("a1", "内容1", "diff")
            t.save_artifact("a2", "内容2", "tech_note")
            path = t.end("completed")
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            self.assertEqual(len(m["artifacts"]), 2)
            ids = {a["id"] for a in m["artifacts"]}
            self.assertEqual(ids, {"a1", "a2"})

    def test_end_status_values(self):
        with temp_traces_root():
            t = peg_trace.Tracer.start("测试")
            for status in ("completed", "aborted", "failed"):
                path = t.end(status)
                with open(path, encoding="utf-8") as f:
                    m = json.load(f)
                self.assertEqual(m["status"], status)


# ============================================================
# 5. 容错与边界
# ============================================================

class TestFailureTolerance(unittest.TestCase):
    def test_log_to_unwritable_path_does_not_raise(self):
        """reasoning 写入失败不应抛异常，只标 error 到 stderr。"""
        with temp_traces_root():
            t = peg_trace.Tracer.start("容错测试")
            # 用包含非法字符（管道符 |）的路径，确保 open() 失败
            # Windows 与 Unix 均不允许 | 在路径中
            t.reasoning_path = "bad|path|with|pipe|reasoning.jsonl"
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                ok = t.log("Plan", "应失败", ["evidence"], "下一步")
            self.assertFalse(ok, "写入失败应返回 False")
            # 不应抛异常即为通过

    def test_save_artifact_to_unwritable_dir_does_not_raise(self):
        """artifact 写入失败不应抛异常，返回 (None, None)。"""
        with temp_traces_root():
            t = peg_trace.Tracer.start("容错测试")
            # 用包含非法字符（管道符 |）的路径，确保 open() 失败
            t.artifacts_dir = "bad|path|with|pipe|artifacts"
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                fpath, sha = t.save_artifact("test", "x", "diff")
            self.assertIsNone(fpath)
            self.assertIsNone(sha)


# ============================================================
# 6. 端到端完整会话
# ============================================================

class TestEndToEnd(unittest.TestCase):
    def test_full_meta_loop_session(self):
        """模拟一次完整 Meta-Loop 会话。"""
        with temp_traces_root():
            t = peg_trace.Tracer.start("端到端测试：修复 verify_method")

            # Plan
            t.log("Plan", "定位文件", ["Glob 无命中"], "查 memory")
            # Act
            t.log("Act", "读文件", ["7 个 .prompt.md 命中"], "跑 checker")
            # Observe
            t.log("Observe", "跑 explainability_check",
                  ["passed:false, critical:1"], "改 verify_method")
            # Reflect
            t.log("Reflect", "根因分析",
                  ["正则不理解'不得'语义"], "改 --text 模式")
            # Coordinate
            diff_content = "diff --git a/file b/file\n-旧\n+新\n"
            fpath, sha = t.save_artifact("fix-001", diff_content, "diff")
            t.log("Coordinate", "保存 diff 草案",
                  [f"saved: {os.path.basename(fpath)}", f"sha: {sha[:8]}"],
                  "等待审核")

            manifest_path = t.end("completed")

            # 验证 reasoning.jsonl 行数 = 1(trace_start) + 5(Meta-Loop) = 6
            with open(t.reasoning_path, encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 6,
                             f"应有 6 条记录，实际: {len(lines)}")

            # 验证 phase 顺序
            phases = [json.loads(line)["phase"] for line in lines]
            self.assertEqual(
                phases,
                ["Plan", "Plan", "Act", "Observe", "Reflect", "Coordinate"])

            # 验证 manifest
            with open(manifest_path, encoding="utf-8") as f:
                m = json.load(f)
            self.assertEqual(m["status"], "completed")
            self.assertEqual(m["step_count"], 6)
            self.assertEqual(len(m["artifacts"]), 1)
            self.assertEqual(m["artifacts"][0]["id"], "fix-001")


# ============================================================
# 7. CLI 子命令
# ============================================================

class TestCLI(unittest.TestCase):
    def _run_cli(self, *args):
        # Windows 子进程默认用 GBK 编码 stdout/stderr，
        # 强制设 PYTHONIOENCODING=utf-8 让子进程用 UTF-8 输出
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "peg_trace.py")] + list(args),
            capture_output=True, timeout=10,
            encoding="utf-8", errors="replace", env=env,
        )
        return result.returncode, result.stdout or "", result.stderr or ""

    def test_cli_no_args_prints_help(self):
        code, out, err = self._run_cli()
        self.assertEqual(code, 2)
        combined = (out + err).lower()
        self.assertIn("usage:", combined)

    def test_cli_list_empty_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty_root = os.path.join(tmp, "empty_traces")
            code, out, err = self._run_cli("list", "--root", empty_root)
            self.assertEqual(code, 1)
            self.assertIn("不存在", err)

    def test_cli_list_with_one_trace(self):
        with temp_traces_root() as root:
            t = peg_trace.Tracer.start("CLI 测试")
            t.end("completed")

            code, out, err = self._run_cli("list", "--root", root)
            self.assertEqual(code, 0)
            self.assertIn(t.trace_id, out)
            self.assertIn("completed", out)

    def test_cli_show_manifest(self):
        with temp_traces_root() as root:
            t = peg_trace.Tracer.start("show 测试")
            t.save_artifact("a1", "内容", "diff")
            t.end("completed")

            code, out, err = self._run_cli("show", t.trace_id,
                                           "--root", root)
            self.assertEqual(code, 0)
            m = json.loads(out)
            self.assertEqual(m["trace_id"], t.trace_id)
            self.assertEqual(len(m["artifacts"]), 1)

    def test_cli_tail_reasoning(self):
        with temp_traces_root() as root:
            t = peg_trace.Tracer.start("tail 测试")
            for i in range(5):
                t.log("Act", f"动作 {i}", [f"证据 {i}"], "下一步")
            t.end("completed")

            code, out, err = self._run_cli("tail", t.trace_id,
                                          "--root", root, "-n", "3")
            self.assertEqual(code, 0)
            # trace_start(1) + 5 = 6 条；末 3 条 = step 4,5,6
            self.assertIn("动作 2", out)  # step 4
            self.assertIn("动作 4", out)  # step 6

    def test_cli_show_nonexistent_trace(self):
        with temp_traces_root() as root:
            code, out, err = self._run_cli("show", "nonexistent_id",
                                           "--root", root)
            self.assertEqual(code, 1)
            self.assertIn("不存在", err)


# ============================================================
# 8. 自指安全验证（防御性）
# ============================================================

class TestSafetyGate(unittest.TestCase):
    def test_peg_trace_source_passes_gate(self):
        """peg_trace.py 源码本身应过 explainability_check 闸门（防御性扫描）。"""
        import explainability_check as ec
        src_path = os.path.join(HERE, "peg_trace.py")
        with open(src_path, encoding="utf-8") as f:
            src = f.read()
        report = ec.check(src)
        self.assertTrue(
            report["passed"],
            f"peg_trace.py 应过闸门，CRITICAL={report['critical_count']}: "
            f"{[a['tag'] for a in report['alerts']]}")


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
