"""
Watertime - Walking Mascot Water Reminder
A transparent 3D character walks directly onto your active screen/application,
displays friendly speech bubbles to remind you to drink water, and tracks daily intake & streaks!
"""

import json
import math
import os
import sys
import time
import random
import threading
import subprocess
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
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
DEFAULT_WORK_START       = 9
DEFAULT_WORK_END         = 21
TRANS_COLOR              = "#010101"

BG_COLOR    = "#E1F5FE"
BLUE_MID    = "#0288D1"
BLUE_DARK   = "#01579B"
WHITE       = "#FFFFFF"
TEXT_COLOR  = "#01579B"
BTN_DRINK   = "#0288D1"
BTN_SKIP    = "#78909C"

MASCOT_QUOTES = [
    "Hey {name}!\nTime for a refreshing sip! 💧",
    "Water break, {name}!\nYour brain needs hydration! 🧠✨",
    "Gulp gulp!\nA cool glass gives you energy! ⚡",
    "Hydration check!\nTake a pause and drink water! 🧊",
    "Stay fresh, {name}!\nDrink a glass to hit your goal! 🎯",
    "Healthy body, sharp mind!\nGrab a cold drink! 🌊",
]


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
# Data Management with History, Streaks, Goal & Active Hours
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
                raw.setdefault("user_name", DEFAULT_NAME)
                raw.setdefault("interval_minutes", DEFAULT_INTERVAL_MINUTES)
                raw.setdefault("goal", DEFAULT_GOAL)
                raw.setdefault("glasses_count", 0)
                raw.setdefault("work_hours_enabled", True)
                raw.setdefault("work_start_hour", DEFAULT_WORK_START)
                raw.setdefault("work_end_hour", DEFAULT_WORK_END)
                raw.setdefault("history", {})
                return raw
            except Exception:
                pass
        return self._fresh(today)

    def _fresh(self, today, prev=None):
        name = prev.get("user_name", DEFAULT_NAME) if prev else DEFAULT_NAME
        interval = prev.get("interval_minutes", DEFAULT_INTERVAL_MINUTES) if prev else DEFAULT_INTERVAL_MINUTES
        goal = prev.get("goal", DEFAULT_GOAL) if prev else DEFAULT_GOAL
        work_enabled = prev.get("work_hours_enabled", True) if prev else True
        work_start = prev.get("work_start_hour", DEFAULT_WORK_START) if prev else DEFAULT_WORK_START
        work_end = prev.get("work_end_hour", DEFAULT_WORK_END) if prev else DEFAULT_WORK_END
        history = dict(prev.get("history", {})) if prev else {}

        if prev and "date" in prev and "glasses_count" in prev:
            history[prev["date"]] = prev["glasses_count"]

        return {
            "date": today,
            "user_name": name,
            "glasses_count": 0,
            "goal": goal,
            "interval_minutes": interval,
            "work_hours_enabled": work_enabled,
            "work_start_hour": work_start,
            "work_end_hour": work_end,
            "history": history
        }

    def _save(self):
        try:
            DATA_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def add_glass(self):
        self._ensure_today()
        self.data["glasses_count"] += 1
        today = str(date.today())
        if "history" not in self.data:
            self.data["history"] = {}
        self.data["history"][today] = self.data["glasses_count"]
        keys = sorted(self.data["history"].keys())
        if len(keys) > 30:
            for old_k in keys[:-30]:
                del self.data["history"][old_k]
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

    def set_goal(self, goal: int):
        self.data["goal"] = max(1, int(goal))
        self._save()

    @property
    def litres_drunk(self):
        return self.count * 0.25

    @property
    def litres_goal(self):
        return self.goal * 0.25

    @property
    def percentage(self):
        return min(100, int((self.count / max(1, self.goal)) * 100))

    @property
    def work_hours_enabled(self):
        return self.data.get("work_hours_enabled", True)

    def set_work_hours_enabled(self, val: bool):
        self.data["work_hours_enabled"] = bool(val)
        self._save()

    @property
    def work_start_hour(self):
        return self.data.get("work_start_hour", DEFAULT_WORK_START)

    def set_work_start_hour(self, h: int):
        self.data["work_start_hour"] = int(h)
        self._save()

    @property
    def work_end_hour(self):
        return self.data.get("work_end_hour", DEFAULT_WORK_END)

    def set_work_end_hour(self, h: int):
        self.data["work_end_hour"] = int(h)
        self._save()

    @property
    def streak(self):
        today = str(date.today())
        today_count = self.count
        goal = self.goal
        history = self.data.get("history", {})

        streak_count = 0
        if today_count >= goal:
            streak_count += 1

        curr_date = date.today() - timedelta(days=1)
        while True:
            d_str = str(curr_date)
            if history.get(d_str, 0) >= goal:
                streak_count += 1
                curr_date -= timedelta(days=1)
            else:
                break
        return streak_count

    def get_last_7_days(self):
        today_date = date.today()
        history = self.data.get("history", {})
        result = []
        for i in range(6, -1, -1):
            d = today_date - timedelta(days=i)
            d_str = str(d)
            cnt = self.count if i == 0 else history.get(d_str, 0)
            result.append((d, d_str, cnt, i == 0))
        return result


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
# Dynamic Tray Icon with Live Count Badge
# ─────────────────────────────────────────────────────────────────
def create_tray_icon_image(count=0, goal=8, size=64):
    """Draw a crisp water droplet with a live numerical badge for current intake."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Water droplet
    cx, cy = size // 2 - 4, size // 2 + 5
    r = size // 3 - 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE_MID, outline=BLUE_DARK, width=2)
    tip_x, tip_y = cx, 4
    left_x, left_y = cx - r + 3, cy - 3
    right_x, right_y = cx + r - 3, cy - 3
    draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], fill=BLUE_MID, outline=BLUE_MID)
    draw.ellipse([cx - r // 3, cy - r // 2, cx, cy - r // 6], fill=(255, 255, 255, 200))

    # Numerical badge in corner
    if count >= 0:
        bx, by = size - 17, size - 17
        br = 15
        bg_col = "#2E7D32" if count >= goal else "#E65100"
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=bg_col, outline="#FFFFFF", width=2)
        txt = str(count) if count < 100 else "99+"
        bbox = draw.textbbox((0, 0), txt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((bx - tw / 2, by - th / 2 - 1), txt, fill="#FFFFFF")

    return img


# ─────────────────────────────────────────────────────────────────
# Transparent Walking Mascot Overlay with Speech Bubble
# ─────────────────────────────────────────────────────────────────
def load_gif_frames(master, target_h=320):
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
    """Borderless, transparent window where 3D character walks in and prompts hydration."""

    WALK_FRAMES = [0, 1, 8, 1]
    DRINK_FRAMES = [2, 3, 4, 5, 6, 5, 6, 7, 8]

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
        self.h = 450
        self.sw = self.win.winfo_screenwidth()
        self.sh = self.win.winfo_screenheight()

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

        self.frames = load_gif_frames(self.win, target_h=320)
        self.canvas.frames_ref = self.frames
        self.cur_frame = 0

        initial_img = self.frames[0] if self.frames else None
        self.char_id = self.canvas.create_image(self.w // 2, 285, image=initial_img)

        # Cartoon Speech Bubble
        self.bubble_items = self._create_speech_bubble()
        self.bubble_text = self.canvas.create_text(
            self.w // 2, 45,
            text="", font=("Segoe UI", 11, "bold"),
            fill=BLUE_DARK, justify="center"
        )

        # Action Buttons
        self.btn_frame_w = tk.Frame(self.win, bg=TRANS_COLOR)
        self.btn_yes = tk.Button(
            self.btn_frame_w, text="  💧 Drink (YES)  ",
            font=("Segoe UI", 10, "bold"),
            bg="#0288D1", fg="#FFFFFF",
            activebackground="#0277BD", activeforeground="#FFFFFF",
            relief="raised", bd=2, cursor="hand2",
            padx=10, pady=4, command=self.on_yes
        )
        self.btn_yes.pack(side="left", padx=6)

        self.btn_later = tk.Button(
            self.btn_frame_w, text="Remind later",
            font=("Segoe UI", 9),
            bg="#ECEFF1", fg="#455A64",
            activebackground="#CFD8DC", activeforeground="#263238",
            relief="raised", bd=2, cursor="hand2",
            padx=8, pady=4, command=self.on_later
        )
        self.btn_later.pack(side="left", padx=4)

        self.btn_window = self.canvas.create_window(self.w // 2, 115, window=self.btn_frame_w)

        self.dismiss_job = None
        self.anim_job = None
        self.move_job = None
        self.step_idx = 0
        self.total_ticks = 0

    def _create_speech_bubble(self):
        x1, y1 = 20, 10
        x2, y2 = self.w - 20, 80
        r = 14
        cx = self.w // 2

        tail = self.canvas.create_polygon([
            cx - 9, y2 - 2,
            cx + 9, y2 - 2,
            cx, y2 + 13
        ], fill="#FFFFFF", outline=BLUE_MID, width=2)

        pts = [
            x1 + r, y1,      x2 - r, y1,      x2, y1,
            x2, y1 + r,      x2, y2 - r,      x2, y2,
            x2 - r, y2,      x1 + r, y2,      x1, y2,
            x1, y2 - r,      x1, y1 + r,      x1, y1
        ]
        bubble = self.canvas.create_polygon(pts, smooth=True, fill="#FFFFFF", outline=BLUE_MID, width=2)
        seam = self.canvas.create_rectangle(cx - 7, y2 - 3, cx + 7, y2 + 1, fill="#FFFFFF", outline="#FFFFFF")
        return [tail, bubble, seam]

    def trigger(self):
        if self.is_active:
            return
        self.is_active = True
        self.step_idx = 0
        self.total_ticks = 0

        for item in self.bubble_items:
            self.canvas.itemconfigure(item, state="hidden")
        self.canvas.itemconfigure(self.bubble_text, state="hidden")
        self.canvas.itemconfigure(self.btn_window, state="hidden")

        if self.frames and self.char_id:
            self.canvas.itemconfig(self.char_id, image=self.frames[0])
            self.canvas.coords(self.char_id, self.w // 2, 285)

        self.curr_x = self.sw
        self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
        self.win.deiconify()
        self.win.lift()
        self.win.wm_attributes("-topmost", True)

        self._cycle_walk()
        self._walk_in_step()

    def _cycle_walk(self):
        if not self.is_active or not self.frames:
            return
        f_idx = self.WALK_FRAMES[self.step_idx % len(self.WALK_FRAMES)]
        self.step_idx += 1
        if self.char_id and f_idx < len(self.frames):
            self.canvas.itemconfig(self.char_id, image=self.frames[f_idx])
        self.anim_job = self.win.after(150, self._cycle_walk)

    def _walk_in_step(self):
        if not self.is_active:
            return
        speed = 7
        if self.curr_x > self.target_x:
            self.curr_x = max(self.target_x, self.curr_x - speed)
            self.total_ticks += 1
            bob = int(math.sin(self.total_ticks * 0.28) * 4)
            if self.char_id:
                self.canvas.coords(self.char_id, self.w // 2, 285 + bob)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
            self.move_job = self.win.after(22, self._walk_in_step)
        else:
            self.curr_x = self.target_x
            if self.char_id:
                self.canvas.coords(self.char_id, self.w // 2, 285)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")

            if self.anim_job:
                self.win.after_cancel(self.anim_job)
                self.anim_job = None

            self._play_drink_at_center(0)

    def _play_drink_at_center(self, drink_idx):
        if not self.is_active or not self.frames:
            return
        if drink_idx < len(self.DRINK_FRAMES):
            f_idx = self.DRINK_FRAMES[drink_idx]
            if self.char_id and f_idx < len(self.frames):
                self.canvas.itemconfig(self.char_id, image=self.frames[f_idx])
            delay = 240 if f_idx in (5, 6) else 150
            self.anim_job = self.win.after(delay, lambda: self._play_drink_at_center(drink_idx + 1))
        else:
            if self.char_id and len(self.frames) > 0:
                self.canvas.itemconfig(self.char_id, image=self.frames[0])

            quote = random.choice(MASCOT_QUOTES).format(name=self.data.user_name)
            self.canvas.itemconfig(self.bubble_text, text=quote)

            for item in self.bubble_items:
                self.canvas.itemconfigure(item, state="normal")
            self.canvas.itemconfigure(self.bubble_text, state="normal")
            self.canvas.itemconfigure(self.btn_window, state="normal")

            self.dismiss_job = self.win.after(20000, self.on_later)

    def on_yes(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.data.add_glass()
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self.canvas.itemconfig(
            self.bubble_text,
            text=f"Awesome, {self.data.user_name}!\nStay healthy & hydrated! 💧✨"
        )
        self.win.after(1100, self._walk_out)

    def on_later(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self.canvas.itemconfig(
            self.bubble_text,
            text=f"No worries, {self.data.user_name}!\nI will remind you soon! 👍"
        )
        self.win.after(1000, self._walk_out)

    def _walk_out(self):
        for item in self.bubble_items:
            self.canvas.itemconfigure(item, state="hidden")
        self.canvas.itemconfigure(self.bubble_text, state="hidden")
        self.canvas.itemconfigure(self.btn_window, state="hidden")

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
                self.canvas.coords(self.char_id, self.w // 2, 285 + bob)
            self.win.geometry(f"{self.w}x{self.h}+{self.curr_x}+{self.target_y}")
            self.move_job = self.win.after(22, self._walk_out_step)
        else:
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
        self.dnd_until = 0
        self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)

        # Root Window
        self.root = tk.Tk()
        self.root.title("Watertime 💧 - Dashboard & Settings")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self._build_dashboard()
        self._center_window(460, 615)

        # Mascot Overlay
        self.mascot = MascotOverlay(self.root, self.data, on_close=self.on_mascot_closed)

        # System Tray
        self.tray = None
        self._init_tray()

        # Global Hotkey Listener (Ctrl + Alt + W)
        self._start_hotkey_listener()

        # Timer loop
        self._check_timer_loop()

    def _build_dashboard(self):
        # 1. Header Frame with Streak Badge
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(fill="x", padx=25, pady=(12, 2))

        tk.Label(
            header_frame, text="Watertime 💧",
            font=("Segoe UI", 18, "bold"), fg=BLUE_DARK, bg=BG_COLOR
        ).pack(side="left")

        self.lbl_streak = tk.Label(
            header_frame, text=f"🔥 {self.data.streak} Day Streak",
            font=("Segoe UI", 10, "bold"), fg="#D84315", bg="#FFECB3",
            padx=10, pady=3, relief="groove", bd=1
        )
        self.lbl_streak.pack(side="right")

        # Status / Snooze Bar
        status_bar = tk.Frame(self.root, bg=BG_COLOR)
        status_bar.pack(fill="x", padx=25, pady=(2, 6))

        self.lbl_status = tk.Label(
            status_bar, text="🟢 Reminders Active",
            font=("Segoe UI", 9, "bold"), fg="#2E7D32", bg=BG_COLOR
        )
        self.lbl_status.pack(side="left")

        # Quick Snooze / DND Buttons
        snooze_btns = tk.Frame(status_bar, bg=BG_COLOR)
        snooze_btns.pack(side="right")
        tk.Label(snooze_btns, text="Snooze:", font=("Segoe UI", 8), fg="#455A64", bg=BG_COLOR).pack(side="left", padx=2)

        for label, mins in [("30m", 30), ("1h", 60), ("2h", 120)]:
            b = tk.Button(
                snooze_btns, text=label, font=("Segoe UI", 8),
                bg="#ECEFF1", fg="#37474F", relief="flat", padx=5, pady=1, cursor="hand2",
                command=lambda m=mins: self.set_snooze(m)
            )
            b.pack(side="left", padx=2)

        self.btn_resume = tk.Button(
            snooze_btns, text="▶ Resume", font=("Segoe UI", 8, "bold"),
            bg="#81C784", fg="#1B5E20", relief="flat", padx=6, pady=1, cursor="hand2",
            command=lambda: self.set_snooze(0)
        )

        # 2. Card: Today's Intake & 7-Day History
        card_stats = tk.Frame(self.root, bg=WHITE, padx=15, pady=8, relief="groove", bd=1)
        card_stats.pack(fill="x", padx=25, pady=(0, 8))

        # Title & Quick Log Button inside card
        stats_top = tk.Frame(card_stats, bg=WHITE)
        stats_top.pack(fill="x")
        tk.Label(
            stats_top, text="Today's Water Intake",
            font=("Segoe UI", 11, "bold"), fg=BLUE_DARK, bg=WHITE
        ).pack(side="left")

        btn_quick_add = tk.Button(
            stats_top, text="+1 Glass (Ctrl+Alt+W)",
            font=("Segoe UI", 8, "bold"), bg="#E1F5FE", fg=BLUE_DARK,
            activebackground="#B3E5FC", relief="groove", bd=1, padx=6, pady=1, cursor="hand2",
            command=self.quick_log_glass
        )
        btn_quick_add.pack(side="right")

        self.lbl_progress = tk.Label(
            card_stats, text=self._get_progress_str(),
            font=("Segoe UI", 10), fg=TEXT_COLOR, bg=WHITE
        )
        self.lbl_progress.pack(anchor="w", pady=(2, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Water.Horizontal.TProgressbar", troughcolor="#E0F7FA", background=BLUE_MID, thickness=13)
        self.pbar = ttk.Progressbar(
            card_stats, style="Water.Horizontal.TProgressbar", length=380, mode="determinate"
        )
        self.pbar["value"] = self.data.percentage
        self.pbar.pack(fill="x", pady=(0, 6))

        # 7-Day Mini Chart
        tk.Label(
            card_stats, text="Last 7 Days History:",
            font=("Segoe UI", 8, "bold"), fg="#546E7A", bg=WHITE
        ).pack(anchor="w")

        self.canvas_chart = tk.Canvas(card_stats, width=380, height=62, bg="#FAFAFA", highlightthickness=1, highlightbackground="#CFD8DC")
        self.canvas_chart.pack(fill="x", pady=(2, 2))
        self._render_weekly_chart()

        # 3. Card: Settings
        settings_card = tk.Frame(self.root, bg=WHITE, padx=15, pady=8, relief="groove", bd=1)
        settings_card.pack(fill="x", padx=25, pady=(0, 8))

        # Name row
        row_name = tk.Frame(settings_card, bg=WHITE)
        row_name.pack(fill="x", pady=2)
        tk.Label(row_name, text="Your Name:", font=("Segoe UI", 9, "bold"), fg=TEXT_COLOR, bg=WHITE, width=15, anchor="w").pack(side="left")
        self.entry_name = tk.Entry(row_name, font=("Segoe UI", 9), width=18)
        self.entry_name.insert(0, self.data.user_name)
        self.entry_name.pack(side="left", padx=4)
        self.entry_name.bind("<FocusOut>", self.on_name_changed)
        self.entry_name.bind("<Return>", self.on_name_changed)

        # Interval row
        row_interval = tk.Frame(settings_card, bg=WHITE)
        row_interval.pack(fill="x", pady=2)
        tk.Label(row_interval, text="Remind every:", font=("Segoe UI", 9, "bold"), fg=TEXT_COLOR, bg=WHITE, width=15, anchor="w").pack(side="left")

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
            row_interval, values=list(self.interval_options.keys()),
            width=15, state="readonly", font=("Segoe UI", 9)
        )
        current_mins = self.data.interval_minutes
        found_key = next((k for k, v in self.interval_options.items() if v == current_mins), f"{current_mins} mins")
        self.combo_interval.set(found_key)
        self.combo_interval.bind("<<ComboboxSelected>>", self.on_interval_selected)
        self.combo_interval.pack(side="left", padx=4)

        # Daily Goal row
        row_goal = tk.Frame(settings_card, bg=WHITE)
        row_goal.pack(fill="x", pady=2)
        tk.Label(row_goal, text="Daily Goal:", font=("Segoe UI", 9, "bold"), fg=TEXT_COLOR, bg=WHITE, width=15, anchor="w").pack(side="left")

        self.goal_options = {
            "6 glasses (1.5 L)": 6,
            "8 glasses (2.0 L)": 8,
            "10 glasses (2.5 L)": 10,
            "12 glasses (3.0 L)": 12,
            "14 glasses (3.5 L)": 14,
        }
        self.combo_goal = ttk.Combobox(
            row_goal, values=list(self.goal_options.keys()),
            width=15, state="readonly", font=("Segoe UI", 9)
        )
        curr_goal = self.data.goal
        found_goal_key = next((k for k, v in self.goal_options.items() if v == curr_goal), f"{curr_goal} glasses")
        self.combo_goal.set(found_goal_key)
        self.combo_goal.bind("<<ComboboxSelected>>", self.on_goal_selected)
        self.combo_goal.pack(side="left", padx=4)

        # Active Hours row
        row_hours = tk.Frame(settings_card, bg=WHITE)
        row_hours.pack(fill="x", pady=2)
        self.var_work_hours = tk.BooleanVar(value=self.data.work_hours_enabled)
        chk_hours = tk.Checkbutton(
            row_hours, text="Active Hours:", variable=self.var_work_hours,
            font=("Segoe UI", 9, "bold"), bg=WHITE, fg=TEXT_COLOR,
            activebackground=WHITE, selectcolor=WHITE,
            command=self.on_work_hours_toggled
        )
        chk_hours.pack(side="left")

        hour_vals = [f"{h:02d}:00" for h in range(24)]
        self.combo_h_start = ttk.Combobox(row_hours, values=hour_vals, width=6, state="readonly", font=("Segoe UI", 8))
        self.combo_h_start.set(f"{self.data.work_start_hour:02d}:00")
        self.combo_h_start.bind("<<ComboboxSelected>>", self.on_work_hours_changed)
        self.combo_h_start.pack(side="left", padx=3)

        tk.Label(row_hours, text="to", font=("Segoe UI", 8), bg=WHITE, fg="#546E7A").pack(side="left")

        self.combo_h_end = ttk.Combobox(row_hours, values=hour_vals, width=6, state="readonly", font=("Segoe UI", 8))
        self.combo_h_end.set(f"{self.data.work_end_hour:02d}:00")
        self.combo_h_end.bind("<<ComboboxSelected>>", self.on_work_hours_changed)
        self.combo_h_end.pack(side="left", padx=3)

        # Auto-start row
        self.var_autostart = tk.BooleanVar(value=is_autostart_enabled())
        self.chk_autostart = tk.Checkbutton(
            settings_card, text="Start automatically on PC boot",
            variable=self.var_autostart, onvalue=True, offvalue=False,
            font=("Segoe UI", 9), bg=WHITE, fg=TEXT_COLOR,
            activebackground=WHITE, selectcolor=WHITE,
            command=self.toggle_autostart
        )
        self.chk_autostart.pack(anchor="w", pady=(2, 0))

        # Shortcut tip banner
        lbl_hint = tk.Label(
            self.root, text="💡 Tip: Press Ctrl + Alt + W anywhere to quickly log a glass!",
            font=("Segoe UI", 8, "italic"), fg="#546E7A", bg=BG_COLOR
        )
        lbl_hint.pack(pady=(0, 4))

        # 4. Bottom Actions
        actions_frame = tk.Frame(self.root, bg=BG_COLOR)
        actions_frame.pack(pady=(0, 6))

        btn_test = tk.Button(
            actions_frame, text="🚶 Test Mascot Now!",
            font=("Segoe UI", 10, "bold"), bg="#FF9800", fg=WHITE,
            activebackground="#F57C00", activeforeground=WHITE,
            relief="flat", bd=0, padx=14, pady=5, cursor="hand2",
            command=self.test_mascot_now
        )
        btn_test.pack(side="left", padx=6)

        btn_min = tk.Button(
            actions_frame, text="Minimize to Tray",
            font=("Segoe UI", 10), bg=BTN_SKIP, fg=WHITE,
            activebackground="#546E7A", activeforeground=WHITE,
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2",
            command=self.hide_dashboard
        )
        btn_min.pack(side="left", padx=6)

    def _render_weekly_chart(self):
        self.canvas_chart.delete("all")
        days = self.data.get_last_7_days()
        w = 380
        col_w = w / 7
        bar_w = 22
        base_y = 45
        max_bar_h = 26
        goal = self.data.goal

        for idx, (d, d_str, cnt, is_today) in enumerate(days):
            cx = idx * col_w + col_w / 2
            bx1 = cx - bar_w / 2
            bx2 = cx + bar_w / 2

            ratio = min(1.0, cnt / max(1, goal))
            bar_h = max(3, int(ratio * max_bar_h))
            by1 = base_y - bar_h
            by2 = base_y

            if cnt >= goal:
                fill_col = "#4CAF50"
            elif cnt > 0:
                fill_col = BLUE_MID
            else:
                fill_col = "#CFD8DC"

            outline_col = "#FF9800" if is_today else fill_col
            border_w = 2 if is_today else 1

            self.canvas_chart.create_rectangle(bx1, base_y - max_bar_h, bx2, base_y, fill="#ECEFF1", outline="", width=0)
            self.canvas_chart.create_rectangle(bx1, by1, bx2, by2, fill=fill_col, outline=outline_col, width=border_w)

            self.canvas_chart.create_text(
                cx, by1 - 5, text=str(cnt),
                font=("Segoe UI", 8, "bold" if is_today else "normal"), fill="#37474F"
            )
            day_name = d.strftime("%a")
            self.canvas_chart.create_text(
                cx, base_y + 9, text=day_name,
                font=("Segoe UI", 8, "bold" if is_today else "normal"),
                fill="#01579B" if is_today else "#78909C"
            )

    def _get_progress_str(self):
        return (f"{self.data.count} of {self.data.goal} glasses "
                f"({self.data.litres_drunk:.2f}L / {self.data.litres_goal:.1f}L) • {self.data.percentage}%")

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
        self._update_status_label()

    def on_goal_selected(self, event=None):
        choice = self.combo_goal.get()
        goal = self.goal_options.get(choice, 8)
        self.data.set_goal(goal)
        self._refresh_ui_progress()

    def on_work_hours_toggled(self):
        self.data.set_work_hours_enabled(self.var_work_hours.get())
        self._update_status_label()

    def on_work_hours_changed(self, event=None):
        try:
            start_h = int(self.combo_h_start.get().split(":")[0])
            end_h = int(self.combo_h_end.get().split(":")[0])
            self.data.set_work_start_hour(start_h)
            self.data.set_work_end_hour(end_h)
            self._update_status_label()
        except Exception:
            pass

    def toggle_autostart(self):
        set_autostart(self.var_autostart.get())

    def set_snooze(self, minutes: int):
        if minutes == 0:
            self.dnd_until = 0
            self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)
        else:
            self.dnd_until = time.time() + (minutes * 60)
            self.next_reminder_time = self.dnd_until
        self._update_status_label()

    # ── Quick Log (Hotkey or Tray or Dashboard) ──
    def quick_log_glass(self, icon=None, item=None):
        """Immediately log 1 glass from anywhere."""
        self.data.add_glass()
        self._refresh_ui_progress()
        toast_msg = f"💧 +1 Glass Logged! ({self.data.count}/{self.data.goal} glasses • {self.data.litres_drunk:.2f}L)"
        self.show_quick_toast(toast_msg)
        if self.tray:
            try:
                self.tray.notify("💧 Water Logged!", toast_msg)
            except Exception:
                pass

    def show_quick_toast(self, text: str):
        """Show a temporary floating notification pill in the bottom right corner."""
        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.wm_attributes("-topmost", True)
            try:
                toast.wm_attributes("-alpha", 0.94)
            except Exception:
                pass
            toast.configure(bg="#01579B")

            lbl = tk.Label(
                toast, text=text,
                font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#01579B",
                padx=16, pady=8
            )
            lbl.pack()

            toast.update_idletasks()
            tw = toast.winfo_width()
            th = toast.winfo_height()
            sw = toast.winfo_screenwidth()
            sh = toast.winfo_screenheight()
            x = sw - tw - 24
            y = sh - th - 55
            toast.geometry(f"+{x}+{y}")
            toast.after(1600, toast.destroy)
        except Exception:
            pass

    # ── Global Hotkey Listener (Ctrl + Alt + W) ──
    def _start_hotkey_listener(self):
        if sys.platform != "win32":
            return
        t = threading.Thread(target=self._hotkey_loop, daemon=True)
        t.start()

    def _hotkey_loop(self):
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        HOTKEY_ID = 4789
        MOD_ALT = 0x0001
        MOD_CONTROL = 0x0002
        VK_W = 0x57  # 'W' key

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_W):
            return

        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                    self.root.after(0, self.quick_log_glass)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            pass
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def _update_status_label(self):
        now = time.time()
        curr_hour = time.localtime().tm_hour

        # Check Snooze
        if self.dnd_until > now:
            mins_left = max(1, int((self.dnd_until - now) / 60))
            until_str = time.strftime("%H:%M", time.localtime(self.dnd_until))
            self.lbl_status.config(text=f"⏸️ Snoozed ({mins_left}m left, until {until_str})", fg="#E65100")
            self.btn_resume.pack(side="left", padx=2)
            if self.tray:
                self.tray.title = f"Watertime 💧 [Snoozed until {until_str}] • {self.data.count}/{self.data.goal} glasses ({self.data.litres_drunk:.2f}L)"
            return
        else:
            self.btn_resume.pack_forget()

        # Check Active Hours
        if self.data.work_hours_enabled:
            s_h = self.data.work_start_hour
            e_h = self.data.work_end_hour
            if not (s_h <= curr_hour < e_h):
                self.lbl_status.config(text=f"🌙 Outside Active Hours (Resumes at {s_h:02d}:00)", fg="#546E7A")
                if self.tray:
                    self.tray.title = f"Watertime 💧 [Quiet Hours until {s_h:02d}:00] • {self.data.count}/{self.data.goal}"
                return

        # Normal Active
        secs_left = max(0, int(self.next_reminder_time - now))
        mins_left = secs_left // 60
        self.lbl_status.config(text=f"🟢 Active (Next reminder in {mins_left}m)", fg="#2E7D32")
        if self.tray:
            self.tray.title = f"Watertime 💧 — {self.data.count}/{self.data.goal} glasses ({self.data.litres_drunk:.2f}L) • Next in {mins_left}m"

    def _refresh_ui_progress(self):
        self.lbl_progress.config(text=self._get_progress_str())
        self.pbar["value"] = self.data.percentage
        self.lbl_streak.config(text=f"🔥 {self.data.streak} Day Streak")
        self._render_weekly_chart()
        self._update_status_label()
        # Dynamically refresh tray icon badge with current count
        if self.tray:
            try:
                self.tray.icon = create_tray_icon_image(self.data.count, self.data.goal, 64)
            except Exception:
                pass

    def test_mascot_now(self):
        self.on_name_changed()
        self.mascot.trigger()

    def hide_dashboard(self):
        self.on_name_changed()
        self.root.withdraw()
        self._update_status_label()

    def show_dashboard(self, icon=None, item=None):
        self.root.after(0, self._show_dashboard_internal)

    def _show_dashboard_internal(self):
        self._refresh_ui_progress()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_mascot_closed(self):
        self._refresh_ui_progress()
        self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)

    def set_interval_from_tray(self, mins):
        self.data.set_interval(mins)
        self.next_reminder_time = time.time() + (mins * 60)
        self.root.after(0, self._sync_interval_ui)

    def _sync_interval_ui(self):
        current_mins = self.data.interval_minutes
        found_key = next((k for k, v in self.interval_options.items() if v == current_mins), f"{current_mins} mins")
        self.combo_interval.set(found_key)
        self._update_status_label()

    # ── Tray Initialization ──
    def _init_tray(self):
        try:
            icon_img = create_tray_icon_image(self.data.count, self.data.goal, 64)

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

            snooze_menu = pystray.Menu(
                pystray.MenuItem("⏸️ Snooze 30 mins", lambda: self.root.after(0, lambda: self.set_snooze(30))),
                pystray.MenuItem("⏸️ Snooze 1 hour", lambda: self.root.after(0, lambda: self.set_snooze(60))),
                pystray.MenuItem("⏸️ Snooze 2 hours", lambda: self.root.after(0, lambda: self.set_snooze(120))),
                pystray.MenuItem("▶️ Resume Reminders", lambda: self.root.after(0, lambda: self.set_snooze(0))),
            )

            menu = pystray.Menu(
                pystray.MenuItem("💧 Watertime Active", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("➕ Quick Log 1 Glass (Ctrl+Alt+W)", self.quick_log_glass),
                pystray.MenuItem("🚶 Show Mascot Now", lambda: self.root.after(0, self.test_mascot_now)),
                pystray.MenuItem("🔕 Snooze / DND", snooze_menu),
                pystray.MenuItem("⏱️ Change Interval", interval_menu),
                pystray.MenuItem("⚙️ Open Settings", self.show_dashboard),
                pystray.MenuItem("🔄 Reset Today's Count", self.reset_count),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Quit Watertime", self.quit_app)
            )
            self.tray = pystray.Icon("Watertime", icon_img, "Watertime 💧", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception as e:
            print(f"[Watertime] System tray error: {e}")
            self.tray = None

    def reset_count(self, icon=None, item=None):
        self.data.reset()
        self.root.after(0, self._refresh_ui_progress)

    def _check_timer_loop(self):
        now = time.time()
        curr_hour = time.localtime().tm_hour

        # Check Snooze
        if self.dnd_until > 0:
            if now < self.dnd_until:
                self._update_status_label()
                self.root.after(1000, self._check_timer_loop)
                return
            else:
                self.dnd_until = 0

        # Check Working Hours
        if self.data.work_hours_enabled:
            s_h = self.data.work_start_hour
            e_h = self.data.work_end_hour
            if not (s_h <= curr_hour < e_h):
                self._update_status_label()
                self.root.after(1000, self._check_timer_loop)
                return

        # Check interval trigger
        if now >= self.next_reminder_time:
            if not self.mascot.is_active:
                self.mascot.trigger()
            self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)

        self._update_status_label()
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
            self.root.after(600, self.test_mascot_now)
        self.root.mainloop()


if __name__ == "__main__":
    ensure_single_instance()
    app = WatertimeApp()
    app.run()
