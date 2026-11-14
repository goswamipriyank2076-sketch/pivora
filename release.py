"""
Pivora Version Release Manager
Usage:
    python release.py <version> [message]
Examples:
    python release.py 1.0.5 "Fix mascot border and startup check"
    python release.py 1.1.0 "Add custom sound notifications"
"""

import sys
import re
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VERSION_FILE = BASE_DIR / "version_info.txt"

def update_version_info(ver_str: str):
    parts = ver_str.split(".")
    while len(parts) < 4:
        parts.append("0")
    major, minor, patch, build = parts[:4]
    tuple_str = f"({major}, {minor}, {patch}, {build})"
    full_ver = f"{major}.{minor}.{patch}.{build}"

    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={tuple_str},
    prodvers={tuple_str},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Pivora App'),
            StringStruct('FileDescription', 'Pivora - Daily Water Companion'),
            StringStruct('FileVersion', '{full_ver}'),
            StringStruct('InternalName', 'Pivora'),
            StringStruct('LegalCopyright', 'Copyright (c) 2026 Pivora. All rights reserved.'),
            StringStruct('OriginalFilename', 'Pivora-Windows-x64.exe'),
            StringStruct('ProductName', 'Pivora - Daily Water Companion'),
            StringStruct('ProductVersion', '{full_ver}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    VERSION_FILE.write_text(content, encoding="utf-8")
    print(f"✅ Updated version_info.txt to {full_ver}")

def get_next_auto_version():
    try:
        res = subprocess.run(["git", "tag", "--sort=-v:refname"], capture_output=True, text=True, check=True)
        tags = [t.strip().lstrip("v") for t in res.stdout.splitlines() if t.strip() and re.match(r"^v?\d+\.\d+", t.strip())]
        if tags:
            latest = tags[0]
            parts = [int(p) for p in latest.split(".") if p.isdigit()]
            while len(parts) < 3:
                parts.append(0)
            parts[-1] += 1
            return ".".join(str(p) for p in parts)
    except Exception:
        pass
    return "1.0.6"

def main():
    # If version not specified, automatically calculate next version (e.g. 1.0.5 -> 1.0.6)
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        raw_ver = sys.argv[1].lstrip("v")
        message = sys.argv[2] if len(sys.argv) > 2 else f"Release v{raw_ver}"
    else:
        raw_ver = get_next_auto_version()
        message = sys.argv[1] if (len(sys.argv) >= 2 and sys.argv[1].startswith("-m")) else f"Automated Release v{raw_ver}"

    if not re.match(r"^\d+\.\d+(?:\.\d+)?$", raw_ver):
        print(f"❌ Invalid version format '{raw_ver}'. Please use format like 1.0.6 or 1.1.0")
        sys.exit(1)

    tag_name = f"v{raw_ver}"

    print("=" * 60)
    print(f"  🚀 Releasing Pivora {tag_name}")
    print("=" * 60)

    # 1. Update version_info.txt
    update_version_info(raw_ver)

    # 2. Stage all changed files
    subprocess.run(["git", "add", "-A"], cwd=str(BASE_DIR), check=True)

    # 3. Commit
    commit_msg = f"Release {tag_name}: {message}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR))

    # 4. Create annotated tag
    print(f"🏷️ Creating tag {tag_name}...")
    subprocess.run(["git", "tag", "-a", tag_name, "-m", message], cwd=str(BASE_DIR), check=True)

    # 5. Push commit and tag to GitHub
    print("📤 Pushing code and tag to GitHub...")
    subprocess.run(["git", "push", "origin", "main", "--tags"], cwd=str(BASE_DIR), check=True)

    print("=" * 60)
    print(f"  🎉 SUCCESS! {tag_name} has been published!")
    print(f"  GitHub Actions is now building Windows, Linux, and macOS packages for {tag_name}.")
    print("  You can view this version release at:")
    print(f"  👉 https://github.com/goswamipriyank2076-sketch/pivora/releases/tag/{tag_name}")
    print("=" * 60)

if __name__ == "__main__":
    main()

