@echo off
cd /d "%~dp0"
if exist "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\pythonw.exe" (
    start "" "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\pythonw.exe" "%~dp0watertime.py"
) else (
    start "" pythonw "%~dp0watertime.py"
)
