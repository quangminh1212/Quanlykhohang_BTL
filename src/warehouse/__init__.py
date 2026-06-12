"""Hệ thống Quản lý Kho hàng (Warehouse Management System).

Gói phần mềm được tổ chức theo kiến trúc phân tầng:
- ui:           Tầng giao diện người dùng (Tkinter).
- services:     Tầng nghiệp vụ.
- repositories: Tầng truy cập dữ liệu.
- models:       Tầng mô hình miền (domain model).
- database:     Hạ tầng kết nối và khởi tạo CSDL (SQLite).
- config:       Cấu hình kết nối CSDL.
- utils:        Tiện ích dùng chung (bảo mật, định dạng...).
"""

__version__ = "1.0.0"
