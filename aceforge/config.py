"""
ACEForge Configuration Manager
Handles API key storage, server settings, and WCID range configuration.
Stored in %APPDATA%/ACEForge/config.json on Windows.
"""

import os
import json
from pathlib import Path
from typing import Optional


DEFAULT_WCID_RANGES = {
    "campaign_creatures":  {"start": 800000, "next": 800064, "label": "Campaign Creatures"},
    "custom_items":        {"start": 810000, "next": 810062, "label": "Custom Items"},
    "custom_portals":      {"start": 820000, "next": 820006, "label": "Custom Portals"},
    "structures":          {"start": 830000, "next": 830032, "label": "Structures"},
    "bosses":              {"start": 840000, "next": 840035, "label": "Bosses"},
    "custom_npcs":         {"start": 850000, "next": 850010, "label": "Custom NPCs"},
    "kill_contracts":      {"start": 860000, "next": 860018, "label": "Kill Contracts"},
    "custom_gear":         {"start": 870000, "next": 870025, "label": "Custom Gear"},
    "kill_tasks":          {"start": 1000000,"next": 1000025,"label": "Kill Tasks (KT Flags)"},
}

DEFAULT_CONFIG = {
    "api_key": "",
    "server_name": "Shattered Dawn",
    "author": "",
    "model": "claude-sonnet-4-20250514",
    "output_dir": str(Path.home() / "Documents" / "ACEForge" / "output"),
    "wcid_ranges": DEFAULT_WCID_RANGES,
    "theme": "dark",
    "last_content_type": "monster",
}


def get_config_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_dir = Path(appdata) / "ACEForge"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


class Config:
    def __init__(self):
        self._path = get_config_path()
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge any missing keys from defaults
                for key, val in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = val
                # Merge missing WCID range categories
                for key, val in DEFAULT_WCID_RANGES.items():
                    if key not in data.get("wcid_ranges", {}):
                        data.setdefault("wcid_ranges", {})[key] = val
                return data
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value

    def get_wcid_ranges(self) -> dict:
        return self._data.get("wcid_ranges", DEFAULT_WCID_RANGES)

    def set_wcid_next(self, category: str, next_val: int):
        self._data["wcid_ranges"][category]["next"] = next_val
        self.save()

    def get_next_wcid(self, category: str) -> int:
        return self._data["wcid_ranges"].get(category, {}).get("next", 0)

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._data["api_key"] = value

    @property
    def server_name(self) -> str:
        return self._data.get("server_name", "My Server")

    @server_name.setter
    def server_name(self, value: str):
        self._data["server_name"] = value

    @property
    def output_dir(self) -> str:
        return self._data.get("output_dir", str(Path.home() / "Documents" / "ACEForge" / "output"))

    @output_dir.setter
    def output_dir(self, value: str):
        self._data["output_dir"] = value

    @property
    def model(self) -> str:
        return self._data.get("model", "claude-sonnet-4-20250514")

    @model.setter
    def model(self, value: str):
        self._data["model"] = value
