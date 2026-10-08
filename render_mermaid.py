#!/usr/bin/env python3
"""
render_mermaid.py
自动解析 Markdown 文件中的 Mermaid 代码块并渲染为 PNG 图片。

依赖:
  - 方案 A (推荐): 安装 mermaid-cli → npm install -g @mermaid-js/mermaid-cli
  - 方案 B (备用): 用 Python 将 Mermaid 代码转为 HTML，通过无头浏览器截图

用法:
  # 渲染所有 Mermaid 代码块
  python render_mermaid.py doc_alignment_architecture.md --output-dir renders/

  # 只渲染指定索引的代码块（从 1 开始）
  python render_mermaid.py doc_alignment_architecture.md --index 1

  # 指定方案（auto / mmdc / playwright）
  python render_mermaid.py doc_alignment_architecture.md --method mmdc

输出:
  renders/
    ├── 01_完整依赖关系图.png
    ├── 02_分层架构视图.png
    └── 03_数据流向图.png

版本: v0.1 (2026-07-22)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_mermaid_blocks(md_path: Path) -> list:
    """从 Markdown 文件中提取所有 ```mermaid 代码块。返回 (caption, code) 列表。"""
    content = md_path.read_text(encoding="utf-8")
    blocks = []
    # 匹配 ```mermaid ... ``` （含可选标题注释）
    pattern = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)
    for match in pattern.finditer(content):
        code = match.group(1).strip()
        # 查找该代码块前面的标题
        before = content[:match.start()]
        title_match = re.findall(r'^#{1,3}\s+(.+?)$', before, re.MULTILINE)
        caption = title_match[-1].strip() if title_match else "mermaid-diagram"
        blocks.append((caption, code))
    return blocks


def render_mmdc(code: str, output_path: Path, scale: int = 2) -> bool:
    """使用 mermaid-cli (mmdc) 渲染。"""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return False

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_mmd = f.name

    try:
        result = subprocess.run(
            [mmdc, "-i", tmp_mmd, "-o", str(output_path),
             "-s", str(scale), "-b", "transparent"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    finally:
        os.unlink(tmp_mmd)


def render_playwright(code: str, output_path: Path, scale: int = 2) -> bool:
    """使用 Playwright 无头浏览器渲染（备用方案）。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script>
<style>body{{background:white;padding:20px;}}</style>
</head><body><pre class="mermaid">{code}</pre></body></html>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp_html = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(f"file:///{tmp_html}")
            page.wait_for_selector("svg", timeout=10000)
            page.wait_for_timeout(1000)
            svg = page.query_selector("svg")
            if svg:
                bbox = svg.bounding_box()
                if bbox:
                    page.set_viewport_size({
                        "width": int(bbox["width"] * scale) + 40,
                        "height": int(bbox["height"] * scale) + 40,
                    })
                svg.screenshot(path=str(output_path), scale="css")
            browser.close()
        return True
    except Exception as e:
        print(f"  ⚠️ Playwright 渲染失败: {e}", file=sys.stderr)
        return False
    finally:
        os.unlink(tmp_html)


def render_mermaid_inline(code: str, output_path: Path) -> bool:
    """
    使用 Mermaid Ink API 渲染（在线方案，无需本地安装）。
    https://mermaid.ink/
    """
    import urllib.request
    import base64
    import zlib

    # 压缩 + base64 编码 Mermaid 代码
    compressed = base64.urlsafe_b64encode(
        zlib.compress(code.encode("utf-8"), 9)
    ).decode("ascii")

    url = f"https://mermaid.ink/img/pako:{compressed}?type=png"
    try:
        urllib.request.urlretrieve(url, str(output_path))
        return True
    except Exception as e:
        print(f"  ⚠️ Mermaid Ink API 失败: {e}", file=sys.stderr)
        return False


def main():
    p = argparse.ArgumentParser(description="Mermaid → PNG 渲染器")
    p.add_argument("markdown", help="Markdown 文件路径")
    p.add_argument("--output-dir", "-o", default="renders", help="PNG 输出目录 (默认 renders/)")
    p.add_argument("--index", "-i", type=int, default=None, help="只渲染指定索引的代码块 (1-based)")
    p.add_argument("--method", "-m", choices=["auto", "mmdc", "playwright", "mermaid_ink"],
                   default="auto", help="渲染方法 (默认 auto: 依次尝试 mmdc → playwright → mermaid_ink)")
    p.add_argument("--scale", "-s", type=int, default=2, help="缩放系数 (默认 2)")
    args = p.parse_args()

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}", file=sys.stderr)
        sys.exit(1)

    blocks = extract_mermaid_blocks(md_path)
    if not blocks:
        print("❌ 未找到 Mermaid 代码块", file=sys.stderr)
        sys.exit(1)

    print(f"📄 源文件: {md_path.name}")
    print(f"   找到 {len(blocks)} 个 Mermaid 代码块\n")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = enumerate(blocks, 1)
    if args.index is not None:
        selected = [(args.index, blocks[args.index - 1])] if 1 <= args.index <= len(blocks) else []
        if not selected:
            print(f"❌ 索引 {args.index} 超出范围 (1–{len(blocks)})", file=sys.stderr)
            sys.exit(1)

    methods = [args.method] if args.method != "auto" else ["mmdc", "playwright", "mermaid_ink"]
    success = 0

    for i, (caption, code) in selected:
        safe_name = re.sub(r'[\\/*?:"<>|]', "", caption)[:40]
        output_path = output_dir / f"{i:02d}_{safe_name}.png"
        print(f"  [{i}/{len(blocks)}] {caption}")

        ok = False
        for method in methods:
            print(f"    尝试 {method} ...", end=" ")
            if method == "mmdc":
                ok = render_mmdc(code, output_path, args.scale)
            elif method == "playwright":
                ok = render_playwright(code, output_path, args.scale)
            elif method == "mermaid_ink":
                ok = render_mermaid_inline(code, output_path)
            if ok:
                print("✅")
                break
            else:
                print("❌")

        if ok:
            success += 1
            size_kb = output_path.stat().st_size / 1024
            print(f"    → {output_path.name} ({size_kb:.1f} KB)")
        else:
            print(f"    ❌ 所有方法均失败", file=sys.stderr)

    print(f"\n{'='*50}")
    print(f"渲染完成: {success}/{len(blocks)} 成功")
    if success:
        print(f"输出目录: {output_dir.resolve()}")


if __name__ == "__main__":
    main()