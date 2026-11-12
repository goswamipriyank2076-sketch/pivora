"""
Watertime - Walking Mascot Water Reminder
A transparent 3D character walks directly onto your active screen/application,
speaks aloud to remind you to drink water, and tracks your daily water intake!
"""

import json
import math
import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk
from datetime import date
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageTk, ImageDraw
except ImportError:
    print("Missing dependencies. Run: pip install pystray Pillow")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# Constants & Colors
# ─────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

GIF_PATH                 = BASE_DIR / "Animated Boy Walking and Drinking Water.gif"
FRAMES_DIR               = BASE_DIR / "gif_frames"
DATA_FILE                = Path.home() / ".watertime_data.json"
DEFAULT_NAME             = "Priyank"
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_GOAL             = 8
TRANS_COLOR              = "#010101"

BG_COLOR    = "#E1F5FE"
BLUE_MID    = "#0288D1"
BLUE_DARK   = "#01579B"
WHITE       = "#FFFFFF"
TEXT_COLOR  = "#01579B"
BTN_DRINK   = "#0288D1"
BTN_SKIP    = "#78909C"


# ─────────────────────────────────────────────────────────────────
# Single Instance Lock
# ─────────────────────────────────────────────────────────────────
_instance_socket = None

def ensure_single_instance(port=47892):
    """Ensure only one instance of the app runs at a time."""
    global _instance_socket
    import socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(("127.0.0.1", port))
    except socket.error:
        print("[Pivora] Another instance is already running. Exiting duplicate.")
        sys.exit(0)


# ─────────────────────────────────────────────────────────────────
# Text to Speech Voice (Disabled as requested)
# ─────────────────────────────────────────────────────────────────
def speak(text: str):
    """Voice disabled as requested by user."""
    pass


# ─────────────────────────────────────────────────────────────────
# Data Management
# ─────────────────────────────────────────────────────────────────
class WaterData:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        today = str(date.today())
        if DATA_FILE.exists():
            try:
                raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if raw.get("date") != today:
                    return self._fresh(today, raw)
                # Ensure fields exist
                raw.setdefault("user_name", DEFAULT_NAME)
                raw.setdefault("interval_minutes", DEFAULT_INTERVAL_MINUTES)
                raw.setdefault("goal", DEFAULT_GOAL)
                raw.setdefault("glasses_count", 0)
                return raw
            except Exception:
                pass
        return self._fresh(today)

    def _fresh(self, today, prev=None):
        name = prev.get("user_name", DEFAULT_NAME) if prev else DEFAULT_NAME
        interval = prev.get("interval_minutes", DEFAULT_INTERVAL_MINUTES) if prev else DEFAULT_INTERVAL_MINUTES
        goal = prev.get("goal", DEFAULT_GOAL) if prev else DEFAULT_GOAL
        return {
            "date": today,
            "user_name": name,
            "glasses_count": 0,
            "goal": goal,
            "interval_minutes": interval
        }

    def _save(self):
        try:
            DATA_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def add_glass(self):
        self._ensure_today()
        self.data["glasses_count"] += 1
        self._save()

    def reset(self):
        self.data = self._fresh(str(date.today()), self.data)
        self._save()

    def _ensure_today(self):
        today = str(date.today())
        if self.data.get("date") != today:
            self.data = self._fresh(today, self.data)

    @property
    def user_name(self):
        return self.data.get("user_name", DEFAULT_NAME)

    def set_user_name(self, name: str):
        if name.strip():
            self.data["user_name"] = name.strip()
            self._save()

    @property
    def interval_minutes(self):
        return self.data.get("interval_minutes", DEFAULT_INTERVAL_MINUTES)

    def set_interval(self, minutes: int):
        self.data["interval_minutes"] = max(1, int(minutes))
        self._save()

    @property
    def count(self):
        self._ensure_today()
        return self.data.get("glasses_count", 0)

    @property
    def goal(self):
        return self.data.get("goal", DEFAULT_GOAL)

    @property
    def percentage(self):
        return min(100, int((self.count / max(1, self.goal)) * 100))


# ─────────────────────────────────────────────────────────────────
# Auto-Start Helper (Windows & Linux)
# ─────────────────────────────────────────────────────────────────
def is_autostart_enabled():
    if sys.platform == "win32":
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        return (startup_dir / "Watertime.lnk").exists()
    else:
        autostart_dir = Path.home() / ".config" / "autostart"
        return (autostart_dir / "watertime.desktop").exists()

def set_autostart(enable: bool):
    if sys.platform == "win32":
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        shortcut_file = startup_dir / "Watertime.lnk"
        if enable:
            script_path = Path(__file__).resolve()
            py_exe = Path(sys.executable).parent / "pythonw.exe"
            if not py_exe.exists():
                py_exe = Path(sys.executable)
            powershell_cmd = (
                f'$WshShell = New-Object -ComObject WScript.Shell; '
                f'$Shortcut = $WshShell.CreateShortcut("{shortcut_file}"); '
                f'$Shortcut.TargetPath = "{py_exe}"; '
                f'$Shortcut.Arguments = \'"{script_path}" --minimized\'; '
                f'$Shortcut.WorkingDirectory = "{script_path.parent}"; '
                f'$Shortcut.Description = "Watertime Auto Reminder"; '
                f'$Shortcut.Save()'
            )
            os.system(f'powershell -Command "{powershell_cmd}"')
        else:
            if shortcut_file.exists():
                try:
                    shortcut_file.unlink()
                except Exception:
                    pass
    else:
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / "watertime.desktop"
        if enable:
            autostart_dir.mkdir(parents=True, exist_ok=True)
            script_path = Path(__file__).resolve()
            content = f"""[Desktop Entry]
Type=Application
Exec=python3 "{script_path}" --minimized
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Watertime
Comment=Water Drink Reminder
"""
            desktop_file.write_text(content, encoding="utf-8")
        else:
            if desktop_file.exists():
                try:
                    desktop_file.unlink()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────────────
# Tray Icon Generator
# ─────────────────────────────────────────────────────────────────
def create_tray_icon_image(size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 5
    r = size // 3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE_MID, outline=BLUE_DARK, width=2)
    tip_x, tip_y = cx, 4
    left_x, left_y = cx - r + 3, cy - 3
    right_x, right_y = cx + r - 3, cy - 3
    draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], fill=BLUE_MID, outline=BLUE_MID)
    draw.ellipse([cx - r // 3, cy - r // 2, cx, cy - r // 6], fill=(255, 255, 255, 200))
    return img


# ─────────────────────────────────────────────────────────────────
# Transparent Walking Mascot Overlay (Using Animated Boy GIF)
# ─────────────────────────────────────────────────────────────────
def load_gif_frames(master, target_h=320):
    """Load or extract and prepare all 9 frames from the animated GIF."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    frames_paths = sorted(list(FRAMES_DIR.glob("frame_*.png")))
    if not frames_paths and GIF_PATH.exists():
        gif = Image.open(GIF_PATH)
        for i in range(getattr(gif, "n_frames", 1)):
            gif.seek(i)
            rgba = gif.convert("RGBA")
            w, h = rgba.size
            target_w = int(w * (target_h / h))
            resized = rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
            out = Image.new("RGB", (target_w, target_h), (1, 1, 1))
            pix_in = resized.load()
            pix_out = out.load()
            for x in range(target_w):
                for y in range(target_h):
                    r, g, b, a = pix_in[x, y]
                    if a > 100:
                        pix_out[x, y] = (r, g, b)
                    else:
                        pix_out[x, y] = (1, 1, 1)
            fpath = FRAMES_DIR / f"frame_{i:02d}.png"
            out.save(fpath)
        frames_paths = sorted(list(FRAMES_DIR.glob("frame_*.png")))

    tk_frames = []
    for p in frames_paths:
        try:
            im = Image.open(p)
            tk_frames.append(ImageTk.PhotoImage(im, master=master))
        except Exception as e:
            print(f"Error loading frame {p}: {e}")
    return tk_frames


class MascotOverlay:
    """Borderless, transparent window where the 3D animated boy walks from Right to Left into the screen center."""

    WALK_FRAMES = [0, 1, 8, 1]                    # Pure footstep walking cycle holding bottle
    DRINK_FRAMES = [2, 3, 4, 5, 6, 5, 6, 7, 8]    # Raises bottle, drinks refreshing sips, smiles

    def __init__(self, master, data: WaterData, on_close=None):
        self.master = master
        self.data = data
        self.on_close = on_close
        self.is_active = False

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        try:
            self.win.wm_attributes("-transparentcolor", TRANS_COLOR)
        except Exception:
            pass
        self.win.configure(bg=TRANS_COLOR)

        self.w = 340
        self.h = 440
        self.sw = self.win.winfo_screenwidth()
        self.sh = self.win.winfo_screenheight()

        # Target center of screen!
        self.target_x = (self.sw - self.w) // 2
        self.target_y = (self.sh - self.h) // 2
        self.curr_x = self.sw
        self.curr_y = self.target_y
        self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
        self.win.withdraw()

        self.canvas = tk.Canvas(
            self.win, width=self.w, height=self.h,
            bg=TRANS_COLOR, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Load all 9 frames from the animated boy GIF
        self.frames = load_gif_frames(self.win, target_h=320)
        self.canvas.frames_ref = self.frames  # Keep reference so Tkinter doesn't garbage collect
        self.cur_frame = 0

        initial_img = self.frames[0] if self.frames else None
        self.char_id = self.canvas.create_image(self.w // 2, 265, image=initial_img)

        # Speech Text (Shadow + Yellow)
        self.text_shadow = self.canvas.create_text(
            self.w // 2 + 2, 36,
            text="", font=("Segoe UI Black", 15, "bold"),
            fill="#B71C1C", justify="center"
        )
        self.text_main = self.canvas.create_text(
            self.w // 2, 34,
            text="", font=("Segoe UI Black", 15, "bold"),
            fill="#FFD600", justify="center"
        )

        # Floating Buttons
        self.btn_frame_w = tk.Frame(self.win, bg=TRANS_COLOR)
        self.btn_yes = tk.Button(
            self.btn_frame_w, text="  YES  ",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF", fg="#212121",
            activebackground="#EEEEEE", activeforeground="#000000",
            relief="raised", bd=2, cursor="hand2",
            padx=14, pady=5, command=self.on_yes
        )
        self.btn_yes.pack(side="left", padx=8)

        self.btn_later = tk.Button(
            self.btn_frame_w, text="Remind me later",
            font=("Segoe UI", 10),
            bg="#FAFAFA", fg="#424242",
            activebackground="#EEEEEE", activeforeground="#000000",
            relief="raised", bd=2, cursor="hand2",
            padx=10, pady=5, command=self.on_later
        )
        self.btn_later.pack(side="left", padx=4)

        self.btn_window = self.canvas.create_window(self.w // 2, 85, window=self.btn_frame_w)

        self.dismiss_job = None
        self.anim_job = None
        self.move_job = None
        self.step_idx = 0
        self.total_ticks = 0

    def trigger(self):
        """Start the walking animation into the screen from the Right."""
        if self.is_active:
            return
        self.is_active = True
        self.step_idx = 0
        self.total_ticks = 0

        name = self.data.user_name
        text_str = f"Hey, {name}!\nDid you drink water?"
        self.canvas.itemconfig(self.text_shadow, text=text_str)
        self.canvas.itemconfig(self.text_main, text=text_str)

        # Hide text & buttons during walk-in
        self.canvas.itemconfigure(self.text_shadow, state="hidden")
        self.canvas.itemconfigure(self.text_main, state="hidden")
        self.canvas.itemconfigure(self.btn_window, state="hidden")

        if self.frames and self.char_id:
            self.canvas.itemconfig(self.char_id, image=self.frames[0])
            self.canvas.coords(self.char_id, self.w // 2, 265)

        # Start from the RIGHT edge of the screen
        self.curr_x = self.sw
        self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
        self.win.deiconify()
        self.win.lift()
        self.win.wm_attributes("-topmost", True)

        # Start walking cycle & moving Right to Left
        self._cycle_walk()
        self._walk_in_step()

    def _cycle_walk(self):
        """Cycle pure walking frames [0, 1, 8, 1] with realistic human footstep cadence."""
        if not self.is_active or not self.frames:
            return
        f_idx = self.WALK_FRAMES[self.step_idx % len(self.WALK_FRAMES)]
        self.step_idx += 1
        if self.char_id and f_idx < len(self.frames):
            self.canvas.itemconfig(self.char_id, image=self.frames[f_idx])
        self.anim_job = self.win.after(150, self._cycle_walk)

    def _walk_in_step(self):
        """Move from Right to Left toward screen center with footstep bobbing."""
        if not self.is_active:
            return
        speed = 7
        if self.curr_x > self.target_x:
            self.curr_x = max(self.target_x, self.curr_x - speed)
            self.total_ticks += 1
            # Human vertical bobbing synced with steps (4px bounce)
            bob = int(math.sin(self.total_ticks * 0.28) * 4)
            if self.char_id:
                self.canvas.coords(self.char_id, self.w // 2, 265 + bob)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
            self.move_job = self.win.after(22, self._walk_in_step)
        else:
            self.curr_x = self.target_x
            if self.char_id:
                self.canvas.coords(self.char_id, self.w // 2, 265)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")

            # Stop walking motion
            if self.anim_job:
                self.win.after_cancel(self.anim_job)
                self.anim_job = None

            # Arrived at center! Play drinking sequence
            self._play_drink_at_center(0)

    def _play_drink_at_center(self, drink_idx):
        """Character pauses at center, raises bottle, drinks water, and smiles."""
        if not self.is_active or not self.frames:
            return
        if drink_idx < len(self.DRINK_FRAMES):
            f_idx = self.DRINK_FRAMES[drink_idx]
            if self.char_id and f_idx < len(self.frames):
                self.canvas.itemconfig(self.char_id, image=self.frames[f_idx])
            delay = 240 if f_idx in (5, 6) else 150
            self.anim_job = self.win.after(delay, lambda: self._play_drink_at_center(drink_idx + 1))
        else:
            # Done drinking! Stand smiling and reveal question & buttons
            if self.char_id and len(self.frames) > 0:
                self.canvas.itemconfig(self.char_id, image=self.frames[0])
            self.canvas.itemconfigure(self.text_shadow, state="normal")
            self.canvas.itemconfigure(self.text_main, state="normal")
            self.canvas.itemconfigure(self.btn_window, state="normal")

            # Auto-dismiss after 20 seconds
            self.dismiss_job = self.win.after(20000, self.on_later)

    def on_yes(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.data.add_glass()
        # Show positive feedback
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self.canvas.itemconfig(self.text_shadow, text="Awesome!\nStay hydrated! 💧")
        self.canvas.itemconfig(self.text_main, text="Awesome!\nStay hydrated! 💧")
        self.win.after(1100, self._walk_out)

    def on_later(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self.canvas.itemconfig(self.text_shadow, text="Okay!\nDrink soon! 👍")
        self.canvas.itemconfig(self.text_main, text="Okay!\nDrink soon! 👍")
        self.win.after(1000, self._walk_out)

    def _walk_out(self):
        # Hide question
        self.canvas.itemconfigure(self.text_shadow, state="hidden")
        self.canvas.itemconfigure(self.text_main, state="hidden")
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        # Resume pure walking cycle and walk out towards the LEFT
        self.step_idx = 0
        self.total_ticks = 0
        self._cycle_walk()
        self._walk_out_step()

    def _walk_out_step(self):
        if not self.is_active:
            return
        speed = 7
        if self.curr_x > -self.w - 50:
            self.curr_x -= speed
            self.total_ticks += 1
            bob = int(math.sin(self.total_ticks * 0.28) * 4)
            if self.char_id:
                self.canvas.coords(self.char_id, self.w // 2, 265 + bob)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
            self.move_job = self.win.after(22, self._walk_out_step)
        else:
            # Fully off-screen on the left
            if self.anim_job:
                self.win.after_cancel(self.anim_job)
                self.anim_job = None
            self.win.withdraw()
            self.is_active = False
            if self.on_close:
                self.on_close()


# ─────────────────────────────────────────────────────────────────
# Main Application Dashboard & Controller
# ─────────────────────────────────────────────────────────────────
class WatertimeApp:
    def __init__(self):
        self.data = WaterData()
        self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)

        # Root Window (Dashboard)
        self.root = tk.Tk()
        self.root.title("Watertime 💧 - Dashboard & Settings")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        # Clicking [X] now completely QUITS the app cleanly
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self._build_dashboard()
        self._center_window(440, 520)

        # Mascot Overlay
        self.mascot = MascotOverlay(self.root, self.data, on_close=self.on_mascot_closed)

        # Setup System Tray
        self.tray = None
        self._init_tray()

        # Start timer check loop
        self._check_timer_loop()

    def _build_dashboard(self):
        # Header
        tk.Label(
            self.root, text="Watertime 💧",
            font=("Segoe UI", 20, "bold"), fg=BLUE_DARK, bg=BG_COLOR
        ).pack(pady=(15, 2))

        self.lbl_sub = tk.Label(
            self.root, text=f"Walking character will pop up every {self.data.interval_minutes} minutes directly on your screen!",
            font=("Segoe UI", 10), fg="#37474F", bg=BG_COLOR, wraplength=380
        )
        self.lbl_sub.pack(pady=(0, 10))

        # Card Frame for Stats
        card = tk.Frame(self.root, bg=WHITE, padx=15, pady=12, relief="groove", bd=1)
        card.pack(fill="x", padx=25, pady=(0, 12))

        tk.Label(
            card, text="Today's Water Intake",
            font=("Segoe UI", 12, "bold"), fg=BLUE_DARK, bg=WHITE
        ).pack(anchor="w")

        self.lbl_progress = tk.Label(
            card, text=self._get_progress_str(),
            font=("Segoe UI", 11), fg=TEXT_COLOR, bg=WHITE
        )
        self.lbl_progress.pack(anchor="w", pady=(4, 6))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Water.Horizontal.TProgressbar", troughcolor="#E0F7FA", background=BLUE_MID, thickness=16)
        self.pbar = ttk.Progressbar(
            card, style="Water.Horizontal.TProgressbar", length=360, mode="determinate"
        )
        self.pbar["value"] = self.data.percentage
        self.pbar.pack(fill="x", pady=(2, 6))

        # Settings Card
        settings_card = tk.Frame(self.root, bg=WHITE, padx=15, pady=12, relief="groove", bd=1)
        settings_card.pack(fill="x", padx=25, pady=(0, 12))

        # Name row
        row_name = tk.Frame(settings_card, bg=WHITE)
        row_name.pack(fill="x", pady=4)
        tk.Label(row_name, text="Your Name:", font=("Segoe UI", 10, "bold"), fg=TEXT_COLOR, bg=WHITE, width=14, anchor="w").pack(side="left")
        self.entry_name = tk.Entry(row_name, font=("Segoe UI", 10), width=18)
        self.entry_name.insert(0, self.data.user_name)
        self.entry_name.pack(side="left", padx=4)
        self.entry_name.bind("<FocusOut>", self.on_name_changed)
        self.entry_name.bind("<Return>", self.on_name_changed)

        # Interval row
        row_interval = tk.Frame(settings_card, bg=WHITE)
        row_interval.pack(fill="x", pady=4)
        tk.Label(row_interval, text="Remind every:", font=("Segoe UI", 10, "bold"), fg=TEXT_COLOR, bg=WHITE, width=14, anchor="w").pack(side="left")

        self.interval_options = {
            "1 min (Test)": 1,
            "5 mins": 5,
            "10 mins": 10,
            "15 mins": 15,
            "20 mins": 20,
            "30 mins": 30,
            "45 mins": 45,
            "60 mins": 60,
        }
        self.combo_interval = ttk.Combobox(
            row_interval,
            values=list(self.interval_options.keys()),
            width=14, state="readonly", font=("Segoe UI", 9)
        )
        current_mins = self.data.interval_minutes
        found_key = None
        for k, v in self.interval_options.items():
            if v == current_mins:
                found_key = k
                break
        self.combo_interval.set(found_key or f"{current_mins} mins")
        self.combo_interval.bind("<<ComboboxSelected>>", self.on_interval_selected)
        self.combo_interval.pack(side="left", padx=4)

        # Auto-start row
        self.var_autostart = tk.BooleanVar(value=is_autostart_enabled())
        self.chk_autostart = tk.Checkbutton(
            settings_card, text="Start automatically on PC boot",
            variable=self.var_autostart, onvalue=True, offvalue=False,
            font=("Segoe UI", 9), bg=WHITE, fg=TEXT_COLOR,
            activebackground=WHITE, selectcolor=WHITE,
            command=self.toggle_autostart
        )
        self.chk_autostart.pack(anchor="w", pady=(4, 0))

        # Bottom Actions
        actions_frame = tk.Frame(self.root, bg=BG_COLOR)
        actions_frame.pack(pady=(4, 8))

        # Test Walk-in Button
        btn_test = tk.Button(
            actions_frame, text="🚶 Test Walk-in Character Now!",
            font=("Segoe UI", 11, "bold"), bg="#FF9800", fg=WHITE,
            activebackground="#F57C00", activeforeground=WHITE,
            relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
            command=self.test_mascot_now
        )
        btn_test.pack(side="left", padx=6)

        # Minimize to Tray
        btn_min = tk.Button(
            actions_frame, text="Minimize to Tray",
            font=("Segoe UI", 11), bg=BTN_SKIP, fg=WHITE,
            activebackground="#546E7A", activeforeground=WHITE,
            relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
            command=self.hide_dashboard
        )
        btn_min.pack(side="left", padx=6)

    def _get_progress_str(self):
        return f"{self.data.count} of {self.data.goal} glasses today ({self.data.percentage}%)"

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def on_name_changed(self, event=None):
        name = self.entry_name.get().strip()
        if name:
            self.data.set_user_name(name)

    def on_interval_selected(self, event=None):
        choice = self.combo_interval.get()
        mins = self.interval_options.get(choice, 5)
        self.data.set_interval(mins)
        self.next_reminder_time = time.time() + (mins * 60)
        self.lbl_sub.config(text=f"Walking character will pop up every {mins} minutes directly on your screen!")

    def toggle_autostart(self):
        set_autostart(self.var_autostart.get())

    def test_mascot_now(self):
        self.on_name_changed()
        self.mascot.trigger()

    def hide_dashboard(self):
        self.on_name_changed()
        self.root.withdraw()
        if self.tray:
            self.tray.title = f"Watertime 💧 — {self.data.count}/{self.data.goal} glasses"

    def show_dashboard(self, icon=None, item=None):
        self.root.after(0, self._show_dashboard_internal)

    def _show_dashboard_internal(self):
        self.lbl_progress.config(text=self._get_progress_str())
        self.pbar["value"] = self.data.percentage
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_mascot_closed(self):
        self.lbl_progress.config(text=self._get_progress_str())
        self.pbar["value"] = self.data.percentage
        self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)
        if self.tray:
            self.tray.title = f"Watertime 💧 — {self.data.count}/{self.data.goal} glasses"

    def set_interval_from_tray(self, mins):
        self.data.set_interval(mins)
        self.next_reminder_time = time.time() + (mins * 60)
        self.root.after(0, self._sync_interval_ui)

    def _sync_interval_ui(self):
        current_mins = self.data.interval_minutes
        found_key = None
        for k, v in self.interval_options.items():
            if v == current_mins:
                found_key = k
                break
        self.combo_interval.set(found_key or f"{current_mins} mins")
        self.lbl_sub.config(text=f"Walking character will pop up every {current_mins} minutes directly on your screen!")

    # ── Tray Initialization ──
    def _init_tray(self):
        try:
            icon_img = create_tray_icon_image(64)

            def make_interval_item(label, mins):
                return pystray.MenuItem(
                    label,
                    lambda icon, item, m=mins: self.set_interval_from_tray(m),
                    checked=lambda item, m=mins: self.data.interval_minutes == m
                )

            interval_menu = pystray.Menu(
                make_interval_item("1 min (Test)", 1),
                make_interval_item("5 mins", 5),
                make_interval_item("10 mins", 10),
                make_interval_item("15 mins", 15),
                make_interval_item("20 mins", 20),
                make_interval_item("30 mins", 30),
                make_interval_item("45 mins", 45),
                make_interval_item("60 mins", 60),
            )

            menu = pystray.Menu(
                pystray.MenuItem("💧 Watertime Active", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("🚶 Show Mascot Now", lambda: self.root.after(0, self.test_mascot_now)),
                pystray.MenuItem("⏱️ Change Interval", interval_menu),
                pystray.MenuItem("⚙️ Open Settings", self.show_dashboard),
                pystray.MenuItem("🔄 Reset Today's Count", self.reset_count),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Quit Watertime", self.quit_app)
            )
            self.tray = pystray.Icon("Watertime", icon_img, "Watertime 💧 (Running)", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception as e:
            print(f"[Watertime] System tray error: {e}")
            self.tray = None

    def reset_count(self, icon=None, item=None):
        self.data.reset()
        self.root.after(0, lambda: self.lbl_progress.config(text=self._get_progress_str()))
        self.root.after(0, lambda: self.pbar.configure(value=0))

    def _check_timer_loop(self):
        if time.time() >= self.next_reminder_time:
            if not self.mascot.is_active:
                self.mascot.trigger()
            self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)

        self.root.after(1000, self._check_timer_loop)

    def quit_app(self, icon=None, item=None):
        global _instance_socket
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        if _instance_socket:
            try:
                _instance_socket.close()
            except Exception:
                pass
        os._exit(0)

    def run(self):
        if "--minimized" in sys.argv:
            self.hide_dashboard()
        else:
            self._show_dashboard_internal()
            # Immediately trigger the walking character demonstration on startup
            self.root.after(600, self.test_mascot_now)
        self.root.mainloop()


if __name__ == "__main__":
    ensure_single_instance()
    app = WatertimeApp()
    app.run()
