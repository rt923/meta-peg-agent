# doc_alignment 快速参考（Quick Reference）

> 版本：v0.1 (2026-07-22)
> 源文件：`prompts/apps/core/services/doc_alignment.prompt.md`
> 状态：★固化（self_test 7/7 PASS，R9 闸门准入）
> 用途：供智能体在做文档一致性检查时快速引用，无需加载完整 prompt。

---

## 角色

对成对/成组的工程文档做**实证对齐检查**，确保代码实现与文档描述完全一致。

## 六条规则速查

| 规则 | 一句话 | 触发条件 |
|---|---|---|
| **D1** · 实证对比 | 逐函数比签名/场景/字段/产出物/行为，分三级偏差 | 任何 `.py` ↔ `.md` 或 `.md` ↔ `.md` 对齐任务 |
| **D2** · 同性质扫描 | 修一处偏差后，主动扫同文件关联文件的同类偏差 | 修复任何偏差后 |
| **D3** · 目录树验证 | 文件名匹配 + 通配覆盖 = 100% 磁盘文件 | 更新 `workspace_map.md` 后 |
| **D4** · 交叉引用 | versions.md ↔ capability_registry.md ↔ workspace_map.md 三向对齐 | 任一登记文件更新后 |
| **D5** · 运行时产物 | 自动生成文件用通配模式，不逐名登记 | 目录树登记时 |
| **D6** · 回溯更新 | 对齐修复后回溯更新能力登记册的演进信号条目 | 补登记 + 修复完成后 |

## 偏差分级

| 级别 | 定义 | 处理 |
|---|---|---|
| **真偏差** | 文档与代码矛盾 | 须修 |
| **轻微不一致** | 措辞模糊但功能无碍 | 标注不改 |
| **数字漂移** | 文档计数与实际运行结果不符 | 须同步 |

## 工作流（5 步）

```
1. 逐项对比 → 输出偏差清单
2. 修真偏差 → 扫描同性质遗漏（D2）
3. 补登记 → 三向交叉验证（D4）→ 目录树验证（D3）
4. 重跑验证脚本 → 确认全 PASS
5. 回溯更新演进信号（D6）→ 完成
```

## 登记文件三向对齐（D4）

| 文件 | 登记内容 |
|---|---|
| `versions.md` | 版本号 + 日期 + 变更摘要 |
| `capability_registry.md` | 演进信号条目（含功能描述 + 对齐修复记录） |
| `workspace_map.md` | 目录树位置 + 用途注释 |

## 运行时产物通配模式（D5）

| 类型 | 通配 | 示例 |
|---|---|---|
| 闸门日志 | `gate_*.jsonl` | `gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl` |
| trace 产物 | `<trace_id>/artifacts/*` | `20260721_104251_0b52/artifacts/*.md` |
| 缓存 | `__pycache__/`、`.pytest_cache/` | — |
| IDE 配置 | `.obsidian/`（目录级注释） | — |

## self_test 验证状态

| # | 用例 | 输入 | 期望 | 状态 |
|---|---|---|---|---|
| 1 | D1:函数签名对比 | `make_mock_hash_store(path, scenario) → 4 scenario + 返回 path + ValueError` | 逐项对比，输出一致 ✅ 或偏差 ❌ | ✅ |
| 2 | D1:真偏差识别 | `文档写 step_count=6，代码实际产出 step_count=5` | 判定为真偏差，建议修文档 | ✅ |
| 3 | D1:数字漂移识别 | `文档写 26 个断言，实际输出 33 个 [✓ PASS]` | 判定为数字漂移，同步为 33 | ✅ |
| 4 | D2:同性质遗漏 | `修复 .md L164 step_count=6→5` | 主动扫描 .py 同名字段 | ✅ |
| 5 | D3:目录树验证 | `83 个磁盘文件，目录树登记 83 个（78 精确 + 5 通配）` | 判定完整 ✅ | ✅ |
| 6 | D5:运行时产物 | `logs/gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl` | 识别为运行时产物，用 gate_*.jsonl 通配 | ✅ |
| 7 | D6:演进信号回溯 | `补登记 40+ 文件后，续4 条目仍写「补 2 个文件」` | 判定低估实际范围，更新为准确数字 | ✅ |

> **R9 闸门**：2026-07-22 验证，7/7 通过（0 CRITICAL）。

## 回滚方式

若需停用本增强块：
1. 从 `capability_registry.md` 可选增强块清单移除 `doc_alignment` 行
2. 从 `workspace_map.md` 目录树移除 `doc_alignment.prompt.md`
3. 保留 `prompts/apps/core/services/doc_alignment.prompt.md` 为历史归档（不删除）

## 依赖

- `core`（必选增强块）
- 无其他外部依赖

---

> 完整提示词见 `prompts/apps/core/services/doc_alignment.prompt.md`。