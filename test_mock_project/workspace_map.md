# 工作区目录树

```
mock_project/
├── core.py                     # 核心模块
├── utils.py                    # 工具函数
├── README.md                   # 项目说明
│   └── old_module.py           # ❌ 虚假条目：已废弃但未清理
│   └── wip.md                  # 草案（实际存在）
│   └── deploy.sh               # 部署脚本（实际存在）
    └── test_new.py             # 测试文件（实际存在）
```

## 说明

- 本目录树包含 3 个虚假条目（ghost.py, deprecated/old_module.py, legacy_config.json）
- 遗漏了 5 个源文件（new_feature.py, config.json, drafts/wip.md, scripts/deploy.sh, tests/test_new.py）

<!-- 自动补登 (2026-08-04) -->
├── config.json  # 自动补登: config.json
├── data.csv  # 自动补登: data.csv
├── wip.md  # 自动补登: drafts/wip.md
├── logo.png  # 自动补登: logo.png
├── gate_20260804_001_PASS.jsonl  # 自动补登: logs/gate_20260804_001_PASS.jsonl
├── gate_20260804_002_REJECT.jsonl  # 自动补登: logs/gate_20260804_002_REJECT.jsonl
├── gate_20260804_003_PASS.jsonl  # 自动补登: logs/gate_20260804_003_PASS.jsonl
├── new_feature.py  # 自动补登: new_feature.py
├── deploy.sh  # 自动补登: scripts/deploy.sh
├── versions.md  # 自动补登: versions.md
├── workspace_map.md  # 自动补登: workspace_map.md