"""Hạ tầng kết nối và khởi tạo cơ sở dữ liệu.

Tương ứng với lớp ``Database`` trong thiết kế. Lớp này nhận một ``DbConfig``,
cung cấp kết nối tới CSDL, khởi tạo/migrate schema và quản lý vòng đời kết nối.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..config.db_config import DbConfig


class Database:
    """Quản lý kết nối SQLite và khởi tạo schema."""

    def __init__(self, config: DbConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Kết nối
    # ------------------------------------------------------------------
    def get_connection(self) -> sqlite3.Connection:
        """Tạo và trả về một kết nối mới tới CSDL.

        Mỗi kết nối được cấu hình:
        - ``row_factory`` = ``sqlite3.Row`` để truy cập cột theo tên.
        - Bật ràng buộc khóa ngoại (PRAGMA foreign_keys).
        - Thiết lập thời gian chờ khi CSDL bận.
        """
        conn = sqlite3.connect(
            self._config.db_path,
            timeout=self._config.busy_timeout_ms / 1000.0,
        )
        conn.row_factory = sqlite3.Row
        if self._config.enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(f"PRAGMA busy_timeout = {self._config.busy_timeout_ms};")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager trả về kết nối và tự đóng khi kết thúc."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager bao một giao dịch (transaction) CSDL.

        Tự động ``COMMIT`` khi thành công và ``ROLLBACK`` khi có lỗi, bảo đảm
        tính toàn vẹn dữ liệu cho các nghiệp vụ nhập/xuất kho.
        """
        conn = self.get_connection()
        try:
            conn.execute("BEGIN;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Khởi tạo schema
    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        """Khởi tạo các bảng nếu chưa tồn tại."""
        with self.connection() as conn:
            conn.executescript(_SCHEMA_SQL)
            conn.commit()

    def close(self) -> None:
        """Giải phóng tài nguyên (SQLite không dùng connection pool nên rỗng)."""
        # Mỗi thao tác đã mở/đóng kết nối riêng nên không cần xử lý thêm.
        return None


# Định nghĩa schema CSDL. Đồng bộ với tài liệu thiết kế (Chương III).
_SCHEMA_SQL = """
-- Bảng người dùng: tài khoản, mật khẩu mã hóa, vai trò và hồ sơ cá nhân.
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('MANAGER', 'STAFF')),
    full_name     TEXT    NOT NULL DEFAULT '',
    email         TEXT    NOT NULL DEFAULT '',
    department    TEXT    NOT NULL DEFAULT '',
    position      TEXT    NOT NULL DEFAULT '',
    phone         TEXT    NOT NULL DEFAULT '',
    bio           TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng nhà cung cấp.
CREATE TABLE IF NOT EXISTS suppliers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT    NOT NULL UNIQUE,
    name           TEXT    NOT NULL,
    contact_person TEXT    NOT NULL DEFAULT '',
    phone          TEXT    NOT NULL DEFAULT '',
    email          TEXT    NOT NULL DEFAULT '',
    address        TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng hàng hóa trong kho.
CREATE TABLE IF NOT EXISTS products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sku          TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT '',
    unit         TEXT    NOT NULL DEFAULT 'cái',
    quantity     INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_quantity INTEGER NOT NULL DEFAULT 0 CHECK (min_quantity >= 0),
    unit_price   REAL    NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    location     TEXT    NOT NULL DEFAULT '',
    supplier_id  INTEGER,
    status       TEXT    NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISCONTINUED')),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE SET NULL
);

-- Bảng giao dịch nhập/xuất kho.
CREATE TABLE IF NOT EXISTS transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT    NOT NULL UNIQUE,
    type             TEXT    NOT NULL CHECK (type IN ('IMPORT', 'EXPORT')),
    product_id       INTEGER NOT NULL,
    product_name     TEXT    NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price       REAL    NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    total            REAL    NOT NULL DEFAULT 0 CHECK (total >= 0),
    partner          TEXT    NOT NULL DEFAULT '',
    user_username    TEXT    NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note             TEXT    NOT NULL DEFAULT '',
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (user_username) REFERENCES users (username)
);

-- Index tối ưu truy vấn.
CREATE INDEX IF NOT EXISTS idx_tx_product ON transactions (product_id);
CREATE INDEX IF NOT EXISTS idx_tx_type    ON transactions (type);
CREATE INDEX IF NOT EXISTS idx_tx_date    ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
"""
