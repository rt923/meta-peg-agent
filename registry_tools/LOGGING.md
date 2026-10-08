# registry_tools 日志系统使用指南

## 概述

`registry_tools` 的三个 CLI 命令（`registry-check`、`registry-fix`、`registry-register`）均已内置详细的 `logger.info` 日志系统。日志输出到 **stderr**，不影响 stdout 的正常输出，方便在 CI/CD 管道中分离日志与业务输出。

## 日志格式

所有日志遵循统一格式：

```
HH:MM:SS [<logger_name>] <LEVEL>: <message>
```

| 字段 | 说明 |
|---|---|
| `HH:MM:SS` | 时间戳（精确到秒） |
| `logger_name` | 日志来源标识 |
| `LEVEL` | 日志级别（INFO / ERROR / DEBUG） |
| `message` | 日志内容 |

### Logger 名称

| CLI 命令 | Logger 名称 |
|---|---|
| `registry-check` / `registry-fix` | `registry_tools.check` |
| `registry-register` | `registry_tools.register` |
| 独立脚本 `fix_versions_refs.py` | `fix_versions_refs` |
| 独立脚本 `auto_register_versions.py` | `auto_register_versions` |

## 日志级别

### INFO（默认）

启动时自动启用，记录关键执行路径和决策点，包括：

- 启动参数（目标目录、模式、文件存在性）
- 文件读取统计（字节数）
- 解析结果（条目数量）
- 磁盘扫描结果（源文件数量、跳过数量）
- 问题检测详情（每个虚假条目/遗漏文件/未登记文件的路径和原因）
- 修复/补登操作详情（条目数、写入字节数）

### DEBUG

需手动开启，额外输出每个解析条目的详细信息：

```python
logging.basicConfig(level=logging.DEBUG)
```

## 使用方式

### 方式一：CLI 直接运行（默认 INFO 级别）

日志自动输出到 stderr，无需任何额外配置：

```bash
# pip 安装后
registry-check --target /path/to/project --dry-run
registry-register --target /path/to/project --dry-run

# 或模块方式
python -m registry_tools.fix_versions_refs --target /path/to/project --dry-run
python -m registry_tools.auto_register_versions --target /path/to/project --dry-run
```

### 方式二：分离 stdout 和 stderr

```bash
# 仅看业务输出（stdout）
registry-check --target ./project --dry-run 2>/dev/null

# 仅看日志（stderr）
registry-check --target ./project --dry-run 1>/dev/null

# 分别保存
registry-check --target ./project --dry-run >output.txt 2>debug.log
```

### 方式三：编程模式自定义日志级别

```python
import logging
from registry_tools.fix_versions_refs import main as check_main
from registry_tools.auto_register_versions import main as register_main

# 开启 DEBUG 级别日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

# 仅对特定模块调整日志级别
logging.getLogger("registry_tools.check").setLevel(logging.DEBUG)
logging.getLogger("registry_tools.register").setLevel(logging.WARNING)
```

### 方式四：输出到文件

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("registry_tools.log", encoding="utf-8"),
        logging.StreamHandler(),  # 同时输出到控制台
    ],
)
```

## 日志覆盖的关键执行点

### registry-check / registry-fix

```
17:57:42 [registry_tools.check] INFO: ============================================================
17:57:42 [registry_tools.check] INFO: registry-check 启动
17:57:42 [registry_tools.check] INFO:   目标目录: /path/to/project
17:57:42 [registry_tools.check] INFO:   workspace_map.md: /path/workspace_map.md (存在=True)
17:57:42 [registry_tools.check] INFO:   versions.md: /path/versions.md (存在=True)
17:57:42 [registry_tools.check] INFO:   模式: dry-run
                          ↓
17:57:42 [registry_tools.check] INFO: 读取 workspace_map.md (1057 字节)
17:57:42 [registry_tools.check] INFO: 读取 versions.md (592 字节)
                          ↓
17:57:42 [registry_tools.check] INFO: 解析 workspace_map: 获得 11 个目录树条目
17:57:42 [registry_tools.check] INFO: 解析 versions.md「工程化产物」表: 获得 3 个条目
                          ↓
17:57:42 [registry_tools.check] INFO: 扫描磁盘文件: 共发现 15 个源文件
                          ↓
17:57:42 [registry_tools.check] INFO: 检测虚假条目 (3.4): 共 7 个
17:57:42 [registry_tools.check] INFO:   虚假条目 L8: ghost.py (原始行: ├── ghost.py ...)
17:57:42 [registry_tools.check] INFO:   虚假条目 L9: deprecated (原始行: ├── deprecated/)
                          ↓
17:57:42 [registry_tools.check] INFO: 检测遗漏文件 (3.5): 共 11 个
17:57:42 [registry_tools.check] INFO:   遗漏文件: config.json
17:57:42 [registry_tools.check] INFO:   遗漏文件: new_feature.py
                          ↓
17:57:42 [registry_tools.check] INFO: versions.md 引用检查: 已登记条目字典 3 项
17:57:42 [registry_tools.check] INFO:   磁盘文件未登记: config.json
17:57:42 [registry_tools.check] INFO: versions.md 引用检查结果: 登记但不存在=0, 磁盘存在但未登记=12
                          ↓
17:57:42 [registry_tools.check] INFO: >>> dry-run 模式，不修改文件 <<<
17:57:42 [registry_tools.check] INFO: registry-check 完成
```

### registry-register

```
17:57:50 [registry_tools.register] INFO: ============================================================
17:57:50 [registry_tools.register] INFO: registry-register 启动
17:57:50 [registry_tools.register] INFO:   目标目录: /path/to/project
17:57:50 [registry_tools.register] INFO:   模式: apply
17:57:50 [registry_tools.register] INFO:   补登日期: 2026-08-04
                          ↓
17:57:50 [registry_tools.register] INFO: list_disk_files: 收集 15 个源文件, 跳过 0 个非源文件
17:57:50 [registry_tools.register] INFO: 磁盘扫描完成: 15 个源文件
                          ↓
17:57:50 [registry_tools.register] INFO: 解析 versions.md: 获得 3 个已登记条目
                          ↓
17:57:50 [registry_tools.register] INFO: find_unregistered: 磁盘=15, 已登记=3
17:57:50 [registry_tools.register] INFO:   排除(自身): 2 个 — ['versions.md', 'workspace_map.md']
17:57:50 [registry_tools.register] INFO:   排除(运行时产物): 3 个
17:57:50 [registry_tools.register] INFO:   排除(非源文件): 2 个 — ['data.csv', 'logo.png']
17:57:50 [registry_tools.register] INFO:   已登记(跳过): 3 个
17:57:50 [registry_tools.register] INFO:   待补登: 5 个 — ['config.json', 'drafts/wip.md', ...]
                          ↓
17:57:50 [registry_tools.register] INFO: >>> 执行补登模式 <<<
17:57:50 [registry_tools.register] INFO: generate_entries: config.json → 源文件
17:57:50 [registry_tools.register] INFO: generate_entries: 共生成 5 条表格行
                          ↓
17:57:50 [registry_tools.register] INFO: apply_registration: 找到「工程化产物」表头 (L12)
17:57:50 [registry_tools.register] INFO: apply_registration: 找到表结束位置 (L18), 将插入 5 条新条目
17:57:50 [registry_tools.register] INFO: apply_registration: 新内容共 28 行 (原 22 行 + 5 条新条目 + 空行)
17:57:50 [registry_tools.register] INFO: 已写入 versions.md (692 字节)
                          ↓
17:57:50 [registry_tools.register] INFO: registry-register 完成
```

## 排查指南

### 场景一：registry-check 报 "workspace_map.md 不存在"

查看日志确认实际路径：
```
ERROR registry_tools.check: workspace_map.md 不存在: /actual/path/workspace_map.md
```
→ 检查 `--target` 参数是否正确，或 CWD 是否在项目目录内。

### 场景二：预期外的文件被标记为"未登记"

查看 `find_unregistered` 的分类日志：
```
INFO  排除(自身): 2 个 — ['versions.md', 'workspace_map.md']
INFO  排除(运行时产物): 3 个
INFO  排除(非源文件): 2 个 — ['data.csv', 'logo.png']
INFO  已登记(跳过): 3 个
INFO  待补登: 5 个 — ['config.json', ...]
```
→ 如果某文件被错误分类，检查 `EXCLUDE_RUNTIME_PATTERNS` 或 `SOURCE_EXTENSIONS` 配置。

### 场景三：registry-register 补登后文件未出现在表格中

查看 `apply_registration` 日志：
```
INFO  apply_registration: 找到「工程化产物」表头 (L12)
INFO  apply_registration: 找到表结束位置 (L18), 将插入 5 条新条目
INFO  apply_registration: 新内容共 28 行
```
→ 如果找不到表头或结束位置，检查 `versions.md` 格式是否正确。

### 场景四：虚假条目/遗漏文件数量异常

查看每个条目的详细信息：
```
INFO  虚假条目 L8: ghost.py (原始行: ├── ghost.py  # ...)
INFO  遗漏文件: config.json
```
→ 逐条确认每个被标记的条目是否合理。

### 场景五：CI/CD 中调试失败原因

在 CI 中开启 DEBUG 日志，获取每个解析步骤的详细信息：

```yaml
# GitHub Actions 示例
- name: Run registry-check
  run: |
    python -c "
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
    from registry_tools.fix_versions_refs import main
    import sys
    sys.argv = ['registry-check', '--target', '.', '--dry-run']
    main()
    "
```

## 日志级别快速参考

| 级别 | 用途 | 何时使用 |
|---|---|---|
| `ERROR` | 致命错误（文件不存在等） | 始终输出 |
| `INFO` | 关键执行路径和决策 | 默认启用，日常排查 |
| `DEBUG` | 每个条目的解析细节 | 深度排查时手动开启 |

## 与 print 输出的关系

| 输出目标 | 用途 | 示例 |
|---|---|---|
| **stdout** (print) | 用户可读的业务摘要 | `🔍 扫描目标: /path`, `✅ 扫描完成` |
| **stderr** (logger) | 可机器解析的详细日志 | `17:57:42 [registry_tools.check] INFO: 检测虚假条目 (3.4): 共 7 个` |

两者互不干扰，可以独立重定向。