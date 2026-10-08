#!/usr/bin/env python3
# peg_trace.py
# PEG-A Meta-Loop 思考过程 + 产出物持久化模块
# 对应 phase0_meta_peg_agent_prompt.md Plan→Act→Observe→Reflect→Coordinate 循环
#
# 用法:
#   from peg_trace import Tracer
#   tracer = Tracer.start(task_summary="修复 verify_method 误报")
#   tracer.log(phase="Plan", action="定位文件", evidence=["Glob 无命中"], next_step="查 memory")
#   tracer.save_artifact(artifact_id="fix-diff-001", content="...", artifact_type="diff")
#   tracer.log(phase="Observe", action="跑 --text 验证", evidence=["passed:true"], next_step="提交")
#   tracer.end(status="completed")
#
# 退出码: 0 = 正常, 1 = trace 写入异常（不阻断业务，仅 stderr 告警）
#
# 设计说明（安全策略，审计人员必读）:
#   - 边界（§12 数据/指令分离）: log() 不接收也不写入 §13 全文或提示词原文。
#     这不是"事后脱敏过滤"，而是 API 设计层就不接收这两类内容——
#     evidence 字段只记判定结果（如 "passed:true, 0 alerts"），不记被扫文本本身。
#     若调用方误传 §13 全文/提示词原文，由调用方负责，peg_trace.py 不做字符串替换/打码。
#   - 不脱敏: evidence 中若出现 token 值（如 GUARDRAIL_TOKEN=abc123），
#     原样写入 reasoning.jsonl，由 traces/ 目录本机权限兜底（操作员责任）。
#   - 不加只读告警: 保持纯记录语义。审计方自行判断 evidence 是否含敏感内容，
#     不在日志末尾追加任何 [WARN] 标记。
#   - 单点真相（继承 spawn_peg_member_prompt.md L6 约定）: traces 根目录
#     动态解析为 os.path.dirname(os.path.abspath(__file__)) + "/traces"，
#     严禁硬编码工作区根目录。
#   - 失败即容错（不阻断业务）: trace 是观测层，写入失败只标 error 到 stderr，
#     不抛异常阻断 PEG-A 主流程。

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timezone

# ---- Windows 控制台 UTF-8 修复 ----
# 根因: PowerShell 默认用 GBK 解码 stdout/stderr 字节流，导致 CLI 中文输出乱码。
# 此处显式 reconfigure stdout/stderr 为 UTF-8，确保跨平台一致输出。
# 注意: 仅修 Python 进程输出层；PowerShell 控制台若仍乱码，
#       需在 PowerShell 跑 chcp 65001 切 UTF-8 代码页。
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, Exception):
    pass  # 某些环境（重定向到文件）不支持 reconfigure，忽略


# ---- 路径解析（单点真相）----
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACES_ROOT = os.path.join(_MODULE_DIR, "traces")

VALID_PHASES = ("Plan", "Act", "Observe", "Reflect", "Coordinate")
VALID_ARTIFACT_TYPES = ("diff", "prompt_md", "tech_note", "verify_report", "other")
VALID_END_STATUSES = ("completed", "aborted", "failed")


def _now_iso():
    """UTC ISO8601 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def _short_id(seed_text, length=4):
    """基于文本生成短哈希 ID（避免长 UUID）。"""
    h = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return h[:length]


def _safe_makedirs(path):
    """容错版 makedirs：失败不抛异常。"""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"[peg_trace WARN] makedirs 失败 {path}: {e}", file=sys.stderr)
        return False
    return True


class Tracer:
    """PEG-A 思考过程 + 产出物持久化器。

    每个实例对应一次完整会话（一个 trace_id 一个子目录）。
    线程安全：否（单线程 Meta-Loop 使用）；多线程请各自创建实例。
    """

    def __init__(self, trace_id, trace_dir, task_summary):
        self.trace_id = trace_id
        self.trace_dir = trace_dir
        self.task_summary = task_summary
        self.reasoning_path = os.path.join(trace_dir, "reasoning.jsonl")
        self.manifest_path = os.path.join(trace_dir, "manifest.json")
        self.artifacts_dir = os.path.join(trace_dir, "artifacts")
        self.started_at = _now_iso()
        self.ended_at = None
        self.status = None
        self.step = 0
        self.artifacts = []
        # 不预先创建目录，惰性创建于首次写

    @classmethod
    def start(cls, task_summary):
        """启动一次 trace 会话。

        参数:
          task_summary: 本次任务摘要（用于生成 trace_id + 写入 manifest）

        返回:
          Tracer 实例。若目录创建失败仍返回实例，后续 log/save_artifact 会标 error 但不阻断。
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_id = f"{ts}_{_short_id(task_summary)}"
        trace_dir = os.path.join(TRACES_ROOT, trace_id)
        # 尝试创建目录，失败不抛
        _safe_makedirs(os.path.join(trace_dir, "artifacts"))
        tracer = cls(trace_id, trace_dir, task_summary)
        # 立即写一条起始 marker 到 reasoning.jsonl
        tracer.log(phase="Plan", action="trace_start",
                   evidence=[f"trace_id={trace_id}", f"task_summary={task_summary}"],
                   next_step="进入 Meta-Loop")
        return tracer

    def log(self, phase, action, evidence, next_step):
        """追加一条 Meta-Loop 思考记录到 reasoning.jsonl。

        安全策略（见模块顶部设计说明）:
          - evidence 原样写入，不做脱敏/打码/告警
          - 调用方负责确保 evidence 不含 §13 全文或提示词原文（§12 边界）
          - token 值若出现则保留原文

        参数:
          phase: Meta-Loop 阶段名（Plan/Act/Observe/Reflect/Coordinate）
          action: 动作摘要
          evidence: 证据列表（如 ["passed:true, 0 alerts", "exit_code=0"]）
          next_step: 下一步

        返回:
          True = 写入成功, False = 写入失败（已标 error 到 stderr）
        """
        if phase not in VALID_PHASES:
            print(f"[peg_trace WARN] 非法 phase={phase}，跳过", file=sys.stderr)
            return False

        self.step += 1
        entry = {
            "ts": _now_iso(),
            "trace_id": self.trace_id,
            "step": self.step,
            "phase": phase,
            "action": action,
            "evidence": list(evidence) if evidence else [],
            "next": next_step,
        }

        try:
            # 追加模式写 JSON Lines
            with open(self.reasoning_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"[peg_trace WARN] reasoning 写入失败 step={self.step}: {e}",
                  file=sys.stderr)
            return False
        return True

    def save_artifact(self, artifact_id, content, artifact_type="other",
                      origin_step=None):
        """保存产出物副本到 artifacts/ 并登记到 manifest。

        安全策略（见模块顶部设计说明）:
          - artifact 副本保留原文，不脱敏
          - 若 artifact 含 §13 全文/提示词原文/token 值，原样保存
          - 调用方负责确保 artifact 内容不违反 §12（如非授权的提示词原文）
          - artifact 文件本机权限兜底（操作员责任）

        参数:
          artifact_id: 产出物唯一 ID（如 "fix-diff-001"）
          content: 产出物内容（字符串）
          artifact_type: 类型（diff/prompt_md/tech_note/verify_report/other）
          origin_step: 该产出物产生于 Meta-Loop 第几步（可选，默认取当前 step）

        返回:
          (artifact_path, sha256) 元组；失败返回 (None, None)
        """
        if artifact_type not in VALID_ARTIFACT_TYPES:
            print(f"[peg_trace WARN] 非法 artifact_type={artifact_type}，"
                  f"回退为 other", file=sys.stderr)
            artifact_type = "other"

        # 惰性确保 artifacts 目录存在
        if not os.path.isdir(self.artifacts_dir):
            _safe_makedirs(self.artifacts_dir)

        # 文件名：artifact_id.<type 短名>
        type_ext = {
            "diff": "diff",
            "prompt_md": "md",
            "tech_note": "md",
            "verify_report": "json",
            "other": "txt",
        }.get(artifact_type, "txt")
        fname = f"{artifact_id}.{type_ext}"
        fpath = os.path.join(self.artifacts_dir, fname)

        # 写入原文（不脱敏）
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            print(f"[peg_trace WARN] artifact 写入失败 {fpath}: {e}",
                  file=sys.stderr)
            return None, None

        # 计算 sha256
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # 登记到 manifest（内存中，end() 时一次性写盘）
        self.artifacts.append({
            "id": artifact_id,
            "type": artifact_type,
            "path": os.path.relpath(fpath, self.trace_dir),
            "sha256": sha,
            "origin_step": origin_step if origin_step is not None else self.step,
            "size_bytes": len(content.encode("utf-8")),
        })
        return fpath, sha

    def end(self, status="completed"):
        """结束本次 trace 会话，写盘 manifest.json。

        参数:
          status: 终态（completed/aborted/failed）

        返回:
          manifest_path（成功）或 None（失败）
        """
        if status not in VALID_END_STATUSES:
            print(f"[peg_trace WARN] 非法 status={status}，回退为 aborted",
                  file=sys.stderr)
            status = "aborted"

        self.ended_at = _now_iso()
        self.status = status

        manifest = {
            "trace_id": self.trace_id,
            "task_summary": self.task_summary,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": status,
            "step_count": self.step,
            "artifacts": self.artifacts,
        }

        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[peg_trace WARN] manifest 写入失败: {e}", file=sys.stderr)
            return None
        return self.manifest_path

    def list_artifacts(self):
        """列出本次 trace 的所有产出物（从内存 manifest，无需读盘）。"""
        return list(self.artifacts)


# ============================================================
# CLI（手动操作 trace，非 PEG-A 运行时使用）
# ============================================================

def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="PEG-A Meta-Loop 思考过程 + 产出物持久化")
    sub = ap.add_subparsers(dest="cmd")

    # list: 列出所有 trace
    p_list = sub.add_parser("list", help="列出所有 trace_id")
    p_list.add_argument("--root", default=TRACES_ROOT, help="traces 根目录")

    # show: 显示某 trace 的 manifest
    p_show = sub.add_parser("show", help="显示某 trace 的 manifest")
    p_show.add_argument("trace_id", help="trace_id")
    p_show.add_argument("--root", default=TRACES_ROOT, help="traces 根目录")

    # tail: 打印某 trace 的 reasoning.jsonl
    p_tail = sub.add_parser("tail", help="打印某 trace 的 reasoning.jsonl")
    p_tail.add_argument("trace_id", help="trace_id")
    p_tail.add_argument("--root", default=TRACES_ROOT, help="traces 根目录")
    p_tail.add_argument("-n", type=int, default=20, help="末尾 N 条")

    args = ap.parse_args()

    if args.cmd == "list":
        if not os.path.isdir(args.root):
            print(f"traces 根目录不存在: {args.root}", file=sys.stderr)
            sys.exit(1)
        rows = []
        for name in sorted(os.listdir(args.root)):
            if name.startswith("_"):
                continue  # 跳过 _historical_index 等特殊文件
            d = os.path.join(args.root, name)
            if not os.path.isdir(d):
                continue
            mf = os.path.join(d, "manifest.json")
            if os.path.isfile(mf):
                try:
                    with open(mf, encoding="utf-8") as f:
                        m = json.load(f)
                    rows.append({
                        "trace_id": name,
                        "status": m.get("status", "?"),
                        "steps": m.get("step_count", "?"),
                        "artifacts": len(m.get("artifacts", [])),
                        "task": m.get("task_summary", "")[:40],
                    })
                except (OSError, json.JSONDecodeError):
                    rows.append({"trace_id": name, "status": "?",
                                 "steps": "?", "artifacts": "?", "task": "?"})
            else:
                rows.append({"trace_id": name, "status": "(无 manifest)",
                             "steps": "?", "artifacts": "?", "task": "?"})
        print(f"{'trace_id':<28} {'status':<12} {'steps':<6} {'arts':<5} task")
        print("-" * 80)
        for r in rows:
            print(f"{r['trace_id']:<28} {r['status']:<12} {str(r['steps']):<6} "
                  f"{str(r['artifacts']):<5} {r['task']}")

    elif args.cmd == "show":
        mf = os.path.join(args.root, args.trace_id, "manifest.json")
        if not os.path.isfile(mf):
            print(f"manifest 不存在: {mf}", file=sys.stderr)
            sys.exit(1)
        with open(mf, encoding="utf-8") as f:
            print(f.read())

    elif args.cmd == "tail":
        rp = os.path.join(args.root, args.trace_id, "reasoning.jsonl")
        if not os.path.isfile(rp):
            print(f"reasoning.jsonl 不存在: {rp}", file=sys.stderr)
            sys.exit(1)
        with open(rp, encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-args.n:]:
            entry = json.loads(line)
        # 重新读并 pretty print
        for line in lines[-args.n:]:
            entry = json.loads(line)
            print(f"[{entry.get('step', '?')}] {entry.get('phase', '?'):<10} "
                  f"{entry.get('action', '?')}")
            for e in entry.get("evidence", []):
                print(f"    - {e}")
            print(f"    → next: {entry.get('next', '?')}")

    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    _cli()
