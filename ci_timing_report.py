#!/usr/bin/env python3
"""
ci_timing_report.py
模拟 CI/CD 流水线运行，输出 11 项检查的耗时分布报告。

用法: python ci_timing_report.py
输出: 终端表格 + ci_timing_report.json
"""
import json
import time
import subprocess
import sys
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_doc_alignment_json.py"
JSON_PATH = HERE / "doc_alignment.json"
REPORT_PATH = HERE / "ci_timing_report.json"

STEPS = [
    ("1. JSON 语法合法性", "语法检查"),
    ("2. 顶层字段完整性", "顶层字段"),
    ("3. meta 字段 + 类型校验", "meta 类型"),
    ("4. role 字段完整性", "role"),
    ("5. D1–D6 规则结构", "D1–D6"),
    ("6. workflow 五步完整性", "workflow"),
    ("7. self_test 7 条完整性", "self_test"),
    ("8. security §12/§13 完整性", "security"),
    ("9. related_files 路径一致性", "路径一致性"),
    ("10. 空值校验", "空值"),
    ("11. 数组非空校验", "数组非空"),
]


def micro_benchmark_check(label, fn, *args):
    """运行单个检查并计时"""
    t0 = time.perf_counter()
    try:
        fn(*args)
        ok = True
        msg = ""
    except AssertionError as e:
        ok = False
        msg = str(e)
    elapsed = (time.perf_counter() - t0) * 1000
    return {"label": label, "ok": ok, "elapsed_ms": round(elapsed, 3), "error": msg}


def run_full_validation():
    """运行完整 validate_doc_alignment_json.py 并计时"""
    t0 = time.perf_counter()
    r = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    total = (time.perf_counter() - t0) * 1000
    return {"ok": r.returncode == 0, "total_ms": round(total, 3), "stdout": r.stdout, "stderr": r.stderr}


def micro_benchmark_all():
    """独立运行 11 项检查，逐项计时"""
    import validate_doc_alignment_json as v

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    results.append(micro_benchmark_check("1. JSON 语法合法性", v.check_json_syntax, str(JSON_PATH)))
    results.append(micro_benchmark_check("2. 顶层字段完整性", v.check_top_level_keys, data))
    results.append(micro_benchmark_check("3. meta 字段 + 类型", v.check_meta, data))
    results.append(micro_benchmark_check("4. role 字段", v.check_role, data))
    results.append(micro_benchmark_check("5. D1–D6 规则结构", v.check_rules, data))
    results.append(micro_benchmark_check("6. workflow 五步", v.check_workflow, data))
    results.append(micro_benchmark_check("7. self_test 7 条", v.check_self_test, data))
    results.append(micro_benchmark_check("8. security §12/§13", v.check_security, data))
    results.append(micro_benchmark_check("9. related_files 路径", v.check_related_files, data))
    results.append(micro_benchmark_check("10. 空值校验", v.check_null_values, data))
    results.append(micro_benchmark_check("11. 数组非空", v.check_array_emptiness, data))
    return results


def main():
    print("=" * 64)
    print("  doc_alignment CI/CD 模拟运行报告")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 64)

    # 1. 完整运行
    print("\n>>> 完整运行 validate_doc_alignment_json.py ...")
    full = run_full_validation()
    print(f"    退出码: {full['ok']}  |  总耗时: {full['total_ms']}ms")

    # 2. 逐项微基准
    print("\n>>> 逐项微基准（11 项独立计时）...\n")
    results = micro_benchmark_all()

    # 表格
    print(f"{'#':<4} {'检查项':<28} {'状态':<8} {'耗时(ms)':<12} {'占比':<8}")
    print("-" * 64)
    total_micro = sum(r["elapsed_ms"] for r in results)
    for r in results:
        pct = f"{r['elapsed_ms']/total_micro*100:.1f}%"
        status = "✅" if r["ok"] else "❌"
        print(f"{results.index(r)+1:<4} {r['label']:<28} {status:<8} {r['elapsed_ms']:<12.3f} {pct:<8}")

    print("-" * 64)
    print(f"{'合计':<4} {'':<28} {'':<8} {total_micro:<12.3f} {'100%':<8}")

    # 3. 对比
    print(f"\n>>> 完整运行 vs 微基准总和")
    print(f"    完整运行: {full['total_ms']}ms")
    print(f"    微基准和: {total_micro:.3f}ms")
    print(f"    差额:     {full['total_ms'] - total_micro:.3f}ms (Python import + 进程启动开销)")

    # 4. 瓶颈分析
    print(f"\n>>> 耗时瓶颈分析")
    sorted_results = sorted(results, key=lambda r: r["elapsed_ms"], reverse=True)
    for i, r in enumerate(sorted_results[:3], 1):
        pct = f"{r['elapsed_ms']/total_micro*100:.1f}%"
        print(f"    Top {i}: {r['label']} — {r['elapsed_ms']:.3f}ms ({pct})")

    # 5. JSON 报告
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python_version": sys.version.split()[0],
        "full_run": {"ok": full["ok"], "total_ms": full["total_ms"]},
        "micro_benchmarks": results,
        "micro_total_ms": round(total_micro, 3),
        "overhead_ms": round(full["total_ms"] - total_micro, 3),
        "top_bottlenecks": [
            {"rank": i+1, "label": r["label"], "elapsed_ms": r["elapsed_ms"]}
            for i, r in enumerate(sorted_results[:3])
        ],
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n>>> JSON 报告已保存: {REPORT_PATH}")

    # 6. 隐藏警告检查
    if full["stderr"]:
        print(f"\n>>> ⚠️ 发现 stderr 输出:")
        print(full["stderr"][:500])
    else:
        print(f"\n>>> ✅ 无隐藏警告（stderr 为空）")

    print(f"\n{'='*64}")
    if full["ok"] and all(r["ok"] for r in results):
        print("  结论: 全部检查通过 ✅ — 可安全部署到 CI/CD")
    else:
        print("  结论: 存在失败项 ❌ — 请修复后重新运行")
    print("=" * 64)


if __name__ == "__main__":
    main()