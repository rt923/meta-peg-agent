#!/usr/bin/env python3
# run_safety_regression.py
# 安全回归 CI：读 safety_eval_suite.json -> 逐条喂给 explainability_check 闸门
# -> 断言 expected.action <-> 闸门结果 -> 输出报告 + 退出码。
#
# 用法:
#   python run_safety_regression.py
#   python run_safety_regression.py --suite safety_eval_suite.json --gate explainability_check.py
#   python run_safety_regression.py --json
# 退出码: 0 = 全绿, 1 = 存在失败用例, 2 = 参数/IO 错误
#
# 对应 ARCHITECTURE_REVIEW.md §3 P0-3：in-repo 回归 CI，10/10 才允许合入。

import sys
import os
import json
import argparse
import importlib.util


def load_module(path):
    spec = importlib.util.spec_from_file_location("gate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="PEG-A 安全回归 CI")
    ap.add_argument("--suite", default=os.path.join(here, "safety_eval_suite.json"))
    ap.add_argument("--gate", default=os.path.join(here, "explainability_check.py"))
    ap.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = ap.parse_args()

    try:
        suite = json.load(open(args.suite, "r", encoding="utf-8"))
        gate = load_module(args.gate)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR loading inputs: {e}", file=sys.stderr)
        sys.exit(2)

    results = []
    passed = 0
    for c in suite["cases"]:
        rpt = gate.check(c["input"])
        got = "allow" if rpt["passed"] else "reject"
        exp = c["expected"]["action"]
        ok = exp == got
        passed += 1 if ok else 0
        results.append({
            "id": c["id"],
            "category": c.get("category"),
            "expected": exp,
            "got": got,
            "ok": ok,
            "gate_tag": rpt["alerts"][0]["tag"] if rpt["alerts"] else None,
            "expected_severity": c["expected"].get("severity"),
        })

    total = len(results)
    failed = total - passed

    if args.json:
        out = {"total": total, "passed": passed, "failed": failed,
               "all_green": failed == 0, "results": results}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"{'RESULT':<7} {'CASE':<12} {'EXP':<7} {'GOT':<7} GATE_TAG")
        print("-" * 60)
        for r in results:
            print(f"{'PASS' if r['ok'] else 'FAIL':<7} {r['id']:<12} {r['expected']:<7} {r['got']:<7} {r['gate_tag'] or '-'}")
        print("-" * 60)
        print(f"SUMMARY: {passed}/{total} green" + ("" if failed == 0 else f"  *** {failed} FAILED ***"))

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
