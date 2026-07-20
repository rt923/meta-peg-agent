#!/usr/bin/env python3
# test_readonly_windows.py
# Windows 只读属性检测/设置修复验证脚本
# 验证 guardrails_enforce.py 中 is_readonly() / set_readonly() 是否正确工作
#
# 运行方式: python test_readonly_windows.py
# 退出码: 0=全部通过, 1=存在失败

import os
import sys
import tempfile
import shutil
import stat

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from guardrails_enforce import is_readonly, set_readonly

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# Test 1: set_readonly(True) 后 is_readonly() 返回 True
# ============================================================
section("Test 1: set_readonly(True) -> is_readonly()=True")

tmpdir = tempfile.mkdtemp(prefix="readonly_test_")
fpath = os.path.join(tmpdir, "test1.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("hello")

set_readonly(fpath, True)
test("is_readonly returns True after set_readonly(True)",
     is_readonly(fpath),
     f"got is_readonly={is_readonly(fpath)}")

# PowerShell 层面交叉验证
import subprocess
ret = subprocess.run(
    ["powershell", "-Command", f"(Get-Item '{fpath}').IsReadOnly"],
    capture_output=True, text=True
)
ps_readonly = ret.stdout.strip().lower() == "true"
test("PowerShell Get-Item IsReadOnly = True",
     ps_readonly,
     f"powershell output: {ret.stdout.strip()}")

# 清理
set_readonly(fpath, False)
os.remove(fpath)


# ============================================================
# Test 2: set_readonly(False) 后 is_readonly() 返回 False
# ============================================================
section("Test 2: set_readonly(False) -> is_readonly()=False")

fpath = os.path.join(tmpdir, "test2.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("hello")

# 先设为只读，再解除
set_readonly(fpath, True)
set_readonly(fpath, False)
test("is_readonly returns False after set_readonly(False)",
     not is_readonly(fpath),
     f"got is_readonly={is_readonly(fpath)}")

ret = subprocess.run(
    ["powershell", "-Command", f"(Get-Item '{fpath}').IsReadOnly"],
    capture_output=True, text=True
)
ps_readonly = ret.stdout.strip().lower() == "true"
test("PowerShell Get-Item IsReadOnly = False",
     not ps_readonly,
     f"powershell output: {ret.stdout.strip()}")

os.remove(fpath)


# ============================================================
# Test 3: 只读文件不可写入 (OS 层强制)
# ============================================================
section("Test 3: readonly file rejects write (OS enforced)")

fpath = os.path.join(tmpdir, "test3.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("original")

set_readonly(fpath, True)

write_blocked = False
try:
    with open(fpath, "a", encoding="utf-8") as f:
        f.write("appended")
except PermissionError:
    write_blocked = True

test("write to readonly file raises PermissionError",
     write_blocked,
     "file was writable despite readonly=True")

# 验证内容未被修改
with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()
test("file content unchanged after blocked write",
     content == "original",
     f"content={content!r}")

set_readonly(fpath, False)
os.remove(fpath)


# ============================================================
# Test 4: 重复 set_readonly(True) 幂等性
# ============================================================
section("Test 4: repeated set_readonly(True) is idempotent")

fpath = os.path.join(tmpdir, "test4.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("hello")

set_readonly(fpath, True)
set_readonly(fpath, True)
set_readonly(fpath, True)
test("is_readonly still True after 3x set_readonly(True)",
     is_readonly(fpath))

set_readonly(fpath, False)
os.remove(fpath)


# ============================================================
# Test 5: set_readonly(False) 后文件可写入
# ============================================================
section("Test 5: file writable after set_readonly(False)")

fpath = os.path.join(tmpdir, "test5.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("original")

set_readonly(fpath, True)
set_readonly(fpath, False)

write_ok = False
try:
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(" appended")
    write_ok = True
except PermissionError:
    pass

test("write succeeds after set_readonly(False)",
     write_ok,
     "file still read-only after set_readonly(False)")

with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()
test("appended content is present",
     content == "original appended",
     f"content={content!r}")

os.remove(fpath)


# ============================================================
# Test 6: 不存在的文件 is_readonly 返回 False
# ============================================================
section("Test 6: is_readonly on nonexistent file returns False")

fake_path = os.path.join(tmpdir, "nonexistent.txt")
test("is_readonly returns False for nonexistent file",
     not is_readonly(fake_path),
     f"got is_readonly={is_readonly(fake_path)}")


# ============================================================
# Test 7: 对比旧方法 os.chmod vs 新方法 ctypes
# ============================================================
section("Test 7: ctypes vs os.chmod cross-validation")

fpath = os.path.join(tmpdir, "test7.txt")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("hello")

# os.chmod 设只读
os.chmod(fpath, stat.S_IREAD)

old_method = not bool(os.stat(fpath).st_mode & stat.S_IWRITE)
new_method = is_readonly(fpath)

test("os.chmod(S_IREAD) -> os.stat reports readonly",
     old_method,
     f"old_method={old_method}")
test("os.chmod(S_IREAD) -> ctypes detects readonly",
     new_method,
     f"new_method={new_method} (expected False on Windows)")

# set_readonly 设只读
os.chmod(fpath, stat.S_IREAD | stat.S_IWRITE)  # 先清除 os.chmod 的效果
set_readonly(fpath, True)

old_method2 = not bool(os.stat(fpath).st_mode & stat.S_IWRITE)
new_method2 = is_readonly(fpath)

test("set_readonly(True) -> os.stat reports readonly",
     old_method2,
     f"old_method={old_method2}")
test("set_readonly(True) -> ctypes detects readonly",
     new_method2,
     f"new_method={new_method2} (expected True)")

set_readonly(fpath, False)
os.remove(fpath)


# ============================================================
# Test 8: guardrails_enforce.py verify 端到端
# ============================================================
section("Test 8: guardrails_enforce.py verify end-to-end")

import subprocess

# 先 protect
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "protect"],
    capture_output=True, text=True,
    env={**os.environ, "GUARDRAIL_TOKEN": "test"}
)
test("protect returns 0",
     ret.returncode == 0,
     f"exit={ret.returncode}, stderr={ret.stderr.strip()}")

# verify
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "verify"],
    capture_output=True, text=True
)
test("verify returns 0",
     ret.returncode == 0,
     f"exit={ret.returncode}")
test("verify output contains 'readonly = True'",
     "readonly    = True" in ret.stdout or "readonly = True" in ret.stdout,
     f"stdout={ret.stdout.strip()}")
test("verify output contains 'RESULT = OK'",
     "RESULT      = OK" in ret.stdout or "RESULT = OK" in ret.stdout,
     f"stdout={ret.stdout.strip()}")


# ============================================================
# Test 9: unlock -> verify FAIL -> protect -> verify OK
# ============================================================
section("Test 9: unlock/protect/verify cycle")

# unlock
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "unlock",
     os.path.join(HERE, "phase0_meta_peg_agent_prompt.md")],
    capture_output=True, text=True,
    env={**os.environ, "GUARDRAIL_TOKEN": "test"}
)
test("unlock returns 0",
     ret.returncode == 0,
     f"exit={ret.returncode}, stderr={ret.stderr.strip()}")

# verify should fail (readonly=False)
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "verify"],
    capture_output=True, text=True
)
test("verify returns 1 after unlock",
     ret.returncode == 1,
     f"exit={ret.returncode}")
test("verify reports 'readonly = False' after unlock",
     "readonly    = False" in ret.stdout or "readonly = False" in ret.stdout,
     f"stdout={ret.stdout.strip()}")

# protect
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "protect"],
    capture_output=True, text=True,
    env={**os.environ, "GUARDRAIL_TOKEN": "test"}
)
test("protect returns 0",
     ret.returncode == 0)

# verify should pass
ret = subprocess.run(
    [sys.executable, os.path.join(HERE, "guardrails_enforce.py"), "verify"],
    capture_output=True, text=True
)
test("verify returns 0 after protect",
     ret.returncode == 0,
     f"exit={ret.returncode}")
test("verify reports 'RESULT = OK' after protect",
     "OK" in ret.stdout,
     f"stdout={ret.stdout.strip()}")


# ============================================================
# Cleanup
# ============================================================
shutil.rmtree(tmpdir, ignore_errors=True)

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*60}")
print(f"  SUMMARY: {passed} passed, {failed} failed")
print(f"{'='*60}")

if failed > 0:
    print(f"\n  {failed} test(s) FAILED")
    sys.exit(1)
else:
    print(f"\n  All {passed} tests PASSED")
    sys.exit(0)
