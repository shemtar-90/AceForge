"""
ACEForge Configuration Manager
Handles API credentials, server settings, and WCID range configuration.
Stored in %APPDATA%/ACEForge/config.json on Windows.
"""

import os
import json
from pathlib import Path


DEFAULT_WCID_RANGES = {
    "campaign_creatures": {"start": 800000, "next": 800065, "label": "Campaign Creatures"},
    "custom_items":       {"start": 810000, "next": 810062, "label": "Custom Items"},
    "custom_portals":     {"start": 820000, "next": 820006, "label": "Custom Portals"},
    "structures":         {"start": 830000, "next": 830032, "label": "Structures"},
    "bosses":             {"start": 840000, "next": 840035, "label": "Bosses"},
    "custom_npcs":        {"start": 850000, "next": 850010, "label": "Custom NPCs"},
    "kill_contracts":     {"start": 860000, "next": 860018, "label": "Kill Contracts"},
    "custom_gear":        {"start": 870000, "next": 870025, "label": "Custom Gear"},
    "kill_tasks":         {"start": 1000000,"next": 1000025,"label": "Kill Tasks (KT Flags)"},
}

# Base WCID ranges shown in Settings — users can edit min/max and add their
# own categories. Distinct from wcid_ranges above, which tracks the AI
# generator's next-available allocation cursor.
# Each range's "folder" controls where files whose WCID falls in the range are
# saved: "" = auto by file type, "default" = main output dir, one of
# "weenie"/"recipe"/"quest"/"event" = that type's configured dir, or an
# absolute path for a custom folder.
DEFAULT_BASE_WCID_RANGES = [
    {"key": "npcs",      "name": "NPCs",      "min": 800000, "max": 809999, "folder": "", "builtin": True},
    {"key": "creatures", "name": "Creatures", "min": 810000, "max": 819999, "folder": "", "builtin": True},
    {"key": "gear",      "name": "Gear",      "min": 820000, "max": 829999, "folder": "", "builtin": True},
    {"key": "items",     "name": "Items",     "min": 830000, "max": 839999, "folder": "", "builtin": True},
]

DEFAULT_CONFIG = {
    # Provider: "anthropic" | "openai" | "compatible"
    "provider":    "ollama",
    "api_key":     "",
    "model":       "claude-sonnet-4-20250514",
    "base_url":    "",          # only used for "compatible" provider
    "auto_open_folder": True,
    "ollama_mode": False,
    "server_name": "Server Name",
    "author":      "",
    "output_dir":  str(Path.home() / "Documents" / "ACEForge" / "output"),
    # Per-type output overrides. Empty string => fall back to output_dir.
    "weenie_output_dir": "",
    "recipe_output_dir": "",
    "quest_output_dir":  "",
    "event_output_dir":  "",
    "wcid_ranges": DEFAULT_WCID_RANGES,
    "base_wcid_ranges": DEFAULT_BASE_WCID_RANGES,
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
                # Self-heal a stale provider value from before the cloud
                # provider picker was removed — every code path now assumes
                # Ollama, so a leftover "anthropic"/"openai"/"groq" value
                # would otherwise cause the API client to misconfigure itself.
                if data.get("provider") not in ("ollama", "compatible"):
                    data["provider"] = "ollama"
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
        return self._data.get("provider", "ollama")

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
        return self._data.get("server_name", "Server Name")

    @server_name.setter
    def server_name(self, value: str):
        self._data["server_name"] = value

    @property
    def output_dir(self) -> str:
        return self._data.get("output_dir", str(Path.home() / "Documents" / "ACEForge" / "output"))

    @property
    def lore_dir(self) -> Path:
        d = Path(self._path).parent / "conversations"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @output_dir.setter
    def output_dir(self, value: str):
        self._data["output_dir"] = value

    def output_dir_for(self, file_type: str) -> str:
        """Resolve the output directory for a given file type
        ('weenie'|'recipe'|'quest'|'event'). Falls back to the default
        output_dir when the type-specific override is unset/blank."""
        key = {
            "weenie": "weenie_output_dir",
            "recipe": "recipe_output_dir",
            "quest":  "quest_output_dir",
            "event":  "event_output_dir",
        }.get(file_type)
        if key:
            override = str(self._data.get(key, "") or "").strip()
            if override:
                return override
        return self.output_dir

    def get_wcid_ranges(self) -> dict:
        return self._data.get("wcid_ranges", DEFAULT_WCID_RANGES)

    def get_base_wcid_ranges(self) -> list:
        ranges = self._data.get("base_wcid_ranges")
        if not isinstance(ranges, list) or not ranges:
            ranges = [dict(r) for r in DEFAULT_BASE_WCID_RANGES]
        return ranges
