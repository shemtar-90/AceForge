"""
ACEForge Manual Editor Panel
The main panel shown in Manual mode.
Left: weenie session list. Center: tab editor. Right: live SQL preview.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
from pathlib import Path

from ..config import Config
from .session import Session
from .weenie_model import WeenieModel
from .sql_builder import build_sql
from .enums_data import PROPERTY_INT_NAMES, PROPERTY_BOOL_NAMES, PROPERTY_FLOAT_NAMES, PROPERTY_STRING_NAMES, PROPERTY_DID_NAMES
from .tabs.identity_tab import IdentityTab
from .tabs.generic_prop_tab import GenericPropTab
from .tabs.attribute_tab import AttributeTab, SkillTab
from .tabs.misc_tabs import BodyPartTab, SpellBookTab, CreateListTab, GeneratorTab, EventFilterTab
from .tabs.emote_tab import EmoteTab

BG_DEEP    = "#0a0a14"
BG_PANEL   = "#11111e"
BG_SIDEBAR = "#0d0d1c"
BG_INPUT   = "#14142a"
AMBER      = "#c8a96e"
AMBER_DARK = "#9a7a45"
BLUE_MID   = "#2a2a4a"
BLUE_DIM   = "#1e1e3a"
TEXT_MAIN  = "#ddddef"
TEXT_DIM   = "#7777aa"
TEXT_CODE  = "#a8e8b0"
GREEN      = "#55bb77"
RED        = "#e05555"
FONT_MONO  = "Consolas"

CONTENT_TYPES = [
    ("⚔  Creature",   "creature"),
    ("💀  Boss",       "boss"),
    ("🧙  NPC",        "npc"),
    ("📦  Item",       "item"),
    ("🗡  Weapon",     "weapon"),
    ("🛡  Armor",      "armor"),
    ("⚙  Generator",  "generator"),
]

TABS = [
    ("Identity",     "identity"),
    ("Int",          "int"),
    ("Bool",         "bool"),
    ("Float",        "float"),
    ("String",       "string"),
    ("DID",          "did"),
    ("Attributes",   "attributes"),
    ("Skills",       "skills"),
    ("Body Parts",   "body_parts"),
    ("Spells",       "spells"),
    ("Emotes",       "emotes"),
    ("Create List",  "create_list"),
    ("Generator",    "generator"),
    ("Events",       "events"),
]


class ManualPanel(ctk.CTkFrame):
    def __init__(self, parent, config: Config, **kwargs):
        super().__init__(parent, fg_color=BG_DEEP, corner_radius=0, **kwargs)
        self.config = config
        self.session = Session()
        self._active_weenie_idx: int = -1
        self._active_tab: str = "identity"
        self._tab_widgets: dict[str, ctk.CTkFrame] = {}
        self._current_tab_widget = None
        self._build()

    def _build(self):
        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color="#080814", corner_radius=0, height=44)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        for label, ctype in CONTENT_TYPES:
            ctk.CTkButton(
                toolbar, text=label, height=30,
                font=ctk.CTkFont(family=FONT_MONO, size=11),
                fg_color=BLUE_DIM, hover_color=BLUE_MID, text_color=TEXT_DIM,
                command=lambda t=ctype: self._add_weenie(t),
            ).pack(side="left", padx=3, pady=7)

        ctk.CTkButton(
            toolbar, text="💾 Save All SQL", height=30, width=130,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=GREEN, hover_color="#44cc66", text_color="#0a0a14",
            command=self._save_all,
        ).pack(side="right", padx=6, pady=7)

        ctk.CTkButton(
            toolbar, text="📋 Copy SQL", height=30, width=100,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=BLUE_MID, hover_color="#3a3a7a", text_color=TEXT_DIM,
            command=self._copy_sql,
        ).pack(side="right", padx=3, pady=7)

        ctk.CTkButton(
            toolbar, text="🗑 Remove", height=30, width=90,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
            command=self._remove_active,
        ).pack(side="right", padx=3, pady=7)

        ctk.CTkButton(
            toolbar, text="📂 Load Session", height=30, width=120,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=BLUE_DIM, hover_color=BLUE_MID, text_color=TEXT_DIM,
            command=self._load_session,
        ).pack(side="right", padx=3, pady=7)

        ctk.CTkButton(
            toolbar, text="💾 Save Session", height=30, width=120,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=BLUE_DIM, hover_color=BLUE_MID, text_color=TEXT_DIM,
            command=self._save_session,
        ).pack(side="right", padx=3, pady=7)

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color=BG_DEEP, corner_radius=0)
        body.pack(fill="both", expand=True)

        # Left: weenie list
        self._weenie_list_panel = ctk.CTkFrame(body, fg_color=BG_SIDEBAR, width=190, corner_radius=0)
        self._weenie_list_panel.pack(side="left", fill="y")
        self._weenie_list_panel.pack_propagate(False)
        self._build_weenie_list()

        # Center: tabs + editor
        center = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=0)
        center.pack(side="left", fill="both", expand=True)

        # Tab strip
        self._tab_strip = ctk.CTkFrame(center, fg_color="#080814", height=34, corner_radius=0)
        self._tab_strip.pack(fill="x")
        self._tab_strip.pack_propagate(False)
        self._tab_buttons: dict[str, ctk.CTkButton] = {}
        for label, key in TABS:
            btn = ctk.CTkButton(
                self._tab_strip, text=label, height=28,
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                fg_color="transparent", hover_color=BLUE_MID, text_color=TEXT_DIM,
                corner_radius=3,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", padx=2, pady=3)
            self._tab_buttons[key] = btn

        # Editor area
        self._editor_area = ctk.CTkFrame(center, fg_color=BG_PANEL, corner_radius=0)
        self._editor_area.pack(fill="both", expand=True)

        # Right: SQL preview
        preview = ctk.CTkFrame(body, fg_color=BG_SIDEBAR, width=360, corner_radius=0)
        preview.pack(side="right", fill="y")
        preview.pack_propagate(False)

        ctk.CTkLabel(preview, text="SQL PREVIEW",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER_DARK).pack(anchor="w", padx=8, pady=(8, 2))

        self._sql_preview = ctk.CTkTextbox(
            preview,
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            fg_color=BG_INPUT, text_color=TEXT_CODE,
            state="disabled", wrap="none",
        )
        self._sql_preview.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Placeholder message
        self._show_placeholder()

    def _build_weenie_list(self):
        for w in self._weenie_list_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._weenie_list_panel, text="SESSION WEENIES",
                     font=ctk.CTkFont(family=FONT_MONO, size=9, weight="bold"),
                     text_color=AMBER_DARK).pack(anchor="w", padx=8, pady=(10, 4))

        self._weenie_scroll = ctk.CTkScrollableFrame(self._weenie_list_panel, fg_color="transparent")
        self._weenie_scroll.pack(fill="both", expand=True, padx=4)

        for i, weenie in enumerate(self.session.weenies):
            name = weenie.get_name()
            wcid = weenie.class_id
            is_active = (i == self._active_weenie_idx)
            btn = ctk.CTkButton(
                self._weenie_scroll,
                text=f"[{wcid}]\n{name[:18]}",
                height=44, anchor="w",
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                fg_color=AMBER_DARK if is_active else BLUE_DIM,
                hover_color=BLUE_MID,
                text_color=BG_DEEP if is_active else TEXT_DIM,
                corner_radius=4,
                command=lambda idx=i: self._select_weenie(idx),
            )
            btn.pack(fill="x", pady=2)

        if not self.session.weenies:
            ctk.CTkLabel(self._weenie_scroll,
                         text="No weenies yet.\nUse the toolbar\nto add content.",
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color=TEXT_DIM, justify="center",
                         ).pack(pady=20)

    def _add_weenie(self, content_type: str):
        wcid = self.config.get_next_wcid(self._type_to_category(content_type))
        weenie = self.session.add_weenie(content_type, wcid)
        weenie.class_name = f"new{content_type}{wcid}"
        self._active_weenie_idx = len(self.session.weenies) - 1
        self._build_weenie_list()
        self._load_editor()

    def _type_to_category(self, ctype: str) -> str:
        mapping = {
            "creature": "campaign_creatures",
            "boss": "bosses",
            "npc": "custom_npcs",
            "item": "custom_items",
            "weapon": "custom_gear",
            "armor": "custom_gear",
            "generator": "campaign_creatures",
        }
        return mapping.get(ctype, "custom_items")

    def _select_weenie(self, idx: int):
        self._active_weenie_idx = idx
        self._build_weenie_list()
        self._load_editor()

    def _remove_active(self):
        if self._active_weenie_idx < 0:
            return
        name = self.session.weenies[self._active_weenie_idx].get_name()
        if not messagebox.askyesno("Remove Weenie", f"Remove '{name}' from the session?"):
            return
        self.session.remove_weenie(self._active_weenie_idx)
        self._active_weenie_idx = max(0, self._active_weenie_idx - 1) if self.session.weenies else -1
        self._build_weenie_list()
        if self._active_weenie_idx >= 0:
            self._load_editor()
        else:
            self._show_placeholder()

    def _load_editor(self):
        if self._active_weenie_idx < 0 or not self.session.weenies:
            self._show_placeholder()
            return
        weenie = self.session.weenies[self._active_weenie_idx]
        self._build_tabs(weenie)
        self._switch_tab(self._active_tab)
        self._update_sql_preview(weenie)

    def _build_tabs(self, weenie: WeenieModel):
        self._tab_widgets.clear()
        if self._current_tab_widget:
            self._current_tab_widget.pack_forget()

        on_change = lambda: self._on_model_change(weenie)

        self._tab_widgets["identity"] = IdentityTab(self._editor_area, weenie, on_change)
        self._tab_widgets["int"]      = GenericPropTab(self._editor_area, weenie, on_change,
            "int", "int_props", PROPERTY_INT_NAMES, "Int Properties")
        self._tab_widgets["bool"]     = GenericPropTab(self._editor_area, weenie, on_change,
            "bool", "bool_props", PROPERTY_BOOL_NAMES, "Bool Properties")
        self._tab_widgets["float"]    = GenericPropTab(self._editor_area, weenie, on_change,
            "float", "float_props", PROPERTY_FLOAT_NAMES, "Float Properties")
        self._tab_widgets["string"]   = GenericPropTab(self._editor_area, weenie, on_change,
            "string", "string_props", PROPERTY_STRING_NAMES, "String Properties")
        self._tab_widgets["did"]      = GenericPropTab(self._editor_area, weenie, on_change,
            "did", "did_props", PROPERTY_DID_NAMES, "DID Properties")
        self._tab_widgets["attributes"] = AttributeTab(self._editor_area, weenie, on_change)
        self._tab_widgets["skills"]   = SkillTab(self._editor_area, weenie, on_change)
        self._tab_widgets["body_parts"] = BodyPartTab(self._editor_area, weenie, on_change)
        self._tab_widgets["spells"]   = SpellBookTab(self._editor_area, weenie, on_change)
        self._tab_widgets["emotes"]   = EmoteTab(self._editor_area, weenie, on_change)
        self._tab_widgets["create_list"] = CreateListTab(self._editor_area, weenie, on_change)
        self._tab_widgets["generator"] = GeneratorTab(self._editor_area, weenie, on_change)
        self._tab_widgets["events"]   = EventFilterTab(self._editor_area, weenie, on_change)

    def _switch_tab(self, key: str):
        self._active_tab = key
        if self._current_tab_widget:
            self._current_tab_widget.pack_forget()

        for k, btn in self._tab_buttons.items():
            if k == key:
                btn.configure(fg_color=AMBER_DARK, text_color=BG_DEEP)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_DIM)

        widget = self._tab_widgets.get(key)
        if widget:
            widget.pack(fill="both", expand=True)
            self._current_tab_widget = widget

    def _on_model_change(self, weenie: WeenieModel):
        self._update_sql_preview(weenie)
        self._build_weenie_list()

    def _update_sql_preview(self, weenie: WeenieModel):
        sql = build_sql(weenie, file_label=f"{weenie.class_id} {weenie.get_name()}.sql")
        self._sql_preview.configure(state="normal")
        self._sql_preview.delete("1.0", "end")
        self._sql_preview.insert("1.0", sql)
        self._sql_preview.configure(state="disabled")

    def _show_placeholder(self):
        if self._current_tab_widget:
            self._current_tab_widget.pack_forget()
            self._current_tab_widget = None

        self._sql_preview.configure(state="normal")
        self._sql_preview.delete("1.0", "end")
        self._sql_preview.configure(state="disabled")

    def _copy_sql(self):
        if self._active_weenie_idx < 0:
            return
        sql = self.session.get_all_sql()
        self.clipboard_clear()
        self.clipboard_append(sql)
        messagebox.showinfo("Copied", "All session SQL copied to clipboard.")

    def _save_all(self):
        output_dir = self.config.output_dir
        if not output_dir:
            output_dir = filedialog.askdirectory(title="Choose output folder")
            if not output_dir:
                return

        written = self.session.save_sql_files(output_dir)
        if written:
            messagebox.showinfo("Saved", f"Saved {len(written)} SQL file(s) to:\n{os.path.dirname(written[0])}")

    def _save_session(self):
        path = filedialog.asksaveasfilename(
            title="Save Session",
            defaultextension=".json",
            filetypes=[("ACEForge Session", "*.json")],
        )
        if path:
            self.session.save_session_json(path)
            messagebox.showinfo("Saved", f"Session saved to {path}")

    def _load_session(self):
        path = filedialog.askopenfilename(
            title="Load Session",
            filetypes=[("ACEForge Session", "*.json")],
        )
        if path:
            self.session.load_session_json(path)
            self._active_weenie_idx = 0 if self.session.weenies else -1
            self._build_weenie_list()
            if self._active_weenie_idx >= 0:
                self._load_editor()
