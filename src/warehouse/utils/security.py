"""Tiện ích bảo mật: băm và xác thực mật khẩu.

Trong tài liệu thiết kế gốc (hệ thống tham khảo) mật khẩu được băm bằng BCrypt.
Ở đây ta dùng PBKDF2-HMAC-SHA256 (có sẵn trong thư viện chuẩn ``hashlib``) để
không phụ thuộc thư viện bên ngoài, đồng thời vẫn đảm bảo:

- Sinh muối (salt) ngẫu nhiên cho mỗi mật khẩu.
- Lặp nhiều vòng (iterations) để chống tấn công dò mật khẩu (brute-force).
- So sánh an toàn theo thời gian hằng số (constant-time) để chống timing attack.

Định dạng chuỗi lưu trữ: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
"""

from __future__ import annotations

import hashlib
import hmac
import os

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 120_000
_SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    """Băm mật khẩu trả về chuỗi có thể lưu trữ trong CSDL."""
    if not password:
        raise ValueError("Mật khẩu không được để trống.")
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"{_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Kiểm tra ``password`` có khớp với chuỗi băm ``stored`` hay không."""
    if not stored or "$" not in stored:
        return False
    try:
        algorithm, iter_str, salt_hex, hash_hex = stored.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)
