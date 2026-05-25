"""
ACEForge Base Tab
Shared base class and UI helpers for all manual editor property tabs.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

# Colour palette (matches app.py)
BG_DEEP    = "#0a0a14"
BG_PANEL   = "#11111e"
BG_INPUT   = "#14142a"
BG_ROW     = "#16162a"
BG_ROW_ALT = "#1a1a30"
AMBER      = "#c8a96e"
AMBER_DARK = "#9a7a45"
BLUE_DIM   = "#1e1e3a"
BLUE_MID   = "#2a2a4a"
TEXT_MAIN  = "#ddddef"
TEXT_DIM   = "#7777aa"
TEXT_CODE  = "#a8e8b0"
GREEN      = "#55bb77"
RED        = "#e05555"
FONT_MONO  = "Consolas"


class BaseTab(ctk.CTkFrame):
    """Base class for all property tabs in the manual editor."""

    def __init__(self, parent, weenie_ref: "WeenieModel", on_change: Callable = None, **kwargs):
        super().__init__(parent, fg_color=BG_PANEL, corner_radius=0, **kwargs)
        self.weenie = weenie_ref
        self.on_change = on_change or (lambda: None)
        self._build()

    def _build(self):
        """Override in subclasses."""
        pass

    def refresh(self):
        """Called when the weenie model changes externally. Override to reload UI."""
        pass

    # ── Shared UI helpers ────────────────────────────────────────────────────

    def _section_header(self, parent, title: str):
        f = ctk.CTkFrame(parent, fg_color="#1a1a30", corner_radius=4, height=30)
        f.pack(fill="x", padx=4, pady=(8, 2))
        f.pack_propagate(False)
        ctk.CTkLabel(
            f, text=f"  {title.upper()}",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color=AMBER_DARK,
        ).pack(side="left", padx=6)
        return f

    def _add_btn(self, parent, text: str, command: Callable, color=BLUE_MID) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent, text=text, command=command,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=28, fg_color=color, hover_color="#3a3a7a",
            text_color=TEXT_MAIN,
        )

    def _del_btn(self, parent, command: Callable) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent, text="✕", command=command, width=28, height=26,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#3a1a1a", hover_color="#5a2222", text_color=RED,
        )

    def _entry(self, parent, width=100, **kwargs) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent, width=width, height=26,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BG_INPUT, text_color=TEXT_MAIN,
            border_color=BLUE_MID, border_width=1,
            **kwargs
        )

    def _label(self, parent, text: str, width: int = None, color=TEXT_DIM) -> ctk.CTkLabel:
        kwargs = {"width": width} if width else {}
        return ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=color,
            anchor="w",
            **kwargs
        )

    def _dropdown(self, parent, variable, values: list, width=160) -> ctk.CTkOptionMenu:
        return ctk.CTkOptionMenu(
            parent, variable=variable, values=values,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=26, width=width,
            fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
            text_color=TEXT_MAIN,
        )

    def _scrollable(self, parent) -> ctk.CTkScrollableFrame:
        return ctk.CTkScrollableFrame(
            parent, fg_color=BG_PANEL, scrollbar_button_color=BLUE_MID,
        )

    def _notify(self):
        """Call after any model change to trigger live SQL update."""
        self.on_change()


class TableRow(ctk.CTkFrame):
    """A single row in a property table — base for all row types."""

    def __init__(self, parent, on_delete: Callable = None, on_change: Callable = None):
        super().__init__(parent, fg_color=BG_ROW, corner_radius=3)
        self.on_delete = on_delete or (lambda: None)
        self.on_change = on_change or (lambda: None)

    def _del_btn(self) -> ctk.CTkButton:
        return ctk.CTkButton(
            self, text="✕", width=24, height=24,
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
            command=self.on_delete,
        )

    def _entry(self, width=80, **kw) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            self, width=width, height=24,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#0e0e22", text_color=TEXT_MAIN,
            border_color=BLUE_DIM, border_width=1,
            **kw
        )
