#!/usr/bin/env python3
"""
test_unlock_hash_check.py
guardrails_enforce.py v0.3 cmd_unlock 哈希比对单元测试

覆盖:
  - hash_token() 函数
  - cmd_set_token() 首次设置 + 轮换
  - cmd_unlock 哈希比对（匹配 / 不匹配 / token 空 / store 缺失）
  - 兼容性（旧 store 无 guardrail_token_hash 字段）
  - 安全边界（不泄露 token / 不泄露哈希原文）
"""
import sys
import os
import json
import shutil
import tempfile
import unittest

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import guardrails_enforce as ge


class TestHashToken(unittest.TestCase):
    """hash_token() 函数测试"""

    def test_hash_token_returns_sha256_hex(self):
        """hash_token 应返回 64 位 SHA256 hex 字符串"""
        h = ge.hash_token("test-token-123")
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_hash_token_deterministic(self):
        """相同输入应产生相同哈希"""
        self.assertEqual(ge.hash_token("abc"), ge.hash_token("abc"))

    def test_hash_token_different_inputs(self):
        """不同输入应产生不同哈希"""
        self.assertNotEqual(ge.hash_token("abc"), ge.hash_token("abd"))

    def test_hash_token_unicode(self):
        """Unicode token 应正常哈希"""
        h = ge.hash_token("操作员令牌-123")
        self.assertEqual(len(h), 64)


class TestCmdSetToken(unittest.TestCase):
    """cmd_set_token() 测试"""

    def setUp(self):
        """临时工作目录 + 备份原 HASH_STORE"""
        self.tmpdir = tempfile.mkdtemp(prefix="guardrail_test_")
        self.old_hash_store = ge.HASH_STORE
        self.old_protected = ge.PROTECTED_FILE
        # 用一个临时文件作为 PROTECTED_FILE
        self.tmp_protected = os.path.join(self.tmpdir, "fake_protected.md")
        with open(self.tmp_protected, "w", encoding="utf-8") as f:
            f.write("# fake protected\n## §13 ...")
        ge.PROTECTED_FILE = self.tmp_protected
        ge.HASH_STORE = self.tmp_protected + ".guardrail.json"

    def tearDown(self):
        ge.HASH_STORE = self.old_hash_store
        ge.PROTECTED_FILE = self.old_protected
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_set_token_first_time_no_existing_store(self):
        """HASH_STORE 不存在时，首次设置应直接写入"""
        if os.path.exists(ge.HASH_STORE):
            os.remove(ge.HASH_STORE)
        os.environ["GUARDRAIL_TOKEN"] = "first-token-abc"
        try:
            rc = ge.cmd_set_token()
            self.assertEqual(rc, 0)
            with open(ge.HASH_STORE, encoding="utf-8") as f:
                store = json.load(f)
            self.assertEqual(store["guardrail_token_hash"], ge.hash_token("first-token-abc"))
        finally:
            os.environ.pop("GUARDRAIL_TOKEN", None)

    def test_set_token_first_time_existing_store_no_hash(self):
        """HASH_STORE 存在但无 guardrail_token_hash 时，首次设置应写入"""
        # 准备一个旧 store（无 guardrail_token_hash 字段）
        with open(ge.HASH_STORE, "w", encoding="utf-8") as f:
            json.dump({"file_hash": "abc", "s13_hash": "def"}, f)
        os.environ["GUARDRAIL_TOKEN"] = "new-token-xyz"
        try:
            rc = ge.cmd_set_token()
            self.assertEqual(rc, 0)
            with open(ge.HASH_STORE, encoding="utf-8") as f:
                store = json.load(f)
            self.assertEqual(store["guardrail_token_hash"], ge.hash_token("new-token-xyz"))
            # 原有字段应保留
            self.assertEqual(store["file_hash"], "abc")
        finally:
            os.environ.pop("GUARDRAIL_TOKEN", None)

    def test_set_token_empty_env_rejected(self):
        """GUARDRAIL_TOKEN 为空时应 exit 2"""
        os.environ.pop("GUARDRAIL_TOKEN", None)
        rc = ge.cmd_set_token()
        self.assertEqual(rc, 2)

    def test_set_token_rotation_requires_current_token(self):
        """已存在 hash 时，轮换需 GUARDRAIL_TOKEN_CURRENT 匹配"""
        # 先设置一次
        os.environ["GUARDRAIL_TOKEN"] = "old-token-123"
        ge.cmd_set_token()
        # 尝试轮换（无 CURRENT）
        os.environ["GUARDRAIL_TOKEN"] = "new-token-456"
        os.environ.pop("GUARDRAIL_TOKEN_CURRENT", None)
        try:
            rc = ge.cmd_set_token()
            self.assertEqual(rc, 2)  # 应拒绝
        finally:
            os.environ.pop("GUARDRAIL_TOKEN", None)
            os.environ.pop("GUARDRAIL_TOKEN_CURRENT", None)

    def test_set_token_rotation_with_matching_current(self):
        """已存在 hash 时，GUARDRAIL_TOKEN_CURRENT 匹配则允许轮换"""
        # 先设置
        os.environ["GUARDRAIL_TOKEN"] = "old-token-123"
        ge.cmd_set_token()
        # 轮换
        os.environ["GUARDRAIL_TOKEN"] = "new-token-456"
        os.environ["GUARDRAIL_TOKEN_CURRENT"] = "old-token-123"
        try:
            rc = ge.cmd_set_token()
            self.assertEqual(rc, 0)
            with open(ge.HASH_STORE, encoding="utf-8") as f:
                store = json.load(f)
            self.assertEqual(store["guardrail_token_hash"], ge.hash_token("new-token-456"))
        finally:
            os.environ.pop("GUARDRAIL_TOKEN", None)
            os.environ.pop("GUARDRAIL_TOKEN_CURRENT", None)


class TestCmdUnlockHashCheck(unittest.TestCase):
    """cmd_unlock() 哈希比对测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="guardrail_unlock_test_")
        self.old_hash_store = ge.HASH_STORE
        self.old_protected = ge.PROTECTED_FILE
        self.tmp_protected = os.path.join(self.tmpdir, "fake_protected.md")
        with open(self.tmp_protected, "w", encoding="utf-8") as f:
            f.write("# fake\n## §13 test")
        ge.PROTECTED_FILE = self.tmp_protected
        ge.HASH_STORE = self.tmp_protected + ".guardrail.json"

    def tearDown(self):
        ge.HASH_STORE = self.old_hash_store
        ge.PROTECTED_FILE = self.old_protected
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("GUARDRAIL_TOKEN", None)

    def test_unlock_empty_token_rejected(self):
        """GUARDRAIL_TOKEN 为空 → exit 2"""
        os.environ.pop("GUARDRAIL_TOKEN", None)
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 2)

    def test_unlock_no_hash_store_falls_back_to_nonempty(self):
        """HASH_STORE 不存在 → 退化为非空校验（兼容旧产物）"""
        if os.path.exists(ge.HASH_STORE):
            os.remove(ge.HASH_STORE)
        os.environ["GUARDRAIL_TOKEN"] = "anything-nonempty"
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 0)  # 退化为非空校验

    def test_unlock_null_token_hash_falls_back_to_nonempty(self):
        """guardrail_token_hash 为 null → 退化为非空校验（兼容旧产物）"""
        with open(ge.HASH_STORE, "w", encoding="utf-8") as f:
            json.dump({"file_hash": "abc", "guardrail_token_hash": None}, f)
        os.environ["GUARDRAIL_TOKEN"] = "anything-nonempty"
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 0)

    def test_unlock_matching_hash_succeeds(self):
        """token 哈希匹配 → exit 0"""
        # 设置 token
        os.environ["GUARDRAIL_TOKEN"] = "correct-token-123"
        ge.cmd_set_token()
        # unlock
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 0)

    def test_unlock_mismatched_hash_rejected(self):
        """token 哈希不匹配 → exit 2（fail-closed）"""
        # 设置 token
        os.environ["GUARDRAIL_TOKEN"] = "correct-token-123"
        ge.cmd_set_token()
        # 换错的 token
        os.environ["GUARDRAIL_TOKEN"] = "wrong-token-456"
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 2)

    def test_unlock_empty_token_even_with_hash_stored_rejected(self):
        """已存哈希但 GUARDRAIL_TOKEN 空 → 仍 exit 2"""
        os.environ["GUARDRAIL_TOKEN"] = "first-token"
        ge.cmd_set_token()
        os.environ.pop("GUARDRAIL_TOKEN", None)
        rc = ge.cmd_unlock(self.tmp_protected)
        self.assertEqual(rc, 2)


class TestSecurityProperties(unittest.TestCase):
    """安全属性测试"""

    def test_no_token_plaintext_in_hash_store(self):
        """HASH_STORE 中不应存 token 原文，只存哈希"""
        tmpdir = tempfile.mkdtemp()
        old_hs, old_pf = ge.HASH_STORE, ge.PROTECTED_FILE
        try:
            tmp_pf = os.path.join(tmpdir, "fake.md")
            with open(tmp_pf, "w", encoding="utf-8") as f:
                f.write("# fake\n## §13 test")
            ge.PROTECTED_FILE = tmp_pf
            ge.HASH_STORE = tmp_pf + ".guardrail.json"
            os.environ["GUARDRAIL_TOKEN"] = "my-secret-token-value"
            ge.cmd_set_token()
            with open(ge.HASH_STORE, encoding="utf-8") as f:
                content = f.read()
            # token 原文不应出现在文件里
            self.assertNotIn("my-secret-token-value", content)
            # 哈希应出现
            self.assertIn(ge.hash_token("my-secret-token-value"), content)
        finally:
            ge.HASH_STORE = old_hs
            ge.PROTECTED_FILE = old_pf
            shutil.rmtree(tmpdir, ignore_errors=True)
            os.environ.pop("GUARDRAIL_TOKEN", None)

    def test_hash_comparison_uses_constant_time(self):
        """哈希比对应使用 secrets.compare_digest（常量时间）"""
        # 间接验证：确认 secrets 模块被 import
        self.assertTrue(hasattr(ge, "secrets"))


class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容性测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="guardrail_compat_")
        self.old_hs, self.old_pf = ge.HASH_STORE, ge.PROTECTED_FILE
        self.tmp_pf = os.path.join(self.tmpdir, "fake.md")
        with open(self.tmp_pf, "w", encoding="utf-8") as f:
            f.write("# fake\n## §13 test")
        ge.PROTECTED_FILE = self.tmp_pf
        ge.HASH_STORE = self.tmp_pf + ".guardrail.json"

    def tearDown(self):
        ge.HASH_STORE = self.old_hs
        ge.PROTECTED_FILE = self.old_pf
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("GUARDRAIL_TOKEN", None)

    def test_old_store_without_token_hash_field_unlocks(self):
        """旧 protect 产物（无 guardrail_token_hash 字段）应能 unlock"""
        # 模拟旧 store
        with open(ge.HASH_STORE, "w", encoding="utf-8") as f:
            json.dump({
                "file": "/fake/path",
                "file_hash": "abc123",
                "s13_hash": "def456",
                "s13_present": True,
                # 注意：没有 guardrail_token_hash 字段
            }, f)
        os.environ["GUARDRAIL_TOKEN"] = "any-nonempty-placeholder"
        rc = ge.cmd_unlock(self.tmp_pf)
        self.assertEqual(rc, 0)  # 兼容旧产物


if __name__ == "__main__":
    unittest.main(verbosity=2)
