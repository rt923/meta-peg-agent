#!/usr/bin/env python3
"""
test_peg_a_v0_6_flow.py
PEG-A v0.6 主流程单元测试（phase0 §3 接入 peg_trace.py 后的端到端验证）

覆盖 phase0 v0.6 新增的 3 处接入点:
  - §3 Meta-Loop trace 持久化说明（Tracer.start/log/save_artifact/end 全流程）
  - §4 trace 持久化类（tracer.log 失败不阻断业务）
  - §11.4.1 Return 前 save_artifact 步骤

测试策略: 不依赖 phase0 文件本身（避免受只读锁影响），直接测试 peg_trace.py API
"""

import sys
import os
import json
import shutil
import tempfile
import unittest

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import peg_trace


class TestMetaLoopFivePhases(unittest.TestCase):
    """phase0 §3: Meta-Loop 五拍全部能被持久化"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_full_meta_loop_five_phases_persisted(self):
        """完整五拍 Plan/Act/Observe/Reflect/Coordinate 全部写入 reasoning.jsonl"""
        tracer = peg_trace.Tracer.start(task_summary="v0.6 五拍测试")
        phases = ["Plan", "Act", "Observe", "Reflect", "Coordinate"]
        for p in phases:
            tracer.log(
                phase=p,
                action=f"{p} 拍动作",
                evidence=[f"{p} 证据"],
                next_step=f"{p} 下一步",
            )
        tracer.end(status="completed")

        # 读 reasoning.jsonl
        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        with open(reasoning_path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]

        # 预期: 1 trace_start(作为 Plan) + 5 拍 = 6 行
        self.assertEqual(len(records), 6)
        # 第 1 条是 trace_start（phase=Plan, action=trace_start）
        self.assertEqual(records[0]["phase"], "Plan")
        self.assertEqual(records[0]["action"], "trace_start")
        # 后 5 条是 5 拍（第 1 拍 Plan 与 trace_start 合一，故后 5 条是 Act/Observe/Reflect/Coordinate + 1 个额外 Plan）
        # 实际: trace_start 是 phase=Plan，然后又 log 了 phase=Plan，所以 6 条里 2 个 Plan + 1 Act + 1 Observe + 1 Reflect + 1 Coordinate
        phase_counts = {}
        for r in records:
            phase_counts[r["phase"]] = phase_counts.get(r["phase"], 0) + 1
        self.assertEqual(phase_counts.get("Plan", 0), 2)  # trace_start + 显式 Plan
        self.assertEqual(phase_counts.get("Act", 0), 1)
        self.assertEqual(phase_counts.get("Observe", 0), 1)
        self.assertEqual(phase_counts.get("Reflect", 0), 1)
        self.assertEqual(phase_counts.get("Coordinate", 0), 1)

    def test_phase_order_in_step_counter(self):
        """step 应按 log 调用顺序递增"""
        tracer = peg_trace.Tracer.start(task_summary="step 测试")
        # Tracer.start 内部已 log 一次（phase=Plan, action=trace_start）
        initial_step = tracer.step
        tracer.log(phase="Plan", action="a1", evidence=[], next_step="n1")
        self.assertEqual(tracer.step, initial_step + 1)
        tracer.log(phase="Act", action="a2", evidence=[], next_step="n2")
        self.assertEqual(tracer.step, initial_step + 2)
        tracer.end(status="completed")


class TestInvalidPhaseRejected(unittest.TestCase):
    """phase0 §3: 非法 phase 应被拒绝（不污染 reasoning）"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_invalid_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_invalid_phase_rejected(self):
        """非法 phase 名应被拒绝，不写入 reasoning"""
        tracer = peg_trace.Tracer.start(task_summary="非法 phase 测试")
        result = tracer.log(
            phase="InvalidPhase",
            action="...",
            evidence=[],
            next_step="...",
        )
        self.assertFalse(result)
        # reasoning 应只有 trace_start 一条
        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        with open(reasoning_path, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 1)


class TestSaveArtifactBeforeReturn(unittest.TestCase):
    """phase0 §11.4.1: Return 前 save_artifact 步骤"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_art_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_artifact_writes_to_artifacts_dir(self):
        """save_artifact 应把产出物写入 artifacts/ 子目录"""
        tracer = peg_trace.Tracer.start(task_summary="save_artifact 测试")
        content = "diff --git a/x b/x\n+新增\n"
        result = tracer.save_artifact(
            artifact_id="diff-001",
            content=content,
            artifact_type="diff",
        )
        self.assertTrue(result[0])  # path
        self.assertTrue(os.path.exists(result[0]))
        with open(result[0], encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_save_artifact_registers_in_manifest(self):
        """save_artifact 应在 manifest.json 登记 sha256 + origin_step"""
        tracer = peg_trace.Tracer.start(task_summary="manifest 测试")
        tracer.log(phase="Plan", action="a", evidence=[], next_step="n")
        tracer.save_artifact(
            artifact_id="note-001",
            content="# TN\n正文",
            artifact_type="tech_note",
        )
        tracer.end(status="completed")

        manifest_path = os.path.join(tracer.trace_dir, "manifest.json")
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(len(manifest["artifacts"]), 1)
        art = manifest["artifacts"][0]
        self.assertEqual(art["id"], "note-001")
        self.assertIn("sha256", art)
        self.assertIn("origin_step", art)

    def test_save_artifact_preserves_token_no_masking(self):
        """phase0 §3 安全边界: evidence 含 token 值应原样保留不脱敏"""
        tracer = peg_trace.Tracer.start(task_summary="token 不脱敏测试")
        tracer.log(
            phase="Plan",
            action="注入 token",
            evidence=["GUARDRAIL_TOKEN=operator-context-present"],  # 占位符
            next_step="act",
        )

        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        with open(reasoning_path, encoding="utf-8") as f:
            content = f.read()
        # token 占位符应原样出现
        self.assertIn("operator-context-present", content)
        # 不应有 [REDACTED] / [MASKED] 等脱敏标记
        self.assertNotIn("[REDACTED]", content)
        self.assertNotIn("[MASKED]", content)


class TestTracerFailureIsolation(unittest.TestCase):
    """phase0 §4: tracer.log 失败应只标 error 不阻断业务（trace 是观测层）"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_fail_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_log_failure_does_not_raise(self):
        """tracer.log 写入失败不应抛异常，只标 error 到 stderr"""
        tracer = peg_trace.Tracer.start(task_summary="失败测试")
        # 破坏 trace_dir 让写入失败（删除目录）
        shutil.rmtree(tracer.trace_dir, ignore_errors=True)
        # log 不应抛异常
        result = tracer.log(
            phase="Plan",
            action="失败后仍继续",
            evidence=["reasoning.jsonl 已不可写"],
            next_step="act",
        )
        # result 可能是 False（写入失败），但不应抛异常
        # 业务应能继续
        tracer.end(status="completed")


class TestEndToEndSession(unittest.TestCase):
    """完整 PEG-A 会话端到端测试（模拟真实使用）"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_e2e_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_full_session_matches_phase0_v0_6_workflow(self):
        """模拟一次完整 PEG-A 会话，匹配 phase0 v0.6 §3 工作流程"""
        # === Tracer.start ===
        tracer = peg_trace.Tracer.start(
            task_summary="PEG-A v0.6 端到端流程验证"
        )

        # === Plan 拍 ===
        tracer.log(
            phase="Plan",
            action="重述任务目标",
            evidence=["目标: 验证 phase0 v0.6 接入"],
            next_step="Act",
        )

        # === Act 拍 ===
        tracer.log(
            phase="Act",
            action="调用工具执行",
            evidence=["工具调用结果: OK"],
            next_step="Observe",
        )

        # === Observe 拍 ===
        tracer.log(
            phase="Observe",
            action="验证产出物",
            evidence=["reasoning.jsonl 3 行", "manifest.json OK"],
            next_step="Reflect",
        )

        # === Reflect 拍 ===
        tracer.log(
            phase="Reflect",
            action="复盘",
            evidence=["目标达成", "无偏离"],
            next_step="Coordinate",
        )

        # === Coordinate 拍 + §11.4.1 save_artifact ===
        final_artifact = "# PEG-A 输出\n这是最终交付物"
        tracer.save_artifact(
            artifact_id=f"{tracer.trace_id}-final",
            content=final_artifact,
            artifact_type="prompt_md",
        )
        tracer.log(
            phase="Coordinate",
            action="save_artifact + 结束",
            evidence=["artifact 已保存"],
            next_step="end(completed)",
        )

        # === end ===
        tracer.end(status="completed")

        # === 断言三件套完整 ===
        reasoning_path = os.path.join(tracer.trace_dir, "reasoning.jsonl")
        manifest_path = os.path.join(tracer.trace_dir, "manifest.json")
        artifacts_dir = os.path.join(tracer.trace_dir, "artifacts")

        # reasoning.jsonl: 1 trace_start + 5 拍 = 6 行
        with open(reasoning_path, encoding="utf-8") as f:
            reasoning_lines = sum(1 for l in f if l.strip())
        self.assertEqual(reasoning_lines, 6)

        # manifest.json
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(manifest["step_count"], 6)
        self.assertEqual(len(manifest["artifacts"]), 1)

        # artifacts/
        artifacts_files = os.listdir(artifacts_dir)
        self.assertEqual(len(artifacts_files), 1)
        with open(os.path.join(artifacts_dir, artifacts_files[0]), encoding="utf-8") as f:
            self.assertEqual(f.read(), final_artifact)


class TestCLIToolsForAudit(unittest.TestCase):
    """phase0 §4 trace 持久化类: CLI 子命令可用（审计用）"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="peg_a_v0_6_cli_")
        self.old_traces_root = peg_trace.TRACES_ROOT
        peg_trace.TRACES_ROOT = self.tmpdir

    def tearDown(self):
        peg_trace.TRACES_ROOT = self.old_traces_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cli_list_shows_trace(self):
        """CLI list 子命令应列出已产生的 trace"""
        tracer = peg_trace.Tracer.start(task_summary="CLI 测试")
        tracer.log(phase="Plan", action="a", evidence=[], next_step="n")
        tracer.end(status="completed")

        # 造一个 trace_id 然后调 list
        import subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # 通过 -c 调用 peg_trace CLI
        cli_path = os.path.join(HERE, "peg_trace.py")
        result = subprocess.run(
            ["python", cli_path, "list", "--root", self.tmpdir],
            capture_output=True, text=True, encoding="utf-8",
            env=env, cwd=HERE,
        )
        self.assertEqual(result.returncode, 0)
        # list 应至少含一条 trace（task_summary 在 stdout 即可）
        self.assertIn("CLI 测试", result.stdout)
        # trace_id 前 8 位（日期）应出现
        date_prefix = tracer.trace_id[:8]
        self.assertIn(date_prefix, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
