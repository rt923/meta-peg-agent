# doc_alignment_validator

`doc_alignment.json` 的 11 项完整性校验工具，打包为 pip 可安装的独立包。

## 安装

```bash
# 从源码安装
pip install .

# 或构建 wheel 后分发
pip install doc_alignment_validator-0.1.0-py3-none-any.whl
```

## 使用

```bash
# 命令行（使用随包分发的 doc_alignment.json）
python -m doc_alignment_validator

# 指定自定义 JSON 路径
python -m doc_alignment_validator --json-path /path/to/doc_alignment.json

# 或使用 entry point
doc-alignment-validate
```

## Python API

```python
from doc_alignment_validator import validate

# 使用默认 JSON
validate()

# 自定义路径
validate("/custom/doc_alignment.json")
```

## CI/CD 集成

```yaml
- name: Validate doc_alignment JSON
  run: python -m doc_alignment_validator
```

## 11 项检查

1. JSON 语法合法性
2. 顶层字段完整性 (7/7)
3. meta 字段 + 类型校验
4. role 字段完整性
5. D1–D6 规则结构 (5 维度 + 3 偏差 + 4 通配)
6. workflow 五步完整性
7. self_test 7 条 + rule 引用有效性
8. security §12/§13 完整性
9. related_files 路径一致性
10. 空值校验 (0 null)
11. 数组非空校验

## 版本

v0.1.0 (2026-07-22)