#!/usr/bin/env bash
# ============================================================
#   registry_tools — 上传到内部 PyPI (Artifactory)
# ============================================================
#
# 使用前请先配置 ~/.pypirc，参考同目录下的 pypirc_template
#
# 方式一：使用 .pypirc 配置文件
#   cp pypirc_template ~/.pypirc
#   # 编辑 ~/.pypirc，填入实际的 Artifactory URL 和凭据
#   ./upload_to_pypi.sh
#
# 方式二：使用环境变量
#   export TWINE_REPOSITORY_URL="https://artifactory.YOUR-COMPANY.com/artifactory/api/pypi/pypi-local"
#   export TWINE_USERNAME="your-username"
#   export TWINE_PASSWORD="your-api-key"
#   ./upload_to_pypi.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEEL_FILE=$(ls "$SCRIPT_DIR/dist"/registry_tools-*.whl 2>/dev/null | head -1)

if [ -z "${WHEEL_FILE:-}" ]; then
    echo "❌ 未找到 wheel 文件，请先运行: python -m build --wheel"
    exit 1
fi

echo "============================================================"
echo "  上传 registry_tools 到内部 PyPI (Artifactory)"
echo "============================================================"
echo ""
echo "  Wheel: $(basename "$WHEEL_FILE")"
echo ""

# 检测仓库配置
if [ -n "${TWINE_REPOSITORY_URL:-}" ]; then
    echo "  使用环境变量 TWINE_REPOSITORY_URL"
    REPO_FLAG="--repository-url ${TWINE_REPOSITORY_URL}"
elif grep -q "internal" ~/.pypirc 2>/dev/null; then
    echo "  使用 ~/.pypirc [internal] 配置"
    REPO_FLAG="--repository internal"
else
    echo "  ⚠️  未检测到仓库配置"
    echo ""
    echo "  请先配置上传目标："
    echo "    方式一: cp pypirc_template ~/.pypirc 并编辑"
    echo "    方式二: export TWINE_REPOSITORY_URL=..."
    exit 1
fi

echo ""

# 检查 twine
if ! python -c "import twine" 2>/dev/null; then
    echo "📦 安装 twine..."
    python -m pip install twine --quiet
fi

# 上传
echo "🚀 上传中..."
python -m twine upload \
    ${REPO_FLAG} \
    --non-interactive \
    "$WHEEL_FILE"

echo ""
echo "✅ 上传完成"
echo ""
echo "💡 团队成员安装命令:"
echo "   pip install registry_tools --index-url <内部 PyPI URL>"