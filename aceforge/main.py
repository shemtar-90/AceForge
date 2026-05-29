"""
ACEForge — Entry Point
Launches the full app as a pywebview desktop window.
"""

import sys
import os
from pathlib import Path


def get_icon() -> str:
    """Find AF_Icon.ico in all the places PyInstaller might put it."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        candidates += [
            base / "AF_Icon.ico",
            base / "aceforge" / "AF_Icon.ico",
        ]
    here = Path(__file__).parent
    candidates += [
        here.parent / "AF_Icon.ico",
        here / "AF_Icon.ico",
        Path.cwd() / "AF_Icon.ico",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return ""


def get_index_html() -> Path:
    """
    Find index.html in all the places PyInstaller might put it.
    PyInstaller one-file mode extracts to a temp folder at sys._MEIPASS.
    We search exhaustively and print every candidate so errors are debuggable.
    """
    candidates = []

    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        candidates += [
            base / "aceforge" / "web" / "index.html",
            base / "web" / "index.html",
            base / "index.html",
        ]

    # Dev mode — relative to this file
    here = Path(__file__).parent
    candidates += [
        here / "web" / "index.html",
        here.parent / "aceforge" / "web" / "index.html",
        Path.cwd() / "aceforge" / "web" / "index.html",
        Path.cwd() / "web" / "index.html",
    ]

    for path in candidates:
        if path.exists():
            return path

    # None found — write a debug report beside the exe so the user can send it
    debug_lines = ["ACEForge could not find index.html\n", f"sys._MEIPASS: {getattr(sys,'_MEIPASS','not set')}\n", f"__file__: {__file__}\n", f"cwd: {os.getcwd()}\n", "\nSearched:\n"]
    debug_lines += [f"  {'EXISTS' if p.exists() else 'missing'}: {p}\n" for p in candidates]

    # Also list what IS in _MEIPASS so we can see where files landed
    if hasattr(sys, "_MEIPASS"):
        debug_lines.append("\nContents of _MEIPASS:\n")
        for root, dirs, files in os.walk(sys._MEIPASS):
            for f in files:
                debug_lines.append(f"  {os.path.join(root, f)}\n")

    debug_path = Path(sys.executable).parent / "aceforge_debug.txt" if not hasattr(sys, "_MEIPASS") else Path(sys._MEIPASS).parent / "aceforge_debug.txt"
    try:
        with open(debug_path, "w") as fh:
            fh.writelines(debug_lines)
    except Exception:
        pass

    raise FileNotFoundError(
        f"index.html not found. A debug report was written to: {debug_path}\n"
        f"Searched {len(candidates)} locations."
    )


def main():
    try:
        import webview
    except ImportError:
        # Fallback: open in browser
        try:
            html = get_index_html()
            import webbrowser
            webbrowser.open(html.as_uri())
        except Exception as e:
            _show_error_window(str(e))
        return

    try:
        html_path = get_index_html()
    except FileNotFoundError as e:
        _show_error_window(str(e))
        return

    from aceforge.app_api import AppAPI
    from aceforge.config import Config

    config = Config()
    api = AppAPI(config)

    icon_path = get_icon()

    window = webview.create_window(
        title="ACEForge — Weenie Workbench",
        url=html_path.as_uri(),
        js_api=api,
        width=1340,
        height=880,
        min_size=(1024, 700),
        background_color="#ede4ce",
        text_select=False,
    )

    api.set_window(window)
    webview.start(debug=False, private_mode=False, icon=icon_path if icon_path else None)


def _show_error_window(message: str):
    """Last-resort: show the error in a basic tkinter window if pywebview fails."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ACEForge — Startup Error", message)
        root.destroy()
    except Exception:
        print("ACEForge ERROR:", message)


if __name__ == "__main__":
    main()
