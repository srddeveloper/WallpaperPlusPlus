import tkinter as tk
from tkinter import filedialog
import threading
import subprocess
import sys
import os
import signal
import atexit

WALLPAPER_ENGINE = '''
import sys
import os
import objc
from Cocoa import (
    NSApplication, NSImage, NSWindow, NSView, NSScreen, NSColor,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSWindowCollectionBehaviorIgnoresCycle,
    NSApplicationActivationPolicyAccessory,
)

WALLPAPER_PATH = sys.argv[1]
PID_FILE = "/tmp/_wallpaper_plus.pid"
OUR_LEVEL = -2147483620

with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

class WallpaperView(NSView):
    def drawRect_(self, rect):
        image = NSImage.alloc().initWithContentsOfFile_(WALLPAPER_PATH)
        if image:
            image.drawInRect_(self.bounds())
        else:
            NSColor.blackColor().set()

def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    screen = NSScreen.mainScreen().frame()
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        screen, 0, 2, False
    )
    window.setLevel_(OUR_LEVEL)
    behavior = (
        NSWindowCollectionBehaviorCanJoinAllSpaces |
        NSWindowCollectionBehaviorStationary |
        NSWindowCollectionBehaviorIgnoresCycle
    )
    window.setCollectionBehavior_(behavior)
    window.setIgnoresMouseEvents_(True)
    window.setOpaque_(True)
    window.setHasShadow_(False)
    view = WallpaperView.alloc().initWithFrame_(screen)
    window.setContentView_(view)
    window.orderBack_(None)
    app.run()

main()
'''

BG      = "#0d0d0d"
SURFACE = "#1a1a1a"
CARD    = "#1e1e1e"
ACCENT  = "#c8f542"
TEXT    = "#f0f0f0"
MUTED   = "#666666"
BORDER  = "#2a2a2a"
RED_BG  = "#3a0808"
RED_FG  = "#ff5555"

PID_FILE    = "/tmp/_wallpaper_plus.pid"
ENGINE_FILE = "/tmp/_wallpaper_plus_engine.py"

wallpaper_proc = None
current_path   = None


def kill_orphan_engine():
    global wallpaper_proc
    if wallpaper_proc and wallpaper_proc.poll() is None:
        wallpaper_proc.terminate()
        wallpaper_proc = None
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass
        finally:
            try:
                os.remove(PID_FILE)
            except FileNotFoundError:
                pass


def make_button(parent, text, command, bg, fg, hover_bg=None):
    """
    macOS tkinter ignores bg on tk.Button.
    Wrap a Label in a Frame to get full color control.
    """
    if hover_bg is None:
        hover_bg = bg

    frame = tk.Frame(parent, bg=bg, cursor="hand2")
    label = tk.Label(
        frame, text=text, bg=bg, fg=fg,
        font=("SF Pro Display", 13, "bold"),
        padx=0, pady=14, anchor="center"
    )
    label.pack(fill="both", expand=True)

    def on_enter(_):
        frame.configure(bg=hover_bg)
        label.configure(bg=hover_bg)

    def on_leave(_):
        frame.configure(bg=bg)
        label.configure(bg=bg)

    def on_click(_):
        command()

    frame.bind("<Enter>", on_enter)
    frame.bind("<Leave>", on_leave)
    frame.bind("<Button-1>", on_click)
    label.bind("<Enter>", on_enter)
    label.bind("<Leave>", on_leave)
    label.bind("<Button-1>", on_click)

    return frame


class WallpaperPlusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wallpaper++")
        self.geometry("520x430")
        self.resizable(False, False)
        self.configure(bg=BG)
        kill_orphan_engine()
        atexit.register(kill_orphan_engine)
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._hide_window)
        # Allow proper quit from dock right-click > Quit
        self.createcommand("::tk::mac::Quit", self._on_close)
        # Clicking the dock icon re-opens the window
        self.createcommand("::tk::mac::ReopenApplication", self._show_window)

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=32, pady=(36, 0))

        title_row = tk.Frame(header, bg=BG)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="Wallpaper",
                 font=("SF Pro Display", 30, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(title_row, text="++",
                 font=("SF Pro Display", 30, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")

        tk.Label(header,
                 text="Made by Saud with ♥",
                 font=("SF Pro Display", 11), bg=BG, fg=MUTED).pack(anchor="w", pady=(6, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=24)

        # ── File path ────────────────────────────────────────────────────────
        path_frame = tk.Frame(self, bg=SURFACE, highlightthickness=1,
                              highlightbackground=BORDER)
        path_frame.pack(padx=32, fill="x")

        self.path_var = tk.StringVar(value="  No file chosen")
        tk.Label(path_frame, textvariable=self.path_var,
                 bg=SURFACE, fg=MUTED,
                 font=("SF Mono", 10), anchor="w",
                 padx=12, pady=11).pack(side="left", fill="x", expand=True)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(padx=32, pady=14, fill="x")

        choose_btn = make_button(btn_row, "Choose Image", self._choose_image,
                                 bg="#2e2e2e", fg="#000000", hover_bg=ACCENT)
        choose_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        apply_btn = make_button(btn_row, "▶  Apply Wallpaper", self._apply_wallpaper,
                                bg=ACCENT, fg="#000000", hover_bg="#d4f55a")
        apply_btn.pack(side="left", fill="x", expand=True)

        # ── Status ───────────────────────────────────────────────────────────
        status_card = tk.Frame(self, bg=CARD, highlightthickness=1,
                               highlightbackground=BORDER)
        status_card.pack(padx=32, pady=(0, 14), fill="x")

        status_inner = tk.Frame(status_card, bg=CARD)
        status_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(status_inner, text="STATUS",
                 font=("SF Pro Display", 9, "bold"),
                 bg=CARD, fg=MUTED).pack(anchor="w")

        dot_row = tk.Frame(status_inner, bg=CARD)
        dot_row.pack(anchor="w", pady=(4, 0))

        self.status_dot = tk.Label(dot_row, text="●",
                                   font=("SF Pro Display", 14),
                                   bg=CARD, fg=MUTED)
        self.status_dot.pack(side="left")

        self.status_var = tk.StringVar(value="Idle — no wallpaper running")
        tk.Label(dot_row, textvariable=self.status_var,
                 bg=CARD, fg=TEXT,
                 font=("SF Pro Display", 11)).pack(side="left", padx=8)

        # ── Stop button ──────────────────────────────────────────────────────
        stop_btn = make_button(self, "■  Stop Wallpaper", self._stop_wallpaper,
                               bg=RED_BG, fg=RED_FG, hover_bg="#4a0a0a")
        stop_btn.pack(padx=32, fill="x")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="Choose a wallpaper image",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.heic *.webp"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        global current_path
        current_path = path
        self.path_var.set(f"  {os.path.basename(path)}")

    def _apply_wallpaper(self):
        if not current_path:
            self._set_status("⚠  Choose an image first", ACCENT)
            return
        kill_orphan_engine()
        self._set_status("Starting…", ACCENT)
        threading.Thread(target=self._launch_engine, daemon=True).start()

    def _launch_engine(self):
        global wallpaper_proc
        with open(ENGINE_FILE, "w") as f:
            f.write(WALLPAPER_ENGINE)
        wallpaper_proc = subprocess.Popen(
            [sys.executable, ENGINE_FILE, current_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.after(0, lambda: self._set_status("Wallpaper++ is active", ACCENT))
        wallpaper_proc.wait()
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        self.after(0, lambda: self._set_status("Idle — no wallpaper running", MUTED))

    def _stop_wallpaper(self):
        kill_orphan_engine()
        self._set_status("Idle — no wallpaper running", MUTED)

    def _set_status(self, msg, color=TEXT):
        self.status_var.set(msg)
        self.status_dot.configure(fg=color)

    def _hide_window(self):
        self.withdraw()

    def _show_window(self):
        self.deiconify()
        self.lift()

    def _on_close(self):
        kill_orphan_engine()
        self.destroy()


if __name__ == "__main__":
    app = WallpaperPlusApp()
    app.mainloop()
