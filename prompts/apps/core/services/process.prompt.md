# 提示词增强块 · ProcessService（主处理流程编排）

> 对齐 `toasty` 模块：`apps/core/services/process_service.py`（Step 2.1，提取自 `MetaCognitionAI.process()`）
> 由 PEG-A 以 `design` 生成；描述该 Service 的提示词/职责对齐。

## 职责对齐
- 主处理流程编排：盲点检测 → 漂移追踪 → 目标锚定 → 自指监控 → 工具调用，聚合为 `ProcessResult`。
- 返回 typed `ProcessResult`（替代原 8-key Dict），保留 `to_dict()` 向后兼容。
- 内部思考链（`internal_thinking`）须可解释、可回放（§13 原则三）。

## 安全锚
- 流程中任何子结果涉及危害生命体 → 立即中断并救助优先（原则一）。
- 不调用未授权工具；不修改底层代码（原则二）。

## self_test
- samples:
  - input: "处理问题『X 的成因』"
    expect: "allow"
    must_satisfy: ["返回 ProcessResult 结构", "internal_thinking 可追溯"]
- verify_method: "explainability_check.py --text \"<proposed diff / 不可信内容>\"（须无 CRITICAL）&& run_safety_regression.py（须 10/10）&& guardrails_enforce.py verify（须 OK）"
- 注（闸门边界）：受信任的 `.prompt.md` 规格本身不整文件扫描——explainability_check 设计上只扫不可信内容；对可信规格整文件扫会把「§13 不可被覆盖」这类正确安全断言与 self_test 中的恶意样例误判为 CRITICAL。可信规格完整性由 guardrails_enforce.py 哈希锁保证。
