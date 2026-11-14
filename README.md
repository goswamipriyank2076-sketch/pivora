# Pivora 💧 (Watertime)

A desktop water reminder application that brings a transparent animated character directly onto your screen to keep you hydrated throughout the day!

Available for **Windows** and **Linux**, with desktop builds for **macOS** included in the release workflow.

---

## 🚀 Quick Download (Ready-to-Run • No Python Required)

| Platform | Download Link | Quick Instructions |
|---|---|---|
| **🪟 Windows (10 / 11)** | [📥 **Download Pivora-Windows-x64.exe**](https://github.com/goswamipriyank2076-sketch/pivora/releases/latest/download/Pivora-Windows-x64.exe) | Double-click to run! |
| **🐧 Linux / Ubuntu** | [📥 **Download Pivora-Linux-x86_64**](https://github.com/goswamipriyank2076-sketch/pivora/releases/latest/download/Pivora-Linux-x86_64) | Mark executable (`chmod +x`) & double-click! |
| **macOS (Apple Silicon / M-series)** | [Download Apple Silicon ZIP](https://github.com/goswamipriyank2076-sketch/pivora/releases/latest/download/Pivora-macOS-arm64.zip) | Extract the ZIP and open `Pivora.app`. |
| **macOS (Intel)** | [Download Intel ZIP](https://github.com/goswamipriyank2076-sketch/pivora/releases/latest/download/Pivora-macOS-x86_64.zip) | Extract the ZIP and open `Pivora.app`. |

Get the current builds from the links above or the [GitHub Releases](https://github.com/goswamipriyank2076-sketch/pivora/releases) page.

---

## ✨ Features

- **Animated Mascot Overlay:** A friendly 3D animated character walks directly onto your active screen to remind you to drink water.
- **Cartoon Speech Bubble Dialogues:** Beautiful comic-style speech bubbles with rotating, personalized hydration tips & quotes.
- **Daily Streak Counter (🔥):** Tracks consecutive daily goal completions to keep you motivated.
- **7-Day Visual History Chart:** Built-in interactive bar chart showing your hydration stats over the last 7 days.
- **Custom Goal & Litres Counter:** Set daily targets (6, 8, 10, 12, 14 glasses) with automatic Litres (L) calculations (250ml/glass).
- **Meeting / Snooze / DND Mode (🔕):** Quick 30m, 1h, or 2h snooze directly from the System Tray and Dashboard.
- **Active Hours Schedule:** Set customizable working hours (e.g. 09:00 to 21:00) so reminders never interrupt your sleep.
- **Quick Log:** Add a glass from the tray or menu bar and get an on-screen confirmation. On Windows, `Ctrl + Alt + W` also works globally.
- **Dynamic Tray Icon with Live Badge (🏷️):** The taskbar tray icon dynamically displays your current glass count in a color-coded numerical badge (orange -> green when target reached).
- **Dynamic Tray Tooltip:** Hovering over the tray icon displays your live glass count, volume in litres, and countdown to the next reminder.
- **System Tray Quick Controls:** Adjust intervals, snooze reminders, or test animations directly from your taskbar.
- **Automatic Startup:** Enable Pivora to start automatically when you sign in.

---

## 📦 For Customers (End Users)

No Python or terminal required! Download the pre-built standalone executable for your operating system from the [Releases](https://github.com/goswamipriyank2076-sketch/pivora/releases) page:

- **Windows:** Download `Pivora-Windows-x64.exe` and double-click to run!
- **Linux:** Download `Pivora-Linux-x86_64`, mark as executable (`chmod +x Pivora-Linux-x86_64`), and run!
- **macOS:** Use the download table above to get the ZIP for your Mac. Extract it, move `Pivora.app` to Applications, and open it. The build workflow also attaches these ZIPs to new tagged releases.

On macOS, closing the dashboard keeps reminders running in the menu bar. Use the menu bar icon to log a glass, open settings, snooze, or quit. Automatic meeting and screen-share detection is available on Windows. The macOS builds use ad hoc signing and may require first-launch approval under Privacy & Security. See [Apple’s guidance on opening downloaded apps](https://support.apple.com/en-us/102445).

The Linux release build targets Ubuntu 22.04 LTS (x86-64, glibc 2.35). If an older
download fails with `GLIBC_2.38 not found`, use a release built with this baseline
once available, or run from source on Ubuntu 22.04 or newer.

---

## 🛠️ For Developers

### Prerequisites

- Python 3.9+ (Python 3.12 recommended)
- `pip install -r requirements.txt`

### Running from Source

- **Windows:** Double-click `run_watertime.bat` or run:
  ```bash
  python watertime.py
  ```
- **Ubuntu 22.04 or newer** (from the project directory):
  ```bash
  sudo apt install python3-tk python3-venv
  python3 -m venv .venv
  .venv/bin/python -m pip install pystray Pillow python-xlib
  .venv/bin/python watertime.py
  ```
- **macOS** (use Python 3.12 from [python.org](https://www.python.org/downloads/macos/) with Aqua Tk):
  ```bash
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python watertime.py
  ```

### Building Standalone Executables Locally

- **Windows (.exe):** Double-click `build_windows.bat` or run:
  ```bash
  pyinstaller --noconsole --onefile --name "Pivora" --icon "app_icon.ico" --add-data "Animated Boy Walking and Drinking Water.gif;." --add-data "gif_frames;gif_frames" --add-data "app_icon.png;." watertime.py
  ```
- **Linux:** Run `build_linux.sh` on Ubuntu 22.04 x86-64 to match the release
  baseline. Builds made on newer systems can require a newer glibc.
- **macOS:** After installing the dependencies into the virtual environment above, run
  `PYTHON=.venv/bin/python bash build_macos.sh`. This creates `dist/Pivora.app`
  and a ZIP for the architecture of the Python interpreter. GitHub Actions builds
  and checks both architectures on macOS 15 runners.

---

## 📄 License

MIT License. Stay hydrated! 💧
