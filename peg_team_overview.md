# 元认知提示工程团队（PEG-A Family）

## 团队架构

```
                        ┌─────────────┐
                        │   用户 / OS  │
                        └──────┬──────┘
                               │
                    ┌──────────▼──────────┐
                    │      PEG-A          │
                    │  (协作枢纽 / 元层)   │
                    │  提示词工程 + 自指   │
                    └──┬───────┬───────┬──┘
                       │       │       │
              ┌────────▼──┐ ┌──▼───────▼────────┐
              │ PEG-Code  │ │    PEG-Guard      │
              │ 代码审查   │ │  安全闸门守护     │
              └───────────┘ └───────────────────┘
```

## 成员一览

| 成员 | 定位 | 核心职责 | 提示词文件 |
|------|------|----------|-----------|
| **PEG-A** | 协作枢纽 / 元层构建者 | 提示词设计、自指改进、多智能体协调、新智能体孵化 | `phase0_meta_peg_agent_prompt.md` |
| **PEG-Code** | 代码审查分支 | 多语言代码审查、漏洞模式检测、安全合规检查 | `C:\Workspace\peg-code\prompt.md` |
| **PEG-Guard** | 安全闸门守护 | §12/§13 闸门执行、NTFS 只读锁、回归测试 | `peg_guard_prompt.md` |

## 职责边界

| 能力维度 | PEG-A | PEG-Code | PEG-Guard |
|----------|-------|----------|-----------|
| 提示词设计 | **主责** | — | — |
| 代码审查 | — | **主责** | — |
| 安全闸门执行 | — | — | **主责** |
| 自指改写 | **主责** | — | 验证方 |
| 反注入检测 | 声明意图 | — | **工程落地** |
| §13 只读锁 | 声明意图 | — | **工程落地** |
| 回归测试 | 发起方 | — | **执行方** |
| 新智能体孵化 | **主责** | — | — |
| 多智能体协调 | **主责** | — | — |

## 协作流程

### 流程 1：自指改进（PEG-A → PEG-Guard）

```
PEG-A 产出 diff
    │
    ▼
PEG-Guard: explainability_check.py 闸门校验
    │
    ├─ REJECT → 阻断，回退 PEG-A
    │
    └─ PASS → PEG-Guard: guardrails verify 只读锁完整性
                │
                ▼
              PEG-Guard: run_safety_regression.py 回归
                │
                ├─ FAIL → 阻断，回退 PEG-A
                │
                └─ PASS → PEG-A 采纳，PEG-Guard re-protect
```

### 流程 2：代码审查（PEG-Code → PEG-Guard）

```
PEG-Code 审查代码
    │
    ├─ 发现安全漏洞 → 标记 + 报告
    │
    └─ 审查完毕 → PEG-Guard 确认审查未触及 §13
```

### 流程 3：新智能体孵化（PEG-A 主导）

```
编排智能体 → PEG-A (intent=incubate)
    │
    ▼
PEG-A 产出种子提示词 (含 self_test)
    │
    ▼
PEG-Guard 闸门校验 (R9 规则)
    │
    ├─ REJECT → 回退 PEG-A 修改
    │
    └─ PASS → 新智能体就绪，登记入 capability_registry
```

## 安全模型

```
§13 最底层安全原则（只读禁区）
    │
    ├── PEG-A: 提示词层声明意图
    │
    ├── PEG-Guard: OS 层强制执行
    │   ├── explainability_check.py (正则 + LLM 双层)
    │   ├── guardrails_enforce.py (哈希 + NTFS 只读)
    │   └── run_safety_regression.py (红队回归)
    │
    └── 不可绕过: 任何成员的任何修改提案触及 §13 即自动驳回
```

## 调用拓扑

| 调用方 | 被调用方 | 触发条件 | 返回 |
|--------|----------|----------|------|
| 编排智能体 | PEG-A | 提示词设计/优化/孵化 | 草案 + self_test |
| PEG-A | PEG-Guard | 自指 diff 产出后 | gate + lock + regress 结果 |
| PEG-Code | PEG-Guard | 审查涉及安全规则时 | lock verify 结果 |
| 任何成员 | PEG-A | 遇到提示词瓶颈 | refactor 建议 |
| 任何成员 | PEG-Guard | 修改了闸门/锁定代码 | full_check 结果 |

## 工具矩阵

| 工具 | 归属 | 用途 |
|------|------|------|
| `explainability_check.py` | PEG-Guard | 反注入 + §13 篡改检测 |
| `guardrails_enforce.py` | PEG-Guard | 哈希校验 + NTFS 只读锁 |
| `run_safety_regression.py` | PEG-Guard | 红队注入样本回归 |
| `test_guardrails_readonly.py` | PEG-Guard | 只读逻辑单元测试 (22 例) |
| `test_r9_runtime.py` | PEG-Guard | R9 三场景自指测试 |
| `self_test_template.md` | PEG-A | 提示词草案自测模板 |
| `safety_eval_suite.json` | PEG-A | 红队注入样本定义 |
| `capability_registry.md` | PEG-A | 智能体能力登记册 |
| `stage1_tool_schema.json` | PEG-A | 工具 JSON schema |

## 测试基线

| 测试套件 | 用例数 | 执行者 | 通过标准 |
|----------|--------|--------|----------|
| `test_guardrails_readonly.py` | 22 | PEG-Guard | 22/22 green |
| `test_r9_runtime.py` | 3 | PEG-Guard | 3/3 green |
| `run_safety_regression.py` | 10 | PEG-Guard | 10/10 green |
| `self_test_template.md` | 10 | PEG-Code | 10/10 green |

**团队总基线：45/45 all green**

## 版本

| 成员 | 版本 | 状态 |
|------|------|------|
| PEG-A | v0.2 (R9 已写入) | 阶段 1 自微调中 |
| PEG-Code | v0.1 | 10 测试用例覆盖 5 语言 |
| PEG-Guard | v0.1 | 35 测试全绿，NTFS + LLM 修复已合入 |
