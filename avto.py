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
        caption = ctypes.c_int(0x00262626)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(caption), ctypes.sizeof(caption))
    except Exception:
        pass


class PopupSelect(tk.Frame):
    def __init__(self, parent, options, variable):
        super().__init__(parent, bg=PANEL)
        self.options = options
        self.var = variable
        self.group = []
        self.popup = None
        self.var.set(options[0])
        self.display = tk.StringVar(value=options[0])
        self.btn = tk.Button(self, textvariable=self.display, relief="flat",
                             bd=0, bg=BG, fg=TEXT, activebackground=BG,
                             activeforeground=TEXT, font=("Segoe UI", 10),
                             padx=10, pady=3, cursor="hand2",
                             highlightthickness=1,
                             highlightbackground="#3a3a3a",
                             highlightcolor=ACCENT)
        self.btn.pack(side="left")
        self.btn.bind("<Button-1>", lambda e: self._toggle())

    def _toggle(self):
        for other in getattr(self, "group", []):
            if other is not self and other.popup and other.popup.winfo_exists():
                other._close()
        if self.popup and self.popup.winfo_exists():
            self._close()
        else:
            self._open()

    def _open(self):
        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.configure(bg="#3a3a3a")
        self.popup.attributes("-topmost", True)
        frame = tk.Frame(self.popup, bg=PANEL)
        frame.pack(padx=1, pady=1)
        for i, text in enumerate(self.options):
            item = tk.Label(frame, text=text, bg=PANEL,
                            fg=ACCENT if text == self.var.get() else TEXT,
                            font=("Segoe UI", 10), padx=20, pady=6,
                            anchor="w", cursor="hand2")
            item.grid(row=i, column=0, sticky="we")
            item.bind("<Enter>",
                      lambda e, w=item: w.config(bg=ACCENT, fg="white"))
            item.bind("<Leave>",
                      lambda e, w=item: w.config(
                          bg=PANEL,
                          fg=ACCENT if (w.cget("text")
                                        == self.var.get()) else TEXT))
            item.bind("<Button-1>",
                      lambda e, t=text: self._choose(t))
        self.popup.bind("<Escape>", lambda e: self._close())
        self.popup.bind("<FocusOut>", lambda e: self._close())
        self.popup.update_idletasks()
        x = self.btn.winfo_rootx()
        y = self.btn.winfo_rooty() + self.btn.winfo_height()
        self.popup.geometry("+{}+{}".format(x, y))
        self.popup.focus_force()

    def _choose(self, text):
        self.var.set(text)
        self._close()

    def _close(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None
        self.display.set(self.var.get())


class AutoClicker:
    def __init__(self):
        self.running = False
        self.delay = 0.05
        self.thread = None
        self.capturing = False
        self.hotkey = "f6"

        self.root = tk.Tk()
        self.root.title("TrueClick")
        self.root.geometry("400x470")
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

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="x", padx=16, pady=8)
        panel = tk.Frame(outer, bg="white")
        panel.pack(fill="x")
        content = tk.Frame(panel, bg=PANEL)
        content.pack(fill="x", padx=1, pady=1)

        row = tk.Frame(content, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(12, 6))
        tk.Label(row, text="Interval", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")

        time_frame = tk.Frame(content, bg=PANEL)
        time_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.h_var = tk.StringVar(value="0")
        self.m_var = tk.StringVar(value="0")
        self.s_var = tk.StringVar(value="0")
        self.ms_var = tk.StringVar(value="1")
        for label, var, maximum, minimum in (("H", self.h_var, 23, 0),
                                            ("M", self.m_var, 59, 0),
                                            ("S", self.s_var, 59, 0),
                                            ("ms", self.ms_var, 999, 1)):
            block = tk.Frame(time_frame, bg=PANEL)
            block.pack(side="left", padx=(0, 10))
            hrow = tk.Frame(block, bg=PANEL)
            hrow.pack()
            tk.Label(hrow, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
            entry = tk.Entry(hrow, textvariable=var, width=4, bg=BG, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightthickness=1, highlightbackground="#3a3a3a",
                             highlightcolor=ACCENT, font=("Segoe UI", 10),
                             justify="center")
            entry.pack(side="left")
            entry.bind("<FocusIn>",
                       lambda e, v=var: v.set("") if v.get() == "0" else None)
            entry.bind("<KeyRelease>",
                       lambda e, v=var, mx=maximum, mn=minimum:
                       self._clamp_delay(v, mx, mn))
            steppers = tk.Frame(hrow, bg=PANEL)
            steppers.pack(side="left", padx=(4, 0))
            for sym, delta in (("\u25b2", 1), ("\u25bc", -1)):
                tk.Button(steppers, text=sym, bd=0, relief="flat", bg=BG,
                          fg=MUTED, activebackground=PANEL,
                          activeforeground=TEXT, font=("Segoe UI", 8),
                          width=2, padx=0, pady=0, cursor="hand2",
                          command=lambda v=var, mx=maximum, mn=minimum,
                          d=delta: self._step_delay(v, mx, d, mn)).pack(
                              side="top", pady=(0, 2))
            entry.bind("<FocusOut>",
                       lambda e, v=var, mn=minimum: v.set(v.get() or mn))

        row = tk.Frame(content, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(6, 12))
        tk.Label(row, text="Button:", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.click_var = tk.StringVar(value="Left Button")
        self.click_select = PopupSelect(
            row, ("Left Button", "Right Button", "Middle Button"),
            self.click_var)
        self.click_select.pack(side="left", padx=(12, 0))
        tk.Label(row, text="Click Type:", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 0))
        self.click_mode_var = tk.StringVar(value="Single Click")
        self.click_mode_select = PopupSelect(
            row, ("Single Click", "Double Click", "Triple Click", "Hold"),
            self.click_mode_var)
        self.click_mode_select.pack(side="left", padx=(8, 0))
        self.click_select.group = [self.click_select, self.click_mode_select]
        self.click_mode_select.group = [self.click_select,
                                        self.click_mode_select]

        houter = tk.Frame(self.root, bg=BG)
        houter.pack(fill="x", padx=16, pady=8)
        hpanel = tk.Frame(houter, bg="white")
        hpanel.pack(fill="x")
        hcontent = tk.Frame(hpanel, bg=PANEL)
        hcontent.pack(fill="x", padx=1, pady=1)

        tk.Label(hcontent, text="Toggle hotkey", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).pack(padx=12, pady=(12, 6), anchor="w")
        row = tk.Frame(hcontent, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(4, 12))
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
        self.start_btn = tk.Button(btn_frame, text="Start", command=self.start,
                                   bg=GREEN, fg="white", bd=0, relief="flat",
                                   activebackground="#3da83d",
                                   activeforeground="white",
                                   font=("Segoe UI", 10, "bold"),
                                   padx=14, pady=6, cursor="hand2")
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

    def _on_root_click(self, event):
        for sel in (self.click_select, self.click_mode_select):
            if event.widget is sel.btn:
                return
        closed = False
        for sel in (self.click_select, self.click_mode_select):
            if sel.popup and sel.popup.winfo_exists():
                sel._close()
                closed = True
        if closed:
            return
        if isinstance(event.widget, (tk.Entry, tk.Button,
                                     tk.Radiobutton, tk.Checkbutton)):
            return
        self.root.focus_set()

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
        button = self.click_var.get().split()[0].lower()
        mode = self.click_mode_var.get()
        if mode == "Hold":
            mouse.press(button)
            try:
                while self.running:
                    time.sleep(self.delay)
            finally:
                mouse.release(button)
            return
        while self.running:
            if not self._inside_window():
                if mode == "Double Click":
                    mouse.double_click(button)
                elif mode == "Triple Click":
                    mouse.click(button)
                    mouse.click(button)
                    mouse.click(button)
                else:
                    mouse.click(button)
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

    def _clamp_delay(self, var, maximum, minimum=0):
        val = var.get()
        digits = "".join(ch for ch in val if ch.isdigit())
        if not digits:
            var.set("")
            return
        num = int(digits)
        if num > maximum:
            var.set(str(maximum))
        elif num < minimum:
            var.set(str(minimum))

    def _step_delay(self, var, maximum, delta, minimum=0):
        try:
            cur = int(var.get())
        except ValueError:
            cur = minimum
        var.set(str(max(minimum, min(maximum, cur + delta))))

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