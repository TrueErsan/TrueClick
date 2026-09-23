import os
import sys
import threading
import time
import ctypes
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


def _resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def _enable_dark_title_bar(root):
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception:
        pass


class AutoClicker:
    def __init__(self):
        self.running = False
        self.delay = 0.05
        self.thread = None
        self.capturing = False
        self.hotkey = "f6"

        self.root = tk.Tk()
        self.root.title("TrueClick")
        self.root.geometry("340x460")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        try:
            self.root.iconbitmap(_resource_path("icon.ico"))
        except tk.TclError:
            pass
        _enable_dark_title_bar(self.root)

        self._build_ui()

        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_reqwidth(),
                          self.root.winfo_reqheight())

        self.root.bind("<Button-1>", self._on_root_click, "+")
        self.toggle_handle = keyboard.add_hotkey(self.hotkey, self.toggle)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(18, 6))
        tk.Label(header, text="TrueClick", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 18, "bold")).pack()

        panel = tk.Frame(self.root, bg=PANEL)
        panel.pack(fill="x", padx=16, pady=8)

        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(14, 6))
        tk.Label(row, text="Delay", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")

        time_frame = tk.Frame(panel, bg=PANEL)
        time_frame.pack(fill="x", padx=12, pady=(0, 14))
        self.h_var = tk.StringVar(value="0")
        self.m_var = tk.StringVar(value="0")
        self.s_var = tk.StringVar(value="1")
        self.ms_var = tk.StringVar(value="0")
        for label, var, maximum in (("H", self.h_var, 23),
                                    ("M", self.m_var, 59),
                                    ("S", self.s_var, 59),
                                    ("ms", self.ms_var, 999)):
            block = tk.Frame(time_frame, bg=PANEL)
            block.pack(side="left", padx=(0, 10))
            entry = tk.Entry(block, textvariable=var, width=4, bg=BG, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightthickness=1, highlightbackground="#3a3a3a",
                             highlightcolor=ACCENT, font=("Segoe UI", 10),
                             justify="center")
            entry.pack()
            entry.bind("<FocusIn>",
                       lambda e, v=var: v.set("") if v.get() == "0" else None)
            entry.bind("<KeyRelease>",
                       lambda e, v=var, mx=maximum: self._clamp_delay(v, mx))
            entry.bind("<FocusOut>",
                       lambda e, v=var: v.set(v.get() or "0"))
            tk.Label(block, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8)).pack()

        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(6, 14))
        tk.Label(row, text="Click type", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.click_var = tk.StringVar(value="Left Button")
        self.click_display = tk.StringVar(value="Left Button")
        self.click_btn = tk.Button(row, textvariable=self.click_display,
                                   relief="flat", bd=0, bg=BG, fg=TEXT,
                                   activebackground=BG,
                                   activeforeground=TEXT,
                                   font=("Segoe UI", 10), padx=10, pady=3,
                                   cursor="hand2", highlightthickness=1,
                                   highlightbackground="#3a3a3a",
                                   highlightcolor=ACCENT)
        self.click_btn.pack(side="left", padx=(12, 0))
        self.click_btn.bind("<Button-1>",
                            lambda e: self._toggle_click_menu())

        hpanel = tk.Frame(self.root, bg=PANEL)
        hpanel.pack(fill="x", padx=16, pady=8)

        tk.Label(hpanel, text="Toggle hotkey", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(padx=12, pady=(12, 6), anchor="w")
        row = tk.Frame(hpanel, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(4, 14))
        self.hotkey_label = tk.Label(row, text=self.hotkey.upper(), bg=BG,
                                     fg=ACCENT, font=("Segoe UI", 12, "bold"),
                                     width=8, pady=4)
        self.hotkey_label.pack(side="left", anchor="center")
        self.capture_btn = self._accent_button(row, "Change",
                                               self.change_hotkey)
        self.capture_btn.pack(side="right", anchor="center")

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

    def _toggle_click_menu(self):
        if getattr(self, "_click_popup", None) and self._click_popup.winfo_exists():
            self._close_click_menu()
            return
        self._open_click_menu()

    def _open_click_menu(self):
        self._click_popup = tk.Toplevel(self.root)
        self._click_popup.overrideredirect(True)
        self._click_popup.configure(bg="#3a3a3a")
        self._click_popup.attributes("-topmost", True)
        frame = tk.Frame(self._click_popup, bg=PANEL)
        frame.pack(padx=1, pady=1)
        for i, text in enumerate(("Left Button", "Right Button",
                                  "Middle Button")):
            item = tk.Label(frame, text=text, bg=PANEL,
                            fg=ACCENT if text == self.click_var.get() else TEXT,
                            font=("Segoe UI", 10), padx=20, pady=6,
                            anchor="w", cursor="hand2")
            item.grid(row=i, column=0, sticky="we")
            item.bind("<Enter>",
                      lambda e, w=item: w.config(bg=ACCENT, fg="white"))
            item.bind("<Leave>",
                      lambda e, w=item: w.config(
                          bg=PANEL,
                          fg=ACCENT if (w.cget("text")
                                        == self.click_var.get()) else TEXT))
            item.bind("<Button-1>",
                      lambda e, t=text: self._choose_click(t))
        self._click_popup.bind("<Escape>", lambda e: self._close_click_menu())
        self._click_popup.bind("<FocusOut>",
                               lambda e: self._close_click_menu())
        self._click_popup.update_idletasks()
        x = self.click_btn.winfo_rootx()
        y = self.click_btn.winfo_rooty() + self.click_btn.winfo_height()
        self._click_popup.geometry("+{}+{}".format(x, y))
        self._click_popup.focus_force()

    def _on_root_click(self, event):
        if event.widget is self.click_btn:
            return
        popup = getattr(self, "_click_popup", None)
        if popup and popup.winfo_exists():
            self._close_click_menu()
            return
        if isinstance(event.widget, (tk.Entry, tk.Button,
                                     tk.Radiobutton, tk.Checkbutton)):
            return
        self.root.focus_set()

    def _choose_click(self, text):
        self.click_var.set(text)
        self._close_click_menu()

    def _close_click_menu(self):
        if getattr(self, "_click_popup", None) and self._click_popup.winfo_exists():
            self._click_popup.destroy()
        self._click_popup = None
        self.click_display.set(self.click_var.get())

    def _update_footer(self):
        self.footer_label.config(
            text="{} = toggle start/stop".format(self.hotkey.upper()))

    def _accent_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=ACCENT,
                         fg="white", activebackground=ACCENT_DARK,
                         activeforeground="white", relief="flat", bd=0,
                         font=("Segoe UI", 10, "bold"), padx=14, pady=6,
                         cursor="hand2")

    def _inside_window(self):
        x1 = self.root.winfo_rootx()
        y1 = self.root.winfo_rooty()
        x2 = x1 + self.root.winfo_width()
        y2 = y1 + self.root.winfo_height()
        px = self.root.winfo_pointerx()
        py = self.root.winfo_pointery()
        return x1 <= px <= x2 and y1 <= py <= y2

    def _click_loop(self):
        while self.running:
            if not self._inside_window():
                mouse.click(self.click_var.get().split()[0].lower())
            time.sleep(self.delay)

    def _get_delay(self):
        def to_int(var):
            try:
                return int(float(var.get()))
            except ValueError:
                return 0
        return max(0.001,
                   to_int(self.h_var) * 3600
                   + to_int(self.m_var) * 60
                   + to_int(self.s_var)
                   + to_int(self.ms_var) / 1000)

    def _clamp_delay(self, var, maximum):
        val = var.get()
        digits = "".join(ch for ch in val if ch.isdigit())
        if not digits:
            var.set("")
            return
        num = int(digits)
        if num > maximum:
            var.set(str(maximum))

    def start(self):
        if self.running:
            return
        self.delay = self._get_delay()
        self.running = True
        self.status_label.config(text="RUNNING", fg=GREEN)
        self.start_btn.config(state="disabled")
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.status_label.config(text="STOPPED", fg=RED)
        self.start_btn.config(state="normal")

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def change_hotkey(self):
        if self.capturing:
            return
        self.capturing = True
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
            self._update_footer()
        else:
            pass

    def _on_close(self):
        keyboard.remove_hotkey(self.toggle_handle)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AutoClicker().run()