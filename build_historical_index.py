#!/usr/bin/env python3
# build_historical_index.py
# 版本: v0.2 (2026-07-21)
#   v0.1 (2026-07-16): 一次性脚本，扫描历史产物，生成静态索引页
#   v0.2 (2026-07-21): 新增第六章「未来 Trace 预览」，扫描 traces/ 子目录
#                      列出 trace_id/status/steps/arts/started/ended/task 七列
#
# 一次性脚本：扫描历史产物，生成静态索引页 traces/_historical_index.md
#
# 用途:
#   peg_trace.py 落地前的历史会话没有思考链 trace（数据未持久化）。
#   本脚本把已有的工程化产物（versions.md / capability_registry.md /
#   drafts/ tech_notes/ fix_reports/）汇总成一个静态 Markdown 索引页，
#   便于审计人员快速定位历史变更。
#
# 第六章（v0.2 新增）:
#   扫描 traces/ 已产生的 trace 子目录，列出当前所有 trace，
#   让审计人员验证思考链是否已被持久化。
#
# 注意:
#   - 本脚本生成的索引是**静态快照**，不动态维护。
#   - 思考链（Meta-Loop 五拍）在 peg_trace.py 落地前从未持久化，
#     本索引只能列出"何时改了什么产物"，无法回答"为什么这样改"。
#   - 完整产物清单以 versions.md / capability_registry.md 为准。
#
# 用法:
#   python build_historical_index.py
#   python build_historical_index.py --root /path/to/meta_peg_agent
#   python build_historical_index.py --output /custom/path/index.md

import os
import sys
import re
import argparse
from datetime import datetime


def _module_dir():
    return os.path.dirname(os.path.abspath(__file__))


def scan_versions_md(meta_dir):
    """从 versions.md 抽取工程化产物表 + 自身提示词表。"""
    path = os.path.join(meta_dir, "versions.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def scan_capability_registry(meta_dir):
    """从 capability_registry.md 抽取演进信号日志段。"""
    path = os.path.join(meta_dir, "capability_registry.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 抽取「演进信号日志」段（## 演进信号日志 到下一个 ## 之间）
    m = re.search(r"## 演进信号日志(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return "(未找到演进信号日志段)"


def scan_dir_files(dir_path, label):
    """列出某目录下所有文件 + mtime，返回 Markdown 表格行。"""
    if not os.path.isdir(dir_path):
        return f"_(目录不存在: {dir_path})_\n"
    rows = []
    for name in sorted(os.listdir(dir_path)):
        full = os.path.join(dir_path, name)
        if not os.path.isfile(full):
            continue
        mtime = os.path.getmtime(full)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        size = os.path.getsize(full)
        rows.append(f"| {name} | {mtime_str} | {size} B |")
    if not rows:
        return f"_(目录为空: {dir_path})_\n"
    header = f"| 文件 | mtime | 大小 |\n|---|---|---|\n"
    return header + "\n".join(rows) + "\n"


def scan_workbuddy_memory(workspace_root):
    """外链 .workbuddy/memory/ 与 trae-cn session_memory，不复制内容。"""
    lines = []
    # .workbuddy/memory/
    wb_mem = os.path.join(workspace_root, ".workbuddy", "memory")
    if os.path.isdir(wb_mem):
        lines.append(f"### .workbuddy/memory/（按日会话摘要）")
        lines.append(f"路径: `{wb_mem}`")
        for name in sorted(os.listdir(wb_mem)):
            full = os.path.join(wb_mem, name)
            if os.path.isfile(full):
                mtime = os.path.getmtime(full)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                lines.append(f"- `{name}` (mtime: {mtime_str})")
        lines.append("")
    # trae-cn session_memory（仅提示存在，不扫描内容）
    trae_mem = os.path.expanduser(
        r"~\.trae-cn\memory\projects\-c-Users-1-Documents-trae-projects-douyin-db")
    if os.path.isdir(trae_mem):
        lines.append(f"### Trae CN session_memory（外部，不复制内容）")
        lines.append(f"路径: `{trae_mem}`")
        lines.append(f"_(按日期子目录组织，含 session_memory_*.jsonl 与 topics.md)_")
    return "\n".join(lines)


def scan_future_traces(traces_root):
    """扫描 traces/ 已存在的 trace 子目录，列出当前所有 trace。

    与历史索引的"历史产物清单"不同：本节列出 peg_trace.py 落地后
    实际产生的 trace 子目录，让审计人员验证思考链是否已被持久化。

    返回:
      (table_md, count) — Markdown 表格 + trace 总数
    """
    if not os.path.isdir(traces_root):
        return "_(traces/ 目录尚未创建，peg_trace.py 未运行过)_\n", 0

    rows = []
    for name in sorted(os.listdir(traces_root)):
        if name.startswith("_"):
            continue  # 跳过 _historical_index.md 等特殊文件
        d = os.path.join(traces_root, name)
        if not os.path.isdir(d):
            continue
        # 读 manifest.json 获取元信息
        mf = os.path.join(d, "manifest.json")
        if os.path.isfile(mf):
            try:
                import json
                with open(mf, encoding="utf-8") as f:
                    m = json.load(f)
                rows.append({
                    "trace_id": name,
                    "status": m.get("status", "?"),
                    "steps": m.get("step_count", "?"),
                    "artifacts": len(m.get("artifacts", [])),
                    "started": m.get("started_at", "?")[:19],
                    "ended": (m.get("ended_at") or "?")[:19],
                    "task": m.get("task_summary", "")[:40],
                })
            except (OSError, ValueError):
                rows.append({
                    "trace_id": name, "status": "(manifest 解析失败)",
                    "steps": "?", "artifacts": "?",
                    "started": "?", "ended": "?", "task": "?",
                })
        else:
            # 无 manifest（未 end() 或被中断）
            rows.append({
                "trace_id": name, "status": "(未结束)",
                "steps": "?", "artifacts": "?",
                "started": "?", "ended": "?", "task": "?",
            })

    if not rows:
        return ("_(traces/ 已创建但尚无 trace 子目录——peg_trace.py 已落地但还未被调用)_\n", 0)

    header = ("| trace_id | status | steps | arts | started | ended | task |\n"
              "|---|---|---|---|---|---|---|\n")
    body = "\n".join(
        f"| {r['trace_id']} | {r['status']} | {r['steps']} | "
        f"{r['artifacts']} | {r['started']} | {r['ended']} | {r['task']} |"
        for r in rows
    )
    return header + body + "\n", len(rows)


def build_index(meta_dir, workspace_root):
    """组装完整索引页 Markdown。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = []
    parts.append("# 历史 Trace 索引（peg_trace.py 落地前）\n")
    parts.append(f"> 生成时间: {now}")
    parts.append(f"> 生成脚本: `build_historical_index.py`")
    parts.append("")
    parts.append("> **仅为审计便利的静态索引。**")
    parts.append("> peg_trace.py 落地前 Meta-Loop 思考链（Plan→Act→Observe→Reflect→Coordinate）"
                 "未持久化，本索引只能回答「何时改了什么产物」，无法回答「为什么这样改」。")
    parts.append("> 完整产物清单以 `versions.md` / `capability_registry.md` 为准。")
    parts.append("")

    parts.append("---\n")
    parts.append("## 一、工程化产物版本历史（versions.md 原文）\n")
    versions = scan_versions_md(meta_dir)
    parts.append("```markdown" if versions else "_(versions.md 不存在)_")
    if versions:
        parts.append(versions)
        parts.append("```")
    parts.append("")

    parts.append("---\n")
    parts.append("## 二、演进信号日志（capability_registry.md 抽取）\n")
    parts.append(scan_capability_registry(meta_dir))
    parts.append("")

    parts.append("---\n")
    parts.append("## 三、产出物文件清单\n")
    parts.append("### drafts/\n")
    parts.append(scan_dir_files(os.path.join(meta_dir, "drafts"), "drafts"))
    parts.append("")
    parts.append("### tech_notes/\n")
    parts.append(scan_dir_files(os.path.join(meta_dir, "tech_notes"), "tech_notes"))
    parts.append("")
    parts.append("### fix_reports/\n")
    parts.append(scan_dir_files(os.path.join(meta_dir, "fix_reports"), "fix_reports"))
    parts.append("")

    parts.append("---\n")
    parts.append("## 四、会话 Memory（外链，不复制内容）\n")
    parts.append(scan_workbuddy_memory(workspace_root))
    parts.append("")

    parts.append("---\n")
    parts.append("## 五、gate 闸门日志（meta_peg_agent/logs/）\n")
    parts.append(scan_dir_files(os.path.join(meta_dir, "logs"), "logs"))

    parts.append("---\n")
    traces_root = os.path.join(meta_dir, "traces")
    future_md, future_count = scan_future_traces(traces_root)
    parts.append("## 六、未来 Trace 预览（peg_trace.py 落地后产生）\n")
    parts.append("> 本节列出 `traces/` 下实际已产生的 trace 子目录，"
                 "对应 peg_trace.py 落地后的会话。")
    parts.append("> 每条 trace 含 `reasoning.jsonl`（思考链）+ `manifest.json`（产出物索引）+ `artifacts/`（产出物副本）。")
    parts.append(f">")
    parts.append(f"> 当前 trace 数: **{future_count}**")
    parts.append(">")
    parts.append("> 命令行查看: `python peg_trace.py list` / `python peg_trace.py show <trace_id>` / `python peg_trace.py tail <trace_id>`")
    parts.append("")
    parts.append(future_md)

    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description="生成历史 trace 静态索引页")
    ap.add_argument("--root", default=_module_dir(),
                    help="meta_peg_agent 目录（默认：脚本所在目录）")
    ap.add_argument("--workspace", default=os.path.dirname(_module_dir()),
                    help="workspace 根目录（默认：脚本父目录，用于扫描 .workbuddy/）")
    ap.add_argument("--output",
                    default=os.path.join(_module_dir(), "traces",
                                         "_historical_index.md"),
                    help="输出路径（默认：traces/_historical_index.md）")
    args = ap.parse_args()

    # 确保 traces/ 目录存在
    traces_dir = os.path.dirname(args.output)
    os.makedirs(traces_dir, exist_ok=True)

    content = build_index(args.root, args.workspace)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] 历史索引页已生成: {args.output}", file=sys.stderr)
    print(f"     大小: {os.path.getsize(args.output)} 字节", file=sys.stderr)


if __name__ == "__main__":
    main()
