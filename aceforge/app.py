"""
ACEForge — Main Application Window
Dual-mode: Manual Editor | AI Generator
Mode switch in the top bar. Each mode is a swappable panel.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from .config import Config
from .skill_loader import SkillLoader
from .api_client import APIClient
from .settings_dialog import SettingsDialog
from .manual.editor import ManualPanel
from .ai.ai_panel import AIPanel

APP_VERSION = "1.0.0"

BG_DEEP   = "#0a0a14"
BG_TOP    = "#080814"
AMBER     = "#c8a96e"
AMBER_DK  = "#9a7a45"
BLUE_MID  = "#2a2a4a"
BLUE_DIM  = "#1e1e3a"
TEXT_MAIN = "#ddddef"
TEXT_DIM  = "#7777aa"
GREEN     = "#55bb77"
FONT_MONO = "Consolas"


class ACEForgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"ACEForge v{APP_VERSION} — ACEmulator Content Generator")
        self.geometry("1340x860")
        self.minsize(1100, 720)
        self.configure(fg_color=BG_DEEP)

        self.config = Config()
        self.skill_loader = SkillLoader()
        self.api_client = APIClient(self.config.api_key, self.config.model)

        self._mode = "manual"           # "manual" | "ai"
        self._manual_panel = None
        self._ai_panel     = None

        self._build_topbar()
        self._build_body()
        self._build_statusbar()

        # Start in manual mode
        self._switch_mode("manual")

        # API key nag if missing (AI mode only relevant then)
        if not self.config.api_key:
            self.after(600, self._nag_api_key)

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=BG_TOP, corner_radius=0, height=52)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo
        ctk.CTkLabel(
            bar, text="⚡ ACEForge",
            font=ctk.CTkFont(family=FONT_MONO, size=20, weight="bold"),
            text_color=AMBER,
        ).pack(side="left", padx=18, pady=14)

        ctk.CTkLabel(
            bar, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_DIM,
        ).pack(side="left")

        # Server name
        self._server_label = ctk.CTkLabel(
            bar, text=f"  ◆  {self.config.server_name}",
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            text_color=TEXT_DIM,
        )
        self._server_label.pack(side="left", padx=16)

        # Right-side controls
        ctk.CTkButton(
            bar, text="⚙  Settings", width=100, height=34,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BLUE_MID, hover_color="#3a3a6a",
            command=self._open_settings,
        ).pack(side="right", padx=8, pady=9)

        # Mode toggle — Manual | AI
        toggle_frame = ctk.CTkFrame(bar, fg_color=BLUE_DIM, corner_radius=8)
        toggle_frame.pack(side="right", padx=12, pady=10)

        self._manual_btn = ctk.CTkButton(
            toggle_frame, text="✏  Manual", width=110, height=32,
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color=AMBER, hover_color="#e0c080", text_color=BG_DEEP,
            corner_radius=6,
            command=lambda: self._switch_mode("manual"),
        )
        self._manual_btn.pack(side="left", padx=3, pady=3)

        self._ai_btn = ctk.CTkButton(
            toggle_frame, text="✨  AI Mode", width=110, height=32,
            font=ctk.CTkFont(family=FONT_MONO, size=13),
            fg_color="transparent", hover_color=BLUE_MID, text_color=TEXT_DIM,
            corner_radius=6,
            command=lambda: self._switch_mode("ai"),
        )
        self._ai_btn.pack(side="left", padx=3, pady=3)

    # ── Body ──────────────────────────────────────────────────────────────────

    def _build_body(self):
        self._body = ctk.CTkFrame(self, fg_color=BG_DEEP, corner_radius=0)
        self._body.pack(fill="both", expand=True)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=BG_TOP, corner_radius=0, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            bar, text="Manual Mode — No API key required.",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_DIM, anchor="w",
        )
        self._status_label.pack(side="left", padx=12, pady=4)

        self._mode_badge = ctk.CTkLabel(
            bar, text="● MANUAL",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=AMBER, anchor="e",
        )
        self._mode_badge.pack(side="right", padx=12, pady=4)

    # ── Mode switching ────────────────────────────────────────────────────────

    def _switch_mode(self, mode: str):
        if mode == self._mode and (self._manual_panel or self._ai_panel):
            return  # Already in this mode

        self._mode = mode

        # Hide both panels
        if self._manual_panel:
            self._manual_panel.pack_forget()
        if self._ai_panel:
            self._ai_panel.pack_forget()

        if mode == "manual":
            # Build manual panel on first access
            if self._manual_panel is None:
                self._manual_panel = ManualPanel(self._body, self.config)
            self._manual_panel.pack(fill="both", expand=True)

            # Toggle button styles
            self._manual_btn.configure(
                fg_color=AMBER, text_color=BG_DEEP,
                font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            )
            self._ai_btn.configure(
                fg_color="transparent", text_color=TEXT_DIM,
                font=ctk.CTkFont(family=FONT_MONO, size=13),
            )
            self._status_label.configure(text="Manual Mode — No API key required.")
            self._mode_badge.configure(text="● MANUAL", text_color=AMBER)

        else:  # AI mode
            if not self.config.api_key:
                result = messagebox.askyesno(
                    "API Key Required",
                    "AI Mode requires an Anthropic API key.\n\nOpen Settings to add your key now?",
                )
                if result:
                    self._open_settings()
                # Don't block — let them into AI mode even without a key
                # (they'll get an error when they try to generate)

            if self._ai_panel is None:
                self._ai_panel = AIPanel(
                    self._body, self.config, self.skill_loader, self.api_client
                )
            self._ai_panel.pack(fill="both", expand=True)

            self._ai_btn.configure(
                fg_color=AMBER, text_color=BG_DEEP,
                font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            )
            self._manual_btn.configure(
                fg_color="transparent", text_color=TEXT_DIM,
                font=ctk.CTkFont(family=FONT_MONO, size=13),
            )
            key_status = "API key configured." if self.config.api_key else "⚠ No API key — add one in Settings."
            self._status_label.configure(text=f"AI Mode — {key_status}")
            self._mode_badge.configure(text="● AI", text_color=GREEN)

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self):
        SettingsDialog(self, self.config, on_save=self._on_settings_saved)

    def _on_settings_saved(self):
        self.api_client.update_credentials(self.config.api_key, self.config.model)
        self._server_label.configure(text=f"  ◆  {self.config.server_name}")
        if self._ai_panel:
            self._ai_panel.refresh_config()
        key_status = "API key configured." if self.config.api_key else "⚠ No API key — add one in Settings."
        if self._mode == "ai":
            self._status_label.configure(text=f"AI Mode — {key_status}")

    def _nag_api_key(self):
        # Only nag if they're already in AI mode or explicitly need it
        # Don't interrupt manual mode with API key nagging
        pass
