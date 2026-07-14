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


def _clear_webview_http_cache():
    """Delete WebView2's persistent HTTP/code caches before the engine starts.

    With private_mode=False the Edge engine keeps a disk cache under
    %APPDATA%\\pywebview\\EBWebView\\Default that survives app restarts, so UI
    changes to index.html/JS could keep rendering from stale cache. Removing
    just the cache folders (never 'Local Storage', which holds user prefs)
    guarantees a fresh load. Safe no-op if the folders don't exist or are held
    open by another instance.
    """
    import shutil
    profile = Path(os.environ.get("APPDATA", "")) / "pywebview" / "EBWebView" / "Default"
    for sub in ("Cache", "Code Cache", "GPUCache"):
        try:
            shutil.rmtree(profile / sub, ignore_errors=True)
        except Exception:
            pass


def main():
    _clear_webview_http_cache()
    # Belt-and-suspenders against stale UI: the folder-delete above can silently
    # no-op if a prior ACEForge/WebView2 process still holds the cache open, in
    # which case the Edge engine keeps serving an OLD index.html/JS from disk
    # cache and edits never appear. Telling the engine to skip its HTTP/disk
    # cache entirely guarantees the freshest files load every launch.
    _prev_args = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
    if "--disable-http-cache" not in _prev_args:
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
            (_prev_args + " ").lstrip() + "--disable-http-cache --disk-cache-size=1"
        ).strip()
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
        url=str(html_path),
        js_api=api,
        width=1340,
        height=880,
        min_size=(1024, 700),
        background_color="#ede4ce",
        text_select=False,
    )

    api.set_window(window)
    # http_server=True serves local files over http://127.0.0.1 instead of file://.
    # WebView2 (the Edge engine pywebview uses on Windows) has a known bug where native
    # <select> dropdown popups silently fail to render when the page origin is file://.
    webview.start(debug=False, private_mode=False, http_server=True, icon=icon_path if icon_path else None)


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
