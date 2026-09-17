import threading
import time
import keyboard
import mouse
import tkinter as tk
from tkinter import ttk


class AutoClicker:
    def __init__(self):
        self.running = False
        self.delay = 0.05
        self.click_type = "left"
        self.thread = None

        self.root = tk.Tk()
        self.root.title("AutoClicker")
        self.root.geometry("320x300")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")

        self._build_ui()

        keyboard.add_hotkey("F6", self.toggle)
        keyboard.add_hotkey("Esc", self.stop)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"))

        ttk.Label(self.root, text="AutoClicker", font=("Segoe UI", 14, "bold")).pack(pady=(12, 6))

        frame = ttk.Frame(self.root)
        frame.pack(pady=6)

        ttk.Label(frame, text="Delay (sec):").grid(row=0, column=0, padx=6, sticky="e")
        self.delay_var = tk.StringVar(value="0.05")
        self.delay_entry = ttk.Entry(frame, textvariable=self.delay_var, width=10)
        self.delay_entry.grid(row=0, column=1, padx=6)

        ttk.Label(frame, text="Click type:").grid(row=1, column=0, padx=6, pady=8, sticky="e")
        self.click_var = tk.StringVar(value="left")
        ttk.Radiobutton(frame, text="Left", variable=self.click_var, value="left").grid(row=1, column=1, sticky="w", padx=6)
        ttk.Radiobutton(frame, text="Right", variable=self.click_var, value="right").grid(row=2, column=1, sticky="w", padx=6)

        self.status_label = ttk.Label(self.root, text="STOPPED", foreground="red", style="Status.TLabel")
        self.status_label.pack(pady=10)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=6)

        self.start_btn = ttk.Button(btn_frame, text="Start (F6)", command=self.start, width=12)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = ttk.Button(btn_frame, text="Stop (F6)", command=self.stop, width=12)
        self.stop_btn.grid(row=0, column=1, padx=6)

        ttk.Label(self.root, text="F6 = toggle | Esc = stop", foreground="#888888").pack(side="bottom", pady=10)

    def _click_loop(self):
        while self.running:
            if self.click_var.get() == "left":
                mouse.click("left")
            else:
                mouse.click("right")
            time.sleep(self.delay)

    def start(self):
        try:
            self.delay = float(self.delay_var.get())
        except ValueError:
            self.delay = 0.05
        if self.delay < 0.001:
            self.delay = 0.001
        self.running = True
        self.status_label.config(text="RUNNING", foreground="lime")
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.status_label.config(text="STOPPED", foreground="red")

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AutoClicker().run()
