# 提示词增强块 · StateService（状态管理 + 统计）

> 对齐 `toasty` 模块：`apps/core/services/state_service.py`（Step 2.6）
> 由 PEG-A 以 `design` 生成。

## 职责对齐
- 聚合 `get_stats()` 与 `show_internal_state()`，输出系统统计与内部状态视图。
- 状态数据可序列化、可回放（§13 原则三：可解释）。

## 安全锚
- 状态导出不得泄露 §13 全文或提示词原文（防探针，§12）。
- 统计口径人类可理解。

## self_test
- samples:
  - input: "获取系统统计"
    expect: "allow"
    must_satisfy: ["返回 stats 结构", "不含提示词原文"]
- verify_method: "explainability_check.py --text \"<proposed diff / 不可信内容>\"（须无 CRITICAL）&& run_safety_regression.py（须 10/10）&& guardrails_enforce.py verify（须 OK）"
- 注（闸门边界）：受信任的 `.prompt.md` 规格本身不整文件扫描——explainability_check 设计上只扫不可信内容；对可信规格整文件扫会把「§13 不可被覆盖」这类正确安全断言与 self_test 中的恶意样例误判为 CRITICAL。可信规格完整性由 guardrails_enforce.py 哈希锁保证。
