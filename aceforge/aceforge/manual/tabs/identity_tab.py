"""
ACEForge Identity Tab
Handles WCID, class_name, weenie type, and the top-level weenie row.
"""

import customtkinter as ctk
import tkinter as tk
from .base_tab import BaseTab, FONT_MONO, AMBER, TEXT_DIM, TEXT_MAIN, BG_INPUT, BLUE_MID
from ..enums_data import WEENIE_TYPES, make_dropdown_list, parse_dropdown_id


WEENIE_TYPE_LIST = [f"{k} — {v}" for k, v in sorted(WEENIE_TYPES.items())]


class IdentityTab(BaseTab):
    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self._section_header(scroll, "Weenie Identity")

        # WCID
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=3)
        self._label(row, "WCID (class_Id):", 160).pack(side="left")
        self._wcid_var = tk.StringVar(value=str(self.weenie.class_id))
        self._wcid_var.trace_add("write", self._on_wcid)
        e = self._entry(row, width=120)
        e.configure(textvariable=self._wcid_var)
        e.pack(side="left", padx=4)
        self._label(row, "Must be unique on your server.", color="#555577").pack(side="left", padx=8)

        # Class name
        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=3)
        self._label(row2, "class_Name:", 160).pack(side="left")
        self._cname_var = tk.StringVar(value=self.weenie.class_name)
        self._cname_var.trace_add("write", self._on_cname)
        e2 = self._entry(row2, width=240)
        e2.configure(textvariable=self._cname_var)
        e2.pack(side="left", padx=4)
        self._label(row2, "Lowercase, no spaces (e.g. tumerokguardian)", color="#555577").pack(side="left", padx=8)

        # Weenie type
        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", padx=8, pady=3)
        self._label(row3, "Weenie Type:", 160).pack(side="left")
        current_type = f"{self.weenie.weenie_type} — {WEENIE_TYPES.get(self.weenie.weenie_type,'?')}"
        self._type_var = tk.StringVar(value=current_type)
        dd = self._dropdown(row3, self._type_var, WEENIE_TYPE_LIST, width=280)
        dd.pack(side="left", padx=4)
        self._type_var.trace_add("write", self._on_type)

        # Auto class_name helper
        self._section_header(scroll, "Helper — Auto-Generate class_Name")
        hint = ctk.CTkFrame(scroll, fg_color="#0e0e1c", corner_radius=4)
        hint.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(
            hint,
            text="Press 'Auto' to generate a class_name from the Name string property.\n"
                 "Format: lowercase, spaces removed. Set the Name in the String Properties tab first.",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_DIM, justify="left", wraplength=600,
        ).pack(side="left", padx=10, pady=8)
        ctk.CTkButton(
            hint, text="Auto", width=60, height=30,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BLUE_MID, hover_color="#3a3a7a",
            command=self._auto_classname,
        ).pack(side="right", padx=10)

        # Info block
        self._section_header(scroll, "Notes")
        info = ctk.CTkLabel(
            scroll,
            text="• Weenie Type determines which fields are relevant (e.g. Creature vs Gem vs Caster).\n"
                 "• WCID must match your server's configured range for this content category.\n"
                 "• class_Name must be unique across all weenies in the database.",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_DIM, justify="left", wraplength=680, anchor="w",
        )
        info.pack(anchor="w", padx=12, pady=8)

    def _on_wcid(self, *_):
        try:
            self.weenie.class_id = int(self._wcid_var.get())
            self._notify()
        except ValueError:
            pass

    def _on_cname(self, *_):
        self.weenie.class_name = self._cname_var.get()
        self._notify()

    def _on_type(self, *_):
        val = parse_dropdown_id(self._type_var.get())
        if val is not None:
            self.weenie.weenie_type = val
            self._notify()

    def _auto_classname(self):
        name = self.weenie.get_string(1, "")
        if name:
            cn = name.lower().replace(" ", "").replace("'", "").replace("-", "")
            self.weenie.class_name = cn
            self._cname_var.set(cn)
            self._notify()

    def refresh(self):
        self._wcid_var.set(str(self.weenie.class_id))
        self._cname_var.set(self.weenie.class_name)
        current_type = f"{self.weenie.weenie_type} — {WEENIE_TYPES.get(self.weenie.weenie_type,'?')}"
        self._type_var.set(current_type)
