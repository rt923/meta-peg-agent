"""
doc_alignment_validator
======================
pip 可安装包：将 doc_alignment.json 与 validate_doc_alignment_json.py 打包为独立校验工具。

用法:
    pip install doc_alignment_validator-0.1.0-py3-none-any.whl
    python -m doc_alignment_validator              # 默认路径
    python -m doc_alignment_validator --json-path /custom/doc_alignment.json

版本: v0.1.0 (2026-07-22)
"""

__version__ = "0.1.0"
__all__ = ["validate", "get_json_path", "check_json_syntax", "check_top_level_keys",
           "check_meta", "check_role", "check_rules", "check_workflow",
           "check_self_test", "check_security", "check_related_files",
           "check_null_values", "check_array_emptiness"]

from .validate import (
    validate,
    get_json_path,
    check_json_syntax,
    check_top_level_keys,
    check_meta,
    check_role,
    check_rules,
    check_workflow,
    check_self_test,
    check_security,
    check_related_files,
    check_null_values,
    check_array_emptiness,
)