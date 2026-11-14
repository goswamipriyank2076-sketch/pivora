import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from PIL import ImageGrab
import watertime as w

def wait_for(root, condition, label, timeout=14):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        root.update()
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError(label)

def click(button):
    x, y = button.winfo_width() // 2, button.winfo_height() // 2
    button.event_generate("<Enter>", x=x, y=y)
    button.event_generate("<ButtonPress-1>", x=x, y=y)
    button.event_generate("<ButtonRelease-1>", x=x, y=y)

with tempfile.TemporaryDirectory() as temporary:
    w.DATA_FILE = Path(temporary) / "water.json"
    data = w.WaterData()
    root = tk.Tk()
    root.configure(bg="white")
    root.overrideredirect(True)
    left, top, right, bottom = w.screen_work_area(root)
    root.geometry(f"{right-left}x{bottom-top}+{left}+{top}")
    ttk.Style(root).theme_use("clam")
    root.update()
    mascot = w.MascotOverlay(root, data)
    errors = []
    root.report_callback_exception = lambda kind, error, trace: errors.append(error)

    def show():
        mascot.trigger()
        wait_for(root, lambda: mascot.btn_frame_w.winfo_ismapped() or errors, "Reminder controls never appeared")
        assert not errors, errors

    try:
        show()
        log, later = mascot.btn_frame_w.winfo_children()
        assert log.cget("text") == "Log a glass"
        assert later.cget("text") == "Remind me later"
        assert all(button.winfo_ismapped() and button.winfo_height() >= 30 for button in (log, later))
        assert mascot.btn_frame_w.winfo_width() <= mascot.w

        x, y = mascot.win.winfo_rootx(), mascot.win.winfo_rooty()
        import sys
        if sys.platform == "darwin":
            shot = ImageGrab.grab().convert("RGB")
            scale_x = shot.width / root.winfo_screenwidth()
            scale_y = shot.height / root.winfo_screenheight()
            shot = shot.crop(tuple(round(p) for p in (
                (x - 12) * scale_x, (y - 5) * scale_y,
                (x + mascot.w + 12) * scale_x, (y + mascot.h + 5) * scale_y)))
        else:
            shot = ImageGrab.grab(bbox=(x - 12, y - 5, x + mascot.w + 12, y + mascot.h + 5)).convert("RGB")
        shot.save("reminder.png")
        colors = shot.getcolors(shot.width * shot.height)
        dark_blue = sum(n for n, (r, g, b) in colors if r < 40 and 15 < g < 65 and g + 12 < b < 100)
        white = sum(n for n, (r, g, b) in colors if min(r, g, b) > 235)
        assert dark_blue > 500 and white > 300, (dark_blue, white, sorted(colors, reverse=True)[:8])
        click(log)
        assert data.count == 1 and w.WaterData().count == 1
        wait_for(root, lambda: not mascot.is_active or errors, "Reminder did not close after logging")
        assert not errors, errors

        show()
        click(later)
        wait_for(root, lambda: not mascot.is_active or errors, "Reminder did not close after Remind me later")
        assert not errors, errors
        assert data.count == 1 and w.WaterData().count == 1
        print("PASS on-screen reminder, Log a glass, saved count, and Remind me later")
    finally:
        root.destroy()

