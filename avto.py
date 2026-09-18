import threading
import time
import keyboard
import mouse
import tkinter as tk

BG = "#1e1e1e"
PANEL = "#262626"
ACCENT = "#7c5cff"
ACCENT_DARK = "#6a4ae0"
TEXT = "#f0f0f0"
MUTED = "#9e9e9e"
GREEN = "#4ec94e"
RED = "#ff5c5c"


class AutoClicker:
    def __init__(self):
        self.running = False
        self.delay = 0.05
        self.thread = None
        self.capturing = False
        self.hotkey = "f6"

        self.root = tk.Tk()
        self.root.title("AutoClicker")
        self.root.geometry("340x460")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self._build_ui()

        self.toggle_handle = keyboard.add_hotkey(self.hotkey, self.toggle)
        self.stop_handle = keyboard.add_hotkey("esc", self.stop)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(18, 6))
        tk.Label(header, text="AutoClicker", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack()
        tk.Label(header, text="Simple and fast mouse autoclicker",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack()

        panel = tk.Frame(self.root, bg=PANEL)
        panel.pack(fill="x", padx=16, pady=8)

        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(14, 6))
        tk.Label(row, text="Delay (sec)", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.delay_var = tk.StringVar(value="0.05")
        tk.Entry(row, textvariable=self.delay_var, bg=BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 highlightthickness=1, highlightbackground="#3a3a3a",
                 highlightcolor=ACCENT, font=("Segoe UI", 10)
                 ).pack(side="right", ipady=4, ipadx=4)

        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(6, 14))
        tk.Label(row, text="Click type", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.click_var = tk.StringVar(value="left")
        for text, val in (("Left", "left"), ("Right", "right")):
            tk.Radiobutton(row, text=text, value=val, variable=self.click_var,
                           bg=PANEL, fg=TEXT, selectcolor=PANEL,
                           activebackground=PANEL, activeforeground=TEXT,
                           font=("Segoe UI", 10), highlightthickness=0
                           ).pack(side="right", padx=(8, 0))

        hpanel = tk.Frame(self.root, bg=PANEL)
        hpanel.pack(fill="x", padx=16, pady=8)

        tk.Label(hpanel, text="Toggle hotkey", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(padx=12, pady=(12, 6), anchor="w")
        row = tk.Frame(hpanel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(0, 4))
        self.hotkey_label = tk.Label(row, text=self.hotkey.upper(), bg=BG,
                                     fg=ACCENT, font=("Segoe UI", 12, "bold"),
                                     width=8, pady=6)
        self.hotkey_label.pack(side="left")
        self.capture_btn = self._accent_button(row, "Change",
                                               self.change_hotkey)
        self.capture_btn.pack(side="right")
        self.hotkey_hint = tk.Label(hpanel, text="Set a new key for toggle",
                                    bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.hotkey_hint.pack(padx=12, pady=(0, 12), anchor="w")

        self.status_label = tk.Label(self.root, text="STOPPED", bg=BG,
                                     fg=RED, font=("Segoe UI", 12, "bold"))
        self.status_label.pack(pady=12)

        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=6)
        self.start_btn = self._accent_button(btn_frame, "Start", self.start)
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop,
                                  bg="#3a3a3a", fg=TEXT,
                                  activebackground="#4a4a4a",
                                  activeforeground=TEXT, relief="flat", bd=0,
                                  font=("Segoe UI", 10, "bold"),
                                  padx=14, pady=6, cursor="hand2")
        self.stop_btn.pack(side="left", padx=6)

        self.footer_label = tk.Label(self.root, bg=BG, fg=MUTED,
                                     font=("Segoe UI", 9))
        self.footer_label.pack(side="bottom", pady=12)
        self._update_footer()

    def _update_footer(self):
        self.footer_label.config(
            text="Esc = stop  |  {} = toggle".format(self.hotkey.upper()))

    def _accent_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=ACCENT,
                         fg="white", activebackground=ACCENT_DARK,
                         activeforeground="white", relief="flat", bd=0,
                         font=("Segoe UI", 10, "bold"), padx=14, pady=6,
                         cursor="hand2")

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
        self.status_label.config(text="RUNNING", fg=GREEN)
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.status_label.config(text="STOPPED", fg=RED)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def change_hotkey(self):
        if self.capturing:
            return
        self.capturing = True
        self.hotkey_hint.config(text="Press any key...", fg=ACCENT)
        self.capture_btn.config(state="disabled")
        threading.Thread(target=self._capture_key, daemon=True).start()

    def _capture_key(self):
        try:
            key = keyboard.read_key()
        except Exception:
            key = None
        self.root.after(0, self._finish_capture, key)

    def _finish_capture(self, key):
        self.capturing = False
        self.capture_btn.config(state="normal")
        if key and key.lower() != "esc":
            keyboard.remove_hotkey(self.toggle_handle)
            self.hotkey = key.lower()
            self.toggle_handle = keyboard.add_hotkey(self.hotkey, self.toggle)
            self.hotkey_label.config(text=self.hotkey.upper())
            self.hotkey_hint.config(text="Set a new key for toggle", fg=MUTED)
            self._update_footer()
        else:
            self.hotkey_hint.config(text="Canceled, keeping current key",
                                    fg=MUTED)

    def _on_close(self):
        keyboard.remove_hotkey(self.toggle_handle)
        keyboard.remove_hotkey(self.stop_handle)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AutoClicker().run()