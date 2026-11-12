#!/usr/bin/env bash
cd "$(dirname "$0")"

# Determine python command (python3 or python)
if command -v python3 &>/dev/null; then
    PY="python3"
elif command -v python &>/dev/null; then
    PY="python"
else
    echo "[ERROR] Python is not installed or not in PATH."
    exit 1
fi

# Check dependencies
$PY -c "import pystray, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Installing dependencies (pystray, Pillow)..."
    pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt
fi

echo "Starting Watertime 💧..."
$PY watertime.py
