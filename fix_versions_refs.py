#!/usr/bin/env python3
"""
fix_versions_refs.py
自动修复 versions.md 中登记的文件引用与实际磁盘文件不一致的问题。

基于迁移扫描报告的 3 个失败项:
  3.2: 目录树文件数不一致
  3.4: 虚假条目（目录树中登记但磁盘上不存在）
  3.5: 目录树遗漏（磁盘上存在但目录树未登记）

模式:
  --dry-run  仅报告差异，不修改文件
  --fix      自动修复 workspace_map.md 和 versions.md

用法:
  python fix_versions_refs.py --dry-run              # 报告差异
  python fix_versions_refs.py --fix                  # 修复
  python fix_versions_refs.py --fix --target <dir>   # 指定目标目录

版本: v0.1 (2026-07-28)
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── 日志 ──────────────────────────────────────────────
logger = logging.getLogger("fix_versions_refs")

# ├──和└──用于解析目录树
TREE_PREFIX = re.compile(r'^(\s*)([├└]──)\s+(.+)$')
# 提取文件名（不含注释）
FILE_IN_TREE = re.compile(r'([\w.+-]+(?:\.\w+)?)')


def parse_workspace_map(text: str) -> list:
    """解析 workspace_map.md 目录树，返回 [(行号, 缩进, 文件名), ...]"""
    entries = []
    for i, line in enumerate(text.splitlines(), 1):
        m = TREE_PREFIX.match(line)
        if m:
            indent = len(m.group(1))
            name = m.group(3).strip()
            # 提取纯文件名（去掉 # 注释）
            fname = name.split("#")[0].strip()
            # 提取可用的文件名部分
            fm = FILE_IN_TREE.match(fname)
            if fm:
                fname = fm.group(1)
            entries.append((i, indent, fname, line.rstrip()))
    return entries


def parse_versions_md(text: str) -> list:
    """解析 versions.md「工程化产物」表格，返回 [(文件名, 行号), ...]
    
    注意：versions.md 包含三张表——
      1. PEG-A 自身提示词（版本 | 日期 | 变更 | 状态）
      2. 工程化产物（文件 | 版本 | 日期 | 备注）← 只解析这张
      3. 弃用记录（项 | 弃用版本 | 替代 | 过渡期）
    仅解析「工程化产物」表，避免将版本号、弃用项误判为文件名。
    """
    entries = []
    in_target_table = False
    for i, line in enumerate(text.splitlines(), 1):
        # 检测「工程化产物」表头
        if line.startswith("| 文件 | 版本 | 日期 | 备注 |"):
            in_target_table = True
            continue
        # 遇到下一个 ## 标题或表头，退出目标表
        if in_target_table and (line.startswith("## ") or line.startswith("| 项 |") or line.startswith("| 版本 |")):
            break
        if in_target_table and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                fname = parts[1]
                # 去掉反引号
                fname = fname.strip("`").strip()
                if fname and not fname.startswith("文件") and not fname.startswith("---"):
                    entries.append((fname, i))
    return entries


def list_disk_files(target: Path) -> set:
    """列出磁盘上的所有源文件（排除运行时产物和 VCS）"""
    files = set()
    exclude_dirs = {
        "__pycache__", ".pytest_cache", "node_modules",
        ".obsidian", "dist", "build",
    }
    exclude_suffixes = {".egg-info", ".dist-info"}
    exclude_patterns = {
        ".pyc", ".pyo", ".egg", ".whl",
    }
    for f in target.rglob("*"):
        if f.is_file():
            parts = f.parts
            skip = False
            for p in parts:
                # 排除明确的非源码目录
                if p in exclude_dirs:
                    skip = True
                    break
                # 排除 .egg-info 等构建产物目录
                if any(p.endswith(s) for s in exclude_suffixes):
                    skip = True
                    break
                # .git 内部所有内容排除，但 .github/ 保留（CI 配置是源文件）
                if p == ".git":
                    skip = True
                    break
                # 排除隐藏目录（.obsidian 等），但保留 .github
                if p.startswith(".") and p not in (".gitignore", ".github", ".git"):
                    skip = True
                    break
            if skip:
                continue
            # 排除扩展名
            if f.suffix in exclude_patterns:
                continue
            # 排除临时文件
            if f.name.startswith("_") and f.name.endswith(".py"):
                continue
            rel = f.relative_to(target)
            files.add(str(rel).replace("\\", "/"))
    return files


def find_phantom_entries(tree_entries: list, disk_files: set, target: Path) -> list:
    """找出目录树中登记但磁盘上不存在的文件（虚假条目）"""
    phantom = []
    for line_no, indent, fname, raw in tree_entries:
        # 跳过目录标记（以 / 结尾的）
        if fname.endswith("/"):
            continue
        # 检查磁盘存在性
        found = False
        for df in disk_files:
            if df.endswith(fname) or fname == os.path.basename(df):
                found = True
                break
        if not found and len(fname) > 2:
            phantom.append((line_no, fname, raw))
    return phantom


def find_missing_files(tree_entries: list, disk_files: set, target: Path) -> list:
    """找出磁盘上存在但目录树中未登记的文件"""
    tree_names = set()
    for _, _, fname, _ in tree_entries:
        if not fname.endswith("/"):
            tree_names.add(fname)

    missing = []
    for df in sorted(disk_files):
        basename = os.path.basename(df)
        # 检查是否在目录树中
        if basename not in tree_names and df.split("/")[-1] not in tree_names:
            # 排除明确不应登记的
            if basename in (".gitignore", "README.md", "pyproject.toml"):
                missing.append(df)
            elif not df.startswith("."):
                missing.append(df)
    return missing


def fix_workspace_map(ws_path: Path, phantom: list, missing: list, target: Path) -> str:
    """修复 workspace_map.md"""
    content = ws_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 移除虚假条目
    phantom_lines = {pl[0] for pl in phantom}
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i not in phantom_lines:
            new_lines.append(line)

    # 添加遗漏文件到末尾
    if missing:
        new_lines.append("")
        new_lines.append(f"<!-- 自动补登 ({datetime.now().strftime('%Y-%m-%d')}) -->")
        for mf in sorted(missing):
            basename = os.path.basename(mf)
            new_lines.append(f"├── {basename}  # 自动补登: {mf}")

    return "\n".join(new_lines)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    p = argparse.ArgumentParser(description="修复 versions.md / workspace_map.md 文件引用一致性")
    p.add_argument("--target", "-t", default=None, help="目标目录 (默认: 脚本所在目录的上级 meta_peg_agent/)")
    p.add_argument("--dry-run", action="store_true", default=True, help="仅报告差异，不修改 (默认)")
    p.add_argument("--fix", action="store_true", help="自动修复")
    args = p.parse_args()

    if args.target:
        target = Path(args.target)
    else:
        target = Path(__file__).resolve().parent

    ws_path = target / "workspace_map.md"
    ver_path = target / "versions.md"

    # ── 启动日志 ──
    logger.info("=" * 60)
    logger.info("fix_versions_refs 启动")
    logger.info("  目标目录: %s", target)
    logger.info("  workspace_map.md: %s (存在=%s)", ws_path, ws_path.exists())
    logger.info("  versions.md: %s (存在=%s)", ver_path, ver_path.exists())
    logger.info("  模式: %s", "dry-run" if not args.fix else "fix")

    if not ws_path.exists():
        logger.error("workspace_map.md 不存在: %s", ws_path)
        print(f"❌ workspace_map.md 不存在: {ws_path}")
        sys.exit(1)
    if not ver_path.exists():
        logger.error("versions.md 不存在: %s", ver_path)
        print(f"❌ versions.md 不存在: {ver_path}")
        sys.exit(1)

    print(f"🔍 扫描目标: {target}")
    print(f"   workspace_map.md: {ws_path}")
    print(f"   versions.md: {ver_path}\n")

    # ── 读取文件 ──
    logger.info("读取 workspace_map.md (%d 字节)", ws_path.stat().st_size)
    ws_text = ws_path.read_text(encoding="utf-8")
    logger.info("读取 versions.md (%d 字节)", ver_path.stat().st_size)
    ver_text = ver_path.read_text(encoding="utf-8")

    # ── 解析 ──
    tree_entries = parse_workspace_map(ws_text)
    logger.info("解析 workspace_map: 获得 %d 个目录树条目", len(tree_entries))

    ver_entries = parse_versions_md(ver_text)
    logger.info("解析 versions.md「工程化产物」表: 获得 %d 个条目", len(ver_entries))

    # ── 磁盘扫描 ──
    disk_files = list_disk_files(target)
    logger.info("扫描磁盘文件: 共发现 %d 个源文件", len(disk_files))

    print(f"   目录树条目: {len(tree_entries)}")
    print(f"   versions.md 条目: {len(ver_entries)}")
    print(f"   磁盘文件数: {len(disk_files)}")

    # ── 3.4 虚假条目 ──
    phantom = find_phantom_entries(tree_entries, disk_files, target)
    logger.info("检测虚假条目 (3.4): 共 %d 个", len(phantom))
    print(f"\n── 3.4 虚假条目（目录树登记但磁盘不存在）: {len(phantom)}")
    if phantom:
        for line_no, fname, raw in phantom:
            logger.info("  虚假条目 L%d: %s", line_no, fname)
        for line_no, fname, raw in phantom[:10]:
            print(f"   L{line_no}: {fname}")
        if len(phantom) > 10:
            print(f"   ... 还有 {len(phantom) - 10} 条")

    # ── 3.5 遗漏文件 ──
    missing = find_missing_files(tree_entries, disk_files, target)
    logger.info("检测遗漏文件 (3.5): 共 %d 个", len(missing))
    print(f"\n── 3.5 遗漏文件（磁盘存在但目录树未登记）: {len(missing)}")
    if missing:
        for mf in missing:
            logger.info("  遗漏文件: %s", mf)
        for mf in missing[:15]:
            print(f"   {mf}")
        if len(missing) > 15:
            print(f"   ... 还有 {len(missing) - 15} 条")

    # ── versions.md 引用检查 ──
    ver_entries_dict = {e[0]: e[1] for e in ver_entries}
    logger.info("versions.md 引用检查: 已登记条目字典 %d 项", len(ver_entries_dict))

    ver_missing = []
    for vname, vline in ver_entries_dict.items():
        if vname.endswith("/"):
            dir_path = target / vname.rstrip("/")
            if not dir_path.is_dir():
                logger.info("  登记目录不存在: %s", vname)
                ver_missing.append(vname)
        else:
            if vname not in disk_files:
                basename = os.path.basename(vname)
                found = any(df.endswith("/" + basename) or df == basename for df in disk_files)
                if not found:
                    logger.info("  登记文件不存在于磁盘: %s (basename=%s)", vname, basename)
                    ver_missing.append(vname)

    ver_unregistered = []
    for df in sorted(disk_files):
        basename = os.path.basename(df)
        if df not in ver_entries_dict and basename not in ver_entries_dict:
            logger.info("  磁盘文件未登记: %s", df)
            ver_unregistered.append(df)

    logger.info("versions.md 引用检查结果: 登记但不存在=%d, 存在但未登记=%d",
                len(ver_missing), len(ver_unregistered))

    print(f"\n── versions.md 引用检查:")
    print(f"   登记但磁盘不存在: {len(ver_missing)}")
    if ver_missing:
        for vm in sorted(ver_missing)[:10]:
            print(f"   ❌ {vm}")
    print(f"   磁盘存在但未登记: {len(ver_unregistered)}")
    if ver_unregistered:
        for vu in sorted(ver_unregistered)[:10]:
            print(f"   ⚠️ {vu}")

    # ── 修复 ──
    if args.fix:
        logger.info(">>> 执行修复模式 <<<")
        logger.info("  移除虚假条目: %d 个, 添加遗漏文件: %d 个", len(phantom), len(missing))
        print(f"\n🔧 执行修复...")
        new_ws = fix_workspace_map(ws_path, phantom, missing, target)
        ws_path.write_text(new_ws, encoding="utf-8")
        logger.info("  已写入 workspace_map.md (%d 字节)", len(new_ws))
        print(f"   ✅ workspace_map.md 已修复（移除 {len(phantom)} 虚假, 添加 {len(missing)} 遗漏）")
    else:
        logger.info(">>> dry-run 模式，不修改文件 <<<")
        print(f"\n💡 运行 --fix 以自动修复上述问题")

    logger.info("fix_versions_refs 完成")
    print(f"\n✅ 扫描完成")


if __name__ == "__main__":
    main()