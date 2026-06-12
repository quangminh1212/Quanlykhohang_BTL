"""Cấu hình chung cho bộ kiểm thử."""

import os
import sys

# Thêm thư mục src vào đường dẫn import.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
