"""
ACEForge Attribute & Skill Tabs
Handles weenie_properties_attribute, attribute_2nd, and skill.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable
from .base_tab import BaseTab, FONT_MONO, BG_ROW, BG_ROW_ALT, BG_INPUT, TEXT_DIM, TEXT_MAIN, BLUE_MID, AMBER, RED
from ..enums_data import PROPERTY_ATTRIBUTE_NAMES, PROPERTY_ATTRIBUTE2ND_NAMES, SKILL_TYPES, SKILL_SAC


class AttributeTab(BaseTab):
    """Handles both attribute and attribute_2nd in one tab."""

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Attributes ──
        self._section_header(scroll, "Attributes (weenie_properties_attribute)")
        col_hdr = ctk.CTkFrame(scroll, fg_color="#14142a", height=22)
        col_hdr.pack(fill="x", padx=2)
        col_hdr.pack_propagate(False)
        for text, w in [("Attribute", 160), ("init_Level", 100), ("lvl_From_CP", 100), ("CP_Spent", 100)]:
            ctk.CTkLabel(col_hdr, text=text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=AMBER, width=w, anchor="w").pack(side="left", padx=4)

        self._attr_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._attr_frame.pack(fill="x", padx=2)
        self._attr_rows: list[dict] = []

        ctk.CTkButton(scroll, text="+ Add Attribute", height=26, width=130,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_attr).pack(anchor="w", padx=4, pady=4)

        # ── Vitals ──
        self._section_header(scroll, "Vitals (weenie_properties_attribute_2nd)")
        col_hdr2 = ctk.CTkFrame(scroll, fg_color="#14142a", height=22)
        col_hdr2.pack(fill="x", padx=2)
        col_hdr2.pack_propagate(False)
        for text, w in [("Vital", 160), ("init_Level", 100), ("current_Level", 120)]:
            ctk.CTkLabel(col_hdr2, text=text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=AMBER, width=w, anchor="w").pack(side="left", padx=4)

        self._vital_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._vital_frame.pack(fill="x", padx=2)
        self._vital_rows: list[dict] = []

        ctk.CTkButton(scroll, text="+ Add Vital", height=26, width=110,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_vital).pack(anchor="w", padx=4, pady=4)

        self._load()

    def _load(self):
        for w in self._attr_frame.winfo_children():
            w.destroy()
        self._attr_rows.clear()
        for i, p in enumerate(sorted(self.weenie.attributes, key=lambda x: x["type"])):
            self._make_attr_row(i, p)

        for w in self._vital_frame.winfo_children():
            w.destroy()
        self._vital_rows.clear()
        for i, p in enumerate(sorted(self.weenie.attribute2nd, key=lambda x: x["type"])):
            self._make_vital_row(i, p)

    def _make_attr_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._attr_frame, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1, padx=2)

        type_list = [f"{k} — {v}" for k, v in sorted(PROPERTY_ATTRIBUTE_NAMES.items())]
        type_var = tk.StringVar(value=f"{p['type']} — {PROPERTY_ATTRIBUTE_NAMES.get(p['type'],'?')}")
        init_var = tk.StringVar(value=str(p.get("init_Level", 0)))
        lvl_var  = tk.StringVar(value=str(p.get("level_From_C_P", 0)))
        cp_var   = tk.StringVar(value=str(p.get("c_P_Spent", 0)))

        entry_data = {"type_var": type_var, "init_var": init_var, "lvl_var": lvl_var, "cp_var": cp_var}
        self._attr_rows.append(entry_data)

        ctk.CTkOptionMenu(row, variable=type_var, values=type_list, width=160, height=24,
                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN,
                          command=lambda _: self._sync()).pack(side="left", padx=3, pady=2)
        for var in [init_var, lvl_var, cp_var]:
            var.trace_add("write", lambda *_: self._sync())
            ctk.CTkEntry(row, textvariable=var, width=90, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=3, pady=2)

        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda r=entry_data, w=row: self._del_attr(r, w),
                      ).pack(side="right", padx=3)

    def _make_vital_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._vital_frame, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1, padx=2)

        type_list = [f"{k} — {v}" for k, v in sorted(PROPERTY_ATTRIBUTE2ND_NAMES.items())]
        type_var    = tk.StringVar(value=f"{p['type']} — {PROPERTY_ATTRIBUTE2ND_NAMES.get(p['type'],'?')}")
        init_var    = tk.StringVar(value=str(p.get("init_Level", 0)))
        current_var = tk.StringVar(value=str(p.get("current_Level", 0)))

        entry_data = {"type_var": type_var, "init_var": init_var, "current_var": current_var}
        self._vital_rows.append(entry_data)

        ctk.CTkOptionMenu(row, variable=type_var, values=type_list, width=160, height=24,
                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN,
                          command=lambda _: self._sync()).pack(side="left", padx=3, pady=2)
        for var in [init_var, current_var]:
            var.trace_add("write", lambda *_: self._sync())
            ctk.CTkEntry(row, textvariable=var, width=110, height=24,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         fg_color="#0e0e22", text_color=TEXT_MAIN,
                         border_color=BLUE_MID, border_width=1,
                         ).pack(side="left", padx=3, pady=2)

        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda r=entry_data, w=row: self._del_vital(r, w),
                      ).pack(side="right", padx=3)

    def _add_attr(self):
        p = {"type": 1, "init_Level": 0, "level_From_C_P": 0, "c_P_Spent": 0}
        self._make_attr_row(len(self._attr_rows), p)
        self._sync()

    def _add_vital(self):
        p = {"type": 1, "init_Level": 0, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 0}
        self._make_vital_row(len(self._vital_rows), p)
        self._sync()

    def _del_attr(self, data: dict, widget):
        if data in self._attr_rows:
            self._attr_rows.remove(data)
        widget.destroy()
        self._sync()

    def _del_vital(self, data: dict, widget):
        if data in self._vital_rows:
            self._vital_rows.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        attrs = []
        for r in self._attr_rows:
            try:
                tid = int(r["type_var"].get().split(" — ")[0])
            except (ValueError, IndexError):
                continue
            attrs.append({
                "type": tid,
                "init_Level": int(r["init_var"].get() or 0),
                "level_From_C_P": int(r["lvl_var"].get() or 0),
                "c_P_Spent": int(r["cp_var"].get() or 0),
            })
        self.weenie.attributes = attrs

        vitals = []
        for r in self._vital_rows:
            try:
                tid = int(r["type_var"].get().split(" — ")[0])
            except (ValueError, IndexError):
                continue
            init = int(r["init_var"].get() or 0)
            vitals.append({
                "type": tid,
                "init_Level": init,
                "level_From_C_P": 0,
                "c_P_Spent": 0,
                "current_Level": int(r["current_var"].get() or 0),
            })
        self.weenie.attribute2nd = vitals
        self._notify()

    def refresh(self):
        self._load()


class SkillTab(BaseTab):
    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._section_header(scroll, "Skills (weenie_properties_skill)")
        ctk.CTkLabel(scroll, text="⚠  Never use retired skill types 1–5 or 8–13.",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#cc7744").pack(anchor="w", padx=8, pady=(4, 2))

        col_hdr = ctk.CTkFrame(scroll, fg_color="#14142a", height=22)
        col_hdr.pack(fill="x", padx=2)
        col_hdr.pack_propagate(False)
        for text, w in [("Skill", 220), ("SAC", 130), ("init_Level", 100)]:
            ctk.CTkLabel(col_hdr, text=text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=AMBER, width=w, anchor="w").pack(side="left", padx=4)

        self._skill_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._skill_frame.pack(fill="x", padx=2)
        self._skill_rows: list[dict] = []

        ctk.CTkButton(scroll, text="+ Add Skill", height=26, width=100,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_skill).pack(anchor="w", padx=4, pady=4)

        self._load()

    def _load(self):
        for w in self._skill_frame.winfo_children():
            w.destroy()
        self._skill_rows.clear()
        for i, p in enumerate(sorted(self.weenie.skills, key=lambda x: x["type"])):
            self._make_row(i, p)

    def _make_row(self, idx: int, p: dict):
        bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
        row = ctk.CTkFrame(self._skill_frame, fg_color=bg, corner_radius=3)
        row.pack(fill="x", pady=1, padx=2)

        skill_list = [f"{k} — {v}" for k, v in sorted(SKILL_TYPES.items())]
        sac_list   = [f"{k} — {v}" for k, v in sorted(SKILL_SAC.items())]

        type_var = tk.StringVar(value=f"{p['type']} — {SKILL_TYPES.get(p['type'],'?')}")
        sac_var  = tk.StringVar(value=f"{p.get('s_a_c',2)} — {SKILL_SAC.get(p.get('s_a_c',2),'Trained')}")
        init_var = tk.StringVar(value=str(p.get("init_Level", 0)))

        entry_data = {"type_var": type_var, "sac_var": sac_var, "init_var": init_var}
        self._skill_rows.append(entry_data)

        for var, values, w in [(type_var, skill_list, 220), (sac_var, sac_list, 130)]:
            ctk.CTkOptionMenu(row, variable=var, values=values, width=w, height=24,
                              font=ctk.CTkFont(family=FONT_MONO, size=11),
                              fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                              text_color=TEXT_MAIN,
                              command=lambda _: self._sync()).pack(side="left", padx=3, pady=2)

        init_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkEntry(row, textvariable=init_var, width=90, height=24,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     fg_color="#0e0e22", text_color=TEXT_MAIN,
                     border_color=BLUE_MID, border_width=1).pack(side="left", padx=3)

        ctk.CTkButton(row, text="✕", width=24, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=lambda r=entry_data, w=row: self._del_skill(r, w),
                      ).pack(side="right", padx=3)

    def _add_skill(self):
        p = {"type": 6, "level_From_P_P": 0, "s_a_c": 2, "p_p": 0,
             "init_Level": 0, "resistance_At_Last_Check": 0, "last_Used_Time": 0}
        self._make_row(len(self._skill_rows), p)
        self._sync()

    def _del_skill(self, data, widget):
        if data in self._skill_rows:
            self._skill_rows.remove(data)
        widget.destroy()
        self._sync()

    def _sync(self):
        skills = []
        for r in self._skill_rows:
            try:
                tid = int(r["type_var"].get().split(" — ")[0])
                sac = int(r["sac_var"].get().split(" — ")[0])
            except (ValueError, IndexError):
                continue
            skills.append({
                "type": tid,
                "level_From_P_P": 0, "s_a_c": sac, "p_p": 0,
                "init_Level": int(r["init_var"].get() or 0),
                "resistance_At_Last_Check": 0, "last_Used_Time": 0,
            })
        self.weenie.skills = skills
        self._notify()

    def refresh(self):
        self._load()
