# Hệ thống Quản lý Kho hàng

Phần mềm quản lý kho hàng viết bằng **Python**, kiến trúc phân tầng, giao diện
**Tkinter**, cơ sở dữ liệu **SQLite**. Dự án được xây dựng theo phương pháp Phân
tích thiết kế hệ thống (PTTKHT), tham khảo cấu trúc từ đề tài Quản lý thư viện.

## Tính năng chính

- Đăng nhập, phân quyền theo vai trò (Quản lý kho / Nhân viên kho).
- Quản lý hồ sơ cá nhân, đổi mật khẩu (mật khẩu băm PBKDF2 có muối).
- Quản lý danh mục hàng hóa (thêm/sửa/xóa/tìm kiếm, cảnh báo tồn thấp).
- Quản lý nhà cung cấp.
- Nhập kho / Xuất kho an toàn bằng giao dịch CSDL (transaction).
- Lịch sử giao dịch nhập/xuất, lọc theo loại.
- Thống kê tổng quan, báo cáo theo thời gian, kết xuất CSV.

## Yêu cầu

- Python 3.10 trở lên (đã kèm `tkinter`, `sqlite3`, `hashlib` -- không cần cài
  thêm gói bên ngoài).

## Chạy ứng dụng

### Cách 1 — Dùng script tự động (khuyến nghị)

Script sẽ tự kiểm tra Python, tkinter, cài thành phần (nếu cần) và khởi chạy.

- **Windows:** nhấp đúp `run.bat` (hoặc chạy `run.bat` trong CMD).
- **macOS:** nhấp đúp `run.command` trong Finder, hoặc chạy trong Terminal:
  ```bash
  chmod +x run.sh && ./run.sh
  ```
- **Linux:**
  ```bash
  chmod +x run.sh && ./run.sh
  ```

> Lưu ý macOS: nếu lần đầu báo chặn "nhà phát triển không xác định", vào
> *System Settings → Privacy & Security → Open Anyway*. Nếu thiếu tkinter:
> `brew install python-tk`. Trên Linux Debian/Ubuntu: `sudo apt install python3-tk`.

### Cách 2 — Chạy thủ công

```bash
python run.py
```

Lần đầu chạy, hệ thống tự tạo CSDL `data/warehouse.db` và nạp dữ liệu mẫu.

**Tài khoản mẫu:**

| Vai trò       | Tên đăng nhập | Mật khẩu |
|---------------|---------------|----------|
| Quản lý kho   | `manager`     | `123456` |
| Nhân viên kho | `staff`       | `123456` |

## Cấu trúc dự án

```
Quanlykhohang_BTL/
├── run.py                      # Điểm khởi chạy ứng dụng
├── run.bat                     # Script khởi chạy cho Windows
├── run.sh                      # Script khởi chạy cho macOS/Linux
├── run.command                 # Double-click chạy trên macOS (Finder)
├── requirements.txt
├── sql/init.sql                # Lược đồ CSDL (tham khảo)
├── src/warehouse/
│   ├── app_context.py          # Composition Root + dữ liệu mẫu
│   ├── config/                 # DbConfig
│   ├── database/               # Database (SQLite + schema + transaction)
│   ├── models/                 # User, Product, Supplier, Transaction
│   ├── repositories/           # Tầng truy cập dữ liệu
│   ├── services/               # Tầng nghiệp vụ
│   ├── utils/                  # security (băm mật khẩu)
│   └── ui/app.py               # Giao diện Tkinter
├── tests/                      # Kiểm thử đơn vị + smoke test GUI
└── docs/report/main.tex        # Báo cáo LaTeX (PTTKHT)
```

## Chạy kiểm thử

```bash
# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -p "test_*.py"
```

## Biên dịch báo cáo

```bash
cd docs/report
pdflatex main.tex   # chạy 2 lần để cập nhật mục lục
```
