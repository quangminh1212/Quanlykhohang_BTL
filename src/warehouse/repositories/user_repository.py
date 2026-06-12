"""Repository truy cập bảng ``users``.

Khác với hệ thống tham khảo (AuthService truy vấn trực tiếp bảng users), ở đây
ta tách riêng ``UserRepository`` để tầng nghiệp vụ không thao tác SQL trực tiếp,
giúp kiến trúc phân tầng rõ ràng hơn.
"""

from __future__ import annotations

from ..database.database import Database
from ..models.user import User


class UserRepository:
    """Thực hiện các truy vấn SQL trên bảng ``users``."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def find_by_username(self, username: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return User.from_row(row) if row else None

    def exists(self, username: str) -> bool:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            return row is not None

    def insert(self, user: User) -> int:
        with self._db.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, full_name, email,
                     department, position, phone, bio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.username,
                    user.password_hash,
                    user.role,
                    user.full_name,
                    user.email,
                    user.department,
                    user.position,
                    user.phone,
                    user.bio,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_profile(self, user: User) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE users
                   SET full_name = ?, email = ?, department = ?,
                       position = ?, phone = ?, bio = ?
                 WHERE username = ?
                """,
                (
                    user.full_name,
                    user.email,
                    user.department,
                    user.position,
                    user.phone,
                    user.bio,
                    user.username,
                ),
            )
            conn.commit()

    def update_password(self, username: str, password_hash: str) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, username),
            )
            conn.commit()

    def find_all(self) -> list[User]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY full_name, username"
            ).fetchall()
            return [User.from_row(r) for r in rows]

    def count(self) -> int:
        with self._db.connection() as conn:
            return int(
                conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            )
