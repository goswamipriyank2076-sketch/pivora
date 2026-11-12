# Pivora 💧 (Watertime)

A desktop water reminder app that brings a transparent animated character directly onto your screen to remind you to drink water and track your daily hydration!

---

## ✨ Features

- **Animated Mascot Overlay:** A friendly 3D animated character walks directly onto your active screen/application to remind you to drink water.
- **Interactive Prompts:** Convenient `YES` and `Remind me later` buttons to quickly log your water intake or dismiss.
- **Daily Intake Tracking:** Set your daily goal and track your glasses throughout the day with a live progress bar.
- **Customizable Intervals:** Choose reminder intervals (e.g., 5 min, 10 min, 15 min, 30 min, 60 min).
- **Auto-Start on Boot:** Toggle automatic startup on Windows boot with a single click.
- **System Tray Integration:** Runs quietly in the background without cluttering your taskbar.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (Python 3.12 recommended)
- Windows / Linux / macOS

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/goswamipriyank2076-sketch/pivora.git
   cd pivora
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   - **Windows:** Double-click `run_watertime.bat` or run:
     ```bash
     python watertime.py
     ```
   - **Linux / macOS:**
     ```bash
     chmod +x run_watertime.sh
     ./run_watertime.sh
     ```

---

## 🛠️ Tech Stack

- **Python** & **Tkinter**
- **Pillow (PIL)** for GIF frame rendering & transparency chroma keying
- **Pystray** for system tray integration

---

## 📄 License

MIT License. Stay hydrated! 💧
