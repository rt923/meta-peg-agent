#!/usr/bin/env python3
"""
auto_register_versions.py
自动扫描磁盘上的合法源文件，将未登记项补登到 versions.md 的「工程化产物」表中。

规则：
  - 仅补登合法源文件（.py / .md / .json / .sh / .ps1 / .toml / .yml / .gitignore / pre-commit 等）
  - 排除运行时产物：logs/gate_*.jsonl、traces/<trace_id>/*（trace 运行时数据）
  - 保留 traces/_historical_index.md（文档类产物）
  - 排除自身：versions.md、workspace_map.md（已在登记表中）

用法：
  python auto_register_versions.py --dry-run    # 仅列出待补登文件
  python auto_register_versions.py --apply      # 执行补登

版本: v0.1 (2026-08-04)
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Set, List, Tuple

# ── 日志 ──────────────────────────────────────────────
logger = logging.getLogger("auto_register_versions")

# ── 配置 ──────────────────────────────────────────────

TARGET = Path(__file__).resolve().parent
VERSIONS_PATH = TARGET / "versions.md"

# 排除的运行时产物模式（D5 通配覆盖的，不逐名登记）
EXCLUDE_RUNTIME_PATTERNS = [
    "logs/gate_",           # gate 日志（gate_*.jsonl）
    "traces/202607",        # 运行时 trace 数据（manifest.json, reasoning.jsonl, artifacts/）
]

# 排除自身引用
EXCLUDE_SELF = {"versions.md", "workspace_map.md"}

# 文件扩展名白名单（只登记合法源文件）
SOURCE_EXTENSIONS = {
    ".py", ".md", ".json", ".sh", ".ps1", ".toml", ".yml", ".yaml",
    ".jsonl", ".txt", ".cfg", ".ini", ".diff", ".patch",
}


# ── 核心逻辑 ──────────────────────────────────────────

def list_disk_files(target: Path) -> Set[str]:
    """列出磁盘上的源文件（与 fix_versions_refs.py 保持一致）"""
    files = set()
    exclude_dirs = {
        "__pycache__", ".pytest_cache", "node_modules",
        ".obsidian", "dist", "build",
    }
    exclude_suffixes = {".egg-info", ".dist-info"}
    exclude_exts = {".pyc", ".pyo", ".egg", ".whl"}

    for f in target.rglob("*"):
        if not f.is_file():
            continue
        parts = f.parts
        skip = False
        for p in parts:
            if p in exclude_dirs:
                skip = True
                break
            if any(p.endswith(s) for s in exclude_suffixes):
                skip = True
                break
            if p == ".git":
                skip = True
                break
            if p.startswith(".") and p not in (".gitignore", ".github", ".git"):
                skip = True
                break
        if skip:
            continue
        if f.suffix in exclude_exts:
            continue
        if f.name.startswith("_") and f.name.endswith(".py"):
            continue
        rel = f.relative_to(target)
        files.add(str(rel).replace("\\", "/"))
    return files


def is_runtime_artifact(rel_path: str) -> bool:
    """检查是否为运行时产物（D5 通配覆盖，不应逐名登记）"""
    for pattern in EXCLUDE_RUNTIME_PATTERNS:
        if rel_path.startswith(pattern):
            # traces/_historical_index.md 是文档，保留
            if rel_path == "traces/_historical_index.md":
                return False
            return True
    return False


def is_source_file(rel_path: str) -> bool:
    """检查是否为合法源文件"""
    basename = os.path.basename(rel_path)
    # 无扩展名的特殊文件（git hooks 等）
    if basename in (".gitignore", "pre-commit", "AUTO_MERGE", "COMMIT_EDITMSG",
                     "FETCH_HEAD", "HEAD", "ORIG_HEAD", "description", "index",
                     "config", "exclude", "master"):
        return basename in (".gitignore", "pre-commit")
    ext = Path(rel_path).suffix.lower()
    return ext in SOURCE_EXTENSIONS


def parse_versions_md(text: str) -> Set[str]:
    """解析 versions.md「工程化产物」表，返回已登记文件名集合"""
    entries = set()
    in_target_table = False
    for line in text.splitlines():
        if line.startswith("| 文件 | 版本 | 日期 | 备注 |"):
            in_target_table = True
            continue
        if in_target_table and (line.startswith("## ") or line.startswith("| 项 |") or line.startswith("| 版本 |")):
            break
        if in_target_table and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                fname = parts[1].strip("`").strip()
                if fname and not fname.startswith("文件") and not fname.startswith("---"):
                    entries.add(fname)
    return entries


def find_unregistered(disk_files: Set[str], registered: Set[str]) -> List[str]:
    """找出磁盘存在但未登记的文件"""
    unregistered = []
    for df in sorted(disk_files):
        basename = os.path.basename(df)
        # 排除自身
        if basename in EXCLUDE_SELF:
            continue
        # 排除运行时产物
        if is_runtime_artifact(df):
            continue
        # 排除非源文件
        if not is_source_file(df):
            continue
        # 检查是否已登记（精确路径 + basename 兜底）
        if df in registered or basename in registered:
            continue
        unregistered.append(df)
    return unregistered


def get_file_description(rel_path: str) -> str:
    """根据文件路径生成备注描述"""
    basename = os.path.basename(rel_path)
    dirname = os.path.dirname(rel_path)

    if basename == ".gitignore":
        return "VCS 忽略规则"
    if basename == "pre-commit":
        return "Git pre-commit hook"
    if "test_" in basename:
        return f"测试：{basename.replace('test_', '').replace('.py', '').replace('_', ' ').strip()}"
    if basename.endswith("_test.py") or basename.endswith("_integration_test.py"):
        return f"集成测试"
    if "drafts/" in rel_path:
        if "self_modify" in basename:
            return f"PEG-A 自修改 diff 草案"
        if "_v0_6_apply_scripts/" in rel_path:
            return f"v0.6 升级脚本"
        return "草案"
    if "fix_reports/" in rel_path:
        return "修复报告"
    if "tech_notes/" in rel_path:
        return "技术笔记"
    if "prompts/domain/agents/" in rel_path:
        return f"领域智能体提示词：{basename.replace('.prompt.md', '').replace('.md', '')}"
    if "prompts/apps/core/services/" in rel_path:
        return f"核心服务提示词：{basename.replace('.prompt.md', '').replace('.md', '')}"
    if "doc_alignment_validator/" in rel_path:
        if "src/" in rel_path:
            return "pip 包核心校验逻辑"
        if basename == "pyproject.toml":
            return "pip 包构建配置"
        if basename == "setup.py":
            return "pip 包安装脚本"
        if basename == "validate.py":
            return "包入口：11 项校验引擎"
        return "doc_alignment_validator 包文件"
    if "traces/" in rel_path:
        return "历史 trace 静态索引页"
    if "logs/" in rel_path:
        return "gate 日志样例"
    if "TRAE/" in rel_path:
        return "TRAE IDE 欢迎文档"
    if basename == "ARCHITECTURE_BRIEF.md":
        return "PEG-A 架构简报"
    if basename == "bootstrap_prompt.md":
        return "引导提示词"
    if basename == "ci_lint.py":
        return "CI 代码检查脚本"
    if basename == "ci_timing_report.json":
        return "CI 耗时报告"
    if basename == "demo_peg_collaboration.py":
        return "PEG-A 多智能体协作演示"
    if basename == "fix_versions_refs.py":
        return "登记册一致性自动修复工具"
    if basename == "guardrails_enforce.v0.2.bak.py":
        return "guardrails_enforce v0.2 备份"
    if basename == "install_mermaid_renderer.py":
        return "Mermaid 渲染器一键安装脚本"
    if basename == "migration_scan_report.json":
        return "迁移扫描 JSON 报告"
    if basename == "migration_scan_report.md":
        return "迁移扫描 Markdown 报告"
    if basename == "mock_helpers.md":
        return "mock_helpers 文档"
    if basename == "mock_integration_test.py":
        return "mock 集成测试"
    if basename == "os_guardrails.md":
        return "OS 护栏文档"
    if basename == "peg_guard_prompt.md":
        return "PEG 护栏提示词"
    if basename == "peg_team_overview.md":
        return "PEG 团队概览"
    if basename == "phase0_meta_peg_agent_prompt.md":
        return "PEG-A 主提示词"
    if basename == "phase0_meta_peg_agent_prompt.md.guardrail.json":
        return "PEG-A 主提示词护栏 JSON"
    if basename == "phase0_meta_peg_agent_prompt_full.md":
        return "PEG-A 主提示词完整版"
    if basename == "run_gate.sh":
        return "gate 运行脚本（Shell）"
    if basename == "self_test_template.md":
        return "self_test 模板"
    if basename == "spawn_peg_member_prompt.md":
        return "PEG 成员孵化提示词"
    if basename == "stage1_prompt.md":
        return "阶段 1 提示词"
    if basename == "stage1_team_prompt.md":
        return "阶段 1 团队提示词"
    if basename == "stage1_tool_schema.json":
        return "阶段 1 工具 Schema"
    return "源文件"


def generate_entries(unregistered: List[str], date_str: str) -> List[str]:
    """为未登记文件生成 versions.md 表格行"""
    lines = []
    for f in unregistered:
        desc = get_file_description(f)
        lines.append(f"| {f} | v0.1 | {date_str} | 基础设施新增：{desc} |")
    return lines


def apply_registration(versions_path: Path, new_entries: List[str]) -> str:
    """将新条目插入 versions.md「工程化产物」表末尾
    
    versions_path 可以是 Path 对象或 str（用于测试）。
    """
    if isinstance(versions_path, str):
        content = versions_path
    else:
        content = versions_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 找到「工程化产物」表最后一行（下一个 ## 标题之前）
    in_table = False
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| 文件 | 版本 | 日期 | 备注 |"):
            in_table = True
            continue
        if in_table and (line.startswith("## ") or line.startswith("| 项 |") or line.startswith("| 版本 |")):
            insert_idx = i
            break

    if insert_idx is None:
        print("❌ 找不到「工程化产物」表的结束位置")
        sys.exit(1)

    # 在表末插入新条目
    new_lines = lines[:insert_idx] + new_entries + [""] + lines[insert_idx:]
    return "\n".join(new_lines)


# ── 主入口 ─────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    p = argparse.ArgumentParser(description="自动扫描并补登未登记文件到 versions.md")
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="仅列出待补登文件，不修改 (默认)")
    p.add_argument("--apply", action="store_true",
                   help="执行补登到 versions.md")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help=f"补登日期 (默认: {datetime.now().strftime('%Y-%m-%d')})")
    args = p.parse_args()

    # ── 启动日志 ──
    logger.info("=" * 60)
    logger.info("auto_register_versions 启动")
    logger.info("  目标目录: %s", TARGET)
    logger.info("  versions.md: %s (存在=%s)", VERSIONS_PATH, VERSIONS_PATH.exists())
    logger.info("  模式: %s", "dry-run" if not args.apply else "apply")
    logger.info("  补登日期: %s", args.date)

    print(f"🔍 扫描目标: {TARGET}")
    print(f"   versions.md: {VERSIONS_PATH}\n")

    # 扫描
    disk_files = list_disk_files(TARGET)
    logger.info("磁盘扫描完成: %d 个源文件", len(disk_files))
    ver_text = VERSIONS_PATH.read_text(encoding="utf-8")
    logger.info("读取 versions.md (%d 字节)", VERSIONS_PATH.stat().st_size)
    registered = parse_versions_md(ver_text)
    logger.info("解析 versions.md: 获得 %d 个已登记条目", len(registered))

    print(f"   磁盘文件数: {len(disk_files)}")
    print(f"   已登记条目: {len(registered)}")

    # 找未登记
    unregistered = find_unregistered(disk_files, registered)
    print(f"\n── 待补登文件: {len(unregistered)}")

    if not unregistered:
        logger.info("全部已登记，无需补登")
        print("   ✅ 全部已登记，无需补登")
        return

    for f in unregistered:
        print(f"   ➕ {f}")

    if args.apply:
        logger.info(">>> 执行补登模式 <<<")
        logger.info("  待补登条目: %d 个", len(unregistered))
        print(f"\n🔧 执行补登 (日期: {args.date})...")
        new_entries = generate_entries(unregistered, args.date)
        logger.info("生成 %d 条新表格行", len(new_entries))
        new_content = apply_registration(VERSIONS_PATH, new_entries)
        VERSIONS_PATH.write_text(new_content, encoding="utf-8")
        logger.info("已写入 versions.md (%d 字节)", len(new_content))
        print(f"   ✅ 已补登 {len(unregistered)} 个文件到 versions.md")
        print(f"\n💡 运行 fix_versions_refs.py --dry-run 验证一致性")
    else:
        logger.info(">>> dry-run 模式，不修改文件 <<<")
        print(f"\n💡 运行 --apply 以执行补登")

    logger.info("auto_register_versions 完成")


if __name__ == "__main__":
    main()