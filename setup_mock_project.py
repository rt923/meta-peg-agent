#!/usr/bin/env python3
"""
setup_mock_project.py
一键构造 mock 项目目录，用于本地测试 registry-check 和 registry-register。

构造特性：
  - 已登记源文件：3 个（core.py, utils.py, README.md）
  - 未登记源文件：5 个（new_feature.py, config.json, drafts/wip.md, 
    scripts/deploy.sh, tests/test_new.py）
  - 虚假条目（workspace_map 登记但磁盘不存在）：3 个（ghost.py, 
    deprecated/old_module.py, legacy_config.json）
  - 运行时产物：3 个（logs/gate_*.jsonl）— 应被排除
  - 非源文件：2 个（logo.png, data.csv）— 应被排除
  - 完整 versions.md（含工程化产物表 + 弃用记录表）

用法:
  python setup_mock_project.py
  cd test_mock_project
  registry-check --target . --dry-run
  registry-register --target . --dry-run
"""

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "test_mock_project"

# 清理旧目录
import shutil
if PROJECT.exists():
    shutil.rmtree(PROJECT)
PROJECT.mkdir()

# ═══════════════════════════════════════════════════════
# 1. 已登记的源文件（在 versions.md 中有记录）
# ═══════════════════════════════════════════════════════
REGISTERED_FILES = {
    "core.py": "# core.py — 核心模块\n\nclass Core:\n    def run(self):\n        return True\n",
    "utils.py": "# utils.py — 工具函数\n\ndef helper(x):\n    return x * 2\n",
    "README.md": "# Mock Project\n\n这是一个测试用的 mock 项目。\n",
}

# ═══════════════════════════════════════════════════════
# 2. 未登记的源文件（磁盘存在但 versions.md 中无记录）
# ═══════════════════════════════════════════════════════
UNREGISTERED_FILES = {
    "new_feature.py": "# new_feature.py — 新功能模块（未登记）\n\ndef new_func():\n    return 'new'\n",
    "config.json": '{\n  "debug": true,\n  "port": 8080\n}\n',
    "drafts/wip.md": "# WIP 草案\n\n还在写，未登记。\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "tests/test_new.py": "import unittest\n\nclass TestNew(unittest.TestCase):\n    def test_pass(self):\n        self.assertTrue(True)\n",
}

# ═══════════════════════════════════════════════════════
# 3. 运行时产物（应被 auto_register 和 fix 排除）
# ═══════════════════════════════════════════════════════
RUNTIME_ARTIFACTS = {
    "logs/gate_20260804_001_PASS.jsonl": '{"status":"pass","check":"D1"}\n',
    "logs/gate_20260804_002_REJECT.jsonl": '{"status":"reject","check":"D3"}\n',
    "logs/gate_20260804_003_PASS.jsonl": '{"status":"pass","check":"D4"}\n',
}

# ═══════════════════════════════════════════════════════
# 4. 非源文件（应被排除）
# ═══════════════════════════════════════════════════════
NON_SOURCE = {
    "logo.png": b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
    "data.csv": b"name,age\nAlice,30\nBob,25\n",
}

# ═══════════════════════════════════════════════════════
# 创建所有文件
# ═══════════════════════════════════════════════════════

def write_files(file_dict: dict, mode="text"):
    for path, content in file_dict.items():
        full = PROJECT / path
        full.parent.mkdir(parents=True, exist_ok=True)
        if mode == "text":
            full.write_text(content, encoding="utf-8")
        else:
            full.write_bytes(content)

print("📁 创建 mock 项目...")
write_files(REGISTERED_FILES)
print(f"   ✅ 已登记源文件: {len(REGISTERED_FILES)} 个")
write_files(UNREGISTERED_FILES)
print(f"   ➕ 未登记源文件: {len(UNREGISTERED_FILES)} 个")
write_files(RUNTIME_ARTIFACTS)
print(f"   🏃 运行时产物: {len(RUNTIME_ARTIFACTS)} 个")
write_files(NON_SOURCE, mode="binary")
print(f"   🚫 非源文件: {len(NON_SOURCE)} 个")

# ═══════════════════════════════════════════════════════
# 创建 workspace_map.md（含虚假条目）
# ═══════════════════════════════════════════════════════
WS_MAP = """# 工作区目录树

```
mock_project/
├── core.py                     # 核心模块
├── utils.py                    # 工具函数
├── README.md                   # 项目说明
├── ghost.py                    # ❌ 虚假条目：已删除但未从目录树移除
├── deprecated/
│   └── old_module.py           # ❌ 虚假条目：已废弃但未清理
├── legacy_config.json          # ❌ 虚假条目：配置文件已迁移
├── drafts/
│   └── wip.md                  # 草案（实际存在）
├── scripts/
│   └── deploy.sh               # 部署脚本（实际存在）
├── logs/                       # 运行时产物目录
└── tests/
    └── test_new.py             # 测试文件（实际存在）
```

## 说明

- 本目录树包含 3 个虚假条目（ghost.py, deprecated/old_module.py, legacy_config.json）
- 遗漏了 5 个源文件（new_feature.py, config.json, drafts/wip.md, scripts/deploy.sh, tests/test_new.py）
"""

(WS_PATH := PROJECT / "workspace_map.md").write_text(WS_MAP, encoding="utf-8")
print("   📋 workspace_map.md 已创建（含 3 个虚假条目）")

# ═══════════════════════════════════════════════════════
# 创建 versions.md（只登记了 3 个文件）
# ═══════════════════════════════════════════════════════
VERSIONS_MD = """# 语义化版本登记册

## PEG-A 自身提示词

| 版本 | 日期 | 变更 | 状态 |
|---|---|---|---|
| v0.1 | 2026-07-13 | 阶段 0 种子提示词 | archived |
| v0.2 | 2026-07-15 | 增加 guardrails | archived |

## 工程化产物

| 文件 | 版本 | 日期 | 备注 |
|---|---|---|---|
| core.py | v0.1 | 2026-07-13 | 核心模块 |
| utils.py | v0.1 | 2026-07-13 | 工具函数 |
| README.md | v0.1 | 2026-07-13 | 项目说明 |

## 弃用记录

| 项 | 弃用版本 | 替代 | 过渡期 |
|---|---|---|---|
| old_parser | v0.1 | new_parser | 阶段 2 |
"""

(VER_PATH := PROJECT / "versions.md").write_text(VERSIONS_MD, encoding="utf-8")
print("   📋 versions.md 已创建（仅登记 3 个文件）")

# ═══════════════════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════════════════
all_files = list(PROJECT.rglob("*"))
file_count = sum(1 for f in all_files if f.is_file())

print(f"\n{'='*50}")
print(f"✅ Mock 项目已就绪: {PROJECT}")
print(f"   总文件数: {file_count}")
print(f"   已登记: {len(REGISTERED_FILES)}")
print(f"   未登记: {len(UNREGISTERED_FILES)}")
print(f"   虚假条目: 3（ghost.py, deprecated/old_module.py, legacy_config.json）")
print(f"   运行时产物: {len(RUNTIME_ARTIFACTS)}（应被排除）")
print(f"   非源文件: {len(NON_SOURCE)}（应被排除）")
print(f"\n💡 测试命令:")
print(f"   cd {PROJECT}")
print(f"   registry-check --target . --dry-run")
print(f"   registry-register --target . --dry-run")
print(f"   registry-check --target . --fix")
print(f"   registry-register --target . --apply")