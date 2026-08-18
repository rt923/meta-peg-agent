#!/usr/bin/env python3
# guardrails_enforce.py
# §13 文件系统只读锁 —— 把 os_guardrails.md §5 的承诺落成可执行脚本。
# 这是「不可破解」硬约束的最后一道防线：即使上层提示被注入绕过，
# 本脚本在 OS 层校验 §13 完整性、设置只读属性、并断言任何自指改写不得改动 §13 段落。
#
# 子命令:
#   protect            计算并存储哈希、设置受保护文件为只读
#   verify            启动时校验：哈希一致 + 文件为只读；输出报告 + 退出码
#   lock <path>       将文件设为只读（OS 层拦截 PEG-A 自指写）
#   unlock <path>     授权下解除只读（需 GUARDRAIL_TOKEN 环境变量非空）
#   check-s13 <old> <new>  断言两段文本中 §13 段落未被改动（供 apply_rewrite 调用）
#
# 退出码: 0 = 通过/成功, 1 = 校验失败/被篡改, 2 = 参数/IO 错误
#
# 对应 ARCHITECTURE_REVIEW.md §3 P0-2。

import sys
import os
import json
import hashlib
import argparse
import stat
import secrets
import logging

HERE = os.path.dirname(os.path.abspath(__file__))
# §13 所在的受保护文件（阶段 0 种子提示词，§13 内嵌其中）
# 归并位置：与 PEG-A 工程产物同处 meta_peg_agent/ 根（2026-07-14 目录整理决定）。
PROTECTED_FILE = os.path.join(HERE, "phase0_meta_peg_agent_prompt.md")
PROTECTED_FILE = os.path.abspath(PROTECTED_FILE)
HASH_STORE = PROTECTED_FILE + ".guardrail.json"

# ---- 结构化日志（写入 stderr，不污染 stdout 的校验报告 / 退出码判定）----
_log = logging.getLogger("guardrail")
if not _log.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter(
        "%(asctime)s.%(msecs)03d [GUARDRAIL] %(levelname)s %(message)s",
        datefmt="%H:%M:%S"))
    _log.addHandler(_h)
# 默认 INFO；可用 GUARDRAIL_LOG_LEVEL=DEBUG / WARNING 调整；=OFF 关闭
_level = os.environ.get("GUARDRAIL_LOG_LEVEL", "INFO").upper()
if _level == "OFF":
    _log.disabled = True
else:
    _log.setLevel(_level)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_s13(text):
    """提取 §13 段落：从 '## 13.' 到 '=== 第0阶段提示词正文结束 ==='。"""
    start = text.find("## 13.")
    if start < 0:
        return None
    end = text.find("=== 第0阶段提示词正文结束 ===", start)
    if end < 0:
        end = len(text)
    return text[start:end]


def is_readonly(path):
    if sys.platform == "win32":
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
        if attrs == -1 or attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
            return False
        FILE_ATTRIBUTE_READONLY = 0x00000001
        return bool(attrs & FILE_ATTRIBUTE_READONLY)
    else:
        return not bool(os.stat(path).st_mode & stat.S_IWRITE)


def set_readonly(path, readonly):
    if sys.platform == "win32":
        import ctypes
        FILE_ATTRIBUTE_READONLY = 0x00000001
        FILE_ATTRIBUTE_NORMAL = 0x00000080
        if readonly:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            if attrs == -1 or attrs == 0xFFFFFFFF:
                raise OSError(f"GetFileAttributesW failed for {path}")
            ctypes.windll.kernel32.SetFileAttributesW(path, attrs | FILE_ATTRIBUTE_READONLY)
        else:
            ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_NORMAL)
    else:
        if readonly:
            os.chmod(path, stat.S_IREAD)
        else:
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


# ---------- 子命令实现 ----------

def cmd_protect():
    try:
        _log.info("protect 开始: 计算哈希 + 抽取 §13 + 设只读")
        cur_hash = sha256_file(PROTECTED_FILE)
        text = open(PROTECTED_FILE, "r", encoding="utf-8").read()
        s13 = extract_s13(text)
        store = {
            "file": PROTECTED_FILE,
            "file_hash": cur_hash,
            "s13_hash": hashlib.sha256(s13.encode("utf-8")).hexdigest() if s13 else None,
            "s13_present": s13 is not None,
        }
        # v0.3: 若 GUARDRAIL_TOKEN 已设置则写入其哈希（首次保护时同步；已存在则不覆盖）
        token = os.environ.get("GUARDRAIL_TOKEN")
        if token and "guardrail_token_hash" not in store:
            store["guardrail_token_hash"] = hash_token(token)
            _log.info("protect: guardrail_token_hash 已写入（首次同步）")
        _log.info("protect 前: file_hash=%s s13_present=%s", cur_hash[:16], store['s13_present'])
        with open(HASH_STORE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        set_readonly(PROTECTED_FILE, True)  # 设为只读
        _log.info("protect 后: 哈希库已写 + 只读属性已设 (readonly=True)")
        print(f"PROTECTED: {PROTECTED_FILE}")
        print(f"  file_hash={cur_hash[:16]}...  s13_present={store['s13_present']}")
        print(f"  hash_store={HASH_STORE}  readonly=True")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"ERROR protect: {e}", file=sys.stderr)
        return 2


def cmd_verify():
    if not os.path.exists(HASH_STORE):
        _log.error("verify 失败: 哈希库不存在")
        print("ERROR: 哈希库不存在，请先运行 protect", file=sys.stderr)
        return 2
    store = json.load(open(HASH_STORE, "r", encoding="utf-8"))
    cur = sha256_file(PROTECTED_FILE)
    readonly = is_readonly(PROTECTED_FILE)
    ok = (cur == store["file_hash"]) and readonly
    _log.info("verify: stored_hash=%s cur_hash=%s hash_match=%s readonly=%s → RESULT=%s",
              store['file_hash'][:16], cur[:16], cur == store['file_hash'], readonly,
              "OK" if ok else "TAMPERED/UNLOCKED")
    print(f"VERIFY {PROTECTED_FILE}")
    print(f"  hash_match = {cur == store['file_hash']}  (stored={store['file_hash'][:16]}... cur={cur[:16]}...)")
    print(f"  readonly    = {readonly}")
    print(f"  RESULT      = {'OK' if ok else 'TAMPERED/UNLOCKED'}")
    return 0 if ok else 1


def cmd_lock(path):
    try:
        set_readonly(path, True)
        print(f"LOCKED (read-only): {path}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"ERROR lock: {e}", file=sys.stderr)
        return 2


def hash_token(token):
    """计算 token 的 SHA256 哈希（hex）。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def cmd_set_token():
    """设置或轮换 GUARDRAIL_TOKEN 的哈希到 HASH_STORE。

    流程:
      - 若 HASH_STORE 不存在或 guardrail_token_hash 为 null: 直接写入新 token 的 SHA256（首次设置）
      - 若 guardrail_token_hash 已存在: 要求当前 GUARDRAIL_TOKEN 匹配才允许轮换（防绕过）
    """
    new_token = os.environ.get("GUARDRAIL_TOKEN")
    if not new_token:
        print("ERROR set_token: 需设置环境变量 GUARDRAIL_TOKEN（新 token 值）", file=sys.stderr)
        return 2

    new_hash = hash_token(new_token)

    # 读现有 store
    if os.path.exists(HASH_STORE):
        with open(HASH_STORE, "r", encoding="utf-8") as f:
            store = json.load(f)
        existing_hash = store.get("guardrail_token_hash")
        if existing_hash:
            # 需校验当前 token 才能轮换
            current_token = os.environ.get("GUARDRAIL_TOKEN_CURRENT") or os.environ.get("GUARDRAIL_TOKEN_OLD")
            if not current_token:
                print("ERROR set_token: 已存在 token 哈希，轮换需额外设置 GUARDRAIL_TOKEN_CURRENT=<当前token>", file=sys.stderr)
                return 2
            current_hash = hash_token(current_token)
            if not secrets.compare_digest(current_hash, existing_hash):
                print("ERROR set_token: GUARDRAIL_TOKEN_CURRENT 不匹配存储的哈希，拒绝轮换", file=sys.stderr)
                return 2
    else:
        store = {}
        existing_hash = None

    # 写入新哈希
    store["guardrail_token_hash"] = new_hash
    with open(HASH_STORE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    _log.info("set_token: guardrail_token_hash 已更新（哈希前缀=%s...）", new_hash[:16])
    print(f"SET_TOKEN: guardrail_token_hash 已更新（hash={new_hash[:16]}...）")
    return 0


def cmd_unlock(path):
    _log.info("unlock 请求: path=%s", path)
    token = os.environ.get("GUARDRAIL_TOKEN")
    _log.info("GUARDRAIL_TOKEN 是否存在=%s", bool(token))
    if not token:
        _log.error("unlock 拒绝: GUARDRAIL_TOKEN 为空 → exit 2（fail-closed；守门员不自行设 token、不以口头授权替代）")
        print("ERROR unlock: 需设置环境变量 GUARDRAIL_TOKEN（授权操作员上下文）", file=sys.stderr)
        return 2

    # 哈希比对（v0.3 新增）
    if not os.path.exists(HASH_STORE):
        _log.warn("unlock WARN: HASH_STORE 不存在，退化为非空校验（弱保护）")
        print("WARN unlock: HASH_STORE 不存在，退化为非空校验（弱保护；建议跑 protect + set_token）", file=sys.stderr)
    else:
        with open(HASH_STORE, "r", encoding="utf-8") as f:
            store = json.load(f)
        stored_hash = store.get("guardrail_token_hash")
        if not stored_hash:
            _log.warn("unlock WARN: guardrail_token_hash 为 null，退化为非空校验（弱保护）")
            print("WARN unlock: guardrail_token_hash 未设置，退化为非空校验（弱保护；建议跑 set_token）", file=sys.stderr)
        else:
            provided_hash = hash_token(token)
            if not secrets.compare_digest(provided_hash, stored_hash):
                _log.error("unlock 拒绝: token 哈希不匹配 → exit 2")
                print("ERROR unlock: GUARDRAIL_TOKEN 哈希不匹配存储的哈希（fail-closed）", file=sys.stderr)
                return 2
            _log.info("令牌哈希校验通过（secrets.compare_digest）")

    _log.info("令牌校验通过，准备解除只读（修改前）")
    try:
        set_readonly(path, False)
        _log.info("只读属性已移除（文件可写）: path=%s", path)
        print(f"UNLOCKED (writable): {path}")
        return 0
    except Exception as e:  # noqa: BLE001
        _log.error("unlock 失败: %s", e)
        print(f"ERROR unlock: {e}", file=sys.stderr)
        return 2


def cmd_check_s13(old_path, new_path):
    _log.info("check-s13: 比对旧/新文本中的 §13 段落（修改后断言）")
    old = open(old_path, "r", encoding="utf-8").read()
    new = open(new_path, "r", encoding="utf-8").read()
    s13_old = extract_s13(old)
    s13_new = extract_s13(new)
    if s13_old is None or s13_new is None:
        _log.error("check-s13 失败: 未找到 §13 段落")
        print("ERROR: 未找到 §13 段落", file=sys.stderr)
        return 2
    unchanged = (s13_old == s13_new)
    _log.info("check-s13: §13 未变=%s → %s", unchanged, "OK" if unchanged else "REJECT(违反只读禁区)")
    if unchanged:
        print("OK: §13 段落未被改动")
        return 0
    print("REJECT: §13 段落发生变更 —— 违反只读禁区，自指改写被驳回", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="§13 文件系统只读锁")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("protect")
    sub.add_parser("verify")
    p_lock = sub.add_parser("lock"); p_lock.add_argument("path")
    p_unlock = sub.add_parser("unlock"); p_unlock.add_argument("path")
    p_s13 = sub.add_parser("check-s13"); p_s13.add_argument("old"); p_s13.add_argument("new")
    sub.add_parser("set_token")
    args = ap.parse_args()

    if args.cmd == "protect":
        sys.exit(cmd_protect())
    elif args.cmd == "verify":
        sys.exit(cmd_verify())
    elif args.cmd == "lock":
        sys.exit(cmd_lock(args.path))
    elif args.cmd == "unlock":
        sys.exit(cmd_unlock(args.path))
    elif args.cmd == "check-s13":
        sys.exit(cmd_check_s13(args.old, args.new))
    elif args.cmd == "set_token":
        sys.exit(cmd_set_token())
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
