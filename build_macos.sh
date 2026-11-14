#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != Darwin ]]; then
    echo "Run this script on macOS." >&2
    exit 1
fi

python_bin="${PYTHON:-python3}"
arch="$("$python_bin" -c 'import platform; print(platform.machine())')"
case "$arch" in
    arm64|x86_64) ;;
    *) echo "Unsupported Python architecture: $arch" >&2; exit 1 ;;
esac

"$python_bin" -c 'import tkinter; root = tkinter.Tk(); assert root.tk.call("tk", "windowingsystem") == "aqua"; root.destroy()'

"$python_bin" -m PyInstaller --noconfirm --windowed --onedir \
    --name Pivora \
    --target-arch "$arch" \
    --osx-bundle-identifier com.pivora.watertime \
    --icon app_icon.png \
    --hidden-import PIL._tkinter_finder \
    --hidden-import PIL._imagingtk \
    --add-data "Animated Boy Walking and Drinking Water.gif:." \
    --add-data "gif_frames:gif_frames" \
    --add-data "app_icon.png:." \
    watertime.py

codesign --verify --deep --strict dist/Pivora.app
ditto -c -k --keepParent dist/Pivora.app "dist/Pivora-macOS-${arch}.zip"
echo "Created dist/Pivora-macOS-${arch}.zip"
