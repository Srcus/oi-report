# -*- coding: utf-8 -*-
"""口令门（软门槛）：脚本启动前校验口令。

说明：这只是防止误用/随手传播，不是真正的访问控制。
仓库如果是公开的，代码本身可读，任何人都能绕过。真保密请用私有仓库。
"""
import hashlib
import os
import sys

SALT = b"oi-report-2026"
ITER = 200000
_HASH = None  # 首次运行时从同目录 key.txt 读取（sha256(口令+salt)）

MSG = ("未通过口令校验。请向报告发布者索取访问口令，"
       "用 --passcode <口令> 传入，或设置环境变量 OI_REPORT_KEY。")


def _expected():
    global _HASH
    if _HASH is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.txt")
        try:
            _HASH = open(path, encoding="utf-8").read().strip()
        except FileNotFoundError:
            _HASH = ""
    return _HASH


def digest(passcode: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", passcode.encode("utf-8"), SALT, ITER).hex()


def require(passcode=None, exit_code=2):
    """校验口令；失败时打印提示并退出。"""
    expected = _expected()
    if not expected:
        # 没有配置 key.txt 视为不设门槛
        return True
    code = passcode or os.environ.get("OI_REPORT_KEY", "")
    if code and digest(code) == expected:
        return True
    print(MSG, file=sys.stderr)
    sys.exit(exit_code)
