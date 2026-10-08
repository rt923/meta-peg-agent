@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM   registry_tools — 上传到内部 PyPI (Artifactory)
REM ============================================================
REM
REM 使用前请先配置 %%USERPROFILE%%\.pypirc，参考同目录下的 pypirc_template

set SCRIPT_DIR=%~dp0
for %%f in ("%SCRIPT_DIR%dist\registry_tools-*.whl") do set WHEEL_FILE=%%f

if not defined WHEEL_FILE (
    echo ❌ 未找到 wheel 文件，请先运行: python -m build --wheel
    exit /b 1
)

echo ============================================================
echo   上传 registry_tools 到内部 PyPI ^(Artifactory^)
echo ============================================================
echo.
echo   Wheel: %WHEEL_FILE%
echo.

REM 检测仓库配置
if defined TWINE_REPOSITORY_URL (
    echo   使用环境变量 TWINE_REPOSITORY_URL
    set REPO_FLAG=--repository-url %TWINE_REPOSITORY_URL%
) else if exist "%USERPROFILE%\.pypirc" (
    echo   使用 %%USERPROFILE%%\.pypirc [internal] 配置
    set REPO_FLAG=--repository internal
) else (
    echo   ⚠️  未检测到仓库配置
    echo.
    echo   请先配置上传目标：
    echo     方式一: copy pypirc_template %%USERPROFILE%%\.pypirc 并编辑
    echo     方式二: set TWINE_REPOSITORY_URL=...
    exit /b 1
)

echo.

REM 检查 twine
python -c "import twine" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 📦 安装 twine...
    python -m pip install twine --quiet
)

REM 上传
echo 🚀 上传中...
python -m twine upload %REPO_FLAG% --non-interactive "%WHEEL_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 上传失败
    exit /b 1
)

echo.
echo ✅ 上传完成
echo.
echo 💡 团队成员安装命令:
echo    pip install registry_tools --index-url ^<内部 PyPI URL^>

pause