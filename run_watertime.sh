#!/usr/bin/env bash
cd "$(dirname "$0")"

# Check if python3-tk is installed
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Tkinter not found. Installing python3-tk..."
    sudo apt update && sudo apt install -y python3-tk
fi

# Check requirements
python3 -c "import pystray, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Installing dependencies (pystray, Pillow)..."
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt
fi

echo "Starting Watertime 💧..."
python3 watertime.py

