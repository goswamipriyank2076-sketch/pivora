@echo off
cd /d "%~dp0"
echo ==============================================
echo   Building Pivora.exe for Windows...
echo ==============================================

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH!
    pause
    exit /b 1
)

:: Install/update dependencies
echo [1/3] Checking dependencies (PyInstaller, Pillow, pystray)...
pip install -r requirements.txt

:: Clean previous builds
echo [2/3] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Compile with PyInstaller
echo [3/3] Compiling standalone Pivora.exe...
pyinstaller --noconsole --onefile --name "Pivora" --icon "app_icon.ico" --add-data "Animated Boy Walking and Drinking Water.gif;." --add-data "gif_frames;gif_frames" --add-data "app_icon.png;." watertime.py

if %errorlevel% equ 0 (
    echo ==============================================
    echo [SUCCESS] Build complete!
    echo Your standalone executable is ready:
    echo   dist\Pivora.exe
    echo ==============================================
) else (
    echo [ERROR] Build failed. Please check the logs above.
)
pause
