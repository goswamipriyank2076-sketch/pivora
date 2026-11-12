# Pivora 💧 (Watertime)

A desktop water reminder application that brings a transparent animated character directly onto your screen to keep you hydrated throughout the day!

Available for both **Windows** and **Linux**.

---

## ✨ Features

- **Animated Mascot Overlay:** A friendly 3D animated character walks directly onto your active screen to remind you to drink water.
- **Cartoon Speech Bubble Dialogues:** Beautiful comic-style speech bubbles with rotating, personalized hydration tips & quotes.
- **Daily Streak Counter (🔥):** Tracks consecutive daily goal completions to keep you motivated.
- **7-Day Visual History Chart:** Built-in interactive bar chart showing your hydration stats over the last 7 days.
- **Custom Goal & Litres Counter:** Set daily targets (6, 8, 10, 12, 14 glasses) with automatic Litres (L) calculations (250ml/glass).
- **Meeting / Snooze / DND Mode (🔕):** Quick 30m, 1h, or 2h snooze directly from the System Tray and Dashboard.
- **Active Hours Schedule:** Set customizable working hours (e.g. 09:00 to 21:00) so reminders never interrupt your sleep.
- **Interactive Prompts:** Quick `YES` and `Remind me later` buttons with positive feedback.
- **System Tray Quick Controls:** Adjust intervals, snooze reminders, or test animations directly from your taskbar.
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
