"""Smoke test giao diện: dựng app, đăng nhập và duyệt qua mọi màn hình.

Không vào mainloop; chỉ kiểm tra việc dựng widget không phát sinh lỗi runtime.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Dùng CSDL tạm để không đụng dữ liệu thật.
fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.remove(db_path)
os.environ["WAREHOUSE_DB_PATH"] = db_path

from warehouse.ui.app import WarehouseApp  # noqa: E402

app = WarehouseApp()
# Đăng nhập bằng tài khoản quản lý (đã seed).
app.current_user = app.ctx.account_service.login("manager", "123456")
app._show_main_shell()

views = [
    ("dashboard", app._view_dashboard),
    ("products", app._view_products),
    ("suppliers", app._view_suppliers),
    ("import", app._view_import),
    ("export", app._view_export),
    ("history", app._view_history),
    ("reports", app._view_reports),
    ("profile", app._view_profile),
]
for key, builder in views:
    app._navigate(key, builder)
    app.root.update_idletasks()
    print(f"  [OK] view: {key}")

app.ctx.close()
app.root.destroy()
if os.path.exists(db_path):
    os.remove(db_path)
print("SMOKE GUI OK")
