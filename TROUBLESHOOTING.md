# TROUBLESHOOTING.md — doc_alignment 常见踩坑与解法

> 基于 doc_alignment 增强块 v0.1（★固化，2026-07-22）
> 从 `doc_alignment_onboarding.md` 第五节独立提取，供快速查阅。

---

## 目录

1. [Windows 路径分隔符混用](#1-windows-路径分隔符混用)
2. [PowerShell 5.1 中文乱码](#2-powershell-51-中文乱码)
3. [JSON/Markdown 写入编码](#3-jsonmarkdown-写入编码)
4. [用完整路径正则匹配目录树](#4-用完整路径正则匹配目录树)
5. [修了一处忘扫同文件](#5-修了一处忘扫同文件)
6. [文档数字过时](#6-文档数字过时)
7. [登记文件低估范围](#7-登记文件低估范围)
8. [把运行时产物逐名登记](#8-把运行时产物逐名登记)

---

## 1. Windows 路径分隔符混用

### 症状

D5 通配模式中写 `logs/*.jsonl`（正斜杠，Unix 风格），PowerShell 脚本中又用 `\`（反斜杠，Windows 风格），跨平台工具（Git Bash、Node.js、Python）在不同终端下行为不一致，报路径找不到。

### 根因

- Windows 原生 API 接受 `\` 和 `/`，但 `cmd.exe` 某些命令只认 `\`
- PowerShell 的 `Get-ChildItem` 用 `\`，但 `Join-Path` 自动适配
- Git Bash / Node.js / Python 在 Windows 上也能处理 `/`，但不一定处理 `\` 转义

### 解法

```
通配模式（文档中）    → 统一用正斜杠 /
PowerShell 脚本路径    → 用 \ 或 Join-Path
Python 脚本路径        → 用 os.path.join() 或 pathlib
```

**正确示例**：

| 场景 | ✅ 正确 | ❌ 错误 |
|---|---|---|
| 通配模式文档 | `logs/gate_*.jsonl` | `logs\gate_*.jsonl` |
| PowerShell 命令 | `Get-ChildItem "$base\src"` | `Get-ChildItem "$base/src"`（cmd 中有时不认） |
| Python 代码 | `os.path.join("logs", "gate_*.jsonl")` | `"logs\\gate_*.jsonl"`（硬编码） |

### 预防

在 `workspace_map.md` 或通配模式文档中加一行注释：

```
> 通配模式统一使用正斜杠 /（Git / Node / 跨平台工具均兼容），
> PowerShell 脚本中 Get-ChildItem 路径用 \ 或 Join-Path。
```

---

## 2. PowerShell 5.1 中文乱码

### 症状

`.ps1` 脚本含中文注释或 `Write-Host` 输出中文（如 `"磁盘文件总数"`、`"全部测试通过"`），终端显示为乱码（如 `"妯℃嫙涓€娆″畬鏁?"`）。

### 根因

PowerShell 5.1 默认用系统 ANSI 代码页（中文 Windows 为 GBK / CP936）解码 `.ps1` 脚本文件。当脚本文件保存为 UTF-8 **无 BOM** 时，PS 5.1 无法识别编码，按 GBK 解码，导致中文变成乱码。

三层原因链：

```
UTF-8 无 BOM 文件
  → PS 5.1 按 GBK 解码字节流（第一层）
  → [Console]::OutputEncoding 默认 GBK（第二层）
  → 子进程 Python 继承 GBK 环境变量（第三层）
```

### 解法（三层修复，缺一不可）

| 层 | 修复 | 具体操作 |
|---|---|---|
| ① 文件编码 | UTF-8 with BOM | 保存 `.ps1` 时选「UTF-8 with BOM」编码 |
| ② 控制台代码页 | `chcp 65001` | 脚本第一行（非注释）加 `chcp 65001 > $null` |
| ③ 子进程环境 | `PYTHONIOENCODING=utf-8` | 调用 Python 前加 `$env:PYTHONIOENCODING='utf-8'` |

**完整修复模板**：

```powershell
# 脚本第一行（非注释）：
chcp 65001 > $null
$env:PYTHONIOENCODING='utf-8'

# 如果还需要 [Console] 输出：
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 你的脚本内容...
python your_script.py
```

### 验证

运行以下命令确认修复生效：

```powershell
chcp 65001 > $null
$env:PYTHONIOENCODING='utf-8'
python -c "print('测试中文输出')"
```

### 注意

- PS 7+ 已原生支持 `-AsPlainText` 和更好的 UTF-8 处理，可考虑升级
- 如果使用 `Write` 工具创建 `.ps1` 文件，工具链通常自动处理 BOM，但仍需 `chcp 65001`

---

## 3. JSON/Markdown 写入编码

### 症状

用 PowerShell `Out-File` 或 `Set-Content` 写入 JSON 文件后，外部工具（Python `json.load`、VS Code、Node.js）读出来是乱码或解析失败。

### 根因

PowerShell 5.1 的 `Out-File` 和 `Set-Content` **默认编码是 UTF-16 LE**（Unicode），不是 UTF-8。而大多数跨平台工具（Python、Node.js、Git）默认期望 UTF-8。

### 解法

**永远显式指定 `-Encoding UTF8`**：

```powershell
# ❌ 错误：默认 UTF-16 LE
$data | Out-File "config.json"
$data | Set-Content "config.json"

# ✅ 正确：显式 UTF-8
$data | Out-File "config.json" -Encoding UTF8
$data | Set-Content "config.json" -Encoding UTF8
```

**Python 侧**：

```python
# ✅ 正确
with open("config.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 跨平台一致性检查清单

| 工具 | 写文件命令 | 正确编码参数 |
|---|---|---|
| PowerShell 5.1 | `Out-File` / `Set-Content` | `-Encoding UTF8` |
| PowerShell 7+ | `Out-File` / `Set-Content` | `-Encoding UTF8`（默认仍是 UTF-16，需显式指定） |
| Python | `open(f, 'w')` | `encoding='utf-8'` |
| Node.js | `fs.writeFileSync` | 默认 UTF-8，无需额外参数 |
| Bash | `echo > file` | 依赖 locale，建议用 `printf` + 重定向 |

### 验证

```powershell
# 检查文件编码（PowerShell）
$bytes = [System.IO.File]::ReadAllBytes("config.json")
if ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
    Write-Host "❌ UTF-16 LE (PowerShell 默认)"
} elseif ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    Write-Host "UTF-8 with BOM"
} else {
    Write-Host "UTF-8 without BOM"
}
```

---

## 4. 用完整路径正则匹配目录树

### 症状

对 `workspace_map.md` 做完整性验证时，83 个磁盘文件报了 43 个 MISSING。

### 根因

目录树文件使用树形字符（`├──`、`│  `、`└──`）展示层级，正则匹配完整路径时这些字符会干扰匹配。

### 解法

**改用文件名匹配**（而非完整路径）：

```powershell
# ❌ 错误：用完整路径正则
$tree -match [regex]::Escape("logs\gate_20260714.jsonl")

# ✅ 正确：按文件名匹配
$tree -match [regex]::Escape("gate_20260714.jsonl")
```

---

## 5. 修了一处忘扫同文件

### 症状

用户对齐报告只指出了 `.md` 文档的问题（如 `step_count=6`），修复后以为完成。但同一个 `.py` 文件的 docstring 注释中也有同样的错误数值，被遗漏。

### 解法

修复任何偏差后，立即执行 **D2 同性质扫描**：

1. 确认修复点在哪个文件（如 `mock_helpers.md` L164）
2. 搜索关联文件中的同名字段/数值（如 `mock_helpers.py` 中搜索 `step_count`）
3. 搜索同目录下其他文件中的同类模式

---

## 6. 文档数字过时

### 症状

文档写「26 个断言」，但实际验证脚本跑出 33 个 `[✓ PASS]`。

### 根因

验证脚本增加测试用例后，文档中的数字没有同步更新。

### 解法

**每次重跑验证后，立即更新文档中的数字**（D1 数字漂移规则）。在验证脚本输出中直接提取计数：

```python
# 验证脚本末尾输出
print(f"assertions: {passed_count}")
# → 文档中的数字直接引用此值
```

---

## 7. 登记文件低估范围

### 症状

实际补了 40+ 个文件，登记条目（如 `capability_registry.md` 演进信号）却写「补 2 个文件」。

### 根因

登记时凭记忆写数字，而非实际盘点。

### 解法

**写登记条目前，运行一次 D3 目录树验证**，用实际磁盘文件数作为登记数字（D6 规则）。

---

## 8. 把运行时产物逐名登记

### 症状

目录树中出现具体的运行时文件名，如 `gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl`。

### 根因

每次运行产生的日志/缓存文件名不同，逐名登记会导致目录树永远跟不上磁盘变化。

### 解法

**改用通配模式**（D5 规则）：

| 文件类型 | ❌ 逐名登记 | ✅ 通配模式 |
|---|---|---|
| 闸门日志 | `gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl` | `gate_*.jsonl` |
| trace 产物 | `20260721_104251_0b52/artifacts/xxx.md` | `<trace_id>/artifacts/*` |
| 缓存 | `__pycache__/build.cpython-312.pyc` | 整目录排除 |

---

## 快速诊断流程图

```
发现偏差
  │
  ├─ 文件路径相关？ → 检查 §1 路径分隔符
  ├─ 中文乱码？     → 检查 §2 PS 5.1 编码
  ├─ JSON 读取出错？ → 检查 §3 写入编码
  ├─ 目录树 MISSING 很多？ → 检查 §4 正则匹配方式
  ├─ 同样错误在多个文件出现？ → 执行 §5 D2 同性质扫描
  ├─ 数字与运行结果不符？ → 执行 §6 数字漂移同步
  ├─ 登记范围严重低估？ → 执行 §7 D6 回溯更新
  └─ 目录树永远跟不上磁盘？ → 执行 §8 D5 通配覆盖
```

---

> 反馈新踩坑：提交 PR 到本文件，附症状 + 根因 + 解法 + 验证命令。