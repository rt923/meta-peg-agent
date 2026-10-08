# TROUBLESHOOTING 踩坑速查表

> 可直接复制到 Confluence / Notion / 飞书文档。基于 doc_alignment 增强块 v0.1（★固化）。
> 复制时选中下方表格区域，粘贴到目标平台即可保留表格格式。

---

## 8 条踩坑速查表

| # | 踩坑 | 症状 | 根因 | 解法 | 关联规则 |
|---|---|---|---|---|---|
| 1 | Windows 路径分隔符混用 | 通配写 `logs/*.jsonl`（`/`），PS 脚本用 `\`，跨平台工具报路径找不到 | Windows 原生 API 接受 `/` 和 `\`，但 `cmd.exe` 某些命令只认 `\` | 通配模式统一用 `/`；PS 脚本内用 `\` 或 `Join-Path`；Python 用 `os.path.join()` | D5 |
| 2 | PowerShell 5.1 中文乱码 | `.ps1` 脚本中 `Write-Host "磁盘文件总数"` 显示为 `"妯℃嫙涓€娆″畬鏁?"` | PS 5.1 无 BOM 时按 GBK 解码 UTF-8 文件（三层：文件解码 → 控制台输出 → 子进程环境） | 三层修复：① 保存为 UTF-8 with BOM；② `chcp 65001`；③ `$env:PYTHONIOENCODING='utf-8'` | — |
| 3 | JSON/Markdown 写入编码 | `Out-File` 写入 JSON 后 Python `json.load` 解析失败或乱码 | PS 5.1 的 `Out-File`/`Set-Content` 默认编码为 UTF-16 LE | 显式指定 `-Encoding UTF8`；Python 侧用 `encoding='utf-8'` | — |
| 4 | 用完整路径正则匹配目录树 | 83 个磁盘文件报了 43 个 MISSING | 树形字符（`├──`、`│  `）干扰路径正则匹配 | 改用文件名匹配，不用完整路径 | D3 |
| 5 | 修了一处忘扫同文件 | 用户只报告 `.md` 的问题，修复后 `.py` 的同名错误被遗漏 | 修复后未执行 D2 同性质扫描 | 修复后立即搜索同文件及关联文件中的同名字段/数值 | D2 |
| 6 | 文档数字过时 | 文档写「26 个断言」，实际验证脚本跑出 33 个 `[✓ PASS]` | 验证脚本增加测试用例后文档未同步 | 每次重跑验证后立即更新文档数字；可在验证脚本输出中直接提取计数 | D1 |
| 7 | 登记文件低估范围 | 实际补了 40+ 个文件，登记条目却写「补 2 个文件」 | 登记时凭记忆写数字，而非实际盘点 | 写登记条目前运行 D3 目录树验证，用实际磁盘文件数 | D6 |
| 8 | 把运行时产物逐名登记 | 目录树出现 `gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl` | 每次运行产生的文件名不同，逐名登记导致目录树永远跟不上磁盘 | 用通配模式：`gate_*.jsonl`、`<trace_id>/artifacts/*`、整目录排除缓存 | D5 |

---

## 快速诊断流程

```
发现偏差
  │
  ├─ 文件路径相关？    → §1 Windows 路径分隔符
  ├─ 中文乱码？        → §2 PS 5.1 编码三层修复
  ├─ JSON 读取出错？   → §3 显式指定 -Encoding UTF8
  ├─ 目录树 MISSING？  → §4 改用文件名匹配
  ├─ 同类错误遗漏？    → §5 D2 同性质扫描
  ├─ 数字不符？        → §6 同步文档数字
  ├─ 登记范围低估？    → §7 D3 验证后再写
  └─ 目录树跟不上？    → §8 D5 通配覆盖
```

---

## 跨平台编码一致性检查清单

| 工具 | 写文件命令 | 正确编码参数 |
|---|---|---|
| PowerShell 5.1 | `Out-File` / `Set-Content` | `-Encoding UTF8` |
| PowerShell 7+ | `Out-File` / `Set-Content` | `-Encoding UTF8`（默认 UTF-16，需显式指定） |
| Python | `open(f, 'w')` | `encoding='utf-8'` |
| Node.js | `fs.writeFileSync` | 默认 UTF-8，无需额外参数 |
| Bash | `echo > file` | 依赖 locale，建议用 `printf` + 重定向 |

---

## Windows 路径分隔符正确/错误对照

| 场景 | ✅ 正确 | ❌ 错误 |
|---|---|---|
| 通配模式文档 | `logs/gate_*.jsonl` | `logs\gate_*.jsonl` |
| PowerShell 命令 | `Get-ChildItem "$base\src"` | `Get-ChildItem "$base/src"`（cmd 中有时不认） |
| Python 代码 | `os.path.join("logs", "gate_*.jsonl")` | `"logs\\gate_*.jsonl"`（硬编码） |

---

> 反馈新踩坑：附症状 + 根因 + 解法 + 验证命令，追加到本表。