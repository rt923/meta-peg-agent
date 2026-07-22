#!/usr/bin/env python3
"""
mock_helpers.py
PEG-A 测试 mock 数据构造工具集（供后续测试复用）

提供 3 个工厂函数:
  - make_mock_hash_store(path, scenario)
      构造 guardrails_enforce.py 的 HASH_STORE 4 种场景
  - make_mock_trace(traces_root, trace_id, status, steps, arts_count, task, manifest_broken)
      构造 peg_trace.py 的 trace 子目录（含 reasoning.jsonl + manifest.json + artifacts/）
  - make_mock_full_session(traces_root, trace_id=None, task=..., status=..., include_artifact=..., artifact_content=...)
      高阶函数：一次性构造完整 PEG-A 会话 trace（固定 5 拍 + 0/1 artifact）

设计原则:
  - 全部在调用方指定的路径下构造，不污染真实 traces/ 或 HASH_STORE
  - 字段命名严格对齐生产代码（如 build_historical_index.py 从 task_summary 读 task）
  - scenario 命名与生产代码行为对应（no_field / null_field / valid_hash / corrupt）

版本: v0.1 (2026-07-21)
"""
import os
import json
import hashlib


def make_mock_hash_store(path, scenario):
    """构造 mock HASH_STORE 的 4 种场景。

    参数:
      path: HASH_STORE 文件路径（如 '<phase0>.guardrail.json'）
      scenario: 场景名，取值:
        - "no_field":    旧产物（v0.2 时代），无 guardrail_token_hash 字段
        - "null_field":  字段存在但值为 None
        - "valid_hash":  字段为 "mock-token-123" 的 SHA256 哈希（用于匹配测试）
        - "corrupt":     非 JSON 内容（用于解析失败测试）

    返回:
      path（原样返回，便于链式调用）

    行为对应:
      - "no_field"    → cmd_unlock 退化为非空校验（WARN）
      - "null_field"  → cmd_unlock 退化为非空校验（WARN）
      - "valid_hash"  → cmd_unlock 走 secrets.compare_digest 比对
      - "corrupt"     → json.load 抛 ValueError（cmd_unlock 会捕获并标记）
    """
    store = {
        "file": "/mock/phase0.md",
        "file_hash": "a" * 64,
        "s13_hash": "b" * 64,
        "s13_present": True,
    }
    if scenario == "no_field":
        pass  # 旧产物，无 guardrail_token_hash 字段
    elif scenario == "null_field":
        store["guardrail_token_hash"] = None
    elif scenario == "valid_hash":
        store["guardrail_token_hash"] = hashlib.sha256(b"mock-token-123").hexdigest()
    elif scenario == "corrupt":
        store = "not a valid json {{{"
    else:
        raise ValueError(f"未知 scenario: {scenario}（合法值: no_field / null_field / valid_hash / corrupt）")

    with open(path, "w", encoding="utf-8") as f:
        f.write(store if isinstance(store, str) else json.dumps(store, ensure_ascii=False, indent=2))
    return path


def make_mock_trace(traces_root, trace_id, status, steps, arts_count, task, manifest_broken=False):
    """构造 mock trace 子目录（含完整三件套）。

    参数:
      traces_root:       traces/ 根目录
      trace_id:          trace 标识（如 "20260721_100000_mock"）
      status:            trace 状态（"completed" / "aborted"）
      steps:             reasoning.jsonl 中的 step 数（不含 trace_start）
      arts_count:        artifacts/ 中的产出物数量
      task:              任务摘要（写入 manifest 的 task_summary 字段）
      manifest_broken:   True 时 manifest.json 写成损坏 JSON（用于解析失败测试）

    返回:
      trace_dir（trace 子目录路径，便于链式调用）

    产出物结构:
      <traces_root>/<trace_id>/
        ├── reasoning.jsonl     # 1 行 trace_start + steps 行 Meta-Loop 记录
        ├── manifest.json       # trace 元信息 + artifacts 索引
        └── artifacts/
            └── <trace_id>-art-<N>.md

    注意:
      - manifest 的 task 字段名是 "task_summary"（对齐 build_historical_index.py:142）
      - reasoning.jsonl 的 trace_start 行 event="trace_start"（对齐 peg_trace.py Tracer.start）
      - artifacts 扩展名按 artifact_type 决定（默认 .md）
    """
    trace_dir = os.path.join(traces_root, trace_id)
    os.makedirs(trace_dir, exist_ok=True)
    artifacts_dir = os.path.join(trace_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # reasoning.jsonl: trace_start + steps 行
    reasoning_path = os.path.join(trace_dir, "reasoning.jsonl")
    with open(reasoning_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "event": "trace_start",
            "ts": "2026-07-21T10:00:00Z",
            "trace_id": trace_id,
            "task": task,
        }) + "\n")
        phases = ["Plan", "Act", "Observe", "Reflect", "Coordinate"]
        for i in range(steps):
            f.write(json.dumps({
                "step": i + 1,
                "ts": "2026-07-21T10:00:00Z",
                "trace_id": trace_id,
                "phase": phases[i % 5],
                "action": f"动作 {i+1}",
                "evidence": [f"证据 {i+1}"],
                "next_step": f"下一步 {i+1}",
            }) + "\n")

    # manifest.json
    manifest_path = os.path.join(trace_dir, "manifest.json")
    if manifest_broken:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("{ broken json")
    else:
        artifacts = []
        for i in range(arts_count):
            art_id = f"{trace_id}-art-{i+1}"
            art_path = os.path.join(artifacts_dir, f"{art_id}.md")
            with open(art_path, "w", encoding="utf-8") as f:
                f.write(f"# Mock artifact {i+1}\n内容\n")
            artifacts.append({
                "id": art_id,
                "type": "tech_note",
                "path": f"artifacts/{art_id}.md",
                "sha256": hashlib.sha256(f"art{i+1}".encode()).hexdigest(),
                "origin_step": i + 1,
            })
        manifest = {
            "trace_id": trace_id,
            "task_summary": task,  # build_historical_index 从 task_summary 读
            "started_at": "2026-07-21T10:00:00Z",
            "ended_at": "2026-07-21T10:05:00Z" if status != "aborted" else None,
            "status": status,
            "step_count": steps,
            "artifacts": artifacts,
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    return trace_dir


def make_mock_full_session(traces_root, trace_id=None, task="mock 完整会话",
                           status="completed", include_artifact=True, artifact_content=None):
    """高阶函数：一次性构造完整的 PEG-A 会话 trace（5 拍 + 1 artifact）。

    参数:
      traces_root:       traces/ 根目录
      trace_id:          trace 标识，None 时自动生成时间戳格式 ID
      task:              任务摘要（默认 "mock 完整会话"）
      status:            trace 状态（"completed" / "aborted"，默认 "completed"）
      include_artifact:  是否包含 1 个 artifact（默认 True）
      artifact_content:  artifact 内容，None 时用默认 mock 内容

    返回:
      dict: {
          "trace_dir":   trace 子目录路径,
          "trace_id":     trace_id,
          "reasoning_path": reasoning.jsonl 路径,
          "manifest_path":  manifest.json 路径,
          "artifact_path":  artifact 文件路径（include_artifact=False 时为 None）,
      }

    产出物结构（完整 PEG-A 会话）:
      <traces_root>/<trace_id>/
        ├── reasoning.jsonl     # 1 行 trace_start + 5 行 Meta-Loop（Plan/Act/Observe/Reflect/Coordinate）
        ├── manifest.json       # status="completed", step_count=5, 1 artifact
        └── artifacts/
            └── <trace_id>-full-art.md

    与 make_mock_trace 的区别:
      - make_mock_trace: 参数化构造（任意 steps/arts_count），适合边界测试
      - make_mock_full_session: 固定 5 拍 + 1 artifact 的标准会话，适合集成测试/演示

    用法:
      >>> from mock_helpers import make_mock_full_session
      >>> result = make_mock_full_session("/tmp/traces")
      >>> result["trace_id"]
      '20260721_100000_full'
      >>> result["artifact_path"]
      '/tmp/traces/20260721_100000_full/artifacts/20260721_100000_full-full-art.md'
    """
    import datetime

    if trace_id is None:
        trace_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_full"

    # 复用 make_mock_trace 构造基础结构
    arts_count = 1 if include_artifact else 0
    trace_dir = make_mock_trace(
        traces_root=traces_root,
        trace_id=trace_id,
        status=status,
        steps=5,  # 固定 5 拍
        arts_count=arts_count,
        task=task,
        manifest_broken=False,
    )

    # 如果指定了 artifact_content，覆盖默认内容
    artifact_path = None
    if include_artifact:
        artifact_filename = f"{trace_id}-full-art.md"
        artifact_path = os.path.join(trace_dir, "artifacts", artifact_filename)
        # make_mock_trace 已经创建了 <trace_id>-art-1.md，重命名为 full-art
        old_artifact_path = os.path.join(trace_dir, "artifacts", f"{trace_id}-art-1.md")
        if os.path.exists(old_artifact_path):
            os.rename(old_artifact_path, artifact_path)
        # 覆盖内容
        if artifact_content is None:
            artifact_content = f"# Mock PEG-A 完整会话 artifact\n\ntrace_id: {trace_id}\ntask: {task}\nstatus: {status}\n"
        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(artifact_content)
        # 同步更新 manifest 中的 artifact 路径
        manifest_path = os.path.join(trace_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        if manifest["artifacts"]:
            manifest["artifacts"][0]["id"] = f"{trace_id}-full-art"
            manifest["artifacts"][0]["path"] = f"artifacts/{artifact_filename}"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {
        "trace_dir": trace_dir,
        "trace_id": trace_id,
        "reasoning_path": os.path.join(trace_dir, "reasoning.jsonl"),
        "manifest_path": os.path.join(trace_dir, "manifest.json"),
        "artifact_path": artifact_path,
    }
