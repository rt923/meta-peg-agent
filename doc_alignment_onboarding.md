# doc_alignment 新项目快速接入指南

> 基于 doc_alignment 增强块 v0.1（★固化，2026-07-22）
> 目标读者：在新项目中首次引入文档对齐检查的智能体/开发者
> 预计耗时：首次接入 ~15 分钟，后续每次对齐 ~5 分钟

---

## 一、前置条件检查（2 分钟）

在开始前确认以下文件存在：

| 文件 | 用途 | 缺失时怎么办 |
|---|---|---|
| `versions.md` | 版本登记册 | 创建：含表头「版本/日期/变更/状态」 |
| `workspace_map.md` | 目录树映射 | 创建：`ls -R` 输出做骨架 |
| `capability_registry.md` | 能力登记册 | 如有智能体体系则创建，否则可跳过 |

> 如果以上文件都不存在，跳到第 3 步先跑一次对齐，再倒推创建登记文件。

---

## 二、首次对齐——最小可行流程（10 分钟）

### 步骤 1：跑一次完整的目录树验证（D3）

```powershell
# Windows PowerShell（D3 步骤 1：递归列出磁盘全部文件）
# 注意：若脚本含中文，需保存为 UTF-8 with BOM，并在脚本头部加 chcp 65001
$base = "你的项目根目录"
$allFiles = Get-ChildItem -Path $base -Recurse -File `
  | Where-Object { $_.FullName -notmatch '\\(__pycache__|\.pytest_cache|\.git|node_modules)\\?' }
Write-Host "磁盘文件总数: $($allFiles.Count)"
```

把这个数字和你的 `workspace_map.md`（或 README 中的目录树）对比。

### 步骤 2：选一对核心文件做逐项对比（D1）

推荐从「代码文件 + 对应文档」开始，例如：

```
你的模块.py  ↔  你的模块.md（或 README 中的 API 说明）
```

逐项对比五项：

| 维度 | 检查什么 | 通过标准 |
|---|---|---|
| 函数签名 | 参数名、个数、默认值、返回类型 | 文档与代码一致 |
| 场景覆盖 | 每个分支/用例在文档中是否有描述 | 无遗漏 |
| 字段名 | 代码读写的字段名 | 与文档一致（注意大小写） |
| 产出物结构 | 目录树、文件名模板 | 与代码实际产出一致 |
| 行为描述 | 代码实际行为 | 与文档描述一一对应 |

### 步骤 3：输出偏差清单

按 D1 三级分类：

```
真偏差（须修）：
  - xxx

轻微不一致（标注不改）：
  - xxx

数字漂移（须同步）：
  - xxx
```

### 步骤 4：修复 + 同性质扫描（D2）

修复真偏差和数字漂移后，**立刻扫描同文件及关联文件**中的同类偏差。

> 例：修复了 `step_count=6→5` 后，检查同一个 `.py` 文件的 docstring 和 `.md` 文档是否也有同样的错误数值。

### 步骤 5：补登记 + 三向对齐（D4）

每修完一个偏差，确认三份登记文件同步：

| 登记文件 | 写什么 |
|---|---|
| `versions.md` | 新增一行：`| 你的文件 | v0.1 | 日期 | 变更摘要 |` |
| `workspace_map.md` | 目录树中补上新增/修改的文件 |
| `capability_registry.md`（可选） | 演进信号日志中追加一条修复记录 |

---

## 三、持续对齐——日常检查清单（每次 3 分钟）

在以下时机触发对齐检查：

| 触发事件 | 执行动作 |
|---|---|
| 新增文件 | 确认 `workspace_map.md` 目录树已补登 |
| 修改函数签名 | 检查文档中的签名是否同步更新 |
| 新增 scenario/分支 | 检查文档中是否增加了对应描述 |
| 重跑验证脚本 | 更新文档中的断言数/测试数 |
| 版本升级 | `versions.md` 新增一行，`capability_registry.md` 追加演进信号 |

---

## 四、通配模式速查（D5）

以下文件**不要逐名登记**到目录树，用通配覆盖：

| 类型 | 通配模式 | 示例 |
|---|---|---|
| 自动日志 | `logs/gate_*.jsonl` | `gate_20260714_PASS_xxx.jsonl` |
| 运行时产物 | `traces/<id>/artifacts/*` | `20260721_xxx/artifacts/*.md` |
| 缓存 | 整目录排除 | `__pycache__/` `.pytest_cache/` `node_modules/` |
| IDE 配置 | 目录级注释 | `.obsidian/` `.vscode/` |

> 通配模式统一使用正斜杠 `/`（Git / Node / 跨平台工具均兼容），PowerShell 脚本中 `Get-ChildItem` 路径用 `\` 或 `Join-Path`。

---

## 五、常见踩坑

| 坑 | 症状 | 解法 |
|---|---|---|
| 用完整路径正则匹配目录树 | 83 个文件报 43 个 MISSING | 改用**文件名**匹配（D3 步骤 2） |
| 修了一处忘扫同文件 | 用户对齐报告只指了 .md 的问题，.py 的同名错误被遗漏 | 修复后立即执行 D2 同性质扫描 |
| 文档数字过时 | 文档写「26 个断言」但实际跑出 33 个 | 每次重跑验证后同步更新数字（D1 数字漂移） |
| 登记文件低估范围 | 补了 40+ 文件，登记条目却写「补 2 个文件」 | 回溯更新时用实际数字（D6） |
| 把运行时产物逐名登记 | 目录树里出现 `gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl` | 改回 `gate_*.jsonl` 通配（D5） |
| Windows 路径分隔符混用 | D5 通配写 `logs/*.jsonl`，PowerShell 示例用 `\`，跨平台工具报路径找不到 | 统一用正斜杠 `/` 写通配模式（Git/Node/跨平台工具均兼容）；PowerShell 脚本内用 `\` 或 `Join-Path` |
| PowerShell 5.1 中文乱码 | `.ps1` 脚本含中文注释（如"磁盘文件总数"），输出显示为乱码（GBK 解码 UTF-8） | 三层修复：① `.ps1` 保存为 UTF-8 with BOM；② 脚本头部加 `chcp 65001`；③ 子进程加 `$env:PYTHONIOENCODING='utf-8'` |
| JSON/Markdown 写入编码 | `Out-File` 默认 UTF-16 LE，导致 JSON 被外部工具读成乱码 | 显式指定 `-Encoding UTF8`：`Out-File -Encoding UTF8`；Python 用 `open(f, 'w', encoding='utf-8')` |

---

## 六、与现有 PEG-A 体系的集成

如果你的项目**已有** PEG-A 体系（capability_registry.md / versions.md / workspace_map.md 三件套）：

1. 在 `capability_registry.md` 可选增强块清单中追加：
   ```
   | `doc_alignment` | 文档对齐检查（D1–D6） | core |
   ```
2. 在 `versions.md` 中追加：
   ```
   | doc_alignment.json | v0.1 | 日期 | 基础设施新增：doc_alignment JSON 导出 |
   ```
3. 在 `workspace_map.md` 中追加 `doc_alignment.json` 到目录树

如果你的项目**没有** PEG-A 体系：

1. 从本指南的步骤 1–5 开始，先跑一次对齐
2. 对齐过程中自然产生 `versions.md` 和 `workspace_map.md` 的雏形
3. 后续慢慢补全 `capability_registry.md`

---

## 七、参考文件

| 文件 | 格式 | 用途 |
|---|---|---|
| [doc_alignment.prompt.md](prompts/apps/core/services/doc_alignment.prompt.md) | Markdown | 完整增强块提示词（含 §12/§13 安全锚） |
| [doc_alignment.json](doc_alignment.json) | JSON | 结构化导出，供外部工具集成 |
| [doc_alignment_quickref.md](doc_alignment_quickref.md) | Markdown | 六条规则速查 + self_test 状态表 |
| [capability_registry.md](capability_registry.md) | Markdown | 能力登记册（L18/L37/L45/L46 含 doc_alignment 条目） |

---

> 反馈：发现本指南与实际操作不符的地方，请触发 D1 真偏差流程——提交偏差报告，由 doc_alignment 增强块处理。