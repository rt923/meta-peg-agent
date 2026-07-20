#!/usr/bin/env python3
"""
test_guardrails_readonly.py
guardrails_enforce.py Windows 只读属性单元测试

覆盖范围:
  - is_readonly() 检测正确性 (ctypes GetFileAttributesW)
  - set_readonly() 设置/解除正确性 (ctypes SetFileAttributesW)
  - OS 层写入拦截 (PermissionError)
  - 幂等性、边界条件、交叉验证
  - guardrails_enforce.py protect/verify/unlock 端到端

运行方式:
  python -m pytest test_guardrails_readonly.py -v
  python test_guardrails_readonly.py           # 直接运行
"""

import os
import sys
import stat
import shutil
import tempfile
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from guardrails_enforce import is_readonly, set_readonly

IS_WIN = sys.platform == "win32"
GUARDRAILS = os.path.join(HERE, "guardrails_enforce.py")
PROTECTED_FILE = os.path.join(HERE, "phase0_meta_peg_agent_prompt.md")


def _run_guardrails(*args, token=None):
    env = {**os.environ}
    if token:
        env["GUARDRAIL_TOKEN"] = token
    return subprocess.run(
        [sys.executable, GUARDRAILS, *args],
        capture_output=True, text=True, env=env
    )


class TestIsReadonly(unittest.TestCase):
    """is_readonly() 单元测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gr_test_")
        self.fpath = os.path.join(self.tmpdir, "test.txt")
        with open(self.fpath, "w", encoding="utf-8") as f:
            f.write("hello")

    def tearDown(self):
        set_readonly(self.fpath, False)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_returns_true_after_set_readonly_true(self):
        """set_readonly(True) 后 is_readonly() 返回 True"""
        set_readonly(self.fpath, True)
        self.assertTrue(is_readonly(self.fpath))

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_returns_false_after_set_readonly_false(self):
        """set_readonly(False) 后 is_readonly() 返回 False"""
        set_readonly(self.fpath, True)
        set_readonly(self.fpath, False)
        self.assertFalse(is_readonly(self.fpath))

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_powershell_cross_validate_true(self):
        """PowerShell Get-Item IsReadOnly 交叉验证为 True"""
        set_readonly(self.fpath, True)
        ret = subprocess.run(
            ["powershell", "-Command",
             f"(Get-Item '{self.fpath}').IsReadOnly"],
            capture_output=True, text=True
        )
        self.assertIn("True", ret.stdout)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_powershell_cross_validate_false(self):
        """PowerShell Get-Item IsReadOnly 交叉验证为 False"""
        set_readonly(self.fpath, True)
        set_readonly(self.fpath, False)
        ret = subprocess.run(
            ["powershell", "-Command",
             f"(Get-Item '{self.fpath}').IsReadOnly"],
            capture_output=True, text=True
        )
        self.assertIn("False", ret.stdout)

    def test_nonexistent_file_returns_false(self):
        """不存在的文件返回 False (不抛异常)"""
        fake = os.path.join(self.tmpdir, "nonexistent.txt")
        self.assertFalse(is_readonly(fake))


class TestSetReadonly(unittest.TestCase):
    """set_readonly() 单元测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gr_test_")
        self.fpath = os.path.join(self.tmpdir, "test.txt")
        with open(self.fpath, "w", encoding="utf-8") as f:
            f.write("hello")

    def tearDown(self):
        set_readonly(self.fpath, False)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_idempotent_multiple_set_true(self):
        """3 次重复 set_readonly(True) 幂等"""
        set_readonly(self.fpath, True)
        set_readonly(self.fpath, True)
        set_readonly(self.fpath, True)
        self.assertTrue(is_readonly(self.fpath))

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_write_blocked_when_readonly(self):
        """只读文件写入触发 PermissionError"""
        set_readonly(self.fpath, True)
        with self.assertRaises(PermissionError):
            with open(self.fpath, "a", encoding="utf-8") as f:
                f.write("appended")

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_content_unchanged_after_blocked_write(self):
        """只读文件内容不被修改"""
        set_readonly(self.fpath, True)
        try:
            with open(self.fpath, "a", encoding="utf-8") as f:
                f.write("appended")
        except PermissionError:
            pass
        with open(self.fpath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "hello")

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_write_succeeds_after_unset_readonly(self):
        """解除只读后可正常追加写入"""
        set_readonly(self.fpath, True)
        set_readonly(self.fpath, False)
        with open(self.fpath, "a", encoding="utf-8") as f:
            f.write(" appended")
        with open(self.fpath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "hello appended")


class TestOsChmodCrossValidation(unittest.TestCase):
    """os.chmod vs ctypes 交叉验证"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gr_test_")
        self.fpath = os.path.join(self.tmpdir, "test.txt")
        with open(self.fpath, "w", encoding="utf-8") as f:
            f.write("hello")

    def tearDown(self):
        os.chmod(self.fpath, stat.S_IREAD | stat.S_IWRITE)
        set_readonly(self.fpath, False)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_os_chmod_sets_posix_readonly(self):
        """os.chmod(S_IREAD) 使 os.stat 报告只读"""
        os.chmod(self.fpath, stat.S_IREAD)
        old_method = not bool(os.stat(self.fpath).st_mode & stat.S_IWRITE)
        self.assertTrue(old_method)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_set_readonly_detected_by_os_stat(self):
        """set_readonly(True) 后 os.stat 也报告只读"""
        set_readonly(self.fpath, True)
        old_method = not bool(os.stat(self.fpath).st_mode & stat.S_IWRITE)
        self.assertTrue(old_method)

    @unittest.skipUnless(IS_WIN, "Windows only")
    def test_set_readonly_detected_by_ctypes(self):
        """set_readonly(True) 后 ctypes 检测到只读"""
        set_readonly(self.fpath, True)
        self.assertTrue(is_readonly(self.fpath))


class TestGuardrailsEndToEnd(unittest.TestCase):
    """guardrails_enforce.py CLI 端到端测试"""

    def setUp(self):
        """每个测试前确保 protect 状态"""
        _run_guardrails("protect", token="test")

    def tearDown(self):
        """每个测试后恢复 protect 状态"""
        _run_guardrails("protect", token="test")

    def test_protect_returns_zero(self):
        """protect 命令返回 0"""
        ret = _run_guardrails("protect", token="test")
        self.assertEqual(ret.returncode, 0,
                         f"stderr={ret.stderr.strip()}")

    def test_verify_returns_zero_after_protect(self):
        """protect 后 verify 返回 0"""
        ret = _run_guardrails("verify")
        self.assertEqual(ret.returncode, 0)

    def test_verify_reports_readonly_true(self):
        """verify 输出包含 readonly = True"""
        ret = _run_guardrails("verify")
        self.assertIn("readonly    = True", ret.stdout)

    def test_verify_reports_result_ok(self):
        """verify 输出包含 RESULT = OK"""
        ret = _run_guardrails("verify")
        self.assertIn("RESULT      = OK", ret.stdout)

    def test_unlock_then_verify_fails(self):
        """unlock 后 verify 返回 1"""
        ret_unlock = _run_guardrails("unlock", PROTECTED_FILE, token="test")
        self.assertEqual(ret_unlock.returncode, 0,
                         f"unlock failed: {ret_unlock.stderr.strip()}")
        ret = _run_guardrails("verify")
        self.assertEqual(ret.returncode, 1,
                         f"expected verify fail after unlock, got: {ret.stdout.strip()}")

    def test_unlock_then_verify_reports_readonly_false(self):
        """unlock 后 verify 输出 readonly = False"""
        ret_unlock = _run_guardrails("unlock", PROTECTED_FILE, token="test")
        self.assertEqual(ret_unlock.returncode, 0,
                         f"unlock failed: {ret_unlock.stderr.strip()}")
        ret = _run_guardrails("verify")
        self.assertIn("readonly    = False", ret.stdout,
                       f"verify output: {ret.stdout.strip()}")

    def test_protect_restore_then_verify_ok(self):
        """unlock -> verify FAIL -> protect -> verify OK"""
        _run_guardrails("unlock", PROTECTED_FILE, token="test")
        ret = _run_guardrails("verify")
        self.assertEqual(ret.returncode, 1,
                         f"expected verify fail after unlock, got: {ret.stdout.strip()}")
        _run_guardrails("protect", token="test")
        ret = _run_guardrails("verify")
        self.assertEqual(ret.returncode, 0)

    def test_unlock_without_token_returns_2(self):
        """无 token 时 unlock 返回 2"""
        ret = _run_guardrails("unlock", PROTECTED_FILE, token=None)
        self.assertEqual(ret.returncode, 2)

    def test_unlock_with_empty_token_returns_2(self):
        """空 token 时 unlock 返回 2"""
        ret = _run_guardrails("unlock", PROTECTED_FILE, token="")
        self.assertEqual(ret.returncode, 2)


class TestHashIntegrity(unittest.TestCase):
    """哈希完整性测试"""

    def setUp(self):
        _run_guardrails("protect", token="test")

    def tearDown(self):
        _run_guardrails("protect", token="test")

    def test_hash_match_after_protect(self):
        """protect 后哈希一致"""
        ret = _run_guardrails("verify")
        self.assertIn("hash_match = True", ret.stdout)


def suite():
    s = unittest.TestSuite()
    loader = unittest.TestLoader()
    s.addTests(loader.loadTestsFromTestCase(TestIsReadonly))
    s.addTests(loader.loadTestsFromTestCase(TestSetReadonly))
    s.addTests(loader.loadTestsFromTestCase(TestOsChmodCrossValidation))
    s.addTests(loader.loadTestsFromTestCase(TestGuardrailsEndToEnd))
    s.addTests(loader.loadTestsFromTestCase(TestHashIntegrity))
    return s


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    sys.exit(0 if result.wasSuccessful() else 1)
