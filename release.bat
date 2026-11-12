@echo off
cd /d "%~dp0"
echo ==============================================
echo   Publishing Next Automated Version Release...
echo ==============================================
python release.py
pause
