"""
ACEForge Generic Property Tab
Reusable tab for weenie_properties_int, _bool, _float, _string, _d_i_d.
Renders a scrollable table of type→value rows with add/delete controls
and a type dropdown sourced from the relevant enum dictionary.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable
from .base_tab import BaseTab, TableRow, FONT_MONO, BG_ROW, BG_ROW_ALT, TEXT_DIM, TEXT_MAIN, BLUE_MID, AMBER, GREEN, RED, BG_INPUT


class PropRow(ctk.CTkFrame):
    """A single editable property row."""

    def __init__(self, parent, type_id: int, value, type_names: dict,
                 prop_type: str, on_delete: Callable, on_change: Callable,
                 row_index: int = 0):
        bg = BG_ROW if row_index % 2 == 0 else BG_ROW_ALT
        super().__init__(parent, fg_color=bg, corner_radius=3)
        self.pack(fill="x", padx=2, pady=1)

        self.type_id = type_id
        self.prop_type = prop_type
        self.on_delete = on_delete
        self.on_change = on_change
        self.type_names = type_names

        self._build(type_id, value)

    def _build(self, type_id: int, value):
        # Type ID dropdown
        type_list = [f"{k} — {v}" for k, v in sorted(self.type_names.items())]
        current = f"{type_id} — {self.type_names.get(type_id, f'type_{type_id}')}"
        self.type_var = tk.StringVar(value=current)
        dd = ctk.CTkOptionMenu(
            self, variable=self.type_var, values=type_list,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=24, width=280,
            fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
            text_color=TEXT_MAIN,
            command=self._on_type_change,
        )
        dd.pack(side="left", padx=(4, 2), pady=2)

        # Value widget — depends on prop_type
        if self.prop_type == "bool":
            self.value_var = tk.BooleanVar(value=bool(value))
            cb = ctk.CTkCheckBox(
                self, variable=self.value_var, text="",
                width=24, height=24,
                checkbox_width=18, checkbox_height=18,
                command=self._on_value_change,
            )
            cb.pack(side="left", padx=4, pady=2)
        else:
            str_val = str(value) if value is not None else ""
            self.value_var = tk.StringVar(value=str_val)
            self.value_var.trace_add("write", lambda *_: self._on_value_change())
            e = ctk.CTkEntry(
                self, textvariable=self.value_var,
                width=200, height=24,
                font=ctk.CTkFont(family=FONT_MONO, size=11),
                fg_color="#0e0e22", text_color=TEXT_MAIN,
                border_color=BLUE_MID, border_width=1,
            )
            e.pack(side="left", padx=4, pady=2)

        # Delete button
        ctk.CTkButton(
            self, text="✕", width=24, height=24,
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
            command=self.on_delete,
        ).pack(side="right", padx=4, pady=2)

    def get_type_id(self) -> int:
        try:
            return int(self.type_var.get().split(" — ")[0])
        except (ValueError, IndexError):
            return self.type_id

    def get_value(self):
        if self.prop_type == "bool":
            return self.value_var.get()
        raw = self.value_var.get().strip()
        if self.prop_type == "int":
            try:
                return int(raw)
            except ValueError:
                return 0
        if self.prop_type == "float":
            try:
                return float(raw)
            except ValueError:
                return 0.0
        return raw  # string / did

    def _on_type_change(self, _=None):
        self.type_id = self.get_type_id()
        self.on_change()

    def _on_value_change(self):
        self.on_change()


class GenericPropTab(BaseTab):
    """Tab for int, bool, float, string, or DID properties."""

    def __init__(self, parent, weenie_ref, on_change: Callable,
                 prop_type: str, prop_list_attr: str,
                 type_names: dict, tab_title: str, **kwargs):
        self.prop_type = prop_type
        self.prop_list_attr = prop_list_attr
        self.type_names = type_names
        self.tab_title = tab_title
        self._rows: list[PropRow] = []
        super().__init__(parent, weenie_ref, on_change, **kwargs)

    def _build(self):
        # Header with add button
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", corner_radius=0, height=44)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=self.tab_title.upper(),
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=AMBER,
        ).pack(side="left", padx=12, pady=12)

        ctk.CTkButton(
            header, text="+ Add Row", width=90, height=28,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=BLUE_MID, hover_color="#3a3a7a", text_color=TEXT_MAIN,
            command=self._add_row,
        ).pack(side="right", padx=8, pady=8)

        ctk.CTkButton(
            header, text="Sort by ID", width=80, height=28,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#1a1a2a", hover_color="#2a2a4a", text_color=TEXT_DIM,
            command=self._sort_rows,
        ).pack(side="right", padx=4, pady=8)

        # Column headers
        col_header = ctk.CTkFrame(self, fg_color="#14142a", corner_radius=0, height=24)
        col_header.pack(fill="x")
        col_header.pack_propagate(False)
        ctk.CTkLabel(col_header, text="  Property Type",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER, width=290, anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(col_header, text="Value",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=2)

        # Scrollable rows
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._load_from_model()

    def _load_from_model(self):
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._rows.clear()

        prop_list = getattr(self.weenie, self.prop_list_attr)
        for i, p in enumerate(sorted(prop_list, key=lambda x: x["type"])):
            self._create_row(p["type"], p["value"], i)

    def _create_row(self, type_id: int, value, row_index: int = 0):
        row = PropRow(
            self._scroll, type_id, value,
            self.type_names, self.prop_type,
            on_delete=lambda r=None: self._delete_row(row if r is None else r),
            on_change=self._sync_and_notify,
            row_index=row_index,
        )
        # Fix the lambda to capture the right row
        row.on_delete = lambda r=row: self._delete_row(r)
        self._rows.append(row)
        return row

    def _add_row(self):
        # Find a type ID not already used
        used = {r.get_type_id() for r in self._rows}
        default_id = next(
            (k for k in sorted(self.type_names.keys()) if k not in used),
            max(self.type_names.keys(), default=0) + 1
        )
        default_val = False if self.prop_type == "bool" else ("" if self.prop_type in ("string","did") else 0)
        self._create_row(default_id, default_val, len(self._rows))
        self._sync_and_notify()

    def _delete_row(self, row: PropRow):
        if row in self._rows:
            self._rows.remove(row)
            row.destroy()
            self._sync_and_notify()

    def _sort_rows(self):
        self._sync_to_model()
        getattr(self.weenie, self.prop_list_attr).sort(key=lambda x: x["type"])
        self._load_from_model()
        self._notify()

    def _sync_and_notify(self):
        self._sync_to_model()
        self._notify()

    def _sync_to_model(self):
        new_list = []
        seen = set()
        for row in self._rows:
            type_id = row.get_type_id()
            if type_id in seen:
                continue
            seen.add(type_id)
            new_list.append({"type": type_id, "value": row.get_value()})
        setattr(self.weenie, self.prop_list_attr, new_list)

    def refresh(self):
        self._load_from_model()
