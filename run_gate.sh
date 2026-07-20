#!/usr/bin/env bash
# run_gate.sh — PEG-A 提示工程 CI 本地/流水线统一入口
# 用法（Windows git-bash / Linux CI 通用）：
#   PYTHON=/path/to/python3 bash meta_peg_agent/run_gate.sh
# 默认用 python3；可用 PYTHON 环境变量覆盖为托管 Python。
set -euo pipefail

PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "== [gate-1] 安全回归（须 10/10 才通过）=="
"$PY" run_safety_regression.py
echo

echo "== [gate-2] 结构门禁（提示词块必带 self_test + §13 锚）=="
"$PY" ci_lint.py
echo

echo "== [gate] 全部通过，可合入 =="
