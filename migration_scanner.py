#!/usr/bin/env python3
"""
migration_scanner.py
基于 doc_alignment_migration_checklist.md 自动扫描指定目录，输出缺失项报告。

扫描维度（D1–D6，共 37 项）：
  D1: 实证文档对齐 — 14 项（函数签名 / 场景覆盖 / 字段名 / 产出物结构 / 行为描述）
  D2: 同性质遗漏扫描 — 4 项
  D3: 目录树完整性 — 5 项
  D4: 登记文件交叉引用 — 5 项
  D5: 运行时产物识别 — 5 项
  D6: 演进信号回溯 — 4 项

用法:
  python migration_scanner.py <target_directory> [--output report.md] [--json report.json]

输出:
  - 终端：逐项检查结果 + 通过率
  - Markdown 报告：完整评估清单（含优先级矩阵）
  - JSON 报告：机器可读结构化数据

版本: v0.1 (2026-07-22)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ── 检查项定义（对齐 doc_alignment_migration_checklist.md） ──

CHECKS = {
    "D1": {
        "label": "实证文档对齐",
        "total": 14,
        "items": [
            # 维度 1: 函数签名
            ("1.1", "所有公开函数的参数名在文档中正确列出", "function_signature"),
            ("1.2", "所有公开函数的默认参数值在文档中正确标注", "function_signature"),
            ("1.3", "所有公开函数的返回值类型在文档中明确标注", "function_signature"),
            ("1.4", "文档中声称的函数签名与代码实际签名一一对应", "function_signature"),
            # 维度 2: 场景覆盖
            ("1.5", "每个 if/else 分支在文档中有对应行为描述", "scenario_coverage"),
            ("1.6", "每个异常处理路径在文档中有说明", "scenario_coverage"),
            ("1.7", "每个配置选项/开关在文档中有说明", "scenario_coverage"),
            # 维度 3: 字段名
            ("1.8", "生产代码中的字段名与文档完全一致", "field_names"),
            ("1.9", "JSON schema / API 响应字段名与文档一致", "field_names"),
            # 维度 4: 产出物结构
            ("1.10", "文档中的目录树与实际磁盘文件一致", "artifact_structure"),
            ("1.11", "文档中的文件名模板与代码实际产出一致", "artifact_structure"),
            ("1.12", "文档中的数值与实际运行结果一致", "artifact_structure"),
            # 维度 5: 行为描述
            ("1.13", "文档中描述的行为与代码实际行为一致", "behavior_description"),
            ("1.14", "文档中的示例代码可实际运行", "behavior_description"),
        ],
    },
    "D2": {
        "label": "同性质遗漏扫描",
        "total": 4,
        "items": [
            ("2.1", "是否存在只修了 .md 忘了 .py 的同类偏差", "cross_file_scan"),
            ("2.2", "是否存在只修了英文文档忘了中文文档的同类偏差", "cross_lang_scan"),
            ("2.3", "是否存在只修了 README 忘了 API 文档的同类偏差", "cross_doc_scan"),
            ("2.4", "是否有已修复的偏差在关联文件中仍有残留旧值", "residual_scan"),
        ],
    },
    "D3": {
        "label": "目录树完整性",
        "total": 5,
        "items": [
            ("3.1", "是否有 workspace_map.md 或等效目录树文件", "workspace_map_exists"),
            ("3.2", "目录树中的文件数与磁盘实际文件数一致", "count_match"),
            ("3.3", "运行时产物未被逐名登记到目录树", "no_runtime_named"),
            ("3.4", "所有目录树中的文件在磁盘上均存在", "no_phantom"),
            ("3.5", "磁盘上的所有源文件在目录树中均有登记", "full_coverage"),
        ],
    },
    "D4": {
        "label": "登记文件交叉引用",
        "total": 5,
        "items": [
            ("4.1", "是否有 versions.md 或等效版本登记文件", "versions_exists"),
            ("4.2", "versions.md 中登记的文件在项目目录中实际存在", "versions_actual"),
            ("4.3", "是否有 capability_registry.md 或等效能力登记册", "cap_registry_exists"),
            ("4.4", "三份登记文件是否有交叉引用", "cross_ref_exists"),
            ("4.5", "最近一次变更是否在三份登记文件中同步更新", "sync_update"),
        ],
    },
    "D5": {
        "label": "运行时产物识别",
        "total": 5,
        "items": [
            ("5.1", "日志文件是否用通配模式覆盖", "wildcard_logs"),
            ("5.2", "trace/artifacts 产物是否用通配覆盖", "wildcard_trace"),
            ("5.3", "缓存目录是否被排除", "cache_excluded"),
            ("5.4", "IDE 配置目录是否用目录级注释处理", "ide_annotated"),
            ("5.5", "通配模式是否统一使用正斜杠 /", "wildcard_slash"),
        ],
    },
    "D6": {
        "label": "演进信号回溯",
        "total": 4,
        "items": [
            ("6.1", "最近一次变更的修复范围是否准确登记", "scope_accurate"),
            ("6.2", "最近一次变更的回归验证结果是否写入登记条目", "regression_included"),
            ("6.3", "演进信号计数是否与变更次数一致", "count_consistent"),
            ("6.4", "是否有未登记的变更", "no_unregistered"),
        ],
    },
}


# ── 扫描逻辑 ──────────────────────────────────────────

def scan_directory(target_dir: Path) -> dict:
    """扫描目标目录，返回每项检查的结果（pass / fail / unknown）。"""
    target = Path(target_dir)
    results = {}

    # ── D3: 可自动检测的项 ──
    # 3.1: workspace_map.md 存在性
    ws_map = target / "workspace_map.md"
    results["3.1"] = ("pass" if ws_map.exists() else "fail", str(ws_map))

    # 3.3: 运行时产物是否被逐名登记
    if ws_map.exists():
        ws_content = ws_map.read_text(encoding="utf-8")
        runtime_patterns = ["gate_", ".jsonl", "artifacts/", "__pycache__"]
        suspicious = [p for p in runtime_patterns if p in ws_content and not ws_content.count(f"*{p}") > 0]
        results["3.3"] = ("pass" if not suspicious else "fail", f"含逐名登记: {suspicious}" if suspicious else "")
    else:
        results["3.3"] = ("unknown", "无 workspace_map.md")

    # 3.2: 文件数一致性
    if ws_map.exists():
        ws_count = ws_content.count("├──") + ws_content.count("└──")
        disk_count = len([f for f in target.rglob("*") if f.is_file()
                          and "__pycache__" not in str(f)
                          and ".pytest_cache" not in str(f)
                          and ".git" not in str(f)
                          and "node_modules" not in str(f)])
        results["3.2"] = ("pass" if abs(ws_count - disk_count) <= 5 else "fail",
                          f"目录树 ≈ {ws_count}, 磁盘 {disk_count} (差 {abs(ws_count - disk_count)})")
    else:
        results["3.2"] = ("unknown", "无 workspace_map.md")

    # 3.4: 目录树虚假条目
    if ws_map.exists():
        phantom = []
        for line in ws_content.splitlines():
            m = re.search(r"├──\s+(\S+)", line)
            if m:
                fname = m.group(1)
                if not (target / fname).exists():
                    phantom.append(fname)
        results["3.4"] = ("pass" if not phantom else "fail", f"虚假条目: {phantom}" if phantom else "")
    else:
        results["3.4"] = ("unknown", "无 workspace_map.md")

    # 3.5: 磁盘文件全覆盖
    if ws_map.exists():
        missing = []
        for f in target.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f) and ".pytest_cache" not in str(f):
                fname = f.name
                if fname not in ws_content:
                    missing.append(fname)
        results["3.5"] = ("pass" if not missing else "fail", f"目录树遗漏: {missing}" if missing else "")
    else:
        results["3.5"] = ("unknown", "无 workspace_map.md")

    # ── D4: 可自动检测的项 ──
    versions = target / "versions.md"
    cap_registry = target / "capability_registry.md"
    results["4.1"] = ("pass" if versions.exists() else "fail", str(versions))
    results["4.3"] = ("pass" if cap_registry.exists() else "fail", str(cap_registry))

    # 4.4: 交叉引用
    if versions.exists() and ws_map.exists() and cap_registry.exists():
        ver_content = versions.read_text(encoding="utf-8")
        cross = all(
            ref in ver_content
            for ref in ["workspace_map", "capability_registry"]
        )
        results["4.4"] = ("pass" if cross else "fail", "三份登记文件无交叉引用")
    else:
        results["4.4"] = ("unknown", "至少一份登记文件缺失")

    # 4.2: versions 登记文件实际存在
    if versions.exists():
        ver_content = versions.read_text(encoding="utf-8")
        registered = re.findall(r"`([^`]+\.(?:py|md|json|yml|ps1))`", ver_content)
        missing_actual = [f for f in registered if not (target / f).exists()]
        results["4.2"] = ("pass" if not missing_actual else "fail",
                          f"登记但不存在: {missing_actual}" if missing_actual else "")
    else:
        results["4.2"] = ("unknown", "无 versions.md")

    # 4.5: 同步更新
    results["4.5"] = ("unknown", "需人工检查最近提交记录")

    # ── D5: 可自动检测的项 ──
    # 5.5: 通配模式正斜杠
    if ws_map.exists():
        has_backslash = "\\" in ws_content and "*" in ws_content
        results["5.5"] = ("pass" if not has_backslash else "fail",
                          "通配模式含反斜杠" if has_backslash else "")
    else:
        results["5.5"] = ("unknown", "无 workspace_map.md")

    # 5.3: 缓存排除
    if ws_map.exists():
        cache_ok = all(
            p not in ws_content
            for p in ["__pycache__/", ".pytest_cache/", "node_modules/"]
        )
        results["5.3"] = ("pass" if cache_ok else "fail", "缓存目录未排除")
    else:
        results["5.3"] = ("unknown", "无 workspace_map.md")

    # 5.1, 5.2, 5.4: 需人工
    results["5.1"] = ("unknown", "需人工检查日志通配")
    results["5.2"] = ("unknown", "需人工检查 trace 通配")
    results["5.4"] = ("unknown", "需人工检查 IDE 配置注释")

    # ── D1, D2, D6: 大部分需人工 ──
    for did in ["D1", "D2", "D6"]:
        for item_id, _, _ in CHECKS[did]["items"]:
            if item_id not in results:
                results[item_id] = ("unknown", "需人工检查代码与文档对齐")

    return results


def generate_report(results: dict, target_dir: str) -> str:
    """生成 Markdown 报告"""
    lines = []
    lines.append(f"# doc_alignment 迁移评估报告")
    lines.append(f"")
    lines.append(f"| 属性 | 值 |")
    lines.append(f"|---|---|")
    lines.append(f"| 目标目录 | `{target_dir}` |")
    lines.append(f"| 扫描时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append(f"| 扫描工具 | migration_scanner.py v0.1 |")
    lines.append(f"")

    summary = {}
    for did in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        info = CHECKS[did]
        passed = 0
        failed = 0
        unknown = 0
        items = []
        for item_id, desc, _ in info["items"]:
            status, detail = results.get(item_id, ("unknown", ""))
            if status == "pass":
                passed += 1
            elif status == "fail":
                failed += 1
            else:
                unknown += 1
            icon = {"pass": "✅", "fail": "❌", "unknown": "⚠️"}[status]
            items.append((item_id, desc, icon, detail))
        summary[did] = {"label": info["label"], "total": info["total"],
                        "passed": passed, "failed": failed, "unknown": unknown,
                        "items": items}

    # 总览表
    lines.append("## 总览")
    lines.append("")
    lines.append(f"| 维度 | 标签 | 通过 | 失败 | 未知 | 通过率 |")
    lines.append(f"|---|---|---|---|---|---|")
    total_pass = 0
    total_fail = 0
    total_unk = 0
    total_all = 0
    for did in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        s = summary[did]
        rate = f"{s['passed']/s['total']*100:.0f}%" if s['total'] > 0 else "0%"
        lines.append(f"| {did} | {s['label']} | {s['passed']} | {s['failed']} | {s['unknown']} | {rate} |")
        total_pass += s["passed"]
        total_fail += s["failed"]
        total_unk += s["unknown"]
        total_all += s["total"]
    overall = f"{total_pass/total_all*100:.0f}%" if total_all > 0 else "0%"
    lines.append(f"| **总计** | | **{total_pass}** | **{total_fail}** | **{total_unk}** | **{overall}** |")
    lines.append("")

    # 逐维度详情
    for did in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        s = summary[did]
        lines.append(f"## {did}: {s['label']} ({s['passed']}/{s['total']} 通过)")
        lines.append("")
        lines.append(f"| # | 检查项 | 状态 | 详情 |")
        lines.append(f"|---|---|---|---|")
        for item_id, desc, icon, detail in s["items"]:
            lines.append(f"| {item_id} | {desc} | {icon} | {detail} |")
        lines.append("")

    # 优先级建议
    lines.append("## 优先级建议")
    lines.append("")
    if total_fail > 0:
        if any(summary[d]["failed"] > 0 for d in ["D1", "D3"]):
            lines.append("🔴 **P0 立即**: 存在真偏差或目录树虚假条目，立即修复")
        if summary["D3"]["failed"] > 2 or summary["D4"]["failed"] > 3:
            lines.append("🟠 **P1 本周**: 登记基础设施缺失，本周补齐")
        if summary["D1"]["unknown"] > 3 or summary["D2"]["failed"] > 1:
            lines.append("🟡 **P2 本月**: 文档质量提升，本月内完成")
        if summary["D5"]["failed"] > 0 or summary["D6"]["failed"] > 0:
            lines.append("🟢 **P3 持续**: 流程规范化，持续改进")
    else:
        lines.append("✅ 所有自动检测项通过 — 该项目已满足 doc_alignment 基线要求")
    lines.append("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="doc_alignment 迁移扫描器")
    p.add_argument("target", help="目标目录路径")
    p.add_argument("--output", "-o", default=None, help="Markdown 报告输出路径")
    p.add_argument("--json", "-j", default=None, help="JSON 报告输出路径")
    args = p.parse_args()

    target = Path(args.target)
    if not target.is_dir():
        print(f"❌ 目标目录不存在: {target}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 扫描目标: {target}")
    print(f"   共 {sum(v['total'] for v in CHECKS.values())} 项检查 (D1–D6)\n")

    results = scan_directory(target)

    # 终端输出
    for did in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        info = CHECKS[did]
        passed = sum(1 for item_id, _, _ in info["items"] if results.get(item_id, ("unknown",))[0] == "pass")
        failed = sum(1 for item_id, _, _ in info["items"] if results.get(item_id, ("unknown",))[0] == "fail")
        unknown = sum(1 for item_id, _, _ in info["items"] if results.get(item_id, ("unknown",))[0] == "unknown")
        print(f"  {did} {info['label']}: {passed}✅ {failed}❌ {unknown}⚠️  / {info['total']}")

    # 输出报告
    md_report = generate_report(results, str(target))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"\n📄 Markdown 报告已保存: {args.output}")
    else:
        out_path = target / "doc_alignment_migration_report.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"\n📄 Markdown 报告已保存: {out_path}")

    if args.json:
        json_report = {
            "target": str(target),
            "timestamp": datetime.now().isoformat(),
            "results": {k: {"status": v[0], "detail": v[1]} for k, v in results.items()},
            "summary": {did: {
                "passed": sum(1 for item_id, _, _ in CHECKS[did]["items"]
                             if results.get(item_id, ("unknown",))[0] == "pass"),
                "failed": sum(1 for item_id, _, _ in CHECKS[did]["items"]
                             if results.get(item_id, ("unknown",))[0] == "fail"),
                "unknown": sum(1 for item_id, _, _ in CHECKS[did]["items"]
                              if results.get(item_id, ("unknown",))[0] == "unknown"),
            } for did in ["D1", "D2", "D3", "D4", "D5", "D6"]},
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        print(f"📊 JSON 报告已保存: {args.json}")

    print("\n✅ 扫描完成")


if __name__ == "__main__":
    main()