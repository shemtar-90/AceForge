"""
ACEForge Skill Loader
Reads SKILL.md and all reference files from the bundled references/ directory.
Constructs the full system prompt that gets sent with every API request.

Works in both dev mode (files on disk) and PyInstaller one-file mode
(files extracted to sys._MEIPASS at runtime).
"""

import os
import sys
from pathlib import Path
from typing import Optional


ALWAYS_LOAD = [
    "SKILL.md",
    "enums.md",
    "spells.md",
    "quests.md",
    "quest_npcs.md",   # Quest emote system — ALWAYS loaded (prevents fake table errors)
    "lore.md",
    "schema.md",
]

CONTENT_TYPE_FILES = {
    "monster":  ["did_values.md", "icons.md", "all_spells.txt"],
    "boss":     ["did_values.md", "icons.md", "all_spells.txt"],
    "npc":      ["did_values.md", "icons.md", "quest_npcs.md"],
    "item":     ["icons.md"],
    "weapon":   ["melee_weapons.md", "missile_weapons.md", "casters.md", "icons.md"],
    "armor":    ["armor.md", "clothing.md", "icons.md"],
    "quest":    ["did_values.md", "icons.md", "all_spells.txt", "quest_npcs.md"],
    "general":  ["did_values.md", "icons.md", "all_spells.txt"],
}


def get_base_dir() -> Path:
    """
    Return the base directory where bundled files live.

    PyInstaller one-file mode: everything is extracted to a temp folder
    stored in sys._MEIPASS at runtime. That folder contains all the
    'datas' entries from the spec, so 'aceforge/references/' is there.

    Dev mode: files are relative to this source file's location.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def get_references_dir() -> Path:
    base = get_base_dir()
    candidates = [
        base / "aceforge" / "references",
        base / "references",
        Path(__file__).parent / "references",
    ]
    for path in candidates:
        if path.exists() and path.is_dir():
            return path

    # Create a fallback empty dir so the app never crashes
    fallback = Path(__file__).parent / "references"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_skill_md_path() -> Optional[Path]:
    base = get_base_dir()
    candidates = [
        base / "aceforge" / "SKILL.md",
        base / "SKILL.md",
        Path(__file__).parent / "SKILL.md",
        Path(__file__).parent.parent / "SKILL.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


class SkillLoader:
    def __init__(self):
        self._refs_dir = get_references_dir()
        self._skill_md = get_skill_md_path()
        self._cache: dict[str, str] = {}

    def _read(self, filename: str) -> str:
        if filename in self._cache:
            return self._cache[filename]

        # SKILL.md has its own search path
        if filename == "SKILL.md":
            if self._skill_md and self._skill_md.exists():
                content = self._skill_md.read_text(encoding="utf-8", errors="replace")
                self._cache[filename] = content
                return content
        else:
            path = self._refs_dir / filename
            if path.exists():
                content = path.read_text(encoding="utf-8", errors="replace")
                self._cache[filename] = content
                return content

        warning = (
            f"[REFERENCE FILE MISSING: {filename}]\n"
            f"This reference file was not bundled with the application.\n"
            f"AI Mode accuracy may be reduced without it.\n"
            f"See README.md for how to add reference files."
        )
        self._cache[filename] = warning
        return warning

    def build_system_prompt(
        self,
        content_type: str,
        server_name: str,
        wcid_ranges: dict,
        author: str = "",
    ) -> str:
        parts = []

        for fname in ALWAYS_LOAD:
            content = self._read(fname)
            parts.append(content)
            if fname == "SKILL.md":
                parts.append(self._build_server_block(server_name, wcid_ranges, author))

        extra_files = CONTENT_TYPE_FILES.get(content_type, CONTENT_TYPE_FILES["general"])
        for fname in extra_files:
            if fname not in ALWAYS_LOAD:
                content = self._read(fname)
                parts.append(f"\n\n{'='*60}\n# {fname}\n{'='*60}\n{content}")

        return "\n".join(parts)

    def _build_server_block(self, server_name: str, wcid_ranges: dict, author: str) -> str:
        lines = [
            "\n\n" + "="*60,
            "# LIVE SERVER CONFIGURATION",
            "="*60,
            f"Server Name: {server_name}",
        ]
        if author:
            lines.append(f"Author/Admin: {author}")

        # ── WCID Ranges ──────────────────────────────────────────────────────
        lines.append("\n## Current WCID Ranges (use Next Available for new content):")
        lines.append("| Category | Range Start | Next Available |")
        lines.append("|----------|-------------|----------------|")
        for key, info in wcid_ranges.items():
            label = info.get("label", key)
            start = info.get("start", "?")
            nxt   = info.get("next", "?")
            lines.append(f"| {label} | {start} | {nxt} |")

        # ── Item Cross-Reference ─────────────────────────────────────────────
        lines.append("\n## CRITICAL: Known In-Game Items — Use Existing WCIDs")
        lines.append(
            "If the user requests an item that matches a name below, use the existing WCID "
            "in weenie_properties_create_list (destination=2). Do NOT create a new weenie file for it."
        )
        lines.append("\n### Currency / Consumables")
        lines.append("| WCID | Item Name |")
        lines.append("|------|-----------|")
        KNOWN_ITEMS = [
            (273,   "Pyreals"),
            (20634, "Mana Charge (MMD Note)"),
            (34,    "Healing Kit"),
            (690,   "Lockpick"),
            (5889,  "Gem of Treasure Finding"),
            (1969,  "Archmage's Salvage Kit"),
            (9061,  "Blank Augmentation Gem"),
            (801,   "Trade Note (100,000)"),
            (12891, "Legendary Key"),
            (21279, "Salvage Bag"),
        ]
        for wcid, name in KNOWN_ITEMS:
            lines.append(f"| {wcid} | {name} |")

        # Inject top weapon/armor names from reference JSONs if available
        try:
            import json, sys
            from pathlib import Path
            base = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(__file__).parent.parent
            web_dir = base / "aceforge" / "web"
            for fname, category in [("items.json", "General Items"), ("weapons.json", "Weapons (partial)"), ("armor.json", "Armor (partial)")]:
                fpath = web_dir / fname
                if fpath.exists():
                    data = json.loads(fpath.read_text(encoding="utf-8"))[:60]
                    lines.append(f"\n### {category}")
                    lines.append("| WCID | Item Name |")
                    lines.append("|------|-----------|")
                    for row in data:
                        lines.append(f"| {row[0]} | {row[1]} |")
        except Exception:
            pass

        # ── Generator note ───────────────────────────────────────────────────
        lines.append("\n## Generator Files")
        lines.append(
            "ACEForge automatically appends a Generator weenie block (type=7) to every "
            "Creature/NPC SQL output at WCID = creature_WCID + 1,000,000. You do NOT need "
            "to generate generator SQL yourself unless the boss/creature needs special spawn "
            "rules (unique location, custom respawn timer, multiple spawn slots)."
        )

        return "\n".join(lines)

    def list_references(self) -> list[str]:
        return [f.name for f in self._refs_dir.iterdir() if f.is_file()]
