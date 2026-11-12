"""
Watertime (Pivora) - Walking Mascot Water Reminder
Handcrafted Consumer Edition featuring the 3D Boy Mascot, Interactive Glasses, and Hydration Analytics.
"""

import json
import math
import os
import sys
import time
import random
import re
import threading
import subprocess
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError:
    print("Missing dependencies. Run: pip install pystray Pillow")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# Brand Palette & Paths
# ─────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

GIF_PATH                 = BASE_DIR / "Animated Boy Walking and Drinking Water.gif"
APP_ICON_PATH            = BASE_DIR / "app_icon.png"
FRAMES_DIR               = BASE_DIR / "gif_frames"
DATA_FILE                = Path.home() / ".watertime_data.json"
DEFAULT_NAME             = "Priyank"
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_GOAL             = 8
DEFAULT_WORK_START       = 9
DEFAULT_WORK_END         = 18
TRANS_COLOR              = "#010101"

# Warm, Friendly Hydration Palette
BG_MAIN          = "#F0F9FF"   # Soft Sky Blue Mist
CARD_BG          = "#FFFFFF"   # Pure White Card
CARD_BORDER      = "#BAE6FD"   # Soft Ocean Border
CARD_HOVER       = "#E0F2FE"   # Subtle Card Hover
TEXT_DARK        = "#0F172A"   # Deep Slate Text
TEXT_PRIMARY     = "#0369A1"   # Ocean Navy Text
TEXT_SECONDARY   = "#475569"   # Muted Slate
TEXT_MUTED       = "#64748B"   # Subtle Slate
OCEAN_BLUE       = "#0284C7"   # Vibrant Water Blue
OCEAN_DARK       = "#0369A1"   # Deep Ocean Blue
EMERALD_GREEN    = "#10B981"   # Target Completed
AMBER_GOLD       = "#F59E0B"   # Warm Streak Gold

MASCOT_QUOTES = [
    ("Hey {name}!", "Time for a refreshing sip!", "💧"),
    ("Water break, {name}!", "Your brain needs hydration!", "✨"),
    ("Gulp gulp, {name}!", "A cool glass gives you energy!", "⚡"),
    ("Hydration check!", "Take a pause and drink water!", "🧊"),
    ("Stay fresh, {name}!", "Drink a glass to hit your goal!", "🎯"),
    ("Healthy body, sharp mind!", "Grab a cold drink!", "🌊"),
]


# ─────────────────────────────────────────────────────────────────
# Single Instance Lock with Auto-Wakeup
# ─────────────────────────────────────────────────────────────────
_instance_socket = None

def ensure_single_instance(port=47892):
    """Ensure only one instance runs at a time; wake up existing window if launched again."""
    global _instance_socket
    import socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(("127.0.0.1", port))
        _instance_socket.listen(5)
    except socket.error:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", port))
            client.sendall(b"SHOW")
            client.close()
        except Exception:
            pass
        print("[Pivora] App is already running in background. Activated existing window.")
        sys.exit(0)


# ─────────────────────────────────────────────────────────────────
# Asset Helpers: Mascot & App Icon
# ─────────────────────────────────────────────────────────────────
def load_app_icon_image(size=38):
    if APP_ICON_PATH.exists():
        try:
            im = Image.open(APP_ICON_PATH).convert("RGBA")
            return im.resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            pass
    return None

def load_dashboard_mascot_image(target_h=150):
    """Load smiling mascot character from GIF frame with clean transparent composite."""
    if not GIF_PATH.exists():
        return None
    try:
        gif = Image.open(GIF_PATH)
        frame_idx = 8 if getattr(gif, "n_frames", 1) > 8 else 0
        gif.seek(frame_idx)
        rgba = gif.convert("RGBA")
        bbox = rgba.getbbox()
        cropped = rgba.crop(bbox) if bbox else rgba
        w, h = cropped.size
        target_w = int(w * (target_h / h))
        resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

        card_img = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))
        card_img.paste(resized, (0, 0), resized)
        return card_img
    except Exception as e:
        print(f"[Pivora] Mascot image error: {e}")
        return None

def render_speech_bubble_image(title: str, subtitle: str = "", emoji_char: str = "", w: int = 310, h: int = 78):
    """Render a crisp antialiased speech bubble with full-color native Windows emojis."""
    raw = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(raw)

    bx1, by1 = 5, 4
    bx2, by2 = w - 5, h - 14
    r = 16

    draw.rounded_rectangle([bx1 + 1, by1 + 2, bx2 + 1, by2 + 2], radius=r, fill=(0, 0, 0, 25))
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=r, fill=(255, 255, 255, 255), outline=(2, 136, 209, 255), width=2)

    cx = w // 2
    tail_pts = [(cx - 9, by2 - 1), (cx + 9, by2 - 1), (cx, by2 + 11)]
    draw.polygon(tail_pts, fill=(255, 255, 255, 255), outline=(2, 136, 209, 255))
    draw.line([(cx - 7, by2 - 1), (cx + 7, by2 - 1)], fill=(255, 255, 255, 255), width=3)

    font_segoe = "C:/Windows/Fonts/segoeuib.ttf" if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else "arial.ttf"
    font_emoji = "C:/Windows/Fonts/seguiemj.ttf" if os.path.exists("C:/Windows/Fonts/seguiemj.ttf") else font_segoe

    try:
        text_font = ImageFont.truetype(font_segoe, 13)
        emoji_font = ImageFont.truetype(font_emoji, 17)
    except Exception:
        text_font = ImageFont.load_default()
        emoji_font = text_font

    t1_box = draw.textbbox((0, 0), title, font=text_font)
    t1_w = t1_box[2] - t1_box[0]
    draw.text(((w - t1_w) // 2, 13), title, font=text_font, fill=(1, 87, 155, 255))

    if subtitle:
        l2_box = draw.textbbox((0, 0), subtitle, font=text_font)
        l2_w = l2_box[2] - l2_box[0]
        em_box = draw.textbbox((0, 0), emoji_char, font=emoji_font) if emoji_char else (0, 0, 0, 0)
        em_w = em_box[2] - em_box[0] if emoji_char else 0

        space = 6 if emoji_char else 0
        total_w = l2_w + em_w + space
        start_x = (w - total_w) // 2

        draw.text((start_x, 36), subtitle, font=text_font, fill=(1, 87, 155, 255))
        if emoji_char:
            try:
                draw.text((start_x + l2_w + space, 34), emoji_char, font=emoji_font, fill=(0, 0, 0, 255), embedded_color=True)
            except Exception:
                draw.text((start_x + l2_w + space, 34), emoji_char, font=emoji_font, fill=(1, 87, 155, 255))

    final_img = Image.new("RGB", (w, h), (1, 1, 1))
    final_img.paste(raw, (0, 0), raw)
    return final_img


# ─────────────────────────────────────────────────────────────────
# Data Management with History, Streaks & Goal
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
                if raw.get("work_end_hour") == 21:
                    raw["work_end_hour"] = DEFAULT_WORK_END
                else:
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
        pause_on_meet = prev.get("pause_on_meeting", True) if prev else True
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
            "pause_on_meeting": pause_on_meet,
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

    def set_glass_count(self, count: int):
        self._ensure_today()
        self.data["glasses_count"] = max(0, int(count))
        today = str(date.today())
        if "history" not in self.data:
            self.data["history"] = {}
        self.data["history"][today] = self.data["glasses_count"]
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
    def pause_on_meeting(self):
        return self.data.get("pause_on_meeting", True)

    def set_pause_on_meeting(self, val: bool):
        self.data["pause_on_meeting"] = bool(val)
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
# Meeting, Screen Share & Presentation Detection
# ─────────────────────────────────────────────────────────────────
def is_meeting_or_screenshare_active() -> tuple[bool, str]:
    """Detect if the user is in an active meeting, presenting, or sharing their screen."""
    if sys.platform != "win32":
        return False, ""

    # 1. Native Windows User Notification State (Presentation Mode & Direct3D Fullscreen)
    try:
        import ctypes
        from ctypes import wintypes
        state = ctypes.c_int()
        # QUNS_PRESENTATION_MODE = 4, QUNS_RUNNING_D3D_FULL_SCREEN = 3
        if ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state)) == 0:
            if state.value == 4:
                return True, "Presentation Mode"
            elif state.value == 3:
                return True, "Fullscreen Presentation / App"
    except Exception:
        pass

    # 2. Check Visible Windows on Input Desktop for Meetings / Screen Shares
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hDesk:
            titles = []
            def enum_proc(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        titles.append(buff.value)
                return True

            EnumDesktopProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumDesktopWindows(hDesk, EnumDesktopProc(enum_proc), 0)
            user32.CloseDesktop(hDesk)

            meeting_keywords = [
                "zoom meeting", "zoom webinar", "cisco webex", "webex meeting",
                "google meet", "meet \u2013", "meet -", "teams meeting",
                "meeting | microsoft teams", "powerpoint slide show",
                "sharing your screen", "screen sharing", "screenshare",
                "you are sharing", "sharing toolbar", "stop sharing"
            ]

            for t in titles:
                t_low = t.lower()
                for kw in meeting_keywords:
                    if kw in t_low:
                        return True, f"Meeting / Screen Share ({t[:26]}...)"
    except Exception:
        pass

    return False, ""


# ─────────────────────────────────────────────────────────────────
# Dynamic Tray Icon with Live Count Badge
# ─────────────────────────────────────────────────────────────────
def create_tray_icon_image(count=0, goal=8, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2 - 4, size // 2 + 5
    r = size // 3 - 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#0288D1", outline="#01579B", width=2)
    tip_x, tip_y = cx, 4
    left_x, left_y = cx - r + 3, cy - 3
    right_x, right_y = cx + r - 3, cy - 3
    draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], fill="#0288D1", outline="#0288D1")
    draw.ellipse([cx - r // 3, cy - r // 2, cx, cy - r // 6], fill=(255, 255, 255, 200))

    if count >= 0:
        bx, by = size - 17, size - 17
        br = 15
        bg_col = "#10B981" if count >= goal else "#F59E0B"
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

        # Full-Color Antialiased Speech Bubble (with Windows Color Emojis)
        self.bubble_photo = None
        self.bubble_item = self.canvas.create_image(self.w // 2, 45, image=None)

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

    def _set_bubble(self, title: str, subtitle: str = "", emoji: str = ""):
        img = render_speech_bubble_image(title, subtitle, emoji, w=310, h=78)
        self.bubble_photo = ImageTk.PhotoImage(img, master=self.win)
        self.canvas.itemconfig(self.bubble_item, image=self.bubble_photo)

    def trigger(self):
        if self.is_active:
            return
        self.is_active = True
        self.step_idx = 0
        self.total_ticks = 0

        self.canvas.itemconfigure(self.bubble_item, state="hidden")
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

            t, s, e = random.choice(MASCOT_QUOTES)
            self._set_bubble(t.format(name=self.data.user_name), s.format(name=self.data.user_name), e)

            self.canvas.itemconfigure(self.bubble_item, state="normal")
            self.canvas.itemconfigure(self.btn_window, state="normal")

            self.dismiss_job = self.win.after(20000, self.on_later)

    def on_yes(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.data.add_glass()
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self._set_bubble(f"Awesome, {self.data.user_name}!", "Stay healthy & hydrated!", "💧")
        self.win.after(1100, self._walk_out)

    def on_later(self):
        if self.dismiss_job:
            self.win.after_cancel(self.dismiss_job)
            self.dismiss_job = None
        self.canvas.itemconfigure(self.btn_window, state="hidden")
        self._set_bubble(f"No worries, {self.data.user_name}!", "I will remind you soon!", "👍")
        self.win.after(1000, self._walk_out)

    def _walk_out(self):
        self.canvas.itemconfigure(self.bubble_item, state="hidden")
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
# Handcrafted Consumer Dashboard with Modern Tab Navigation
# ─────────────────────────────────────────────────────────────────
class WatertimeApp:
    def __init__(self):
        self.data = WaterData()
        self.dnd_until = 0
        self.next_reminder_time = time.time() + (self.data.interval_minutes * 60)
        self.active_tab = "tracker"

        # Root Window
        self.root = tk.Tk()
        self.root.title("Pivora 💧 - Daily Water Companion")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_dashboard)

        # Set Application Taskbar & Window Icon (replaces default Python icon)
        # Must call SetCurrentProcessExplicitAppUserModelID BEFORE creating any window/tray
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "PivoraApp.WaterReminder.1.0"
                )
            except Exception:
                pass

        ico_file = BASE_DIR / "app_icon.ico"
        png_file = BASE_DIR / "app_icon.png"

        # iconbitmap works on Windows for the title bar
        if sys.platform == "win32" and ico_file.exists():
            try:
                self.root.iconbitmap(default=str(ico_file.resolve()))
            except Exception:
                pass

        # iconphoto works cross-platform (and overrides in notification area on some systems)
        if png_file.exists():
            try:
                self._app_window_icon = ImageTk.PhotoImage(
                    Image.open(str(png_file.resolve())).resize((64, 64), Image.Resampling.LANCZOS),
                    master=self.root
                )
                self.root.iconphoto(True, self._app_window_icon)
            except Exception:
                pass

        self._init_theme()
        self._build_dashboard()
        self._center_window(490, 540)

        # Mascot Overlay (Screen Walker)
        self.mascot = MascotOverlay(self.root, self.data, on_close=self.on_mascot_closed)

        # System Tray
        self.tray = None
        self._init_tray()

        # Global Hotkey Listener (Ctrl + Alt + W)
        self._start_hotkey_listener()

        # IPC listener to pop window to front if launched again
        self._start_ipc_listener()

        # Timer loop
        self._check_timer_loop()

    def _init_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Pivora.TCombobox",
            fieldbackground="#FFFFFF",
            background="#F0F9FF",
            foreground=TEXT_DARK,
            arrowcolor=OCEAN_BLUE,
            bordercolor=CARD_BORDER,
            lightcolor=CARD_BORDER,
            darkcolor=CARD_BORDER,
            padding=3
        )
        style.map("Pivora.TCombobox",
            fieldbackground=[("focus", "#FFFFFF"), ("!disabled", "#FFFFFF")],
            selectbackground=[("focus", "#E0F2FE"), ("!disabled", "#E0F2FE")],
            selectforeground=[("focus", TEXT_DARK), ("!disabled", TEXT_DARK)],
            foreground=[("focus", TEXT_DARK), ("!disabled", TEXT_DARK)]
        )

    def _build_dashboard(self):
        # 1. Header with Real App Icon & Streak
        header_frame = tk.Frame(self.root, bg=BG_MAIN)
        header_frame.pack(fill="x", padx=20, pady=(12, 4))

        brand_f = tk.Frame(header_frame, bg=BG_MAIN)
        brand_f.pack(side="left")

        # Load real App Icon
        icon_img = load_app_icon_image(36)
        if icon_img:
            self.tk_app_icon = ImageTk.PhotoImage(icon_img, master=self.root)
            lbl_icon = tk.Label(brand_f, image=self.tk_app_icon, bg=BG_MAIN)
            lbl_icon.pack(side="left", padx=(0, 10))

        title_text_f = tk.Frame(brand_f, bg=BG_MAIN)
        title_text_f.pack(side="left")

        tk.Label(
            title_text_f, text="Pivora",
            font=("Segoe UI", 16, "bold"), fg=OCEAN_DARK, bg=BG_MAIN
        ).pack(anchor="w")

        tk.Label(
            title_text_f, text="Daily Water Companion",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_MAIN
        ).pack(anchor="w")

        # Streak Badge on right
        self.lbl_streak = tk.Label(
            header_frame, text=f"🔥 {self.data.streak} Day Streak",
            font=("Segoe UI", 9, "bold"), fg="#B45309", bg="#FEF3C7",
            padx=10, pady=4, relief="flat", highlightthickness=1, highlightbackground="#FDE68A"
        )
        self.lbl_streak.pack(side="right")

        # 2. Sleek Segmented Tab Selector Bar
        tab_nav_frame = tk.Frame(self.root, bg="#E0F2FE", padx=3, pady=3, highlightthickness=1, highlightbackground=CARD_BORDER)
        tab_nav_frame.pack(fill="x", padx=20, pady=(4, 8))

        self.btn_tab_tracker = tk.Button(
            tab_nav_frame, text="💧 Today's Tracker", font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF", fg=OCEAN_BLUE, activebackground="#FFFFFF", activeforeground=OCEAN_BLUE,
            relief="flat", bd=0, padx=14, pady=5, cursor="hand2",
            command=lambda: self.switch_tab("tracker")
        )
        self.btn_tab_tracker.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_tab_pref = tk.Button(
            tab_nav_frame, text="⚙️ Preferences & Schedule", font=("Segoe UI", 9, "bold"),
            bg="#E0F2FE", fg=TEXT_MUTED, activebackground="#BAE6FD", activeforeground=TEXT_DARK,
            relief="flat", bd=0, padx=14, pady=5, cursor="hand2",
            command=lambda: self.switch_tab("pref")
        )
        self.btn_tab_pref.pack(side="left", expand=True, fill="x", padx=2)

        # 3. Main Content Container
        self.container = tk.Frame(self.root, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True, padx=20)

        # ── TAB 1: Today's Tracker ──
        self.tab_tracker = tk.Frame(self.container, bg=BG_MAIN)

        # Status & Snooze Row
        status_bar = tk.Frame(self.tab_tracker, bg=BG_MAIN)
        status_bar.pack(fill="x", pady=(0, 6))

        self.lbl_status = tk.Label(
            status_bar, text="🟢 Active (Next in 5m)",
            font=("Segoe UI", 9, "bold"), fg="#059669", bg=BG_MAIN
        )
        self.lbl_status.pack(side="left")

        snooze_f = tk.Frame(status_bar, bg=BG_MAIN)
        snooze_f.pack(side="right")
        tk.Label(snooze_f, text="Snooze:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_MAIN).pack(side="left", padx=2)

        for label, mins in [("30m", 30), ("1h", 60), ("2h", 120)]:
            b = tk.Button(
                snooze_f, text=label, font=("Segoe UI", 8, "bold"),
                bg="#E2E8F0", fg=TEXT_SECONDARY, relief="flat", bd=0, padx=6, pady=1, cursor="hand2",
                command=lambda m=mins: self.set_snooze(m)
            )
            b.bind("<Enter>", lambda e, btn=b: btn.configure(bg="#CBD5E1"))
            b.bind("<Leave>", lambda e, btn=b: btn.configure(bg="#E2E8F0"))
            b.pack(side="left", padx=2)

        self.btn_resume = tk.Button(
            snooze_f, text="▶ Resume", font=("Segoe UI", 8, "bold"),
            bg="#D1FAE5", fg="#065F46", relief="flat", bd=0, padx=6, pady=1, cursor="hand2",
            command=lambda: self.set_snooze(0)
        )
        self.btn_resume.bind("<Enter>", lambda e: self.btn_resume.configure(bg="#A7F3D0"))
        self.btn_resume.bind("<Leave>", lambda e: self.btn_resume.configure(bg="#D1FAE5"))

        # Hero Mascot Card
        card_hero = tk.Frame(self.tab_tracker, bg=CARD_BG, padx=14, pady=10, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_hero.pack(fill="x", pady=(0, 8))

        mascot_pil = load_dashboard_mascot_image(target_h=140)
        if mascot_pil:
            self.tk_dash_mascot = ImageTk.PhotoImage(mascot_pil, master=self.root)
            lbl_mascot_hero = tk.Label(card_hero, image=self.tk_dash_mascot, bg=CARD_BG, cursor="hand2")
            lbl_mascot_hero.bind("<Button-1>", lambda e: self.test_mascot_now())
            lbl_mascot_hero.pack(side="left", padx=(0, 14))

        info_f = tk.Frame(card_hero, bg=CARD_BG)
        info_f.pack(side="left", fill="both", expand=True)

        self.lbl_greeting = tk.Label(
            info_f, text=self._get_greeting_str(),
            font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG, justify="left", wraplength=260
        )
        self.lbl_greeting.pack(anchor="w", pady=(2, 2))

        self.lbl_hero_litres = tk.Label(
            info_f, text=f"{self.data.litres_drunk:.2f} L",
            font=("Segoe UI", 24, "bold"), fg=OCEAN_BLUE, bg=CARD_BG
        )
        self.lbl_hero_litres.pack(anchor="w")

        self.lbl_hero_sub = tk.Label(
            info_f, text=f"{self.data.count} of {self.data.goal} glasses today ({self.data.percentage}%)",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG
        )
        self.lbl_hero_sub.pack(anchor="w", pady=(0, 6))

        btn_action_row = tk.Frame(info_f, bg=CARD_BG)
        btn_action_row.pack(anchor="w")

        btn_drink = tk.Button(
            btn_action_row, text="+ Drink a Glass 💧",
            font=("Segoe UI", 9, "bold"), bg=OCEAN_BLUE, fg="#FFFFFF",
            activebackground=OCEAN_DARK, activeforeground="#FFFFFF",
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2",
            command=self.quick_log_glass
        )
        btn_drink.bind("<Enter>", lambda e: btn_drink.configure(bg=OCEAN_DARK))
        btn_drink.bind("<Leave>", lambda e: btn_drink.configure(bg=OCEAN_BLUE))
        btn_drink.pack(side="left")

        btn_reset_quick = tk.Button(
            btn_action_row, text="🔄 Reset",
            font=("Segoe UI", 8, "bold"), bg="#F1F5F9", fg="#DC2626",
            activebackground="#FEE2E2", activeforeground="#991B1B",
            relief="flat", bd=0, padx=8, pady=5, cursor="hand2",
            command=self.reset_count
        )
        btn_reset_quick.pack(side="left", padx=(8, 0))

        # Visual Glasses Tracker Card
        card_glasses = tk.Frame(self.tab_tracker, bg=CARD_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_glasses.pack(fill="x", pady=(0, 8))

        tk.Label(
            card_glasses, text="DAILY GLASSES (CLICK A GLASS TO LOG)",
            font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=CARD_BG
        ).pack(anchor="w")

        self.canvas_glasses = tk.Canvas(card_glasses, width=420, height=48, bg=CARD_BG, highlightthickness=0, cursor="hand2")
        self.canvas_glasses.pack(fill="x", pady=(4, 0))
        self.canvas_glasses.bind("<Button-1>", self.on_glass_canvas_clicked)
        self._render_interactive_glasses()

        # Last 7 Days Activity Card
        card_activity = tk.Frame(self.tab_tracker, bg=CARD_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_activity.pack(fill="x", pady=(0, 4))

        tk.Label(
            card_activity, text="LAST 7 DAYS ACTIVITY",
            font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=CARD_BG
        ).pack(anchor="w", pady=(0, 2))

        self.canvas_chart = tk.Canvas(card_activity, width=420, height=58, bg=CARD_BG, highlightthickness=0)
        self.canvas_chart.pack(fill="x")
        self._render_weekly_chart()

        # ── TAB 2: Preferences & Schedule ──
        self.tab_pref = tk.Frame(self.container, bg=BG_MAIN)

        # Scrollable inner frame for preferences
        pref_canvas = tk.Canvas(self.tab_pref, bg=BG_MAIN, highlightthickness=0, bd=0)
        pref_scroll = tk.Scrollbar(self.tab_pref, orient="vertical", command=pref_canvas.yview)
        pref_canvas.configure(yscrollcommand=pref_scroll.set)
        pref_canvas.pack(side="left", fill="both", expand=True)

        pref_inner = tk.Frame(pref_canvas, bg=BG_MAIN)
        pref_inner_window = pref_canvas.create_window((0, 0), window=pref_inner, anchor="nw")

        def _on_pref_resize(event):
            pref_canvas.itemconfig(pref_inner_window, width=event.width)
        def _on_pref_configure(event):
            pref_canvas.configure(scrollregion=pref_canvas.bbox("all"))
        pref_canvas.bind("<Configure>", _on_pref_resize)
        pref_inner.bind("<Configure>", _on_pref_configure)

        def _pref_mousewheel(event):
            pref_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        pref_canvas.bind("<MouseWheel>", _pref_mousewheel)
        pref_inner.bind("<MouseWheel>", _pref_mousewheel)

        # Card 1: Profile & Daily Target
        card_p1 = tk.Frame(pref_inner, bg=CARD_BG, padx=16, pady=12, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_p1.pack(fill="x", pady=(0, 8))

        tk.Label(card_p1, text="👤  PERSONAL PROFILE & TARGET", font=("Segoe UI", 8, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w", pady=(0, 6))

        # Name row
        r_name = tk.Frame(card_p1, bg=CARD_BG)
        r_name.pack(fill="x", pady=3)
        tk.Label(r_name, text="Your Name:", font=("Segoe UI", 9, "bold"), fg=TEXT_SECONDARY, bg=CARD_BG, width=15, anchor="w").pack(side="left")
        self.entry_name = tk.Entry(
            r_name, font=("Segoe UI", 9), bg="#F8FAFC", fg=TEXT_DARK,
            relief="flat", bd=0, highlightthickness=1, highlightbackground=CARD_BORDER,
            highlightcolor=OCEAN_BLUE, width=20
        )
        self.entry_name.insert(0, self.data.user_name)
        self.entry_name.pack(side="left", padx=4)
        self.entry_name.bind("<FocusOut>", self.on_name_changed)
        self.entry_name.bind("<Return>", self.on_name_changed)

        # Goal row
        r_goal = tk.Frame(card_p1, bg=CARD_BG)
        r_goal.pack(fill="x", pady=3)
        tk.Label(r_goal, text="Daily Target:", font=("Segoe UI", 9, "bold"), fg=TEXT_SECONDARY, bg=CARD_BG, width=15, anchor="w").pack(side="left")

        self.goal_options = {
            "6 glasses (1.5 L)": 6,
            "8 glasses (2.0 L)": 8,
            "10 glasses (2.5 L)": 10,
            "12 glasses (3.0 L)": 12,
            "14 glasses (3.5 L)": 14,
        }
        self.combo_goal = ttk.Combobox(
            r_goal, style="Pivora.TCombobox", values=list(self.goal_options.keys()),
            width=18, state="normal", font=("Segoe UI", 9)
        )
        curr_goal = self.data.goal
        found_goal_key = next((k for k, v in self.goal_options.items() if v == curr_goal), f"{curr_goal} glasses")
        self.combo_goal.set(found_goal_key)
        self.combo_goal.bind("<<ComboboxSelected>>", self.on_goal_selected)
        self.combo_goal.bind("<Return>", self.on_goal_selected)
        self.combo_goal.bind("<FocusOut>", self.on_goal_selected)
        self.combo_goal.pack(side="left", padx=4)

        # Card 2: Schedule & Quiet Hours
        card_p2 = tk.Frame(pref_inner, bg=CARD_BG, padx=16, pady=12, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_p2.pack(fill="x", pady=(0, 8))

        tk.Label(card_p2, text="⏰  REMINDERS & SCHEDULE", font=("Segoe UI", 8, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w", pady=(0, 6))

        # Interval row
        r_int = tk.Frame(card_p2, bg=CARD_BG)
        r_int.pack(fill="x", pady=3)
        tk.Label(r_int, text="Remind Every:", font=("Segoe UI", 9, "bold"), fg=TEXT_SECONDARY, bg=CARD_BG, width=15, anchor="w").pack(side="left")

        self.interval_options = {
            "1 min": 1,
            "5 mins": 5,
            "10 mins": 10,
            "15 mins": 15,
            "20 mins": 20,
            "30 mins": 30,
            "45 mins": 45,
            "60 mins": 60,
        }
        self.combo_interval = ttk.Combobox(
            r_int, style="Pivora.TCombobox", values=list(self.interval_options.keys()),
            width=18, state="normal", font=("Segoe UI", 9)
        )
        current_mins = self.data.interval_minutes
        found_key = next((k for k, v in self.interval_options.items() if v == current_mins), f"{current_mins} mins")
        self.combo_interval.set(found_key)
        self.combo_interval.bind("<<ComboboxSelected>>", self.on_interval_selected)
        self.combo_interval.bind("<Return>", self.on_interval_selected)
        self.combo_interval.bind("<FocusOut>", self.on_interval_selected)
        self.combo_interval.pack(side="left", padx=4)

        # Active Hours row
        r_hours = tk.Frame(card_p2, bg=CARD_BG)
        r_hours.pack(fill="x", pady=3)
        self.var_work_hours = tk.BooleanVar(value=self.data.work_hours_enabled)
        chk_hours = tk.Checkbutton(
            r_hours, text="Active Hours:", variable=self.var_work_hours,
            font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_DARK,
            activebackground=CARD_BG, selectcolor="#F0F9FF",
            command=self.on_work_hours_toggled
        )
        chk_hours.pack(side="left")

        hour_vals = [f"{h:02d}:00" for h in range(24)]
        self.combo_h_start = ttk.Combobox(r_hours, style="Pivora.TCombobox", values=hour_vals, width=6, state="normal", font=("Segoe UI", 8))
        self.combo_h_start.set(f"{self.data.work_start_hour:02d}:00")
        self.combo_h_start.bind("<<ComboboxSelected>>", self.on_work_hours_changed)
        self.combo_h_start.bind("<Return>", self.on_work_hours_changed)
        self.combo_h_start.bind("<FocusOut>", self.on_work_hours_changed)
        self.combo_h_start.pack(side="left", padx=4)

        tk.Label(r_hours, text="to", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")

        self.combo_h_end = ttk.Combobox(r_hours, style="Pivora.TCombobox", values=hour_vals, width=6, state="normal", font=("Segoe UI", 8))
        self.combo_h_end.set(f"{self.data.work_end_hour:02d}:00")
        self.combo_h_end.bind("<<ComboboxSelected>>", self.on_work_hours_changed)
        self.combo_h_end.bind("<Return>", self.on_work_hours_changed)
        self.combo_h_end.bind("<FocusOut>", self.on_work_hours_changed)
        self.combo_h_end.pack(side="left", padx=4)

        tk.Label(
            card_p2, text="💡 Outside active hours, character reminders are paused so you can sleep peacefully.",
            font=("Segoe UI", 8, "italic"), fg=TEXT_MUTED, bg=CARD_BG, wraplength=410, justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Meeting Mode & Screen Share Auto-Pause
        self.var_meeting_mode = tk.BooleanVar(value=self.data.pause_on_meeting)
        chk_meeting = tk.Checkbutton(
            card_p2, text="Auto-pause mascot during meetings & screen share",
            variable=self.var_meeting_mode,
            font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_DARK,
            activebackground=CARD_BG, selectcolor="#F0F9FF",
            command=self.on_meeting_mode_toggled
        )
        chk_meeting.pack(anchor="w", pady=(6, 0))

        tk.Label(
            card_p2, text="🛡️ Mascot automatically stays quiet during Zoom, Teams, Google Meet, or presentations.",
            font=("Segoe UI", 8, "italic"), fg=TEXT_MUTED, bg=CARD_BG, wraplength=410, justify="left"
        ).pack(anchor="w", pady=(1, 0))

        # Card 3: System & Quick Controls
        card_p3 = tk.Frame(pref_inner, bg=CARD_BG, padx=16, pady=12, highlightthickness=1, highlightbackground=CARD_BORDER)
        card_p3.pack(fill="x", pady=(0, 4))

        tk.Label(card_p3, text="⚡  SYSTEM & SHORTCUTS", font=("Segoe UI", 8, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w", pady=(0, 6))

        self.var_autostart = tk.BooleanVar(value=is_autostart_enabled())
        autostart_text = "Start Pivora automatically on PC boot" if sys.platform == "win32" else "Start Pivora automatically on Linux startup"
        chk_autostart = tk.Checkbutton(
            card_p3, text=autostart_text,
            variable=self.var_autostart, onvalue=True, offvalue=False,
            font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_SECONDARY,
            activebackground=CARD_BG, selectcolor="#F0F9FF",
            command=self.toggle_autostart
        )
        chk_autostart.pack(anchor="w")

        tk.Label(
            card_p3, text="⌨️ Hotkey: Ctrl + Alt + W  —  Log a glass from anywhere",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG
        ).pack(anchor="w", pady=(6, 4))

        r_reset_row = tk.Frame(card_p3, bg=CARD_BG)
        r_reset_row.pack(fill="x", pady=(4, 2))

        btn_reset_cnt = tk.Button(
            r_reset_row, text="🔄 Reset Today's Count to 0", font=("Segoe UI", 8, "bold"),
            bg="#FEE2E2", fg="#DC2626", activebackground="#FCA5A5", activeforeground="#991B1B",
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            command=self.reset_count
        )
        btn_reset_cnt.pack(side="left")

        tk.Label(
            r_reset_row, text="(Clears today's glasses back to 0)",
            font=("Segoe UI", 8, "italic"), fg=TEXT_MUTED, bg=CARD_BG
        ).pack(side="left", padx=8)

        # Bind mousewheel to all children of pref_inner for smooth scrolling
        def _bind_scroll_children(widget):
            widget.bind("<MouseWheel>", _pref_mousewheel)
            for child in widget.winfo_children():
                _bind_scroll_children(child)
        _bind_scroll_children(pref_inner)

        # Show initial tab
        self.tab_tracker.pack(fill="both", expand=True)

    def switch_tab(self, tab_name: str):
        """Switch smoothly between Tracker and Preferences views."""
        self.active_tab = tab_name
        if tab_name == "tracker":
            self.tab_pref.pack_forget()
            self.tab_tracker.pack(fill="both", expand=True)
            self.btn_tab_tracker.configure(bg="#FFFFFF", fg=OCEAN_BLUE)
            self.btn_tab_pref.configure(bg="#E0F2FE", fg=TEXT_MUTED)
        else:
            self.tab_tracker.pack_forget()
            self.tab_pref.pack(fill="both", expand=True)
            self.btn_tab_pref.configure(bg="#FFFFFF", fg=OCEAN_BLUE)
            self.btn_tab_tracker.configure(bg="#E0F2FE", fg=TEXT_MUTED)

    def _get_greeting_str(self):
        name = self.data.user_name
        cnt = self.data.count
        goal = self.data.goal
        if cnt >= goal:
            return f"Awesome, {name}! 🎉\nDaily goal completed! Keep shining!"
        elif cnt >= goal // 2:
            return f"Great pace, {name}! 💧\nOver halfway to your target!"
        else:
            return f"Hey, {name}! 💧\nDrink fresh water & stay energized!"

    def _render_interactive_glasses(self):
        """Render a row of interactive, clickable visual water glasses."""
        self.canvas_glasses.delete("all")
        goal = max(1, self.data.goal)
        count = self.data.count
        w = 420
        col_w = w / goal
        gw = min(32, col_w - 4)
        gh = 38
        gy1 = 4
        gy2 = gy1 + gh

        for i in range(goal):
            cx = i * col_w + col_w / 2
            gx1 = cx - gw / 2
            gx2 = cx + gw / 2

            filled = i < count
            bg_col = OCEAN_BLUE if filled else "#F0F9FF"
            border_col = OCEAN_DARK if filled else CARD_BORDER
            txt_col = "#FFFFFF" if filled else TEXT_MUTED

            pts = [
                gx1, gy1,
                gx2, gy1,
                gx2 - 3, gy2,
                gx1 + 3, gy2
            ]
            self.canvas_glasses.create_polygon(pts, fill=bg_col, outline=border_col, width=2)

            if filled:
                self.canvas_glasses.create_text(cx, gy1 + gh // 2, text="💧", font=("Segoe UI", 10), fill="#FFFFFF")
            else:
                self.canvas_glasses.create_text(cx, gy1 + gh // 2, text=str(i + 1), font=("Segoe UI", 8, "bold"), fill=txt_col)

    def on_glass_canvas_clicked(self, event):
        goal = max(1, self.data.goal)
        w = 420
        col_w = w / goal
        idx = int(event.x // col_w)
        if 0 <= idx < goal:
            new_count = idx + 1
            self.data.set_glass_count(new_count)
            self._refresh_ui_progress()
            self.show_quick_toast(f"💧 Updated: {self.data.count}/{self.data.goal} glasses ({self.data.litres_drunk:.2f}L)")

    def _render_weekly_chart(self):
        self.canvas_chart.delete("all")
        days = self.data.get_last_7_days()
        w = 420
        col_w = w / 7
        bar_w = 20
        base_y = 36
        max_bar_h = 22
        goal = self.data.goal

        for idx, (d, d_str, cnt, is_today) in enumerate(days):
            cx = idx * col_w + col_w / 2
            bx1 = cx - bar_w / 2
            bx2 = cx + bar_w / 2

            ratio = min(1.0, cnt / max(1, goal))
            bar_h = max(3, int(ratio * max_bar_h))
            by1 = base_y - bar_h
            by2 = base_y

            fill_col = EMERALD_GREEN if cnt >= goal else (OCEAN_BLUE if cnt > 0 else "#E2E8F0")

            self.canvas_chart.create_rectangle(bx1, base_y - max_bar_h, bx2, base_y, fill="#F1F5F9", outline="", width=0)
            self.canvas_chart.create_rectangle(bx1, by1, bx2, by2, fill=fill_col, outline="", width=0)

            cnt_color = OCEAN_DARK if is_today or cnt > 0 else TEXT_MUTED
            self.canvas_chart.create_text(
                cx, by1 - 5, text=str(cnt),
                font=("Segoe UI", 8, "bold" if is_today else "normal"), fill=cnt_color
            )

            day_name = d.strftime("%a")
            day_color = OCEAN_DARK if is_today else TEXT_MUTED
            self.canvas_chart.create_text(
                cx, base_y + 8, text=day_name,
                font=("Segoe UI", 8, "bold" if is_today else "normal"),
                fill=day_color
            )

            if is_today:
                self.canvas_chart.create_oval(cx - 2, base_y + 14, cx + 2, base_y + 18, fill=OCEAN_BLUE, outline="")

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
            self.lbl_greeting.config(text=self._get_greeting_str())

    def on_interval_selected(self, event=None):
        choice = self.combo_interval.get().strip()
        mins = None
        if choice in self.interval_options:
            mins = self.interval_options[choice]
        else:
            m = re.search(r'\d+', choice)
            if m:
                mins = max(1, min(720, int(m.group(0))))
        if mins is not None:
            self.data.set_interval(mins)
            self.next_reminder_time = time.time() + (mins * 60)
            disp = next((k for k, v in self.interval_options.items() if v == mins), f"{mins} mins")
            self.combo_interval.set(disp)
            self._update_status_label()

    def on_goal_selected(self, event=None):
        choice = self.combo_goal.get().strip()
        goal = None
        if choice in self.goal_options:
            goal = self.goal_options[choice]
        else:
            m = re.search(r'\d+', choice)
            if m:
                goal = max(1, min(50, int(m.group(0))))
        if goal is not None:
            self.data.set_goal(goal)
            disp = next((k for k, v in self.goal_options.items() if v == goal), f"{goal} glasses ({goal * 0.25:.1f} L)")
            self.combo_goal.set(disp)
            self._refresh_ui_progress()

    def on_work_hours_toggled(self):
        self.data.set_work_hours_enabled(self.var_work_hours.get())
        self._update_status_label()

    def on_meeting_mode_toggled(self):
        self.data.set_pause_on_meeting(self.var_meeting_mode.get())
        self._update_status_label()
        status = "Active" if self.var_meeting_mode.get() else "Disabled"
        self.show_quick_toast(f"🔇 Meeting Auto-Pause: {status}")

    def toggle_meeting_mode_tray(self):
        new_val = not self.data.pause_on_meeting
        self.data.set_pause_on_meeting(new_val)
        if hasattr(self, "var_meeting_mode"):
            self.var_meeting_mode.set(new_val)
        self.root.after(0, self._update_status_label)
        status = "Active" if new_val else "Disabled"
        self.show_quick_toast(f"🔇 Meeting Auto-Pause: {status}")

    def on_work_hours_changed(self, event=None):
        def parse_hour(val: str, default: int) -> int:
            s = val.strip()
            if ":" in s:
                parts = s.split(":")
                if parts[0].isdigit():
                    return max(0, min(23, int(parts[0])))
            m = re.search(r'\d+', s)
            if m:
                return max(0, min(23, int(m.group(0))))
            return default

        try:
            start_h = parse_hour(self.combo_h_start.get(), self.data.work_start_hour)
            end_h = parse_hour(self.combo_h_end.get(), self.data.work_end_hour)
            self.data.set_work_start_hour(start_h)
            self.data.set_work_end_hour(end_h)
            self.combo_h_start.set(f"{start_h:02d}:00")
            self.combo_h_end.set(f"{end_h:02d}:00")
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
        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.wm_attributes("-topmost", True)
            try:
                toast.wm_attributes("-alpha", 0.95)
            except Exception:
                pass
            toast.configure(bg="#0369A1")

            lbl = tk.Label(
                toast, text=text,
                font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#0369A1",
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
        VK_W = 0x57

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
            self.lbl_status.config(text=f"⏸️ Snoozed ({mins_left}m left, until {until_str})", fg="#B45309")
            self.btn_resume.pack(side="left", padx=2)
            if self.tray:
                self.tray.title = f"Pivora 💧 [Snoozed until {until_str}] • {self.data.count}/{self.data.goal} ({self.data.litres_drunk:.2f}L)"
            return
        else:
            self.btn_resume.pack_forget()

        # Check Active Hours
        if self.data.work_hours_enabled:
            s_h = self.data.work_start_hour
            e_h = self.data.work_end_hour
            if not (s_h <= curr_hour < e_h):
                self.lbl_status.config(text=f"🌙 Outside Active Hours (Resumes at {s_h:02d}:00)", fg=TEXT_MUTED)
                if self.tray:
                    self.tray.title = f"Pivora 💧 [Quiet Hours until {s_h:02d}:00] • {self.data.count}/{self.data.goal}"
                return

        # Check Meeting / Screen Share Suppression
        if self.data.pause_on_meeting:
            in_meeting, meeting_desc = is_meeting_or_screenshare_active()
            if in_meeting:
                self.lbl_status.config(text=f"🖥️ {meeting_desc} (Mascot Paused)", fg="#D97706")
                if self.tray:
                    self.tray.title = f"Pivora 💧 [Meeting Mode Active] • {self.data.count}/{self.data.goal}"
                return

        # Normal Active
        secs_left = max(0, int(self.next_reminder_time - now))
        mins_left = secs_left // 60
        self.lbl_status.config(text=f"🟢 Active (Next reminder in {mins_left}m)", fg="#059669")
        if self.tray:
            self.tray.title = f"Pivora 💧 — {self.data.count}/{self.data.goal} glasses ({self.data.litres_drunk:.2f}L) • Next in {mins_left}m"

    def _refresh_ui_progress(self):
        self.lbl_greeting.config(text=self._get_greeting_str())
        self.lbl_hero_litres.config(text=f"{self.data.litres_drunk:.2f} L")
        self.lbl_hero_sub.config(text=f"{self.data.count} of {self.data.goal} glasses today ({self.data.percentage}%)")
        self._render_interactive_glasses()
        self.lbl_streak.config(text=f"🔥 {self.data.streak} Day Streak")
        self._render_weekly_chart()
        self._update_status_label()

        if self.tray:
            try:
                self.tray.icon = create_tray_icon_image(self.data.count, self.data.goal, 64)
            except Exception:
                pass

    def test_mascot_now(self):
        self.on_name_changed()
        if self.data.pause_on_meeting:
            in_meet, desc = is_meeting_or_screenshare_active()
            if in_meet:
                self.show_quick_toast(f"💡 {desc} active. Testing mascot anyway!")
        self.mascot.trigger()

    def hide_dashboard(self):
        self.on_name_changed()
        if self.tray:
            self.root.withdraw()
            self._update_status_label()
        else:
            self.quit_app()

    def show_dashboard(self, icon=None, item=None, tab="tracker"):
        self.switch_tab(tab)
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

    def _start_ipc_listener(self):
        global _instance_socket
        if not _instance_socket:
            return
        def loop():
            while True:
                try:
                    conn, _ = _instance_socket.accept()
                    data = conn.recv(64)
                    if data == b"SHOW":
                        self.root.after(0, lambda: self.show_dashboard(tab="tracker"))
                    conn.close()
                except Exception:
                    break
        threading.Thread(target=loop, daemon=True).start()

    # ── Tray Initialization ──
    def _init_tray(self):
        try:
            icon_img = create_tray_icon_image(self.data.count, self.data.goal, 64)

            def make_interval_item(label, mins):
                def on_click(icon, item):
                    self.set_interval_from_tray(mins)
                def is_checked(item):
                    return self.data.interval_minutes == mins
                return pystray.MenuItem(label, on_click, checked=is_checked)

            def make_snooze_item(label, mins):
                def on_click(icon, item):
                    self.root.after(0, lambda: self.set_snooze(mins))
                return pystray.MenuItem(label, on_click)

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
                make_snooze_item("⏸️ Snooze 30 mins", 30),
                make_snooze_item("⏸️ Snooze 1 hour", 60),
                make_snooze_item("⏸️ Snooze 2 hours", 120),
                make_snooze_item("▶️ Resume Reminders", 0),
            )

            menu = pystray.Menu(
                pystray.MenuItem("💧 Pivora Active", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("➕ Quick Log 1 Glass (Ctrl+Alt+W)", lambda icon, item: self.quick_log_glass()),
                pystray.MenuItem("🚶 Show Mascot Now", lambda icon, item: self.root.after(0, self.test_mascot_now)),
                pystray.MenuItem("🔕 Snooze / DND", snooze_menu),
                pystray.MenuItem("⏱️ Change Interval", interval_menu),
                pystray.MenuItem("⚙️ Open Settings", lambda icon, item: self.show_dashboard(tab="pref")),
                pystray.MenuItem("🛡️ Auto-Pause in Meetings", lambda icon, item: self.toggle_meeting_mode_tray(), checked=lambda item: self.data.pause_on_meeting),
                pystray.MenuItem("🔄 Reset Today's Count", lambda icon, item: self.reset_count()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Quit Pivora", lambda icon, item: self.quit_app())
            )
            self.tray = pystray.Icon("Pivora", icon_img, "Pivora 💧", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception as e:
            print(f"[Pivora] System tray error: {e}")
            self.tray = None

    def reset_count(self, icon=None, item=None):
        self.data.reset()
        self.root.after(0, self._refresh_ui_progress)

    def _check_timer_loop(self):
        now = time.time()
        curr_hour = time.localtime().tm_hour

        # Check Snooze
        if self.dnd_until > now:
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

        # Check Meeting / Screen Share Suppression
        if self.data.pause_on_meeting:
            in_meeting, _ = is_meeting_or_screenshare_active()
            if in_meeting:
                self._update_status_label()
                self.root.after(2000, self._check_timer_loop)
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
