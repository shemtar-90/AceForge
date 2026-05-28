"""
ACEForge AI Panel
The AI generation panel (streaming mode).
Extracted from app.py to be a swappable panel in the dual-mode app.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
from pathlib import Path
from datetime import datetime

from ..config import Config
from ..skill_loader import SkillLoader
from ..api_client import APIClient
from ..sql_parser import parse_and_save_files, estimate_file_count

BG_DEEP    = "#0a0a14"
BG_PANEL   = "#11111e"
BG_SIDEBAR = "#0d0d1c"
BG_INPUT   = "#14142a"
AMBER      = "#c8a96e"
AMBER_DARK = "#9a7a45"
AMBER_DIM  = "#5a4a28"
BLUE_DIM   = "#1e1e3a"
BLUE_MID   = "#2a2a4a"
TEXT_MAIN  = "#ddddef"
TEXT_DIM   = "#7777aa"
TEXT_CODE  = "#a8e8b0"
GREEN      = "#55bb77"
RED        = "#e05555"
FONT_MONO  = "Consolas"

CONTENT_TYPES = [
    ("⚔  Monster",   "monster"),
    ("💀  Boss",      "boss"),
    ("🧙  NPC",       "npc"),
    ("📦  Item",      "item"),
    ("🗡  Weapon",    "weapon"),
    ("🛡  Armor",     "armor"),
    ("📜  Quest",     "quest"),
    ("✨  General",   "general"),
]

CONTENT_PROMPTS = {
    "monster": "Describe the monster:\n\nExample: New Monster: Level 150 Tumerok in snowy areas, uses spear and shield, 20% chance to self-heal, drops a Seal of the Tumerok Capital quest item.",
    "boss":    "Describe the boss:\n\nExample: New Boss: Level 255 named Dericost Vault Guardian, melee + magic hybrid, always drops vault seal quest item.",
    "npc":     "Describe the NPC:\n\nExample: New NPC: Dereth Marketer. Waves on double-click. Accepts Seal of the Tumerok Capital (810060) and awards 15% XP.",
    "item":    "Describe the item:\n\nExample: New Item: Seal of the Tumerok Capital. Quest hand-in gem. Bonded, Attuned, no direct use.",
    "weapon":  "Describe the weapon:\n\nExample: New Weapon: Custom HeavyWeapons greatsword, high damage, lv150 wield requirement, fire damage type.",
    "armor":   "Describe the armor:\n\nExample: New Armor: Full set of Dericost tomb plate. High AL, cold resist bonus, dark palette.",
    "quest":   "Describe the quest:\n\nExample: New Quest: Level 250 undead-themed quest, at least 3 steps, NPC start/end, reward: 25% XP, 40,000 luminance, 5 trade notes.",
    "general": "Enter any content request:\n\nExample: Create a kill contract item for a Frost Golem kill task with a 20-hour daily cooldown.",
}


class AIPanel(ctk.CTkFrame):
    def __init__(self, parent, config: Config, skill_loader: SkillLoader, api_client: APIClient, **kwargs):
        super().__init__(parent, fg_color=BG_DEEP, corner_radius=0, **kwargs)
        self.config = config
        self.skill_loader = skill_loader
        self.api_client = api_client

        self._current_type = "monster"
        self._is_generating = False
        self._full_response = ""
        self._saved_files: list[str] = []

        self._build()

    def _build(self):
        # Sidebar — content type
        sidebar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, width=170, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="CONTENT TYPE",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER_DARK).pack(padx=12, pady=(16, 8), anchor="w")

        self._sidebar_buttons = {}
        for label, ctype in CONTENT_TYPES:
            btn = ctk.CTkButton(
                sidebar, text=label,
                font=ctk.CTkFont(family=FONT_MONO, size=13),
                height=38, anchor="w",
                fg_color="transparent", hover_color=BLUE_MID, text_color=TEXT_DIM,
                corner_radius=4,
                command=lambda t=ctype: self._apply_content_type(t),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._sidebar_buttons[ctype] = btn

        # WCID tracker
        ctk.CTkFrame(sidebar, fg_color=BLUE_DIM, height=1).pack(fill="x", padx=8, pady=12)
        ctk.CTkLabel(sidebar, text="WCID TRACKER",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER_DARK).pack(padx=12, pady=(4, 6), anchor="w")
        self.wcid_display = ctk.CTkTextbox(
            sidebar, font=ctk.CTkFont(family=FONT_MONO, size=10),
            fg_color=BG_INPUT, text_color=TEXT_DIM, state="disabled", height=200)
        self.wcid_display.pack(fill="x", padx=8, pady=(0, 8))
        self._refresh_wcid_display()

        # Center — prompt + output
        center = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0)
        center.pack(side="left", fill="both", expand=True, padx=1)

        # Prompt area
        prompt_frame = ctk.CTkFrame(center, fg_color=BG_INPUT, corner_radius=6)
        prompt_frame.pack(fill="x", padx=12, pady=(12, 6))

        self.prompt_label = ctk.CTkLabel(prompt_frame, text="",
                                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                                          text_color=TEXT_DIM, anchor="w", justify="left", wraplength=700)
        self.prompt_label.pack(anchor="w", padx=12, pady=(10, 6))

        self.prompt_input = ctk.CTkTextbox(
            prompt_frame, font=ctk.CTkFont(family=FONT_MONO, size=13),
            fg_color="#0e0e22", text_color=TEXT_MAIN, height=120,
            border_color=BLUE_MID, border_width=1, wrap="word")
        self.prompt_input.pack(fill="x", padx=12, pady=(0, 8))

        btn_row = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        self.generate_btn = ctk.CTkButton(
            btn_row, text="▶  Generate",
            font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
            height=40, fg_color=AMBER, hover_color="#e0c080", text_color="#0a0a14",
            command=self._start_generation)
        self.generate_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_row, text="⏹  Stop", width=90, height=40,
            font=ctk.CTkFont(family=FONT_MONO, size=13),
            fg_color=BLUE_MID, hover_color="#4a2222", text_color=TEXT_DIM,
            state="disabled", command=self._stop_generation)
        self.stop_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row, text="🗑  Clear", width=90, height=40,
            font=ctk.CTkFont(family=FONT_MONO, size=13),
            fg_color=BLUE_MID, hover_color="#3a3a6a", text_color=TEXT_DIM,
            command=self._clear_output).pack(side="left", padx=4)

        self.save_btn = ctk.CTkButton(
            btn_row, text="💾  Save Files", width=120, height=40,
            font=ctk.CTkFont(family=FONT_MONO, size=13),
            fg_color=GREEN, hover_color="#44cc66", text_color="#0a0a14",
            state="disabled", command=self._save_files)
        self.save_btn.pack(side="right")

        # Output
        out_hdr = ctk.CTkFrame(center, fg_color="transparent")
        out_hdr.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(out_hdr, text="OUTPUT",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER_DARK).pack(side="left")
        self.stream_indicator = ctk.CTkLabel(out_hdr, text="",
                                              font=ctk.CTkFont(family=FONT_MONO, size=11),
                                              text_color=AMBER)
        self.stream_indicator.pack(side="left", padx=8)

        self.output_box = ctk.CTkTextbox(
            center, font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BG_INPUT, text_color=TEXT_CODE, state="disabled",
            wrap="none", border_color=BLUE_DIM, border_width=1)
        self.output_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right file panel
        panel = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, width=220, corner_radius=0)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        ctk.CTkLabel(panel, text="GENERATED FILES",
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color=AMBER_DARK).pack(padx=12, pady=(16, 8), anchor="w")

        self.file_listbox = ctk.CTkScrollableFrame(panel, fg_color=BG_INPUT, corner_radius=4)
        self.file_listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        ctk.CTkLabel(self.file_listbox, text="No files yet.",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_DIM).pack(pady=20)

        ctk.CTkButton(panel, text="📂  Open Folder", height=34,
                      font=ctk.CTkFont(family=FONT_MONO, size=12),
                      fg_color=BLUE_MID, hover_color="#3a3a6a", text_color=TEXT_DIM,
                      command=self._open_output_dir).pack(fill="x", padx=8, pady=(0, 12))

        self._apply_content_type("monster")

    def _apply_content_type(self, ctype: str):
        self._current_type = ctype
        for t, btn in self._sidebar_buttons.items():
            btn.configure(fg_color=AMBER_DIM if t == ctype else "transparent",
                          text_color=AMBER if t == ctype else TEXT_DIM)
        self.prompt_label.configure(text=CONTENT_PROMPTS.get(ctype, ""))

    def _start_generation(self):
        if self._is_generating:
            return
        prompt = self.prompt_input.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("No Prompt", "Please enter a description.")
            return
        if not self.config.api_key:
            messagebox.showerror("No API Key", "Add your Anthropic API key in Settings.")
            return

        self._is_generating = True
        self._full_response = ""
        self.generate_btn.configure(state="disabled", fg_color=AMBER_DARK)
        self.stop_btn.configure(state="normal")
        self.save_btn.configure(state="disabled")
        self._clear_output(keep_prompt=True)
        self.stream_indicator.configure(text="● GENERATING...")
        self.api_client.update_credentials(self.config.api_key, self.config.model)

        system_prompt = self.skill_loader.build_system_prompt(
            content_type=self._current_type,
            server_name=self.config.server_name,
            wcid_ranges=self.config.get_wcid_ranges(),
            author=self.config.get("author", ""),
        )
        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system_prompt, prompt, self._on_chunk, self._on_done, self._on_error),
            daemon=True,
        ).start()

    def _stop_generation(self):
        self._is_generating = False
        self.stream_indicator.configure(text="⏹ STOPPED")
        self.stop_btn.configure(state="disabled")
        self.generate_btn.configure(state="normal", fg_color=AMBER)
        if self._full_response:
            self.save_btn.configure(state="normal")

    def _on_chunk(self, text: str):
        if not self._is_generating:
            return
        self._full_response += text
        self.after(0, self._append_output, text)

    def _on_done(self, full_text: str):
        self._is_generating = False
        self._full_response = full_text
        count = estimate_file_count(full_text)
        self.after(0, lambda: self._generation_complete(count))

    def _on_error(self, message: str):
        self._is_generating = False
        self.after(0, self._generation_error, message)

    def _generation_complete(self, file_count: int):
        self.generate_btn.configure(state="normal", fg_color=AMBER)
        self.stop_btn.configure(state="disabled")
        self.save_btn.configure(state="normal")
        self.stream_indicator.configure(text=f"✓ DONE  ({file_count} files)")
        self.output_box.see("1.0")

    def _generation_error(self, message: str):
        self.generate_btn.configure(state="normal", fg_color=AMBER)
        self.stop_btn.configure(state="disabled")
        self.stream_indicator.configure(text="✗ ERROR")
        self._append_output(f"\n\n[ERROR] {message}")

    def _append_output(self, text: str):
        self.output_box.configure(state="normal")
        self.output_box.insert("end", text)
        self.output_box.configure(state="disabled")
        self.output_box.see("end")

    def _clear_output(self, keep_prompt: bool = False):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")
        self._full_response = ""
        self.save_btn.configure(state="disabled")
        self.stream_indicator.configure(text="")

    def _save_files(self):
        if not self._full_response:
            return
        output_dir = self.config.output_dir or filedialog.askdirectory(title="Choose output folder")
        if not output_dir:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subfolder = f"{self._current_type}_{timestamp}"
        try:
            written = parse_and_save_files(self._full_response, output_dir, subfolder)
            self._update_file_list(written)
            self.save_btn.configure(text="✓  Saved!", fg_color=GREEN)
            self.after(3000, lambda: self.save_btn.configure(text="💾  Save Files"))
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _update_file_list(self, files: list[str]):
        for w in self.file_listbox.winfo_children():
            w.destroy()
        if not files:
            ctk.CTkLabel(self.file_listbox, text="No files yet.",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_DIM).pack(pady=20)
            return
        for fpath in files:
            fname = os.path.basename(fpath)
            row = ctk.CTkFrame(self.file_listbox, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"📄 {fname}",
                         font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MAIN,
                         anchor="w", wraplength=190, justify="left",
                         ).pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkButton(row, text="↗", width=24, height=20,
                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                          fg_color=BLUE_MID, hover_color="#3a3a6a",
                          command=lambda p=fpath: os.startfile(p),
                          ).pack(side="right", padx=2)

    def _open_output_dir(self):
        path = self.config.output_dir or str(Path.home() / "Documents" / "ACEForge" / "output")
        Path(path).mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_wcid_display(self):
        self.wcid_display.configure(state="normal")
        self.wcid_display.delete("1.0", "end")
        for key, info in self.config.get_wcid_ranges().items():
            label = info.get("label", key)
            nxt   = info.get("next", "?")
            short = label.replace("Custom ", "").replace(" Weapons", "")
            self.wcid_display.insert("end", f"{short[:16]:<16}  {nxt}\n")
        self.wcid_display.configure(state="disabled")

    def refresh_config(self):
        """Called when settings change."""
        self._refresh_wcid_display()
