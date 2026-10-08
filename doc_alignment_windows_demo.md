# doc_alignment Windows 环境新项目接入演示

> 基于 [doc_alignment_onboarding.md](doc_alignment_onboarding.md) v0.1
> 模拟项目：`win-utils`（Windows 系统工具集，Python + PowerShell）
> 环境：Windows 11 + PowerShell 5.1 + Python 3.12

---

## 项目背景

`win-utils` 是一个 Windows 系统管理工具集，包含：

```
C:\Projects\win-utils\
├── src\
│   ├── __init__.py
│   ├── disk_cleaner.py        # 磁盘清理模块
│   └── service_manager.ps1    # 服务管理脚本（含中文注释）
├── tests\
│   └── test_disk_cleaner.py   # 磁盘清理测试
├── README.md                  # 项目文档（手写）
└── logs\                      # 运行时日志（自动生成）
```

项目已有一个手写 `README.md`，需要首次接入 doc_alignment 做文档与代码一致性检查。

---

## 阶段一：前置条件检查（预计 2 分钟）

### 检查 1：三份登记文件是否存在

```powershell
# 在项目根目录执行
$base = "C:\Projects\win-utils"
Test-Path "$base\versions.md"
Test-Path "$base\workspace_map.md"
Test-Path "$base\capability_registry.md"
```

**结果**：全部返回 `False` → 项目无 PEG-A 体系，按「无体系」路径走。

### 检查 2：磁盘文件清单

```powershell
chcp 65001 > $null
$base = "C:\Projects\win-utils"
$allFiles = Get-ChildItem -Path $base -Recurse -File `
  | Where-Object { $_.FullName -notmatch '\\(__pycache__|\.pytest_cache|\.git|node_modules)\\?' }
Write-Host "磁盘文件总数: $($allFiles.Count)"
$allFiles | ForEach-Object { $_.FullName.Replace($base, '').TrimStart('\') }
```

**输出**：
```
磁盘文件总数: 5
src\__init__.py
src\disk_cleaner.py
src\service_manager.ps1
tests\test_disk_cleaner.py
README.md
```

> ⚠️ 注意：`logs\` 目录存在但为空（无 `.jsonl` 文件），`Get-ChildItem -File` 不统计目录。

### 检查 3：编码验证（预防 Windows 特有坑）

```powershell
# 检查 .ps1 脚本编码（是否为 UTF-8 BOM）
$bytes = [System.IO.File]::ReadAllBytes("C:\Projects\win-utils\src\service_manager.ps1")
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    Write-Host "✅ UTF-8 with BOM — 安全"
} else {
    Write-Host "❌ 无 BOM — PS 5.1 会按 GBK 解码中文注释，立即修复"
}
```

**结果**：`❌ 无 BOM` → 后续对齐时需修复。

---

## 阶段二：首次对齐（预计 10 分钟）

### 步骤 1：D3 目录树验证

```
磁盘文件: 5
README 声称的目录树:
  win-utils/
  ├── src/
  │   ├── disk_cleaner.py
  │   └── service_manager.ps1
  ├── tests/
  │   └── test_disk_cleaner.py
  ├── README.md
  └── logs/

README 声称 4 个文件，磁盘 5 个文件。
→ 🔴 真偏差: src\__init__.py 在磁盘上存在但 README 目录树未列出
→ 🟡 轻微: logs/ 是目录不是文件，README 列了但无文件内容
```

### 步骤 2：D1 逐项对比 `disk_cleaner.py` ↔ `README.md`

**代码实际签名**：

```python
def clean_temp_files(paths=None, dry_run=False):
    """清理临时文件。返回 (deleted_count, freed_bytes)。"""
    ...

def get_disk_usage(path="C:\\"):
    """获取磁盘使用率。返回 (used_gb, total_gb, percent)。"""
    ...

def schedule_cleanup(interval_hours=24):
    """注册定时清理任务。返回任务名称。"""
    ...
```

**README 声称的 API**：

| 函数 | README 签名 | 代码实际签名 |
|---|---|---|
| `clean_temp_files` | `clean_temp_files(paths)` | `clean_temp_files(paths=None, dry_run=False)` |
| `get_disk_usage` | `get_disk_usage()` | `get_disk_usage(path="C:\\")` |
| `schedule_cleanup` | `schedule_cleanup(interval)` | `schedule_cleanup(interval_hours=24)` |

**D1 逐项对比**：

| 维度 | 结果 |
|---|---|
| 函数签名 | 🔴 `clean_temp_files` 缺 `dry_run` 参数；`schedule_cleanup` 参数名 `interval` ≠ `interval_hours` |
| 场景覆盖 | 🟡 `get_disk_usage` 的 `path` 参数未在 README 中说明 |
| 字段名 | ✅ 无冲突 |
| 产出物结构 | 🔴 `src\__init__.py` 缺失 |
| 行为描述 | ✅ 返回值描述一致 |

### 步骤 3：偏差清单

```
🔴 真偏差（须修）:
  1. clean_temp_files(): README 缺 dry_run 参数
  2. schedule_cleanup(): README 参数名 interval → 应为 interval_hours
  3. src\__init__.py 在磁盘存在但 README 目录树未列出

🟡 轻微不一致（标注不改）:
  1. get_disk_usage(): README 未说明 path 参数（但默认值兼容）
  2. service_manager.ps1 无 UTF-8 BOM（编码问题，非文档问题）

🔵 数字漂移: 无
```

### 步骤 4：D2 同性质扫描 + 修复

修复偏差 1 后，扫描 README 中是否还有其他函数漏了参数：

```powershell
# 搜索 README 中所有函数签名
Select-String -Path "C:\Projects\win-utils\README.md" -Pattern "def |### " -Encoding UTF8
```

**结果**：无其他遗漏 → D2 扫描通过。

### 步骤 5：修复编码问题（Windows 特有）

```powershell
# 修复 service_manager.ps1 编码（无 BOM → UTF-8 with BOM）
$content = Get-Content "C:\Projects\win-utils\src\service_manager.ps1" -Raw -Encoding UTF8
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText(
    "C:\Projects\win-utils\src\service_manager.ps1",
    $content,
    $utf8Bom
)
Write-Host "✅ service_manager.ps1 已转为 UTF-8 with BOM"
```

### 步骤 6：D4 补登记

按「无 PEG-A 体系」路径，创建 `versions.md` 和 `workspace_map.md`：

```powershell
# 创建 versions.md
@"
# 语义化版本登记册

| 文件 | 版本 | 日期 | 变更 |
|---|---|---|---|
| README.md | v0.1 | 2026-07-22 | 首次 doc_alignment 对齐：修复 3 处真偏差 |
| src/disk_cleaner.py | v0.1 | 2026-07-22 | 初始版本 |
"@ | Out-File "C:\Projects\win-utils\versions.md" -Encoding UTF8

# 创建 workspace_map.md
@"
# 工作区映射

win-utils/
├── src/
│   ├── __init__.py
│   ├── disk_cleaner.py
│   └── service_manager.ps1      # UTF-8 BOM 编码
├── tests/
│   └── test_disk_cleaner.py
├── logs/                        # 运行时日志（gate_*.jsonl）
├── README.md
└── versions.md
"@ | Out-File "C:\Projects\win-utils\workspace_map.md" -Encoding UTF8
```

---

## 关键检查点清单

以下是 Windows 环境下新项目接入 doc_alignment 的完整检查清单，可逐项打勾：

### 前置检查

- [ ] 三份登记文件检查（versions.md / workspace_map.md / capability_registry.md）
- [ ] 磁盘文件递归列出（排除 `__pycache__`、`.pytest_cache`、`.git`、`node_modules`）
- [ ] `.ps1` 脚本 UTF-8 BOM 编码验证
- [ ] 所有 `.py`/`.md`/`.json` 文件编码确认（UTF-8）
- [ ] `chcp 65001` 代码页切换确认（PS 5.1 需要在脚本头部）

### 首次对齐

- [ ] D3: 磁盘文件数 vs README 目录树文件数对比
- [ ] D1: 每个公开函数的签名对比（参数名、个数、默认值、返回类型）
- [ ] D1: 字段名一致性（注意 `task_summary` ≠ `task` 类陷阱）
- [ ] D1: 产出物结构对比（目录树、文件名模板、注释中的数值）
- [ ] D2: 修复每个偏差后扫描同文件及关联文件
- [ ] 编码修复：`.ps1` 无 BOM → UTF-8 with BOM（三层修复）
- [ ] D4: 创建 `versions.md`（登记本次对齐修复）
- [ ] D4: 创建 `workspace_map.md`（写入实际目录树，通配覆盖运行时产物）

### 持续对齐

- [ ] 新增文件 → `workspace_map.md` 目录树补登
- [ ] 修改函数签名 → 文档签名同步更新
- [ ] 新增 scenario/branch → 文档增加对应描述
- [ ] 重跑验证脚本 → 更新文档中的断言数/测试数
- [ ] 版本升级 → `versions.md` 新增一行，演进信号 +1

### Windows 特有

- [ ] PS 5.1 脚本第一行：`chcp 65001 > $null`
- [ ] 子进程 Python：`$env:PYTHONIOENCODING='utf-8'`
- [ ] 所有 `Out-File` / `Set-Content`：`-Encoding UTF8`
- [ ] 通配模式用 `/`，PS 命令用 `\` 或 `Join-Path`
- [ ] `Get-ChildItem` 排除正则用 `\\`（Windows 转义）

---

## 本次演示产出

| 文件 | 路径 | 用途 |
|---|---|---|
| 原始 README.md | `C:\Projects\win-utils\README.md` | 修复前的文档（含 3 真偏差） |
| 修复后 README.md | `C:\Projects\win-utils\README.md` | 已修复：补 dry_run、改名 interval_hours、补 __init__.py |
| versions.md | `C:\Projects\win-utils\versions.md` | 新建：登记首次对齐 |
| workspace_map.md | `C:\Projects\win-utils\workspace_map.md` | 新建：磁盘实际目录树（logs/ 通配注释） |

---

> 反馈：本演示中发现的实际流程与接入指南不一致之处，请触发 D1 真偏差流程提交修正。