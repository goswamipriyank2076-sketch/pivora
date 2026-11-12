#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "  Building Pivora for Linux..."
echo "=============================================="

# Install dependencies
pip3 install -r requirements.txt

# Clean old build
rm -rf build dist

# Compile with PyInstaller
pyinstaller --noconsole --onefile \
    --name "Pivora-Linux" \
    --add-data "Animated Boy Walking and Drinking Water.gif:." \
    --add-data "gif_frames:gif_frames" \
    --add-data "app_icon.png:." \
    watertime.py

chmod +x dist/Pivora-Linux
echo "=============================================="
echo "[SUCCESS] Linux executable created:"
echo "  dist/Pivora-Linux"
echo "=============================================="
