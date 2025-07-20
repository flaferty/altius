import tkinter as tk
import asyncio
import time
import math
from async_tkinter_loop import async_mainloop

from arm_leg_usage import get_arm_leg_usage
from stability import get_stability
from smoothness import get_smoothness_score
from fall_rhythm import get_rhythm, get_falls
from grip_count import get_grip_count

import logger  # your updated logger module

### ---------- Globals ----------

root = None
canvas = None
animation = None
logger_task = None
logger_stop_event = None
status_var = None
logger_widgets = []  # elements to remove on stop


### ---------- Logger Integration ----------

async def start_logger():
    global logger_task, logger_stop_event
    logger_stop_event = asyncio.Event()

    connected_devices = []

    def update_status(msg):
        print(msg)

        if "Connected to" in msg:
            dev = msg.split("Connected to")[-1].strip()
            if dev not in connected_devices:
                connected_devices.append(dev)
            status_lines = ["[+] Connected devices:"] + connected_devices
            status_var.set("\n".join(status_lines))
        else:
            status_var.set(msg)

    logger_task = asyncio.create_task(
        logger.main(print_callback=update_status, stop_event=logger_stop_event)
    )
def stop_logger(event=None):
    global logger_task, logger_stop_event

    if logger_stop_event:
        logger_stop_event.set()
    if logger_task:
        logger_task.cancel()

    animation.stop()
    clear_logger_screen()
    asyncio.create_task(show_scores())

def clear_logger_screen():
    for widget in logger_widgets:
        try:
            widget.destroy()
        except Exception:
            pass


### ---------- Animation ----------

class DotAnimation:
    def __init__(self, canvas):
        self.canvas = canvas
        self.dot1 = self.canvas.create_oval(0, 0, 0, 0, fill='white')
        self.dot2 = self.canvas.create_oval(0, 0, 0, 0, fill='white')
        self.center_x = 350
        self.center_y = 375
        self.radius = 10
        self.max_offset = 70
        self.duration = 0.75
        self.start_time = time.time()
        self.phase = 0
        self.phase_toggle_ready = True
        self.running = True
        self.animate()

    def animate(self):
        if not self.running:
            return

        now = time.time()
        elapsed = (now - self.start_time) % (2 * self.duration)
        t = elapsed / self.duration
        if t > 1:
            t = 2 - t
        eased = math.sin(t * math.pi / 2) ** 4
        offset = eased * self.max_offset

        if elapsed < 0.1 and self.phase_toggle_ready:
            self.phase = (self.phase + 1) % 2
            self.phase_toggle_ready = False
        elif elapsed > 0.1:
            self.phase_toggle_ready = True

        if self.phase == 0:
            x1, y1 = self.center_x, self.center_y - offset
            x2, y2 = self.center_x, self.center_y + offset
        else:
            x1, y1 = self.center_x - offset, self.center_y
            x2, y2 = self.center_x + offset, self.center_y

        self.canvas.coords(self.dot1, x1 - self.radius, y1 - self.radius, x1 + self.radius, y1 + self.radius)
        self.canvas.coords(self.dot2, x2 - self.radius, y2 - self.radius, x2 + self.radius, y2 + self.radius)

        self.canvas.after(16, self.animate)

    def stop(self):
        self.running = False


### ---------- Show Score Page ----------

async def show_scores():
    def safe(fn, default, *args):
        try:
            return fn(*args)
        except Exception as e:
            print(f"[!] {fn.__name__} failed: {e}")
            return default

    usage = await asyncio.to_thread(lambda: safe(get_arm_leg_usage, {
        "arm_usage_ratio": 0,
        "leg_usage_ratio": 0,
        "comment": "No data recorded"
    }, "data"))

    stability_score = safe(get_stability, 0.0, "data")
    smoothness_score = await asyncio.to_thread(lambda: safe(get_smoothness_score, 0.0, "data"))
    rhythm = await asyncio.to_thread(lambda: safe(get_rhythm, {
    "mean_interval": 0.0,
    "std_interval": 0.0,
    "rhythm_score": 0.0
        }, "data"))
    grip_count = safe(get_grip_count, ["No data", "No data"], "data")
    falls = safe(get_falls, {"partial_falls": [], "full_falls": []}, "data")



    label_cfg = {"font": ("Helvetica", 20, "bold"), "bg": "black", "fg": "white"}
    small_label_cfg = {**label_cfg, "font": ("Helvetica", 15)}

    tk.Label(root, text=f"Smoothness: {smoothness_score:.1f}%", **label_cfg).place(relx=0.2, rely=0.15, anchor='w')
    tk.Label(root, text=f"Stability: {stability_score * 100:.1f}%", **label_cfg).place(relx=0.2, rely=0.23, anchor='w')
    tk.Label(root, text=f"Arm/Leg Usage: {usage['arm_usage_ratio'] * 100:.0f}% / {usage['leg_usage_ratio'] * 100:.0f}%", **label_cfg).place(relx=0.2, rely=0.31, anchor='w')
    tk.Label(root, text=usage['comment'], **small_label_cfg).place(relx=0.25, rely=0.36, anchor='w')

    tk.Label(root, text="Rhythm/Flow:", **label_cfg).place(relx=0.2, rely=0.45, anchor='w')
    tk.Label(root, text=f"Mean Move Time: {rhythm['mean_interval']} s", **small_label_cfg).place(relx=0.25, rely=0.50, anchor='w')
    tk.Label(root, text=f"Rhythm Score: {rhythm['rhythm_score']}", **small_label_cfg).place(relx=0.25, rely=0.55, anchor='w')

    tk.Label(root, text=f"Grip Count (L): {grip_count[0]}", **label_cfg).place(relx=0.2, rely=0.63, anchor='w')
    tk.Label(root, text=f"Grip Count (R): {grip_count[1]}", **label_cfg).place(relx=0.2, rely=0.68, anchor='w')

    tk.Label(root, text="Fall Detection:", **label_cfg).place(relx=0.2, rely=0.78, anchor='w')
    tk.Label(
        root,
        text=f"Partial Falls: {', '.join(f'{p} @ {t}' for t, p in falls['partial_falls']) or 'None'}",
        **small_label_cfg
    ).place(relx=0.25, rely=0.83, anchor='w')

    tk.Label(
        root,
        text=f"Full Falls: {', '.join(falls['full_falls']) or 'None'}",
        **small_label_cfg
    ).place(relx=0.25, rely=0.88, anchor='w')

### ---------- Main ----------

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='black')
    root.geometry("700x600")
    root.title("Altius Logger")

    canvas = tk.Canvas(root, width=700, height=600, bg='black')
    canvas.pack()

    animation = DotAnimation(canvas)

    status_var = tk.StringVar()
    status_var.set("Waiting to start...")

    status_label = tk.Label(root, textvariable=status_var, font=("Helvetica", 20), fg='white', bg='black')
    canvas.create_window(350, 200, window=status_label)
    logger_widgets.append(status_label)

    stop_btn = tk.Label(root, text=" X ", font=("Helvetica", 24, "bold"), fg='white', bg='black', cursor="hand2")
    stop_btn.bind("<Button-1>", stop_logger)
    canvas.create_window(350, 500, window=stop_btn)
    logger_widgets.append(stop_btn)
    logger_widgets.append(canvas)  # also remove canvas if needed

    async def start_logger_after_gui_loads():
        await start_logger()

    root.after(0, lambda: asyncio.create_task(start_logger_after_gui_loads()))
    async_mainloop(root)
