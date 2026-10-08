# doc_alignment_validator — 快速使用指南

> 版本: v0.1.0 | 更新时间: 2026-07-28

## 5 分钟接入

### 1. 安装

```bash
# 方式 A: wheel 安装（推荐，无需网络）
pip install doc_alignment_validator-0.1.0-py3-none-any.whl

# 方式 B: 源码安装
pip install /path/to/doc_alignment_validator/
```

### 2. 验证安装

```bash
python -c "from doc_alignment_validator import validate; validate()"
```

预期输出:
```
加载 JSON: .../doc_alignment.json
  [✓] 1. JSON 语法合法
  [✓] 2. 顶层字段完整 (7/7)
  ...
  [✓] 11. 数组非空校验通过
==================================================
全部校验通过 ✅ — 外部工具可安全加载
```

### 3. 三行代码集成

```python
from doc_alignment_validator import validate

# 使用随包分发的 doc_alignment.json
validate()

# 或指定自定义 JSON
validate("/path/to/your/doc_alignment.json")
```

---

## 11 项检查明细

| # | 检查项 | 说明 |
|---|---|---|
| 1 | JSON 语法合法性 | 确保 `json.load()` 不抛异常 |
| 2 | 顶层字段完整性 | 7 个顶层 key 全部存在 |
| 3 | meta 字段 + 类型校验 | `r9_gate.critical` 必须为 0 |
| 4 | role 字段完整性 | identity / responsibility 不可为空 |
| 5 | D1–D6 规则结构 | 5 维度 + 3 偏差 + 4 通配 |
| 6 | workflow 五步完整性 | step 必须从 1 连续递增 |
| 7 | self_test 7 条 + rule 引用 | rule 值必须在 {D1,...,D6} 中 |
| 8 | security §12/§13 | 两条安全锚均不可缺 |
| 9 | related_files 路径一致性 | 自引用 + 磁盘存在性 |
| 10 | 空值校验 | 递归扫描，0 null 容忍 |
| 11 | 数组非空校验 | dimensions / self_test / steps 不为空 |

---

## CI/CD 集成

### GitHub Actions

```yaml
- name: Validate doc_alignment JSON
  run: python -m doc_alignment_validator
```

### GitLab CI

```yaml
validate:
  script:
    - python -c "from doc_alignment_validator import validate; validate()"
```

### Jenkins / 通用

```bash
python -m doc_alignment_validator --json-path ./doc_alignment.json
exit $?  # 0=通过, 1=失败
```

---

## 常见问题

### Q: 安装后 import 报 ModuleNotFoundError？

```bash
# 检查安装位置
python -m pip show doc_alignment_validator
# 确认 Python 版本 >= 3.8
python --version
```

### Q: 第 9 项（related_files 路径）在安装包中失败？

预期行为。安装包中 `validate()` 会自动跳过源 repo 的磁盘检查，仅校验自引用完整性。如需完整检查，在源 repo 目录下运行。

### Q: 如何更新包内的 doc_alignment.json？

```bash
# 卸载旧版
pip uninstall doc_alignment_validator -y
# 重新安装新版
pip install doc_alignment_validator-0.2.0-py3-none-any.whl
```

### Q: 如何只检查特定项？

```python
from doc_alignment_validator import check_meta, check_rules
import json

with open("doc_alignment.json") as f:
    data = json.load(f)

check_meta(data)    # 只检查 meta
check_rules(data)   # 只检查 D1–D6 规则
```

---

## 分发到其他团队

```
发给其他团队的文件:
├── doc_alignment_validator-0.1.0-py3-none-any.whl   ← 主文件
└── QUICKSTART.md                                     ← 本指南

他们只需要:
  pip install doc_alignment_validator-0.1.0-py3-none-any.whl
  python -c "from doc_alignment_validator import validate; validate()"
```

---

> 依赖: Python >= 3.8 | 零外部依赖 | 仅 stdlib