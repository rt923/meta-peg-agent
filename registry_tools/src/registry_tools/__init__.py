"""
registry_tools — PEP-A 登记册一致性工具集
===========================================

pip 可安装包：将 fix_versions_refs.py 与 auto_register_versions.py 打包为独立工具。

用法：
    pip install registry_tools-0.1.0-py3-none-any.whl

    # 核对登记册一致性（dry-run）
    registry-check --target /path/to/project

    # 自动修复登记册
    registry-fix --target /path/to/project

    # 自动补登未登记文件
    registry-register --target /path/to/project --dry-run
    registry-register --target /path/to/project --apply

版本: v0.1.0 (2026-08-04)
"""

__version__ = "0.1.0"
__all__ = [
    # fix_versions_refs
    "parse_workspace_map", "parse_versions_md", "list_disk_files",
    "find_phantom_entries", "find_missing_files", "fix_workspace_map",
    "main_fix",
    # auto_register_versions
    "is_runtime_artifact", "is_source_file", "find_unregistered",
    "get_file_description", "generate_entries", "apply_registration",
    "main_register",
]

from .fix_versions_refs import (
    parse_workspace_map,
    parse_versions_md,
    list_disk_files,
    find_phantom_entries,
    find_missing_files,
    fix_workspace_map,
    main as main_fix,
)
from .auto_register_versions import (
    is_runtime_artifact,
    is_source_file,
    find_unregistered,
    get_file_description,
    generate_entries,
    apply_registration,
    main as main_register,
)