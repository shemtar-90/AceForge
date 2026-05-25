"""
ACEForge Settings Dialog
Handles API key, server configuration, WCID ranges, output directory.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable
from .config import Config


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config: Config, on_save: Callable = None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save

        self.title("ACEForge Settings")
        self.geometry("720x680")
        self.resizable(False, False)
        self.grab_set()  # Modal

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 360
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 340
        self.geometry(f"+{px}+{py}")

        self._build()

    def _build(self):
        # Title bar
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="⚙  Settings",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#c8a96e",
        ).pack(side="left", padx=20, pady=16)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="#12121f")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── API Configuration ──
        self._section(scroll, "API Configuration")

        self._label(scroll, "Anthropic API Key")
        self.api_key_var = tk.StringVar(value=self.config.api_key)
        api_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        api_frame.pack(fill="x", padx=20, pady=(0, 12))
        self.api_entry = ctk.CTkEntry(
            api_frame,
            textvariable=self.api_key_var,
            placeholder_text="sk-ant-...",
            show="•",
            font=ctk.CTkFont(family="Consolas", size=13),
            height=38,
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            api_frame,
            text="Show",
            width=60,
            height=38,
            fg_color="#2a2a4a",
            hover_color="#3a3a6a",
            command=self._toggle_key_visibility,
            font=ctk.CTkFont(family="Consolas", size=12),
        ).pack(side="left")

        self._label(scroll, "Model")
        self.model_var = tk.StringVar(value=self.config.model)
        ctk.CTkOptionMenu(
            scroll,
            variable=self.model_var,
            values=[
                "claude-sonnet-4-20250514",
                "claude-opus-4-20250514",
                "claude-haiku-4-5-20251001",
            ],
            font=ctk.CTkFont(family="Consolas", size=13),
            height=38,
            fg_color="#1e1e3a",
            button_color="#2a2a5a",
            button_hover_color="#3a3a7a",
        ).pack(fill="x", padx=20, pady=(0, 16))

        # ── Server Configuration ──
        self._section(scroll, "Server Configuration")

        self._label(scroll, "Server Name")
        self.server_name_var = tk.StringVar(value=self.config.server_name)
        ctk.CTkEntry(
            scroll,
            textvariable=self.server_name_var,
            placeholder_text="My Server",
            font=ctk.CTkFont(family="Consolas", size=13),
            height=38,
        ).pack(fill="x", padx=20, pady=(0, 12))

        self._label(scroll, "Author / Admin Name (optional)")
        self.author_var = tk.StringVar(value=self.config.get("author", ""))
        ctk.CTkEntry(
            scroll,
            textvariable=self.author_var,
            placeholder_text="Your name",
            font=ctk.CTkFont(family="Consolas", size=13),
            height=38,
        ).pack(fill="x", padx=20, pady=(0, 16))

        # ── Output Directory ──
        self._section(scroll, "Output Directory")
        self._label(scroll, "SQL files will be saved here")
        dir_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dir_frame.pack(fill="x", padx=20, pady=(0, 16))
        self.output_dir_var = tk.StringVar(value=self.config.output_dir)
        ctk.CTkEntry(
            dir_frame,
            textvariable=self.output_dir_var,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=38,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            dir_frame,
            text="Browse",
            width=80,
            height=38,
            fg_color="#2a2a4a",
            hover_color="#3a3a6a",
            command=self._browse_dir,
            font=ctk.CTkFont(family="Consolas", size=12),
        ).pack(side="left")

        # ── WCID Ranges ──
        self._section(scroll, "WCID Ranges")
        ctk.CTkLabel(
            scroll,
            text="Configure the starting WCID and next available WCID for each content category.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#8888aa",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.wcid_vars = {}
        wcid_ranges = self.config.get_wcid_ranges()

        # Header row
        hrow = ctk.CTkFrame(scroll, fg_color="#1e1e3a", corner_radius=4)
        hrow.pack(fill="x", padx=20, pady=(0, 2))
        for col, text, w in [("cat", "Category", 200), ("start", "Range Start", 130), ("next", "Next Available", 130)]:
            ctk.CTkLabel(
                hrow,
                text=text,
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                text_color="#c8a96e",
                width=w,
                anchor="w",
            ).pack(side="left", padx=8, pady=6)

        for key, info in wcid_ranges.items():
            row = ctk.CTkFrame(scroll, fg_color="#16162a", corner_radius=4)
            row.pack(fill="x", padx=20, pady=1)

            ctk.CTkLabel(
                row,
                text=info.get("label", key),
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color="#ccccdd",
                width=200,
                anchor="w",
            ).pack(side="left", padx=8, pady=6)

            start_var = tk.StringVar(value=str(info.get("start", 0)))
            next_var  = tk.StringVar(value=str(info.get("next", 0)))
            self.wcid_vars[key] = {"start": start_var, "next": next_var}

            for var, w in [(start_var, 120), (next_var, 120)]:
                ctk.CTkEntry(
                    row,
                    textvariable=var,
                    font=ctk.CTkFont(family="Consolas", size=12),
                    height=30,
                    width=w,
                ).pack(side="left", padx=8, pady=4)

        # Bottom padding
        ctk.CTkFrame(scroll, fg_color="transparent", height=20).pack()

        # Save / Cancel buttons
        btn_bar = ctk.CTkFrame(self, fg_color="#0e0e1c", corner_radius=0, height=60)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            width=100,
            height=38,
            fg_color="#2a2a4a",
            hover_color="#3a3a6a",
            font=ctk.CTkFont(family="Consolas", size=13),
            command=self.destroy,
        ).pack(side="right", padx=8, pady=11)

        ctk.CTkButton(
            btn_bar,
            text="Save Settings",
            width=140,
            height=38,
            fg_color="#c8a96e",
            hover_color="#e0c080",
            text_color="#0e0e1c",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=self._save,
        ).pack(side="right", padx=4, pady=11)

    def _section(self, parent, title: str):
        f = ctk.CTkFrame(parent, fg_color="#1a1a30", corner_radius=6, height=36)
        f.pack(fill="x", padx=20, pady=(16, 8))
        f.pack_propagate(False)
        ctk.CTkLabel(
            f,
            text=f"  {title.upper()}",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#c8a96e",
        ).pack(side="left", padx=8, pady=8)

    def _label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#aaaacc",
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(4, 4))

    def _toggle_key_visibility(self):
        current = self.api_entry.cget("show")
        self.api_entry.configure(show="" if current == "•" else "•")

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_dir_var.set(path)

    def _save(self):
        # Validate WCID fields are integers
        for key, vars_ in self.wcid_vars.items():
            for field, var in vars_.items():
                try:
                    int(var.get())
                except ValueError:
                    messagebox.showerror(
                        "Invalid WCID",
                        f"WCID range '{key}' {field} must be an integer.",
                        parent=self,
                    )
                    return

        # Save config
        self.config.api_key = self.api_key_var.get().strip()
        self.config.model = self.model_var.get()
        self.config.server_name = self.server_name_var.get().strip()
        self.config.set("author", self.author_var.get().strip())
        self.config.output_dir = self.output_dir_var.get().strip()

        # Save WCID ranges
        wcid_ranges = self.config.get_wcid_ranges()
        for key, vars_ in self.wcid_vars.items():
            wcid_ranges[key]["start"] = int(vars_["start"].get())
            wcid_ranges[key]["next"]  = int(vars_["next"].get())
        self.config.set("wcid_ranges", wcid_ranges)

        self.config.save()

        if self.on_save:
            self.on_save()

        self.destroy()
        messagebox.showinfo("Saved", "Settings saved successfully.")
