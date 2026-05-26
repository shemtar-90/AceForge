"""
ACEForge Configuration Manager
Handles API credentials, server settings, and WCID range configuration.
Stored in %APPDATA%/ACEForge/config.json on Windows.
"""

import os
import json
from pathlib import Path


DEFAULT_WCID_RANGES = {
    "campaign_creatures": {"start": 800000, "next": 800064, "label": "Campaign Creatures"},
    "custom_items":       {"start": 810000, "next": 810062, "label": "Custom Items"},
    "custom_portals":     {"start": 820000, "next": 820006, "label": "Custom Portals"},
    "structures":         {"start": 830000, "next": 830032, "label": "Structures"},
    "bosses":             {"start": 840000, "next": 840035, "label": "Bosses"},
    "custom_npcs":        {"start": 850000, "next": 850010, "label": "Custom NPCs"},
    "kill_contracts":     {"start": 860000, "next": 860018, "label": "Kill Contracts"},
    "custom_gear":        {"start": 870000, "next": 870025, "label": "Custom Gear"},
    "kill_tasks":         {"start": 1000000,"next": 1000025,"label": "Kill Tasks (KT Flags)"},
}

DEFAULT_CONFIG = {
    # Provider: "anthropic" | "openai" | "compatible"
    "provider":    "anthropic",
    "api_key":     "",
    "model":       "claude-sonnet-4-20250514",
    "base_url":    "",          # only used for "compatible" provider
    "server_name": "Shattered Dawn",
    "author":      "",
    "output_dir":  str(Path.home() / "Documents" / "ACEForge" / "output"),
    "wcid_ranges": DEFAULT_WCID_RANGES,
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
                # Merge missing keys from defaults
                for key, val in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = val
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

    # ── Typed accessors ───────────────────────────────────────────────────────

    @property
    def provider(self) -> str:
        return self._data.get("provider", "anthropic")

    @provider.setter
    def provider(self, value: str):
        self._data["provider"] = value

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._data["api_key"] = value

    @property
    def model(self) -> str:
        return self._data.get("model", "claude-sonnet-4-20250514")

    @model.setter
    def model(self, value: str):
        self._data["model"] = value

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "")

    @base_url.setter
    def base_url(self, value: str):
        self._data["base_url"] = value

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

    def get_wcid_ranges(self) -> dict:
        return self._data.get("wcid_ranges", DEFAULT_WCID_RANGES)
