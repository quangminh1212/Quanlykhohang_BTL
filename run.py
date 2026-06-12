"""Điểm khởi chạy Hệ thống Quản lý Kho hàng.

Cách chạy:
    python run.py
"""

import os
import sys

# Thêm thư mục src vào sys.path để import gói warehouse.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from warehouse.ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
