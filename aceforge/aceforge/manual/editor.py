"""
ACEForge Manual Editor Panel
Hosts the Weenie Farmer workbench HTML UI inside a pywebview window
embedded as a frame within the main CustomTkinter application.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

from ..config import Config

BG_PANEL  = "#11111e"
AMBER     = "#c8a96e"
TEXT_DIM  = "#7777aa"
TEXT_MAIN = "#ddddef"
BLUE_MID  = "#2a2a4a"
GREEN     = "#55bb77"
FONT_MONO = "Consolas"


def get_web_dir() -> Path:
    """Find the web/ directory containing workbench.html."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent

    candidates = [
        base / "web",
        Path(__file__).parent / "web",
    ]
    for p in candidates:
        if (p / "workbench.html").exists():
            return p
    return Path(__file__).parent / "web"


class ManualPanel(ctk.CTkFrame):
    def __init__(self, parent, config: Config, **kwargs):
        super().__init__(parent, fg_color=BG_PANEL, corner_radius=0, **kwargs)
        self.config = config
        self._webview_started = False
        self._build()

    def _build(self):
        # Top toolbar
        toolbar = ctk.CTkFrame(self, fg_color="#080814", corner_radius=0, height=44)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar, text="✏  Manual Mode — Weenie Workbench",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            text_color=AMBER,
        ).pack(side="left", padx=14, pady=12)

        ctk.CTkButton(
            toolbar, text="📂  Open Output Folder", height=30, width=160,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=BLUE_MID, hover_color="#3a3a6a", text_color=TEXT_DIM,
            command=self._open_output_dir,
        ).pack(side="right", padx=8, pady=7)

        # Main content — the workbench lives here
        self._content = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0)
        self._content.pack(fill="both", expand=True)

        self._launch_webview()

    def _launch_webview(self):
        """Launch the workbench HTML in a pywebview window."""
        try:
            import webview
        except ImportError:
            self._show_fallback("pywebview not installed.\n\nRun: pip install pywebview\nthen restart ACEForge.")
            return

        web_dir = get_web_dir()
        html_path = web_dir / "workbench.html"

        if not html_path.exists():
            self._show_fallback(f"workbench.html not found at:\n{html_path}")
            return

        # Launch pywebview in a background thread
        threading.Thread(target=self._run_webview, args=(html_path,), daemon=True).start()
        self._webview_started = True

    def _run_webview(self, html_path: Path):
        import webview

        api = WorkbenchAPI(self.config)

        window = webview.create_window(
            title="ACEForge Workbench",
            url=html_path.as_uri(),
            js_api=api,
            width=1300,
            height=860,
            min_size=(1000, 700),
            background_color="#ede4ce",
        )
        webview.start(debug=False)

    def _show_fallback(self, message: str):
        """Show a friendly message if pywebview can't launch."""
        frame = ctk.CTkFrame(self._content, fg_color="#14142a", corner_radius=8)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text="⚠  Workbench Unavailable",
            font=ctk.CTkFont(family=FONT_MONO, size=16, weight="bold"),
            text_color=AMBER,
        ).pack(padx=30, pady=(24, 8))

        ctk.CTkLabel(
            frame, text=message,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            text_color=TEXT_DIM, justify="center",
        ).pack(padx=30, pady=(0, 16))

        ctk.CTkButton(
            frame, text="Open Workbench in Browser Instead",
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BLUE_MID, hover_color="#3a3a6a", height=36,
            command=self._open_in_browser,
        ).pack(padx=30, pady=(0, 24))

    def _open_in_browser(self):
        import webbrowser
        web_dir = get_web_dir()
        html_path = web_dir / "workbench.html"
        if html_path.exists():
            webbrowser.open(html_path.as_uri())
        else:
            messagebox.showerror("Not Found", f"workbench.html not found at:\n{html_path}")

    def _open_output_dir(self):
        path = self.config.output_dir or str(Path.home() / "Documents" / "ACEForge" / "output")
        Path(path).mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))


class WorkbenchAPI:
    """
    Python API exposed to the workbench HTML via pywebview's js_api.
    Methods here are callable from JavaScript as window.pywebview.api.method_name()
    """

    def __init__(self, config: Config):
        self.config = config

    def save_sql(self, sql_text: str, wcid: int, name: str) -> dict:
        """Save SQL text to the configured output directory as its own file."""
        try:
            output_dir = self.config.output_dir
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subfolder = Path(output_dir) / f"manual_{timestamp}"
            subfolder.mkdir(parents=True, exist_ok=True)

            safe_name = name.lower().replace(" ", "_").replace("'", "")[:40]
            filename = f"{wcid}_{safe_name}.sql"
            fpath = subfolder / filename
            fpath.write_text(sql_text, encoding="utf-8")

            return {"success": True, "path": str(fpath)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def forge(self, prompt: str, content_type: str) -> dict:
        """
        Pass an AI forge prompt back to the main app.
        The main app handles the API call.
        """
        return {"prompt": prompt, "content_type": content_type}

    def get_config(self) -> dict:
        """Return current server config to the workbench."""
        return {
            "server_name": self.config.server_name,
            "wcid_ranges": self.config.get_wcid_ranges(),
            "author": self.config.get("author", ""),
        }
