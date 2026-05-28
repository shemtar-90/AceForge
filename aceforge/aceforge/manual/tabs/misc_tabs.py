"""
ACEForge — Body Part, Spell Book, Create List, Generator, Event Filter Tabs
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable
from .base_tab import BaseTab, FONT_MONO, BG_ROW, BG_ROW_ALT, BG_INPUT, TEXT_DIM, TEXT_MAIN, BLUE_MID, AMBER, RED
from ..enums_data import BODY_PART_KEYS, DAMAGE_TYPES, DESTINATION_TYPE, REGEN_LOCATION_TYPE, REGEN_TYPE_WHEN


# ─────────────────────────────────────────────────────────────────────────────
# Body Part Tab
# ─────────────────────────────────────────────────────────────────────────────

BODY_PART_COLS = [
    ("key",           60, "Body Part"),
    ("d_Type",        70, "dmg_Type"),
    ("d_Val",         55, "d_Val"),
    ("d_Var",         55, "d_Var"),
    ("base_Armor",    70, "base_AL"),
    ("armor_Vs_Slash",55, "Slash"),
    ("armor_Vs_Pierce",55,"Pierce"),
    ("armor_Vs_Bludgeon",55,"Bludge"),
    ("armor_Vs_Cold", 55, "Cold"),
    ("armor_Vs_Fire", 55, "Fire"),
    ("armor_Vs_Acid", 55, "Acid"),
    ("armor_Vs_Electric",55,"Elec"),
    ("armor_Vs_Nether",55,"Nether"),
    ("b_h",           40, "b_h"),
]

FLOAT_COLS = [
    ("h_l_f","h_l_f"), ("m_l_f","m_l_f"), ("l_l_f","l_l_f"),
    ("h_r_f","h_r_f"), ("m_r_f","m_r_f"), ("l_r_f","l_r_f"),
    ("h_l_b","h_l_b"), ("m_l_b","m_l_b"), ("l_l_b","l_l_b"),
    ("h_r_b","h_r_b"), ("m_r_b","m_r_b"), ("l_r_b","l_r_b"),
]


class BodyPartTab(BaseTab):
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", corner_radius=0, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="BODY PARTS (weenie_properties_body_part)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(header, text="+ Add Row", width=90, height=28,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_row).pack(side="right", padx=8)

        ctk.CTkLabel(self, text="  27 columns per row. Float hit-location columns scroll right.",
                     font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_DIM,
                     anchor="w").pack(fill="x", padx=8, pady=2)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        self._rows_data: list[dict] = []
        self._row_frames: list[ctk.CTkFrame] = []
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows_data.clear()
        self._row_frames.clear()
        for i, p in enumerate(sorted(self.weenie.body_parts, key=lambda x: x["key"])):
            self._make_row(i, p)

    def _make_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        outer = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=3)
        outer.pack(fill="x", pady=1, padx=2)

        row_vars: dict[str, tk.StringVar] = {}

        # Part name dropdown
        part_list = [f"{k} — {v}" for k, v in sorted(BODY_PART_KEYS.items())]
        key_var = tk.StringVar(value=f"{p['key']} — {BODY_PART_KEYS.get(p['key'],'?')}")
        row_vars["key"] = key_var

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=2, pady=2)

        ctk.CTkOptionMenu(inner, variable=key_var, values=part_list, width=140, height=22,
                          font=ctk.CTkFont(family=FONT_MONO, size=10),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN, command=lambda _: self._sync(),
                          ).pack(side="left", padx=2)

        # dmg_type dropdown
        dmg_list = [f"{k} — {v}" for k, v in sorted(DAMAGE_TYPES.items())]
        dtype_var = tk.StringVar(value=f"{p.get('d_Type',4)} — {DAMAGE_TYPES.get(p.get('d_Type',4),'?')}")
        row_vars["d_Type"] = dtype_var
        ctk.CTkOptionMenu(inner, variable=dtype_var, values=dmg_list, width=120, height=22,
                          font=ctk.CTkFont(family=FONT_MONO, size=10),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN, command=lambda _: self._sync(),
                          ).pack(side="left", padx=2)

        # Numeric fields
        int_fields = ["d_Val", "base_Armor",
                      "armor_Vs_Slash","armor_Vs_Pierce","armor_Vs_Bludgeon",
                      "armor_Vs_Cold","armor_Vs_Fire","armor_Vs_Acid",
                      "armor_Vs_Electric","armor_Vs_Nether","b_h"]
        float_fields = ["d_Var"] + [f for f, _ in FLOAT_COLS]

        for field in int_fields + float_fields:
            var = tk.StringVar(value=str(p.get(field, 0)))
            row_vars[field] = var
            var.trace_add("write", lambda *_: self._sync())
            w = 48 if field in float_fields else 52
            ctk.CTkEntry(inner, textvariable=var, width=w, height=22,
                         font=ctk.CTkFont(family=FONT_MONO, size=9),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=1)

        ctk.CTkButton(inner, text="✕", width=22, height=22,
                      font=ctk.CTkFont(family=FONT_MONO, size=9),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda r=row_vars, w=outer: self._del_row(r, w),
                      ).pack(side="right", padx=2)

        self._rows_data.append(row_vars)
        self._row_frames.append(outer)

    def _add_row(self):
        next_key = len(self._rows_data)
        p = {
            "key": next_key, "d_Type": 4, "d_Val": 0, "d_Var": 0.0,
            "base_Armor": 100,
            "armor_Vs_Slash": 100, "armor_Vs_Pierce": 100, "armor_Vs_Bludgeon": 100,
            "armor_Vs_Cold": 100, "armor_Vs_Fire": 100, "armor_Vs_Acid": 100,
            "armor_Vs_Electric": 100, "armor_Vs_Nether": 0, "b_h": 1,
            "h_l_f": 0.0, "m_l_f": 0.0, "l_l_f": 0.0,
            "h_r_f": 0.0, "m_r_f": 0.0, "l_r_f": 0.0,
            "h_l_b": 0.0, "m_l_b": 0.0, "l_l_b": 0.0,
            "h_r_b": 0.0, "m_r_b": 0.0, "l_r_b": 0.0,
        }
        self._make_row(len(self._rows_data), p)
        self._sync()

    def _del_row(self, data: dict, widget):
        if data in self._rows_data:
            self._rows_data.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        parts = []
        for r in self._rows_data:
            try:
                key = int(r["key"].get().split(" — ")[0])
                d_type = int(r["d_Type"].get().split(" — ")[0])
            except (ValueError, IndexError):
                continue
            p = {
                "key": key, "d_Type": d_type,
                "d_Val": int(r["d_Val"].get() or 0),
                "d_Var": float(r["d_Var"].get() or 0),
                "base_Armor": int(r["base_Armor"].get() or 0),
                "armor_Vs_Slash":    int(r["armor_Vs_Slash"].get() or 0),
                "armor_Vs_Pierce":   int(r["armor_Vs_Pierce"].get() or 0),
                "armor_Vs_Bludgeon": int(r["armor_Vs_Bludgeon"].get() or 0),
                "armor_Vs_Cold":     int(r["armor_Vs_Cold"].get() or 0),
                "armor_Vs_Fire":     int(r["armor_Vs_Fire"].get() or 0),
                "armor_Vs_Acid":     int(r["armor_Vs_Acid"].get() or 0),
                "armor_Vs_Electric": int(r["armor_Vs_Electric"].get() or 0),
                "armor_Vs_Nether":   int(r["armor_Vs_Nether"].get() or 0),
                "b_h": int(r["b_h"].get() or 1),
            }
            for field, _ in FLOAT_COLS:
                p[field] = float(r[field].get() or 0.0)
            parts.append(p)
        self.weenie.body_parts = parts
        self._notify()

    def refresh(self):
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Spell Book Tab
# ─────────────────────────────────────────────────────────────────────────────

class SpellBookTab(BaseTab):
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="SPELL BOOK (weenie_properties_spell_book)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(header, text="+ Add Spell", width=90, height=28,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_spell).pack(side="right", padx=8)

        hint = ctk.CTkLabel(self,
            text="  Probability: <=2.0 → actual% = value/100  |  >2.0 → actual% = value-2.0   (e.g. 2.20 = 20%, 1.04 = 1.04%)",
            font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_DIM, anchor="w")
        hint.pack(fill="x", padx=8, pady=2)

        col_hdr = ctk.CTkFrame(self, fg_color="#14142a", height=22)
        col_hdr.pack(fill="x", padx=2)
        col_hdr.pack_propagate(False)
        for text, w in [("Spell ID", 100), ("Probability", 120), ("Spell Name (reference)", 300)]:
            ctk.CTkLabel(col_hdr, text=text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=AMBER, width=w, anchor="w").pack(side="left", padx=4)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._rows: list[dict] = []
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        for i, p in enumerate(sorted(self.weenie.spell_book, key=lambda x: x.get("probability", 0))):
            self._make_row(i, p)

    def _make_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1, padx=2)

        spell_var = tk.StringVar(value=str(p.get("spell", 0)))
        prob_var  = tk.StringVar(value=str(p.get("probability", 1.04)))
        name_var  = tk.StringVar(value=p.get("name", ""))  # optional label

        data = {"spell_var": spell_var, "prob_var": prob_var, "name_var": name_var}
        self._rows.append(data)

        for var, w in [(spell_var, 90), (prob_var, 110), (name_var, 280)]:
            var.trace_add("write", lambda *_: self._sync())
            ctk.CTkEntry(row, textvariable=var, width=w, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=3, pady=2)

        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda d=data, w=row: self._del_row(d, w),
                      ).pack(side="right", padx=3)

    def _add_spell(self):
        p = {"spell": 1788, "probability": 1.04, "name": "Eye of the Storm"}
        self._make_row(len(self._rows), p)
        self._sync()

    def _del_row(self, data: dict, widget):
        if data in self._rows:
            self._rows.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        spells = []
        for r in self._rows:
            try:
                spells.append({
                    "spell": int(r["spell_var"].get() or 0),
                    "probability": float(r["prob_var"].get() or 1.04),
                })
            except ValueError:
                pass
        self.weenie.spell_book = spells
        self._notify()

    def refresh(self):
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Create List Tab
# ─────────────────────────────────────────────────────────────────────────────

class CreateListTab(BaseTab):
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="CREATE LIST (weenie_properties_create_list)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(header, text="+ Add Entry", width=100, height=28,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_row).pack(side="right", padx=8)

        col_hdr = ctk.CTkFrame(self, fg_color="#14142a", height=22)
        col_hdr.pack(fill="x", padx=2)
        col_hdr.pack_propagate(False)
        for text, w in [("Destination", 160), ("WCID", 90), ("Stack", 60), ("Palette", 60), ("Shade", 60), ("TryBond", 60)]:
            ctk.CTkLabel(col_hdr, text=text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=AMBER, width=w, anchor="w").pack(side="left", padx=4)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._rows: list[dict] = []
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        for i, p in enumerate(self.weenie.create_list):
            self._make_row(i, p)

    def _make_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1, padx=2)

        dest_list = [f"{k} — {v}" for k, v in sorted(DESTINATION_TYPE.items())]
        dest_val  = p.get("destination_Type", 9)
        dest_var  = tk.StringVar(value=f"{dest_val} — {DESTINATION_TYPE.get(dest_val,'?')}")
        wcid_var  = tk.StringVar(value=str(p.get("weenie_Class_Id", 0)))
        stack_var = tk.StringVar(value=str(p.get("stack_Size", 1)))
        pal_var   = tk.StringVar(value=str(p.get("palette", 0)))
        shade_var = tk.StringVar(value=str(p.get("shade", 1.0)))
        bond_var  = tk.BooleanVar(value=bool(p.get("try_To_Bond", False)))

        data = {"dest_var": dest_var, "wcid_var": wcid_var, "stack_var": stack_var,
                "pal_var": pal_var, "shade_var": shade_var, "bond_var": bond_var}
        self._rows.append(data)

        ctk.CTkOptionMenu(row, variable=dest_var, values=dest_list, width=155, height=24,
                          font=ctk.CTkFont(family=FONT_MONO, size=10),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN, command=lambda _: self._sync(),
                          ).pack(side="left", padx=2, pady=2)

        for var, w in [(wcid_var, 80), (stack_var, 50), (pal_var, 50), (shade_var, 50)]:
            var.trace_add("write", lambda *_: self._sync())
            ctk.CTkEntry(row, textvariable=var, width=w, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=2)

        ctk.CTkCheckBox(row, variable=bond_var, text="", width=24, height=24,
                        checkbox_width=18, checkbox_height=18,
                        command=self._sync).pack(side="left", padx=2)

        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda d=data, w=row: self._del_row(d, w),
                      ).pack(side="right", padx=3)

    def _add_row(self):
        p = {"destination_Type": 9, "weenie_Class_Id": 0, "stack_Size": 1,
             "palette": 0, "shade": 1.0, "try_To_Bond": False}
        self._make_row(len(self._rows), p)
        self._sync()

    def _del_row(self, data: dict, widget):
        if data in self._rows:
            self._rows.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        items = []
        for r in self._rows:
            try:
                dest = int(r["dest_var"].get().split(" — ")[0])
            except (ValueError, IndexError):
                dest = 9
            items.append({
                "destination_Type": dest,
                "weenie_Class_Id": int(r["wcid_var"].get() or 0),
                "stack_Size": int(r["stack_var"].get() or 1),
                "palette": int(r["pal_var"].get() or 0),
                "shade": float(r["shade_var"].get() or 1.0),
                "try_To_Bond": r["bond_var"].get(),
            })
        self.weenie.create_list = items
        self._notify()

    def refresh(self):
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Generator Tab
# ─────────────────────────────────────────────────────────────────────────────

class GeneratorTab(BaseTab):
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="GENERATOR (weenie_properties_generator)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(header, text="+ Add Entry", width=100, height=28,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_row).pack(side="right", padx=8)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._rows: list[dict] = []
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        for i, p in enumerate(self.weenie.generator):
            self._make_row(i, p)

    def _make_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        outer = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=3)
        outer.pack(fill="x", pady=1, padx=2)

        fields_row1 = ctk.CTkFrame(outer, fg_color="transparent")
        fields_row1.pack(fill="x", padx=4, pady=(4, 0))
        fields_row2 = ctk.CTkFrame(outer, fg_color="transparent")
        fields_row2.pack(fill="x", padx=4, pady=(0, 4))

        vars_dict = {}

        simple_fields = [
            ("probability", "Prob", 60, "-1"),
            ("weenie_Class_Id", "Spawn WCID", 90, "0"),
            ("delay", "Delay (s)", 75, "1800"),
            ("init_Create", "Init", 45, "1"),
            ("max_Create", "Max", 45, "1"),
        ]
        for field, label, w, default in simple_fields:
            ctk.CTkLabel(fields_row1, text=label, font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color=TEXT_DIM).pack(side="left", padx=(6,1))
            var = tk.StringVar(value=str(p.get(field, default)))
            var.trace_add("write", lambda *_: self._sync())
            vars_dict[field] = var
            ctk.CTkEntry(fields_row1, textvariable=var, width=w, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=(0,4))

        # When/Where dropdowns
        when_list  = [f"{k} — {v}" for k, v in sorted(REGEN_TYPE_WHEN.items())]
        where_list = [f"{k} — {v}" for k, v in sorted(REGEN_LOCATION_TYPE.items())]

        when_val  = p.get("when_Create", 1)
        where_val = p.get("where_Create", 4)
        when_var  = tk.StringVar(value=f"{when_val} — {REGEN_TYPE_WHEN.get(when_val,'?')}")
        where_var = tk.StringVar(value=f"{where_val} — {REGEN_LOCATION_TYPE.get(where_val,'?')}")
        vars_dict["when_Create"]  = when_var
        vars_dict["where_Create"] = where_var

        for label, var, values in [("When", when_var, when_list), ("Where", where_var, where_list)]:
            ctk.CTkLabel(fields_row2, text=label, font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color=TEXT_DIM).pack(side="left", padx=(6,1))
            ctk.CTkOptionMenu(fields_row2, variable=var, values=values, width=140, height=24,
                              font=ctk.CTkFont(family=FONT_MONO, size=10),
                              fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                              text_color=TEXT_MAIN, command=lambda _: self._sync(),
                              ).pack(side="left", padx=(0,6))

        # Angle/origin fields (simplified)
        angle_fields = [
            ("angles_W","W",45,"1.0"),("angles_X","X",45,"0.0"),
            ("angles_Y","Y",45,"0.0"),("angles_Z","Z",45,"0.0"),
        ]
        for field, label, w, default in angle_fields:
            ctk.CTkLabel(fields_row2, text=label, font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color=TEXT_DIM).pack(side="left", padx=(4,1))
            var = tk.StringVar(value=str(p.get(field, default)))
            var.trace_add("write", lambda *_: self._sync())
            vars_dict[field] = var
            ctk.CTkEntry(fields_row2, textvariable=var, width=w, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=(0,2))

        ctk.CTkButton(fields_row1, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda d=vars_dict, w=outer: self._del_row(d, w),
                      ).pack(side="right", padx=4)

        self._rows.append(vars_dict)

    def _add_row(self):
        p = {
            "probability": -1, "weenie_Class_Id": 0, "delay": 1800,
            "init_Create": 1, "max_Create": 1, "when_Create": 1, "where_Create": 4,
            "stack_Size": -1, "palette_Id": 0, "shade": 0.0, "obj_Cell_Id": 0,
            "origin_X": 0.0, "origin_Y": 0.0, "origin_Z": 0.0,
            "angles_W": 1.0, "angles_X": 0.0, "angles_Y": 0.0, "angles_Z": 0.0,
        }
        self._make_row(len(self._rows), p)
        self._sync()

    def _del_row(self, data: dict, widget):
        if data in self._rows:
            self._rows.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        gens = []
        for r in self._rows:
            try:
                when  = int(r["when_Create"].get().split(" — ")[0])
                where = int(r["where_Create"].get().split(" — ")[0])
            except (ValueError, IndexError):
                when, where = 1, 4
            gens.append({
                "probability":     float(r["probability"].get() or -1),
                "weenie_Class_Id": int(r["weenie_Class_Id"].get() or 0),
                "delay":           int(r["delay"].get() or 1800),
                "init_Create":     int(r["init_Create"].get() or 1),
                "max_Create":      int(r["max_Create"].get() or 1),
                "when_Create": when, "where_Create": where,
                "stack_Size": -1, "palette_Id": 0, "shade": 0.0, "obj_Cell_Id": 0,
                "origin_X": 0.0, "origin_Y": 0.0, "origin_Z": 0.0,
                "angles_W": float(r.get("angles_W", tk.StringVar(value="1.0")).get() or 1.0),
                "angles_X": float(r.get("angles_X", tk.StringVar(value="0.0")).get() or 0.0),
                "angles_Y": float(r.get("angles_Y", tk.StringVar(value="0.0")).get() or 0.0),
                "angles_Z": float(r.get("angles_Z", tk.StringVar(value="0.0")).get() or 0.0),
            })
        self.weenie.generator = gens
        self._notify()

    def refresh(self):
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Event Filter Tab
# ─────────────────────────────────────────────────────────────────────────────

class EventFilterTab(BaseTab):
    EVENT_NAMES = {94: "ATTACK_NOTIFICATION_EVENT", 414: "PLAYER_DEATH_EVENT (items/NPCs only)"}

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._section_header(scroll, "Event Filter (weenie_properties_event_filter)")

        ctk.CTkLabel(scroll,
            text="⚠  Never add event 414 (PLAYER_DEATH_EVENT) to monsters/creatures.\n"
                 "   Event 414 is valid only on items, NPCs, and objects.",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color="#cc7744", justify="left", anchor="w",
        ).pack(anchor="w", padx=8, pady=4)

        self._ef_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._ef_frame.pack(fill="x", padx=8)
        self._ef_vars: list[dict] = []

        ctk.CTkButton(scroll, text="+ Add Event", width=100, height=28,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_event).pack(anchor="w", padx=8, pady=4)

        self._load()

    def _load(self):
        for w in self._ef_frame.winfo_children():
            w.destroy()
        self._ef_vars.clear()
        for i, ev in enumerate(self.weenie.event_filters):
            self._make_row(i, ev)

    def _make_row(self, idx: int, event_id: int):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._ef_frame, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1)

        ev_var = tk.StringVar(value=str(event_id))
        ev_var.trace_add("write", lambda *_: self._sync())
        data = {"ev_var": ev_var}
        self._ef_vars.append(data)

        ctk.CTkLabel(row, text="Event ID:", font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color=TEXT_DIM).pack(side="left", padx=8, pady=4)
        ctk.CTkEntry(row, textvariable=ev_var, width=80, height=24,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     fg_color="#0e0e22", text_color=TEXT_MAIN,
                     border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=4)
        name = self.EVENT_NAMES.get(event_id, "")
        ctk.CTkLabel(row, text=name, font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color=TEXT_DIM).pack(side="left", padx=8)
        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda d=data, w=row: self._del_event(d, w),
                      ).pack(side="right", padx=6)

    def _add_event(self):
        self._make_row(len(self._ef_vars), 94)
        self._sync()

    def _del_event(self, data: dict, widget):
        if data in self._ef_vars:
            self._ef_vars.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        events = []
        for r in self._ef_vars:
            try:
                events.append(int(r["ev_var"].get()))
            except ValueError:
                pass
        self.weenie.event_filters = events
        self._notify()

    def refresh(self):
        self._load()
