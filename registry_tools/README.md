# registry_tools — PEP-A 登记册一致性工具集

> pip 可安装包：`fix_versions_refs.py` + `auto_register_versions.py`  
> 版本: v0.1.0 | 更新时间: 2026-08-04

---

## 5 分钟接入

### 安装

```bash
# 方式 A: wheel 安装（推荐）
pip install registry_tools-0.1.0-py3-none-any.whl

# 方式 B: 源码安装
pip install /path/to/registry_tools/
```

### 三个命令

```bash
# 1. 核对登记册一致性（dry-run）
registry-check --target /path/to/project

# 2. 自动修复 workspace_map.md
registry-check --target /path/to/project --fix

# 3. 自动补登未登记文件到 versions.md
registry-register --target /path/to/project --dry-run   # 预览
registry-register --target /path/to/project --apply     # 执行
```

### 编程模式

```python
from registry_tools import (
    parse_versions_md, list_disk_files, find_phantom_entries,
    find_unregistered, generate_entries, apply_registration,
)

# 自定义扫描流程
disk = list_disk_files(Path("/path/to/project"))
registered = parse_versions_md(versions_text)
unreg = find_unregistered(disk, registered)
entries = generate_entries(unreg, "2026-08-04")
```

---

## 检查维度

| 维度 | 说明 | 对应脚本 |
|---|---|---|
| D3.4 | 虚假条目（目录树登记但磁盘不存在） | `fix_versions_refs.py` |
| D3.5 | 遗漏文件（磁盘存在但目录树未登记） | `fix_versions_refs.py` |
| D4.2 | versions.md 登记文件实际存在性 | `fix_versions_refs.py` |
| D4 补登 | 自动补登未登记源文件 | `auto_register_versions.py` |

---

## 智能排除规则

`auto_register_versions.py` 自动排除以下文件：
- **运行时产物**：`logs/gate_*.jsonl`、`traces/<trace_id>/*`
- **构建产物**：`.egg-info`、`.dist-info`、`__pycache__`
- **VCS 内部**：`.git/` 下所有文件
- **自引用**：`versions.md`、`workspace_map.md`
- **非源文件**：图片、视频、二进制等

---

## 分发清单

```
发给其他团队的文件:
├── registry_tools-0.1.0-py3-none-any.whl   ← 主文件
└── README.md                                ← 本指南

他们只需要:
  pip install registry_tools-0.1.0-py3-none-any.whl
  registry-check --target /path/to/project
```

---

> 依赖: Python >= 3.8 | 零外部依赖 | 仅 stdlib