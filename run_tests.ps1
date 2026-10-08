# run_tests.ps1
# peg_trace.py 单元测试 PowerShell 包装脚本
# 修复: PowerShell 控制台默认用 GBK 解码 UTF-8 字节流导致中文乱码。
#
# 用法:
#   .\run_tests.ps1                    # 跑 test_peg_trace.py 全部测试
#   .\run_tests.ps1 -Verbose           # 详细模式
#   .\run_tests.ps1 -File test_xxx.py  # 跑其他测试文件
#
# 编码修复三层（缺一不可）:
#   1. 脚本文件本身保存为 UTF-8 with BOM（让 PS 5.x 用 UTF-8 解码脚本字面量）
#   2. 脚本开头 chcp 65001 + [Console]::OutputEncoding=UTF8（控制台解码 UTF-8）
#   3. 子进程设 PYTHONIOENCODING=utf-8（Python 输出 UTF-8 字节）
#
# 回滚: 关闭当前 PowerShell 窗口再开新窗口即恢复默认 GBK。

param(
    [string]$File = "test_peg_trace.py",
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# ---- 切到脚本所在目录 ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ---- 编码修复（第 2 层: 控制台解码 UTF-8）----
# 必须在 Write-Host 中文之前执行，否则中文仍乱码
try {
    chcp 65001 | Out-Null
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    Write-Warning "UTF-8 代码页切换失败: $_"
}

# ---- 环境变量（第 3 层: 子进程 Python 用 UTF-8 输出）----
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Write-Host "=== 测试运行环境 ===" -ForegroundColor Cyan
Write-Host "  测试文件: $File"
Write-Host "  PYTHONIOENCODING: $env:PYTHONIOENCODING"
Write-Host "  控制台代码页: $(chcp)"
Write-Host "  Console.OutputEncoding: $([Console]::OutputEncoding.WebName)"
Write-Host ""

# ---- 跑测试（直接用 PowerShell 跑，不再绕道 cmd.exe）----
# 因为脚本已 UTF-8 BOM + Console.OutputEncoding 已 UTF-8，三层修复完整
if ($Verbose) {
    python -m unittest $File -v
} else {
    python -m unittest $File
}

$exitCode = $LASTEXITCODE
Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "=== 全部测试通过 (exit=$exitCode) ===" -ForegroundColor Green
} else {
    Write-Host "=== 测试失败 (exit=$exitCode) ===" -ForegroundColor Red
}
exit $exitCode
