#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ci_lint.py — PEG-A 提示工程结构门禁（CI 第二道闸）

职责：确保任何「新增/修改的提示词块」都携带元认知安全基线的不可省略项：
  1. 必带 `self_test`（§10 可验证闭环的硬要求）
  2. 必含 §13 安全锚（`§13` 或 `安全原则` 字样，杜绝遗漏最底层原则）

设计边界：
  - 本 lint 只查「结构不变量」，不查语义。语义级安全由 explainability_check.py + run_safety_regression.py 负责。
  - phase0 主文档 / bootstrap / stage1 为核心种子，已稳定，不纳入本 lint 扫描（避免对已固化文件重复告警）。
  - 扫描对象：`prompts/**/*.prompt.md`（模块增强块）与 `drafts/**/*.md`（范例草案）。

退出码：全部通过=0；任一文件缺项=1（CI 即失败、阻断合入）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def scan_dir(rel):
    root = os.path.join(HERE, rel)
    if not os.path.isdir(root):
        return []
    out = []
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".prompt.md") or f.endswith(".md"):
                out.append(os.path.join(base, f))
    return sorted(out)


def lint_file(path):
    text = open(path, encoding="utf-8").read()
    low = text.lower()
    problems = []
    if "self_test" not in low:
        problems.append("缺少 self_test 必带项")
    if "§13" not in text and "安全原则" not in text:
        problems.append("缺少 §13 安全锚")
    return problems


def main():
    targets = scan_dir("prompts") + scan_dir("drafts")
    if not targets:
        print("[ci_lint] 无扫描目标（prompts/ 与 drafts/ 均空）")
        return 0
    failed = 0
    print("[ci_lint] 扫描 %d 个提示词块" % len(targets))
    for p in targets:
        rel = os.path.relpath(p, HERE)
        probs = lint_file(p)
        if probs:
            failed += 1
            print("  FAIL %s -> %s" % (rel, "; ".join(probs)))
        else:
            print("  PASS %s" % rel)
    if failed:
        print("--- [ci_lint] 失败 %d 个文件（CI 须阻断）---" % failed)
        return 1
    print("--- [ci_lint] 全部通过 ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
