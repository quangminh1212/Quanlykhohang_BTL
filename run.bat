@echo off
REM =====================================================================
REM  Khoi chay He thong Quan ly Kho hang (Windows)
REM  - Kiem tra Python va tkinter
REM  - Cai dat thanh phan (neu can)
REM  - Khoi chay ung dung
REM =====================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   HE THONG QUAN LY KHO HANG - Khoi chay (Windows)
echo ============================================================
echo.

REM --- 1. Tim trinh thong dich Python ---
set "PY="
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if !errorlevel!==0 set "PY=python"
)

if "!PY!"=="" (
    echo [LOI] Khong tim thay Python tren may.
    echo       Vui long cai dat Python 3.10+ tai: https://www.python.org/downloads/
    echo       Nho tick chon "Add Python to PATH" khi cai dat.
    pause
    exit /b 1
)

echo [1/4] Da tim thay Python:
!PY! --version
echo.

REM --- 2. Kiem tra phien ban Python >= 3.10 ---
!PY! -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [CANH BAO] Phien ban Python qua cu. Khuyen nghi 3.10 tro len.
    echo            Van se thu khoi chay...
    echo.
)

REM --- 3. Kiem tra tkinter (giao dien) ---
echo [2/4] Kiem tra thu vien giao dien tkinter...
!PY! -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay tkinter.
    echo       Hay cai lai Python tu python.org ^(da kem tkinter^).
    pause
    exit /b 1
)
echo       OK - tkinter san sang.
echo.

REM --- 4. Cai dat thanh phan (du an chi dung thu vien chuan) ---
echo [3/4] Kiem tra/cai dat thanh phan phu thuoc...
if exist requirements.txt (
    !PY! -m pip install -r requirements.txt >nul 2>nul
    if errorlevel 1 (
        echo       [bo qua] Khong cai duoc qua pip - du an khong bat buoc goi ngoai.
    ) else (
        echo       OK - khong co goi ngoai bat buoc.
    )
)
echo.

REM --- 5. Khoi chay ung dung ---
echo [4/4] Dang khoi chay ung dung...
echo ------------------------------------------------------------
!PY! run.py
set "EXITCODE=%errorlevel%"

echo ------------------------------------------------------------
if not "%EXITCODE%"=="0" (
    echo [LOI] Ung dung ket thuc voi ma loi %EXITCODE%.
    pause
    exit /b %EXITCODE%
)

echo Da dong ung dung.
pause
endlocal
