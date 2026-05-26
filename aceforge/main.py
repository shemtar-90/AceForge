"""
ACEForge — Entry Point
Launches the full app as a pywebview desktop window.
No tkinter/customtkinter required at runtime.
"""

import sys
import os
from pathlib import Path


def get_web_dir() -> Path:
    """Find the web/ directory — works in dev and PyInstaller one-file mode."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    for candidate in [base / "web", Path(__file__).parent / "web"]:
        if (candidate / "index.html").exists():
            return candidate
    return Path(__file__).parent / "web"


def main():
    try:
        import webview
    except ImportError:
        import webbrowser
        html = get_web_dir() / "index.html"
        if html.exists():
            webbrowser.open(html.as_uri())
        else:
            print("ERROR: pywebview not installed and index.html not found.")
            print("Run: pip install pywebview")
        return

    from aceforge.app_api import AppAPI
    from aceforge.config import Config

    config = Config()
    api = AppAPI(config)

    web_dir = get_web_dir()
    html_path = web_dir / "index.html"

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

    webview.start(debug=False, private_mode=False)


if __name__ == "__main__":
    main()
