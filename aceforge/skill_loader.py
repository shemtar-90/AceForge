"""
ACEForge Skill Loader
Reads SKILL.md and all reference files from the bundled references/ directory.
Constructs the full system prompt that gets sent with every API request.
"""

import os
from pathlib import Path
from typing import Optional


# Reference files to load — ordered by priority (most important first)
# Smaller files that are always useful load fully; large files load selectively
ALWAYS_LOAD = [
    "SKILL.md",
    "enums.md",
    "spells.md",
    "quests.md",
    "lore.md",
    "schema.md",
]

ON_DEMAND = [
    "all_spells.txt",
    "armor.md",
    "clothing.md",
    "melee_weapons.md",
    "missile_weapons.md",
    "casters.md",
    "did_values.md",
    "icons.md",
]

# Content type → which on-demand files to include
CONTENT_TYPE_FILES = {
    "monster":  ["did_values.md", "icons.md", "all_spells.txt"],
    "boss":     ["did_values.md", "icons.md", "all_spells.txt"],
    "npc":      ["did_values.md", "icons.md"],
    "item":     ["icons.md"],
    "weapon":   ["melee_weapons.md", "missile_weapons.md", "casters.md", "icons.md"],
    "armor":    ["armor.md", "clothing.md", "icons.md"],
    "quest":    ["did_values.md", "icons.md", "all_spells.txt"],
    "general":  ["did_values.md", "icons.md", "all_spells.txt"],
}


def get_references_dir() -> Path:
    """Find the references directory — works both in dev and bundled (PyInstaller) mode."""
    # PyInstaller sets sys._MEIPASS when bundled
    import sys
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # Dev mode: references are relative to this file
        base = Path(__file__).parent

    candidates = [
        base / "references",
        base.parent / "references",
        Path(__file__).parent / "references",
    ]
    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find the references/ directory. "
        "Make sure it is bundled alongside the application."
    )


class SkillLoader:
    def __init__(self):
        self._refs_dir = get_references_dir()
        self._cache: dict[str, str] = {}

    def _read(self, filename: str) -> str:
        if filename in self._cache:
            return self._cache[filename]
        path = self._refs_dir / filename
        if not path.exists():
            # Try parent (for SKILL.md which lives one level up)
            path = self._refs_dir.parent / filename
        if not path.exists():
            return f"[{filename} not found]"
        content = path.read_text(encoding="utf-8", errors="replace")
        self._cache[filename] = content
        return content

    def build_system_prompt(
        self,
        content_type: str,
        server_name: str,
        wcid_ranges: dict,
        author: str = "",
    ) -> str:
        """
        Construct the full system prompt for a generation request.
        Combines SKILL.md + always-loaded refs + content-type-specific refs.
        Injects current server config so WCID ranges are always accurate.
        """
        parts = []

        # 1 — Always-loaded files
        for fname in ALWAYS_LOAD:
            content = self._read(fname)
            if fname == "SKILL.md":
                # Inject live server config block right after SKILL.md
                server_block = self._build_server_block(server_name, wcid_ranges, author)
                parts.append(content)
                parts.append(server_block)
            else:
                parts.append(f"\n\n{'='*60}\n# {fname}\n{'='*60}\n{content}")

        # 2 — Content-type-specific files
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
            "# These values override any defaults in SKILL.md.",
            "# Always use these WCID ranges when assigning IDs.",
            "="*60,
            f"Server Name: {server_name}",
        ]
        if author:
            lines.append(f"Author/Admin: {author}")
        lines.append("\n## Current WCID Ranges (use 'next' as the next available ID):")
        lines.append("| Category | Range Start | Next Available |")
        lines.append("|----------|-------------|----------------|")
        for key, info in wcid_ranges.items():
            label = info.get("label", key)
            start = info.get("start", "?")
            nxt   = info.get("next", "?")
            lines.append(f"| {label} | {start} | {nxt} |")
        lines.append("\nAlways use the 'Next Available' value as the starting WCID for new content.")
        lines.append("If generating multiple WCIDs in one response, increment sequentially from 'Next Available'.")
        return "\n".join(lines)

    def list_references(self) -> list[str]:
        return [f.name for f in self._refs_dir.iterdir() if f.is_file()]
