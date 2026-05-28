"""
ACEForge Emote Tab
Full row-by-row editor for weenie_properties_emote and weenie_properties_emote_action.
Emotes are listed in a collapsible accordion. Each emote expands to show its actions.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable
from .base_tab import BaseTab, FONT_MONO, BG_ROW, BG_ROW_ALT, BG_INPUT, BG_PANEL, TEXT_DIM, TEXT_MAIN, BLUE_MID, AMBER, RED, GREEN
from ..enums_data import EMOTE_CATEGORY, EMOTE_TYPE


CATEGORY_LIST = [f"{k} — {v}" for k, v in sorted(EMOTE_CATEGORY.items())]
TYPE_LIST     = [f"{k} — {v}" for k, v in sorted(EMOTE_TYPE.items())]


class EmoteActionRow(ctk.CTkFrame):
    """A single emote action row."""

    def __init__(self, parent, action: dict, order: int, on_delete: Callable, on_change: Callable):
        super().__init__(parent, fg_color=BG_ROW if order % 2 == 0 else BG_ROW_ALT, corner_radius=2)
        self.pack(fill="x", pady=1, padx=2)
        self.on_delete = on_delete
        self.on_change = on_change
        self.action = action
        self._build(action, order)

    def _build(self, action: dict, order: int):
        # Order label
        ctk.CTkLabel(self, text=f"[{order}]", width=30,
                     font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_DIM).pack(side="left", padx=2)

        # EmoteType dropdown
        type_val = action.get("type", 10)
        type_str = f"{type_val} — {EMOTE_TYPE.get(type_val, str(type_val))}"
        self.type_var = tk.StringVar(value=type_str)
        ctk.CTkOptionMenu(self, variable=self.type_var, values=TYPE_LIST, width=200, height=22,
                          font=ctk.CTkFont(family=FONT_MONO, size=10),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN, command=lambda _: self._sync(),
                          ).pack(side="left", padx=2, pady=2)

        # Delay
        self.delay_var = tk.StringVar(value=str(action.get("delay", 0)))
        self.delay_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="delay:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(4,1))
        ctk.CTkEntry(self, textvariable=self.delay_var, width=38, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # Message (most common field)
        self.message_var = tk.StringVar(value=action.get("message") or "")
        self.message_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="msg:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(2,1))
        ctk.CTkEntry(self, textvariable=self.message_var, width=200, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # WCID (for Give, TakeItems, etc.)
        self.wcid_var = tk.StringVar(value=str(action.get("weenie_Class_Id") or ""))
        self.wcid_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="wcid:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(2,1))
        ctk.CTkEntry(self, textvariable=self.wcid_var, width=70, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # Percent (for AwardLevelProportionalXP etc.)
        self.pct_var = tk.StringVar(value=str(action.get("percent") or ""))
        self.pct_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="pct:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(2,1))
        ctk.CTkEntry(self, textvariable=self.pct_var, width=50, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # hero_XP (AwardLuminance)
        self.hero_var = tk.StringVar(value=str(action.get("hero_X_P_64") or ""))
        self.hero_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="lum:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(2,1))
        ctk.CTkEntry(self, textvariable=self.hero_var, width=70, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # Stack size
        self.stack_var = tk.StringVar(value=str(action.get("stack_Size") or ""))
        self.stack_var.trace_add("write", lambda *_: self._sync())
        ctk.CTkLabel(self, text="stack:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(2,1))
        ctk.CTkEntry(self, textvariable=self.stack_var, width=40, height=22,
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,2))

        # Delete
        ctk.CTkButton(self, text="✕", width=22, height=22,
                      font=ctk.CTkFont(family=FONT_MONO, size=9),
                      fg_color="#2a1010", hover_color="#4a2020", text_color=RED,
                      command=self.on_delete,
                      ).pack(side="right", padx=3)

    def _sync(self):
        type_val = 10
        try:
            type_val = int(self.type_var.get().split(" — ")[0])
        except (ValueError, IndexError):
            pass

        self.action.update({
            "type": type_val,
            "delay": float(self.delay_var.get() or 0),
            "message": self.message_var.get() or None,
            "weenie_Class_Id": int(self.wcid_var.get()) if self.wcid_var.get().strip().isdigit() else None,
            "percent": float(self.pct_var.get()) if self.pct_var.get().strip() else None,
            "hero_X_P_64": int(self.hero_var.get()) if self.hero_var.get().strip().isdigit() else None,
            "stack_Size": int(self.stack_var.get()) if self.stack_var.get().strip().isdigit() else None,
        })
        self.on_change()

    def get_action(self) -> dict:
        self._sync()
        return self.action


class EmoteBlock(ctk.CTkFrame):
    """One emote (header + collapsible action list)."""

    def __init__(self, parent, emote: dict, index: int, on_delete: Callable, on_change: Callable):
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=5)
        self.pack(fill="x", pady=3, padx=4)
        self.emote = emote
        self.index = index
        self.on_delete_emote = on_delete
        self.on_change = on_change
        self._expanded = True
        self._action_rows: list[EmoteActionRow] = []
        self._build()

    def _build(self):
        # Header bar
        header = ctk.CTkFrame(self, fg_color="#14142a", corner_radius=4, height=34)
        header.pack(fill="x", padx=2, pady=2)
        header.pack_propagate(False)

        # Toggle expand
        self.toggle_btn = ctk.CTkButton(
            header, text="▼", width=28, height=28,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="transparent", hover_color=BLUE_MID, text_color=AMBER,
            command=self._toggle,
        )
        self.toggle_btn.pack(side="left", padx=4)

        # Category dropdown
        cat_val = self.emote.get("category", 7)
        cat_str = f"{cat_val} — {EMOTE_CATEGORY.get(cat_val, str(cat_val))}"
        self.cat_var = tk.StringVar(value=cat_str)
        ctk.CTkOptionMenu(header, variable=self.cat_var, values=CATEGORY_LIST,
                          width=220, height=26,
                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                          fg_color=BG_INPUT, button_color=BLUE_MID, button_hover_color="#3a3a7a",
                          text_color=TEXT_MAIN, command=lambda _: self._sync_header(),
                          ).pack(side="left", padx=4)

        # Probability
        self.prob_var = tk.StringVar(value=str(self.emote.get("probability", 1)))
        self.prob_var.trace_add("write", lambda *_: self._sync_header())
        ctk.CTkLabel(header, text="prob:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(8,2))
        ctk.CTkEntry(header, textvariable=self.prob_var, width=55, height=26,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # WCID filter (for Give category)
        self.wcid_var = tk.StringVar(value=str(self.emote.get("weenie_Class_Id") or ""))
        self.wcid_var.trace_add("write", lambda *_: self._sync_header())
        ctk.CTkLabel(header, text="wcid filter:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(4,2))
        ctk.CTkEntry(header, textvariable=self.wcid_var, width=80, height=26,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # Quest filter
        self.quest_var = tk.StringVar(value=self.emote.get("quest") or "")
        self.quest_var.trace_add("write", lambda *_: self._sync_header())
        ctk.CTkLabel(header, text="quest:", font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(4,2))
        ctk.CTkEntry(header, textvariable=self.quest_var, width=160, height=26,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     fg_color="#0e0e22", text_color=TEXT_MAIN, border_color=BLUE_MID, border_width=1,
                     ).pack(side="left", padx=(0,4))

        # Delete emote
        ctk.CTkButton(header, text="✕ Emote", width=70, height=26,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color="#3a1010", hover_color="#5a2020", text_color=RED,
                      command=self.on_delete_emote,
                      ).pack(side="right", padx=6)

        # Action list container
        self._action_container = ctk.CTkFrame(self, fg_color="#12122a", corner_radius=0)
        self._action_container.pack(fill="x", padx=2, pady=(0, 2))

        # Add action button
        action_btn_row = ctk.CTkFrame(self._action_container, fg_color="transparent")
        action_btn_row.pack(fill="x", padx=4, pady=4)
        ctk.CTkButton(action_btn_row, text="+ Add Action", width=100, height=24,
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      fg_color=BLUE_MID, hover_color="#3a3a7a", text_color=TEXT_MAIN,
                      command=self._add_action).pack(side="left")

        # Load existing actions
        for i, action in enumerate(self.emote.get("actions", [])):
            self._make_action_row(i, action)

    def _toggle(self):
        self._expanded = not self._expanded
        self.toggle_btn.configure(text="▼" if self._expanded else "▶")
        if self._expanded:
            self._action_container.pack(fill="x", padx=2, pady=(0, 2))
        else:
            self._action_container.pack_forget()

    def _make_action_row(self, order: int, action: dict):
        row = EmoteActionRow(
            self._action_container, action, order,
            on_delete=lambda r=None: self._del_action(row if r is None else r),
            on_change=self.on_change,
        )
        row.on_delete = lambda r=row: self._del_action(r)
        self._action_rows.append(row)
        return row

    def _add_action(self):
        action = {
            "type": 10, "delay": 0, "extent": 1,
            "motion": None, "message": None, "test_String": None,
            "min": None, "max": None, "min_64": None, "max_64": None,
            "min_Dbl": None, "max_Dbl": None, "stat": None, "display": None,
            "amount": None, "amount_64": None, "hero_X_P_64": None, "percent": None,
            "spell_Id": None, "wealth_Rating": None, "treasure_Class": None,
            "treasure_Type": None, "p_Script": None, "sound": None,
            "destination_Type": None, "weenie_Class_Id": None, "stack_Size": None,
            "palette": None, "shade": None, "try_To_Bond": None,
            "obj_Cell_Id": None, "origin_X": None, "origin_Y": None, "origin_Z": None,
            "angles_W": None, "angles_X": None, "angles_Y": None, "angles_Z": None,
        }
        self.emote.setdefault("actions", []).append(action)
        self._make_action_row(len(self._action_rows), action)
        self.on_change()

    def _del_action(self, row: EmoteActionRow):
        if row in self._action_rows:
            idx = self._action_rows.index(row)
            self._action_rows.remove(row)
            if "actions" in self.emote and idx < len(self.emote["actions"]):
                self.emote["actions"].pop(idx)
            row.destroy()
            self.on_change()

    def _sync_header(self):
        try:
            cat = int(self.cat_var.get().split(" — ")[0])
        except (ValueError, IndexError):
            cat = 7
        self.emote["category"] = cat
        self.emote["probability"] = float(self.prob_var.get() or 1)
        wcid_raw = self.wcid_var.get().strip()
        self.emote["weenie_Class_Id"] = int(wcid_raw) if wcid_raw.isdigit() else None
        self.emote["quest"] = self.quest_var.get().strip() or None
        self.on_change()


class EmoteTab(BaseTab):
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#0e0e1c", height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="EMOTES (weenie_properties_emote + emote_action)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=AMBER).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(header, text="+ Add Emote", width=110, height=30,
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      fg_color=BLUE_MID, hover_color="#3a3a7a",
                      command=self._add_emote).pack(side="right", padx=8)

        ctk.CTkLabel(self,
            text="  Each emote has a category, filters, and a list of actions. "
                 "Expand/collapse with ▼▶. Add actions inside each emote block.",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_DIM, anchor="w",
        ).pack(fill="x", padx=8, pady=2)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        self._emote_blocks: list[EmoteBlock] = []
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._emote_blocks.clear()
        for i, emote in enumerate(self.weenie.emotes):
            self._make_block(i, emote)

    def _make_block(self, idx: int, emote: dict):
        block = EmoteBlock(
            self._scroll, emote, idx,
            on_delete=lambda b=None: self._del_emote(block if b is None else b, emote),
            on_change=self._notify,
        )
        block.on_delete_emote = lambda b=block, e=emote: self._del_emote(b, e)
        self._emote_blocks.append(block)

    def _add_emote(self):
        emote = {
            "category": 7,  # Use
            "probability": 1.0,
            "weenie_Class_Id": None,
            "style": None,
            "substyle": None,
            "quest": None,
            "vendor_Type": None,
            "min_Health": None,
            "max_Health": None,
            "actions": [],
        }
        self.weenie.emotes.append(emote)
        self._make_block(len(self._emote_blocks), emote)
        self._notify()

    def _del_emote(self, block: EmoteBlock, emote: dict):
        if block in self._emote_blocks:
            self._emote_blocks.remove(block)
        if emote in self.weenie.emotes:
            self.weenie.emotes.remove(emote)
        block.destroy()
        self._notify()

    def refresh(self):
        self._load()
