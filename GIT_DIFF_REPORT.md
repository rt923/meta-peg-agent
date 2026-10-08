# Git Diff 报告 — 登记册一致性修复

> 生成时间: 2026-08-04
> 分支: `(detached)`
> 涉及文件: 4 个（2 修改 + 2 新增）

---

## 变更摘要

| 文件 | 状态 | 变更类型 | 行数变化 |
|---|---|---|---|
| `fix_versions_refs.py` | 新增 (untracked) | 扫描器修复 | +292 行 |
| `auto_register_versions.py` | 新增 (untracked) | 自动补登工具 | +260 行 |
| `versions.md` | 修改 (staged+unstaged) | 补登 68 个文件 | +100/-1 行 |
| `workspace_map.md` | 修改 (unstaged) | 目录树对齐 + 补登 | +107/-2 行 |

---

## 1. `fix_versions_refs.py` — 扫描器三个 Bug 修复

### 修复内容

**Bug A: `parse_versions_md()` 解析了错误的表**
- 原因：原解析器遍历所有表格行，将「PEG-A 自身提示词」表（版本号列）和「弃用记录」表（弃用项列）的第一列都当作文件名
- 修复：改为只解析 `| 文件 | 版本 | 日期 | 备注 |` 表头对应的「工程化产物」表

**Bug B: `list_disk_files()` 排除了 `.github/` 目录**
- 原因：`.github` 以 `.` 开头被隐藏目录排除逻辑误杀
- 修复：`.git` 内部全部排除，`.github` 保留（CI 配置是合法源文件）

**Bug C: versions.md 路径比较用 basename 而非全路径**
- 原因：`disk_names` 只取 `os.path.basename()`，导致 `drafts/PEG-2026-07-13-001.md` 无法匹配 `PEG-2026-07-13-001.md`
- 修复：先精确匹配完整相对路径，再用 basename 兜底

### 验证结果
```
3.4 虚假条目: 0 ✅  (修复前: 4)
3.5 遗漏文件: 0 ✅  (修复前: 83)
versions.md 登记但不存在: 0 ✅  (修复前: 14，含误报)
```

---

## 2. `auto_register_versions.py` — 自动补登工具

### 功能
- 自动扫描磁盘源文件，找出未在 `versions.md`「工程化产物」表中登记的文件
- **智能排除**：运行时产物（`logs/gate_*.jsonl`、`traces/<trace_id>/*`）、构建产物（`.egg-info`）、自引用（`versions.md`）
- 按文件路径自动生成有意义的备注描述
- 支持 `--dry-run`（预览）和 `--apply`（执行）
- 本次补登 **68 个文件**，日期标记 `2026-08-04`

### 用法
```bash
python auto_register_versions.py --dry-run   # 预览
python auto_register_versions.py --apply     # 执行
```

---

## 3. `versions.md` — 补登 68 个文件

### 新增条目分类

| 类别 | 数量 | 示例 |
|---|---|---|
| 核心提示词 | 8 | `phase0_meta_peg_agent_prompt.md`, `bootstrap_prompt.md`, `stage1_prompt.md`, ... |
| 领域智能体提示词 | 5 | `prompts/domain/agents/orchestrator.prompt.md`, ... |
| 核心服务提示词 | 7 | `prompts/apps/core/services/feedback.prompt.md`, ... |
| 测试文件 | 8 | `test_guardrails_readonly.py`, `test_peg_trace.py`, ... |
| 工具脚本 | 8 | `fix_versions_refs.py`, `install_mermaid_renderer.py`, `ci_lint.py`, ... |
| doc_alignment 产物 | 10 | `doc_alignment.json`, `doc_alignment_quickref.md`, `validate_doc_alignment_json.py`, ... |
| doc_alignment_validator 包 | 5 | `QUICKSTART.md`, `setup.py`, `pyproject.toml`, `src/.../validate.py`, ... |
| 草案 / 报告 | 14 | `drafts/self_modify_*.diff.md`, `fix_reports/`, `migration_scan_report.*`, ... |
| 基础设施 | 3 | `.gitignore`, `hooks/pre-commit`, `traces/_historical_index.md` |

### 正确排除（未登记，符合 D5 规则）

| 文件 | 排除原因 |
|---|---|
| `logs/gate_*.jsonl` (3 个) | D5 运行时产物，通配 `gate_*.jsonl` 覆盖 |
| `traces/20260721_*/` 下文件 (6 个) | D5 运行时 trace 数据，通配 `<trace_id>/artifacts/*` 覆盖 |
| `versions.md` | 自引用，无需登记 |

---

## 4. `workspace_map.md` — 目录树对齐

### 变更
- 添加 68 个遗漏文件到目录树（含 `auto_register_versions.py`）
- 移除 4 个虚假条目（目录被误登记为文件）
- 移除 10 个 egg-info 构建产物（`PKG-INFO`, `SOURCES.txt` 等）

---

## 最终对齐状态

```
目录树条目: 106
versions.md 条目: 101
磁盘文件数: 109

3.4 虚假条目:       0 ✅
3.5 遗漏文件:       0 ✅
versions.md 登记但不存在: 0 ✅
磁盘存在但未登记:   11 (全部为运行时产物或自引用，符合 D5)
```

---

## 提交建议

```bash
git add fix_versions_refs.py auto_register_versions.py versions.md workspace_map.md
git commit -m "fix: 修复登记册一致性扫描器 + 补登 68 个未登记源文件

- fix_versions_refs.py: 修复三个解析器 bug（表解析/目录排除/路径匹配）
- auto_register_versions.py: 新增自动补登工具
- versions.md: 补登 68 个合法源文件到工程化产物表
- workspace_map.md: 目录树对齐（移除虚假条目 + 补登遗漏）
- 验证: 3.4/3.5/登记不存在 三项全部归零"
```