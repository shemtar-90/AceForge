"""
ACEForge Session Manager
Manages a multi-weenie editing session.
Holds a list of WeenieModel objects and handles saving them all to disk.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

from .weenie_model import WeenieModel
from .sql_builder import build_sql
from .templates import TEMPLATE_FUNCS, apply_creature_template, apply_generator_template


class Session:
    def __init__(self):
        self.weenies: list[WeenieModel] = []
        self.name: str = "Untitled Session"
        self._session_file: Optional[Path] = None

    def add_weenie(self, content_type: str = "creature", wcid: int = 0) -> WeenieModel:
        m = WeenieModel()
        m.class_id = wcid
        func = TEMPLATE_FUNCS.get(content_type)
        if func:
            func(m)
        self.weenies.append(m)
        return m

    def add_empty(self, wcid: int = 0) -> WeenieModel:
        m = WeenieModel()
        m.class_id = wcid
        self.weenies.append(m)
        return m

    def remove_weenie(self, index: int):
        if 0 <= index < len(self.weenies):
            self.weenies.pop(index)

    def move_up(self, index: int):
        if index > 0:
            self.weenies[index - 1], self.weenies[index] = \
                self.weenies[index], self.weenies[index - 1]

    def move_down(self, index: int):
        if index < len(self.weenies) - 1:
            self.weenies[index], self.weenies[index + 1] = \
                self.weenies[index + 1], self.weenies[index]

    def duplicate_weenie(self, index: int, new_wcid: int = 0) -> WeenieModel:
        if 0 <= index < len(self.weenies):
            original = self.weenies[index]
            new_m = WeenieModel.from_dict(original.to_dict())
            new_m.class_id = new_wcid
            self.weenies.insert(index + 1, new_m)
            return new_m
        raise IndexError(f"No weenie at index {index}")

    def save_sql_files(
        self,
        output_dir: str,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> list[str]:
        """
        Write each weenie as its own .sql file.
        Returns list of file paths written.
        on_progress(current, total, filename) called per file.
        """
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = output_path / f"session_{timestamp}"
        session_folder.mkdir(parents=True, exist_ok=True)

        written = []
        total = len(self.weenies)

        for i, weenie in enumerate(self.weenies):
            name = weenie.get_name()
            fname = _safe_filename(f"{weenie.class_id} {name}.sql")
            file_label = f"{weenie.class_id} {name}.sql"
            sql = build_sql(weenie, file_label=file_label)
            fpath = session_folder / fname
            fpath.write_text(sql, encoding="utf-8")
            written.append(str(fpath))
            if on_progress:
                on_progress(i + 1, total, fname)

        return written

    def save_session_json(self, path: str):
        """Save the session to a JSON file for later reopening."""
        data = {
            "name": self.name,
            "weenies": [w.to_dict() for w in self.weenies],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._session_file = Path(path)

    def load_session_json(self, path: str):
        """Load a previously saved session."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.name = data.get("name", "Loaded Session")
        self.weenies = [
            WeenieModel.from_dict(w) for w in data.get("weenies", [])
        ]
        self._session_file = Path(path)

    def get_preview_sql(self, index: int) -> str:
        """Get the SQL preview for a single weenie by index."""
        if 0 <= index < len(self.weenies):
            w = self.weenies[index]
            return build_sql(w, file_label=f"{w.class_id} {w.get_name()}.sql")
        return ""

    def get_all_sql(self) -> str:
        """Get all weenie SQL concatenated (for preview)."""
        parts = []
        for w in self.weenies:
            parts.append(build_sql(w, file_label=f"{w.class_id} {w.get_name()}.sql"))
        return "\n\n".join(parts)


def _safe_filename(name: str) -> str:
    illegal = r'\/:*?"<>|'
    for ch in illegal:
        name = name.replace(ch, "_")
    return name
