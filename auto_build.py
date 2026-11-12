"""
Pivora Auto-Builder & File Watcher
Monitors `watertime.py` and project files for any changes.
Whenever a change is saved, automatically recompiles and updates `downloads/Pivora-Windows-x64.exe`.
"""

import time
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TARGET_FILE = BASE_DIR / "watertime.py"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DIST_DIR = BASE_DIR / "dist"

def run_build():
    print("\n" + "=" * 55)
    print("  [Auto-Build] Code change detected in watertime.py!")
    print("  Compiling fresh Pivora-Windows-x64.exe...")
    print("=" * 55)

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name", "Pivora-Windows-x64",
        "--icon", "app_icon.ico",
        "--add-data", "Animated Boy Walking and Drinking Water.gif;.",
        "--add-data", "gif_frames;gif_frames",
        "--add-data", "app_icon.png;.",
        "watertime.py"
    ]

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode == 0:
        built_exe = DIST_DIR / "Pivora-Windows-x64.exe"
        if built_exe.exists():
            target_exe = DOWNLOADS_DIR / "Pivora-Windows-x64.exe"
            shutil.copy2(built_exe, target_exe)
            print("=" * 55)
            print("  [SUCCESS] Updated downloads/Pivora-Windows-x64.exe!")
            print(f"  Time: {time.strftime('%H:%M:%S')}")
            print("=" * 55 + "\n")
    else:
        print("[ERROR] Build failed. Please check your syntax.\n")

def watch():
    print("=" * 55)
    print("  Pivora Auto-Builder is RUNNING...")
    print("  Watching 'watertime.py' for any saved changes.")
    print("  Press Ctrl+C to stop.")
    print("=" * 55)

    last_mtime = TARGET_FILE.stat().st_mtime if TARGET_FILE.exists() else 0

    while True:
        try:
            time.sleep(2)
            if not TARGET_FILE.exists():
                continue
            curr_mtime = TARGET_FILE.stat().st_mtime
            if curr_mtime != last_mtime:
                last_mtime = curr_mtime
                run_build()
        except KeyboardInterrupt:
            print("\nStopped auto-builder.")
            break
        except Exception as e:
            print(f"Watch error: {e}")

if __name__ == "__main__":
    watch()

