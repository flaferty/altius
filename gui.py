import tkinter as tk
import asyncio
import sys
import time
import math
import signal
from async_tkinter_loop import async_mainloop
from arm_leg_usage import analyze_usage_from_csv

proc = None
usage = analyze_usage_from_csv("data") 

class DotAnimation:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=600, height=600, bg='black')
        self.canvas.pack()
        self.center_x = 300
        self.center_y = 300
        self.radius = 10
        self.dot1 = self.canvas.create_oval(0, 0, 0, 0, fill='white')
        self.dot2 = self.canvas.create_oval(0, 0, 0, 0, fill='white')
        self.max_offset = 70
        self.duration = 0.75  # seconds per half-cycle
        self.start_time = time.time()
        self.phase = 0  # 0=up/down, 1=left/right

        self.animate()
        
        self.stop_label = tk.Label(root, text=" X ",font=("Helvetica", 24, "bold"),fg='white', bg='black', cursor="pointinghand")
        self.stop_label.bind("<Button-1>", stop_logger_process)
        self.canvas.create_window(300, 500, window=self.stop_label)
        
        self.loading_text = self.canvas.create_text(300, 450, text="Collecting data...", fill="white", font=("Helvetica", 20, "bold"), anchor='center')


    def animate(self):
        try:
            now = time.time()
            elapsed = (now - self.start_time) % (2 * self.duration)

        # Use sinusoidal easing for smooth motion
            t = elapsed / self.duration
            if t > 1:
                t = 2 - t  # Reverse in the second half of cycle

        # Easing: smoothstep (you can try sin(t * pi / 2), etc.)
            eased = math.sin(t * math.pi / 2) ** 4
            offset = eased * self.max_offset

        # Switch phase every full cycle
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

            self.root.after(16, self.animate)  # ~60 FPS
        except tk.TclError:
            return
        
    def make_black(self):
        self.canvas.configure(bg='black')  
        self.canvas.delete("all")       
        
    phase_toggle_ready = True
    
def show_finished_screen(root):
    animation.make_black()
    tk.Label(root, text="Average Score:", font=("Helvetica", 24, "bold"), bg='black').place(relx=0.2, rely=0.2, anchor='w')
    tk.Label(root, text="Smoothness:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.3, anchor='w')
    tk.Label(root, text="Stability:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.4, anchor='w')
    tk.Label(root, text="Arm/Leg Usage:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.5, anchor='w')
    tk.Label(root, text=f"  Arm: {usage['arm_usage_ratio']*100:.0f}%  |  Leg: {usage['leg_usage_ratio']*100:.0f}%", 
         font=("Helvetica", 16), bg='black', fg='white').place(relx=0.25, rely=0.55, anchor='w')
    tk.Label(root, text="Rhythm/Flow:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.6, anchor='w')
    tk.Label(root, text="Grip Count:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.7, anchor='w')
    # tk.Label(root, text="Reach/Extension:", font=("Helvetica", 20, "bold"), bg='black').place(relx=0.25, rely=0.8, anchor='w')    
    

async def run_main_and_update_gui(root):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "logger.py"
    )
    await proc.wait()
    root.after(0, show_finished_screen, root)

def stop_logger_process(event=None):
    global proc
    if proc and proc.returncode is None:
        proc.send_signal(signal.SIGINT)

async def run_main_and_update_gui(root):
    global proc
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "logger.py"
    )
    await proc.wait()
    root.after(0, show_finished_screen, root)

def start_asyncio_loop(root):
    loop = asyncio.get_event_loop()
    loop.create_task(run_main_and_update_gui(root))
    def poll_loop():
        loop.stop()
        loop.run_forever()
        root.after(50, poll_loop)
    root.after(50, poll_loop)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-topmost', 1)
    animation = DotAnimation(root)
    start_asyncio_loop(root)
    root.mainloop()