# mock_helpers.py API 文档

> 版本: v0.1 (2026-07-21)
> 配套验证脚本: [verify_mock_helpers.py](verify_mock_helpers.py)（33 个断言全 PASS）
> 配套测试: [mock_integration_test.py](mock_integration_test.py)（16 个测试全 PASS）
> 登记位置: [versions.md](versions.md#L37)

## 概述

`mock_helpers.py` 是 PEG-A 测试 mock 数据工厂，提供 3 个工厂函数构造测试用的 `HASH_STORE` 与 `trace` 数据，避免测试污染真实数据。

**设计原则**:
- 零依赖（仅用 stdlib：`os` / `json` / `hashlib` / `datetime`）
- 全部在调用方指定路径下构造，不污染真实 `traces/` 或 `HASH_STORE`
- 字段命名严格对齐生产代码（如 `build_historical_index.py` 从 `task_summary` 读 task）
- scenario 命名与生产代码行为对应（`no_field` / `null_field` / `valid_hash` / `corrupt`）

## API

### 1. `make_mock_hash_store(path, scenario)`

构造 mock `HASH_STORE` 的 4 种场景，用于测试 `guardrails_enforce.py v0.3` 的 `cmd_unlock` 哈希比对逻辑。

**参数**:

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | str | HASH_STORE 文件路径（如 `'<phase0>.guardrail.json'`） |
| `scenario` | str | 场景名，取值见下表 |

**scenario 取值**:

| scenario | 含义 | 行为对应 |
|---|---|---|
| `"no_field"` | 旧产物（v0.2 时代），无 `guardrail_token_hash` 字段 | `cmd_unlock` 退化为非空校验（WARN） |
| `"null_field"` | 字段存在但值为 `None` | `cmd_unlock` 退化为非空校验（WARN） |
| `"valid_hash"` | 字段为 `"mock-token-123"` 的 SHA256 哈希 | `cmd_unlock` 走 `secrets.compare_digest` 比对 |
| `"corrupt"` | 非 JSON 内容（字符串 `"not a valid json {{{"`） | `json.load` 抛 `ValueError`（`cmd_unlock` 会捕获并标记） |

**返回**: `path`（原样返回，便于链式调用）

**异常**: `ValueError`（未知 scenario 时）

**用法示例**:

```python
from mock_helpers import make_mock_hash_store
import tempfile, os

tmp = tempfile.mkdtemp()
hs_path = os.path.join(tmp, "phase0.guardrail.json")

# 写入 "mock-token-123" 的哈希
make_mock_hash_store(hs_path, "valid_hash")

# 测试 cmd_unlock
import os
os.environ["GUARDRAIL_TOKEN"] = "mock-token-123"  # 匹配
rc = guardrails_enforce.cmd_unlock("phase0.md")  # → exit 0

os.environ["GUARDRAIL_TOKEN"] = "wrong-token"     # 不匹配
rc = guardrails_enforce.cmd_unlock("phase0.md")  # → exit 2
```

---

### 2. `make_mock_trace(traces_root, trace_id, status, steps, arts_count, task, manifest_broken=False)`

构造 mock trace 子目录（含完整三件套），用于测试 `peg_trace.py` 与 `build_historical_index.py`。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `traces_root` | str | — | `traces/` 根目录 |
| `trace_id` | str | — | trace 标识（如 `"20260721_100000_mock"`） |
| `status` | str | — | trace 状态（`"completed"` / `"aborted"`） |
| `steps` | int | — | `reasoning.jsonl` 中的 step 数（不含 trace_start） |
| `arts_count` | int | — | `artifacts/` 中的产出物数量 |
| `task` | str | — | 任务摘要（写入 manifest 的 `task_summary` 字段） |
| `manifest_broken` | bool | `False` | `True` 时 manifest.json 写成损坏 JSON |

**返回**: `trace_dir`（trace 子目录路径）

**产出物结构**:

```
<traces_root>/<trace_id>/
  ├── reasoning.jsonl     # 1 行 trace_start + steps 行 Meta-Loop 记录
  ├── manifest.json       # trace 元信息 + artifacts 索引
  └── artifacts/
      └── <trace_id>-art-<N>.md
```

**字段对齐说明**:
- `manifest.task_summary` 字段对齐 `build_historical_index.py:142`（从 `task_summary` 读 task）
- `reasoning.jsonl` 第一行 `event="trace_start"` 对齐 `peg_trace.py Tracer.start`
- `phase` 顺序为 `["Plan", "Act", "Observe", "Reflect", "Coordinate"]`（按 `i % 5` 循环）

**用法示例**:

```python
from mock_helpers import make_mock_trace
import tempfile, os

tmp = tempfile.mkdtemp()
traces_root = os.path.join(tmp, "traces")
os.makedirs(traces_root)

# 造 1 条 completed trace，5 拍 + 2 个 artifact
trace_dir = make_mock_trace(
    traces_root=traces_root,
    trace_id="20260721_100000_mock",
    status="completed",
    steps=5,
    arts_count=2,
    task="测试任务",
)

# 造 1 条 manifest 损坏的 trace（测 build_historical_index 兜底）
make_mock_trace(
    traces_root=traces_root,
    trace_id="20260721_100001_brok",
    status="completed",
    steps=3,
    arts_count=0,
    task="损坏测试",
    manifest_broken=True,
)
```

---

### 3. `make_mock_full_session(traces_root, trace_id=None, task="mock 完整会话", status="completed", include_artifact=True, artifact_content=None)`

高阶函数：一次性构造完整的 PEG-A 会话 trace（固定 5 拍 + 1 artifact），适合集成测试与演示。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `traces_root` | str | — | `traces/` 根目录 |
| `trace_id` | str / None | `None` | trace 标识，`None` 时自动生成 `<时间戳>_full` |
| `task` | str | `"mock 完整会话"` | 任务摘要 |
| `status` | str | `"completed"` | trace 状态（`"completed"` / `"aborted"`） |
| `include_artifact` | bool | `True` | 是否包含 1 个 artifact |
| `artifact_content` | str / None | `None` | artifact 内容，`None` 时用默认 mock 内容 |

**返回**: `dict`，包含 5 个字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `trace_dir` | str | trace 子目录路径 |
| `trace_id` | str | trace 标识 |
| `reasoning_path` | str | `reasoning.jsonl` 路径 |
| `manifest_path` | str | `manifest.json` 路径 |
| `artifact_path` | str / None | artifact 文件路径（`include_artifact=False` 时为 `None`） |

**产出物结构**（完整 PEG-A 会话）:

```
<traces_root>/<trace_id>/
  ├── reasoning.jsonl     # 1 行 trace_start + 5 行 Meta-Loop（Plan/Act/Observe/Reflect/Coordinate）
  ├── manifest.json       # status="completed", step_count=5, 1 artifact
  └── artifacts/
      └── <trace_id>-full-art.md
```

**与 `make_mock_trace` 的分工**:

| 函数 | 定位 | steps | arts_count | 用途 |
|---|---|---|---|---|
| `make_mock_trace` | 参数化边界测试 | 任意 | 任意 | 测 0/多 step、0/多 artifact、manifest 损坏等边界 |
| `make_mock_full_session` | 标准会话构造 | 固定 5 | 0 或 1 | 集成测试、演示、快速造数据 |

**用法示例**:

```python
from mock_helpers import make_mock_full_session
import tempfile

tmp = tempfile.mkdtemp()

# 用法 1: 造一条标准 PEG-A 会话 trace
result = make_mock_full_session(tmp, task="测试任务")
print(result["trace_id"])         # 20260721_100000_full
print(result["artifact_path"])    # /tmp/.../artifacts/...-full-art.md

# 用法 2: 造无 artifact 的 trace
result = make_mock_full_session(tmp, include_artifact=False)
assert result["artifact_path"] is None

# 用法 3: 自定义 artifact 内容
result = make_mock_full_session(
    tmp,
    artifact_content="# 我的 artifact\n内容\n",
)
```

## 验证与测试

| 脚本 | 用途 | 断言数 |
|---|---|---|
| [verify_mock_helpers.py](verify_mock_helpers.py) | API 验证脚本 | 33 |
| [mock_integration_test.py](mock_integration_test.py) | 4 个目标集成测试 | 16 |

**运行**:

```powershell
cd 'C:\Users\1\WorkBuddy\2026-07-13-11-57-54\meta_peg_agent'
$env:PYTHONIOENCODING='utf-8'
python verify_mock_helpers.py      # 33 个断言
python mock_integration_test.py    # 16 个测试
```

## 与生产代码的字段对齐

| mock_helpers 字段 | 生产代码位置 | 说明 |
|---|---|---|
| `manifest.task_summary` | `build_historical_index.py:142` | 索引页第六章从 `task_summary` 读 task |
| `manifest.status` | `build_historical_index.py:130` | 索引页第六章 status 列 |
| `manifest.step_count` | `build_historical_index.py:133` | 索引页第六章 steps 列 |
| `manifest.artifacts` | `build_historical_index.py:136` | 索引页第六章 arts 列 |
| `reasoning.jsonl` 第一行 `event="trace_start"` | `peg_trace.py Tracer.start` | trace 起始标记 |
| `reasoning.jsonl` 后续行 `phase` | `peg_trace.py Tracer.log` | Meta-Loop 五拍 |
| `HASH_STORE.guardrail_token_hash` | `guardrails_enforce.py v0.3 cmd_unlock` | 哈希比对字段 |

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-07-21 | 首版：3 个工厂函数（`make_mock_hash_store` / `make_mock_trace` / `make_mock_full_session`） |

## 回滚方式

`mock_helpers.py` 是纯新增基础设施模块，删除文件即完全回滚。删除后：
- `mock_integration_test.py` 会 ImportError（需同步删除）
- `verify_mock_helpers.py` 会 ImportError（需同步删除）
- 不影响生产代码（`peg_trace.py` / `guardrails_enforce.py` / `build_historical_index.py`）
