"""Cấu hình kết nối cơ sở dữ liệu.

Tương ứng với lớp ``DbConfig`` trong thiết kế. Lớp này chịu trách nhiệm
nạp thông tin cấu hình kết nối từ biến môi trường hoặc giá trị mặc định.

Hệ thống sử dụng SQLite (CSDL nhúng, không cần cài đặt máy chủ) để bảo đảm
phần mềm có thể chạy được ngay trên mọi máy có Python mà không cần thiết lập
thêm. Thiết kế lớp vẫn tách bạch phần cấu hình để dễ dàng chuyển sang một
hệ quản trị CSDL khác (MySQL, PostgreSQL...) khi cần.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_db_path() -> str:
    """Trả về đường dẫn mặc định tới tệp CSDL SQLite.

    Tệp dữ liệu được đặt trong thư mục ``data`` ở gốc dự án.
    """
    # .../src/warehouse/config/db_config.py -> gốc dự án là cấp thứ 4 lên trên
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "warehouse.db")


@dataclass(frozen=True)
class DbConfig:
    """Đối tượng giữ thông tin cấu hình kết nối CSDL."""

    db_path: str
    busy_timeout_ms: int = 5000
    enable_foreign_keys: bool = True

    @staticmethod
    def load() -> "DbConfig":
        """Nạp cấu hình từ biến môi trường, nếu không có thì dùng mặc định.

        - ``WAREHOUSE_DB_PATH``: đường dẫn tới tệp CSDL.
        - ``WAREHOUSE_DB_TIMEOUT_MS``: thời gian chờ khi CSDL bận (ms).
        """
        db_path = os.environ.get("WAREHOUSE_DB_PATH", _default_db_path())
        timeout = int(os.environ.get("WAREHOUSE_DB_TIMEOUT_MS", "5000"))
        return DbConfig(db_path=db_path, busy_timeout_ms=timeout)
