"""Sinh ID dạng ULID có tiền tố (SPEC 07 §2, 09 §1).

ULID = 48-bit thời gian (ms) + 80-bit ngẫu nhiên, mã hoá Crockford Base32 (26 ký tự),
sắp xếp được theo thời gian. Tiền tố giúp đọc log dễ (vd `job_01H...`, `trc_01H...`).
Tự hiện thực — không thêm dependency.
"""

from __future__ import annotations

import os
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TIME_LEN = 10  # 50 bit (đủ cho 48-bit ms)
_RAND_LEN = 16  # 80 bit


def _encode(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def ulid() -> str:
    ms = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), "big")
    return _encode(ms, _TIME_LEN) + _encode(rand, _RAND_LEN)


def new_id(prefix: str) -> str:
    return f"{prefix}_{ulid()}"
