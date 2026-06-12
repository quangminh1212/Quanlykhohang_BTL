#!/usr/bin/env bash
# =====================================================================
#  Khởi chạy Hệ thống Quản lý Kho hàng (macOS / Linux)
#  - Kiểm tra Python và tkinter
#  - Cài đặt thành phần (nếu cần)
#  - Khởi chạy ứng dụng
#
#  Cách dùng:
#     chmod +x run.sh      (chỉ cần làm 1 lần)
#     ./run.sh
# =====================================================================
set -u

# Chuyển về thư mục chứa script
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  HỆ THỐNG QUẢN LÝ KHO HÀNG - Khởi chạy (macOS/Linux)"
echo "============================================================"
echo

# --- 1. Tìm trình thông dịch Python ---
PY=""
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi

if [ -z "$PY" ]; then
    echo "[LỖI] Không tìm thấy Python trên máy."
    echo "      Cài đặt Python 3.10+:"
    echo "      - macOS:  brew install python   (hoặc tải tại python.org)"
    echo "      - Linux:  sudo apt install python3 python3-tk"
    exit 1
fi

echo "[1/4] Đã tìm thấy Python:"
$PY --version
echo

# --- 2. Kiểm tra phiên bản Python >= 3.10 ---
if ! $PY -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"; then
    echo "[CẢNH BÁO] Phiên bản Python quá cũ. Khuyến nghị 3.10 trở lên."
    echo "           Vẫn sẽ thử khởi chạy..."
    echo
fi

# --- 3. Kiểm tra tkinter (giao diện) ---
echo "[2/4] Kiểm tra thư viện giao diện tkinter..."
if ! $PY -c "import tkinter" >/dev/null 2>&1; then
    echo "[LỖI] Không tìm thấy tkinter."
    echo "      - macOS (Homebrew):  brew install python-tk"
    echo "      - Linux (Debian/Ubuntu):  sudo apt install python3-tk"
    echo "      - Hoặc cài Python từ python.org (đã kèm tkinter)."
    exit 1
fi
echo "      OK - tkinter sẵn sàng."
echo

# --- 4. Cài đặt thành phần (dự án chỉ dùng thư viện chuẩn) ---
echo "[3/4] Kiểm tra/cài đặt thành phần phụ thuộc..."
if [ -f requirements.txt ]; then
    if $PY -m pip install -r requirements.txt >/dev/null 2>&1; then
        echo "      OK - không có gói ngoài bắt buộc."
    else
        echo "      [bỏ qua] Không cài được qua pip - dự án không bắt buộc gói ngoài."
    fi
fi
echo

# --- 5. Khởi chạy ứng dụng ---
echo "[4/4] Đang khởi chạy ứng dụng..."
echo "------------------------------------------------------------"
$PY run.py
EXITCODE=$?
echo "------------------------------------------------------------"

if [ "$EXITCODE" -ne 0 ]; then
    echo "[LỖI] Ứng dụng kết thúc với mã lỗi $EXITCODE."
    exit "$EXITCODE"
fi

echo "Đã đóng ứng dụng."
