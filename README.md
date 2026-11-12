# Pivora 💧 (Watertime)

A desktop water reminder application that brings a transparent animated character directly onto your screen to keep you hydrated throughout the day!

Available for both **Windows** and **Linux**.

---

## ✨ Features

- **Animated Mascot Overlay:** A friendly 3D animated character walks directly onto your active screen to remind you to drink water.
- **Natural Walking & Drinking:** Walks in from the left, takes refreshing sips from his water bottle, and asks if you've hydrated.
- **Interactive Prompts:** Quick `YES` and `Remind me later` buttons with positive feedback.
- **Daily Intake Tracking:** Set your daily target and monitor progress with a live progress bar.
- **Customizable Intervals:** Choose reminder intervals (e.g., 5 min, 10 min, 15 min, 30 min, 60 min).
- **Auto-Start on Boot:** Toggle automatic startup on system boot with a single click.
- **Cross-Platform:** Native support for both **Windows** and **Linux**.

---

## 📦 For Customers (End Users)

No Python or terminal required! Download the pre-built standalone executable for your operating system from the [Releases](https://github.com/goswamipriyank2076-sketch/pivora/releases) page:

- **Windows:** Download `Pivora-Windows-x64.exe` and double-click to run!
- **Linux:** Download `Pivora-Linux-x86_64`, mark as executable (`chmod +x Pivora-Linux-x86_64`), and run!

---

## 🛠️ For Developers

### Prerequisites

- Python 3.8+ (Python 3.12 recommended)
- `pip install -r requirements.txt`

### Running from Source

- **Windows:** Double-click `run_watertime.bat` or run:
  ```bash
  python watertime.py
  ```
- **Linux:**
  ```bash
  chmod +x run_watertime.sh
  ./run_watertime.sh
  ```

### Building Standalone Executables Locally

- **Windows (.exe):** Double-click `build_windows.bat` or run:
  ```bash
  pyinstaller --noconsole --onefile --name "Pivora" --icon "app_icon.ico" --add-data "Animated Boy Walking and Drinking Water.gif;." --add-data "gif_frames;gif_frames" --add-data "app_icon.png;." watertime.py
  ```
- **Linux:** Run `build_linux.sh`

---

## 📄 License

MIT License. Stay hydrated! 💧
