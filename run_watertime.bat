@echo off
cd /d "%~dp0"

REM 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 2. Check and install dependencies if missing
python -c "import pystray, PIL" >nul 2>nul
if %errorlevel% neq 0 (
    echo [Watertime] Installing required libraries Pillow and pystray...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM 3. Launch Watertime
echo [Pivora] Starting Watertime...
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw watertime.py
) else (
    start "" python watertime.py
)
exit /b 0
