#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_mermaid_renderer.py
一键安装脚本：自动检测环境并安装 render_mermaid.py 所需的缺失依赖。

支持三种渲染方案（按优先级降级）:
  方案 A: mmdc (mermaid-cli) — npm install -g @mermaid-js/mermaid-cli
  方案 B: playwright — pip install playwright && playwright install chromium
  方案 C: mermaid_ink — 在线 API，无需本地安装（但可能被墙）

用法:
  python install_mermaid_renderer.py            # 自动检测并安装
  python install_mermaid_renderer.py --method mmdc  # 强制安装指定方案
  python install_mermaid_renderer.py --check-only   # 仅检查，不安装

版本: v0.1 (2026-07-28)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def check_command(cmd: str) -> bool:
    """检查命令是否可用"""
    return shutil.which(cmd) is not None


def check_python_module(module: str) -> bool:
    """检查 Python 模块是否已安装"""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def check_node() -> bool:
    """检查 Node.js 是否可用"""
    if not check_command("node"):
        return False
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def check_npm() -> bool:
    """检查 npm 是否可用"""
    return check_command("npm")


def check_mmdc() -> bool:
    """检查 mermaid-cli (mmdc) 是否可用"""
    return check_command("mmdc")


def check_playwright() -> bool:
    """检查 Playwright 是否可用"""
    if not check_python_module("playwright"):
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch()
            return True
    except Exception:
        return False


def check_mermaid_ink() -> bool:
    """检查 Mermaid Ink API 是否可达"""
    import urllib.request
    try:
        req = urllib.request.Request("https://mermaid.ink/", method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def install_mmdc() -> bool:
    """安装 mermaid-cli"""
    if not check_node():
        print("  ❌ Node.js 未安装，无法安装 mmdc")
        print("     请先安装 Node.js: https://nodejs.org/")
        return False
    if not check_npm():
        print("  ❌ npm 未找到")
        return False

    print("  📦 npm install -g @mermaid-js/mermaid-cli ...")
    try:
        result = subprocess.run(
            ["npm", "install", "-g", "@mermaid-js/mermaid-cli"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  ✅ mmdc 安装成功")
            return True
        else:
            print(f"  ❌ 安装失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ 安装异常: {e}")
        return False


def install_playwright() -> bool:
    """安装 Playwright + Chromium"""
    print("  📦 pip install playwright ...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "playwright"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        print("  ❌ pip install playwright 失败")
        return False

    print("  📦 playwright install chromium ...")
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True, check=True
        )
        print("  ✅ Playwright 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Chromium 安装失败: {e.stderr[:200] if e.stderr else '未知错误'}")
        print("     手动安装: playwright install chromium")
        return False


def render_test(method: str) -> bool:
    """用简单 Mermaid 图测试渲染是否正常"""
    test_mmd = "graph TD\n    A[Test] --> B[OK]"
    test_dir = Path(__file__).resolve().parent / "renders"
    test_dir.mkdir(exist_ok=True)
    test_path = test_dir / "_install_test.png"

    render_script = Path(__file__).resolve().parent / "render_mermaid.py"
    if not render_script.exists():
        # 用内联方式测试
        if method == "mmdc":
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
                f.write(test_mmd)
                tmp = f.name
            try:
                result = subprocess.run(
                    ["mmdc", "-i", tmp, "-o", str(test_path), "-s", "1"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
            finally:
                os.unlink(tmp)
        elif method == "playwright":
            try:
                from playwright.sync_api import sync_playwright
                html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script></head>
<body><pre class="mermaid">{test_mmd}</pre></body></html>"""
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.set_content(html)
                    page.wait_for_selector("svg", timeout=5000)
                    svg = page.query_selector("svg")
                    if svg:
                        svg.screenshot(path=str(test_path))
                    browser.close()
                return test_path.exists()
            except Exception:
                return False
        elif method == "mermaid_ink":
            import urllib.request
            import base64, zlib
            compressed = base64.urlsafe_b64encode(
                zlib.compress(test_mmd.encode("utf-8"), 9)
            ).decode("ascii")
            url = f"https://mermaid.ink/img/pako:{compressed}?type=png"
            try:
                urllib.request.urlretrieve(url, str(test_path))
                return test_path.exists()
            except Exception:
                return False
    return False


def main():
    p = argparse.ArgumentParser(description="render_mermaid.py 一键安装依赖")
    p.add_argument("--method", "-m", choices=["mmdc", "playwright", "mermaid_ink", "auto"],
                   default="auto", help="强制安装指定方案 (默认: auto)")
    p.add_argument("--check-only", action="store_true", help="仅检查环境，不安装")
    args = p.parse_args()

    print_header("Mermaid 渲染器依赖安装向导")

    # 环境检测
    print("\n📋 环境检测:")
    print(f"   Python:   {sys.version.split()[0]}")
    print(f"   Node.js:  {'✅' if check_node() else '❌ 未安装'}")
    print(f"   npm:      {'✅' if check_npm() else '❌ 未安装'}")
    print(f"   mmdc:     {'✅ 已安装' if check_mmdc() else '❌ 未安装'}")
    print(f"   playwright: {'✅ 已安装' if check_playwright() else '❌ 未安装'}")
    print(f"   mermaid_ink: {'✅ 可访问' if check_mermaid_ink() else '❌ 不可达'}")

    if args.check_only:
        print(f"\n💡 仅检查模式，不执行安装")
        return

    # 确定安装方案
    if args.method != "auto":
        methods = [args.method]
    else:
        methods = []
        if check_node() and check_npm():
            methods.append("mmdc")
        if True:  # Python 环境总是可用
            methods.append("playwright")
        methods.append("mermaid_ink")  # 在线 API 总是尝试

    print(f"\n🔧 安装方案: {' → '.join(methods)}")

    installed = False
    for method in methods:
        print_header(f"尝试方案: {method}")

        if method == "mmdc" and not check_mmdc():
            if args.method == "auto":
                print("  mmdc 未安装，正在安装...")
                installed = install_mmdc()
            else:
                installed = install_mmdc()
        elif method == "playwright" and not check_playwright():
            if args.method == "auto":
                print("  Playwright 未安装，正在安装...")
                installed = install_playwright()
            else:
                installed = install_playwright()
        elif method == "mermaid_ink":
            if check_mermaid_ink():
                print("  ✅ Mermaid Ink API 可用，无需本地安装")
                installed = True
            else:
                print("  ⚠️ Mermaid Ink API 不可达（可能被墙），跳过")
                continue
        else:
            print(f"  ✅ {method} 已安装")
            installed = True

        if installed:
            print(f"\n  🧪 测试渲染...")
            if render_test(method):
                print(f"  ✅ 渲染测试通过")
                break
            else:
                print(f"  ⚠️ 渲染测试失败，尝试下一个方案...")
                installed = False

    print_header("安装结果")
    if installed:
        print("✅ 安装成功！使用方法:")
        print(f"   python render_mermaid.py doc_alignment_architecture.md")
    else:
        print("❌ 所有方案安装失败")
        print("\n手动安装方案（任选其一）:")
        print("  方案 A: npm install -g @mermaid-js/mermaid-cli")
        print("  方案 B: pip install playwright && playwright install chromium")
        print("  方案 C: 无需安装，但需要 mermaid.ink 可访问（当前被墙）")

    print()


if __name__ == "__main__":
    main()