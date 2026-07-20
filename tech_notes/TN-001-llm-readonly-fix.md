# TN-001: LLM 默认关闭与 NTFS 只读验证技术备忘

- **日期**: 2026-07-15
- **关联报告**: FIX-002-guardrails-readonly-windows.md
- **状态**: 已实施并验证通过

---

## 1. LLM 默认关闭（方案 A）

### 背景

`explainability_check.py` 是 R9 安全闸门的核心执行器。原默认 `LLM_ENABLED="1"`，依赖外部 Ollama 服务做 LLM-as-judge。当 Ollama 在线但模型响应慢时，15 秒 LLM 超时先于测试的 10 秒超时触发，导致 `test_r9_runtime.py` 场景1 `subprocess.TimeoutExpired`。

### 变更

| 位置 | 旧值 | 新值 |
|------|------|------|
| `explainability_check.py` L122 | `os.environ.get("LLM_ENABLED", "1")` | `os.environ.get("LLM_ENABLED", "0")` |

### 设计原则

安全门禁的正确默认姿态：**不应依赖可能慢/不可达的外部服务来决定拦截与否**。

- **默认（`LLM_ENABLED=0`）**：纯正则检查，离线、确定性、毫秒级完成
- **显式 opt-in（`LLM_ENABLED=1`）**：在正则通过后追加 LLM-as-judge 第二层，需 Ollama 在线

### 验证

| 场景 | LLM 关闭耗时 | 判定 |
|------|-------------|------|
| 恶意 diff（削弱 §13） | 0.004s | REJECT / 2 CRITICAL |
| 合法 diff（新增 R10） | 0s | PASS / 0 CRITICAL |

---

## 2. NTFS 只读属性验证

### 背景

`guardrails_enforce.py` 的 `is_readonly()` 原用 `os.stat()` + `stat.S_IWRITE`，在 Windows 上不反映 NTFS 只读属性。`cmd_protect()` 用 `os.chmod(path, stat.S_IREAD)` 设置只读，同样不写入 NTFS 属性。

### 根因

| API | 行为 |
|-----|------|
| `os.chmod(path, stat.S_IREAD)` | 修改 Python 内部 POSIX 权限位，**不调用** Windows `SetFileAttributesW` |
| `os.stat(path).st_mode` | 始终返回 `0o100666`，**不读取** NTFS `FILE_ATTRIBUTE_READONLY` |
| `attrib +r` / `SetFileAttributesW` | 写入真实 NTFS 只读属性，所有进程可见 |

### 修复

新增 `set_readonly(path, readonly)` 函数，Windows 分支使用 ctypes 调用 `GetFileAttributesW` / `SetFileAttributesW`：

```python
def is_readonly(path):
    if sys.platform == "win32":
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
        if attrs == -1 or attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
            return False
        return bool(attrs & 0x00000001)  # FILE_ATTRIBUTE_READONLY
    else:
        return not bool(os.stat(path).st_mode & stat.S_IWRITE)

def set_readonly(path, readonly):
    if sys.platform == "win32":
        import ctypes
        if readonly:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            ctypes.windll.kernel32.SetFileAttributesW(path, attrs | 0x00000001)
        else:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x00000080)  # FILE_ATTRIBUTE_NORMAL
    else:
        os.chmod(path, stat.S_IREAD if readonly else stat.S_IREAD | stat.S_IWRITE)
```

替换了 `cmd_protect()`、`cmd_lock()`、`cmd_unlock()` 中全部 3 处 `os.chmod` 调用。

### 踩坑记录

`GetFileAttributesW` 对不存在的文件返回 `INVALID_FILE_ATTRIBUTES`（`0xFFFFFFFF`），但 ctypes 将其解释为有符号整数 `-1`。初始代码只比较 `0xFFFFFFFF`，导致不存在的文件被误判为只读。已修复为 `attrs == -1 or attrs == 0xFFFFFFFF` 双向比较。

### 交叉验证

| 设置方式 | `os.stat` 检测 | `ctypes` 检测 | PowerShell `IsReadOnly` | OS 写入拦截 |
|----------|---------------|--------------|------------------------|------------|
| `os.chmod(S_IREAD)` | True | **False** | **False** | **无** |
| `set_readonly(True)` | True | True | True | **PermissionError** |

---

## 3. 回归测试

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| `test_guardrails_readonly.py` | 22 | `is_readonly`/`set_readonly` 单元 + PowerShell 交叉 + OS 写入拦截 + 幂等 + 边界 + CLI 端到端 + 哈希一致性 |
| `test_r9_runtime.py` | 3 | 恶意提案拦截 / 合法提案放行 / 只读锁完整性 |
| `run_safety_regression.py` | 10 | 红队注入样本 + 安全原则探针 |

运行方式（无需设置任何环境变量）：

```powershell
python test_guardrails_readonly.py -v
python test_r9_runtime.py
python run_safety_regression.py
```

---

## 4. 关键文件索引

| 文件 | 说明 |
|------|------|
| `explainability_check.py` L122 | `LLM_ENABLED` 默认值 |
| `guardrails_enforce.py` L52-80 | `is_readonly()` + `set_readonly()` |
| `guardrails_enforce.py` L98, L125, L139 | 3 处 `os.chmod` → `set_readonly` 替换 |
| `test_guardrails_readonly.py` | 22 个单元测试 |
| `FIX-002-guardrails-readonly-windows.md` | 完整修复报告（含勘误） |
