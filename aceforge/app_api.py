"""
ACEForge App API
Python methods exposed to the JavaScript frontend via pywebview's js_api.
Called from JS as: window.pywebview.api.method_name(args)
"""

import queue
import re
from aceforge.lore_api import LoreMixin
import threading
import json
import os
from pathlib import Path
from datetime import datetime

from .config import Config
from .skill_loader import SkillLoader
from .api_client import APIClient, KNOWN_ENDPOINTS, DEFAULT_MODELS, GROQ_BASE_URL, OLLAMA_BASE_URL
from .sql_parser import parse_and_save_files
from .ai.agent_loop import AgentLoop
from .json_to_sql import extract_and_convert as _json_to_sql
from .quest_templates import get_all_templates, get_template_fields, run_template
from .emote_parser import parse_emote_text


class AppAPI(LoreMixin):
    def __init__(self, config: Config):
        self.config = config
        self.skill_loader = SkillLoader()
        self.api_client = APIClient(
            api_key=config.api_key,
            model=config.model,
            provider=config.provider,
            base_url=config.base_url,
        )
        self._window = None
        self._generating = False
        self._chunk_queue      = queue.Queue()
        self._last_ai_response = ''  # stored Python-side to avoid bridge size limit
        self._agent_loop = None  # AgentLoop instance for Advanced Generation mode
        self._saved_index = []          # cached searchable saved-item index
        self._saved_index_built = False # rebuilt lazily / after saves

    def set_window(self, window):
        self._window = window

    # ── Configuration ─────────────────────────────────────────────────────────

    def get_config(self) -> dict:
        return {
            "provider":     self.config.provider,
            "api_key_set":  bool(self.config.api_key),
            "model":        self.config.model,
            "base_url":     self.config.base_url,
            "server_name":  self.config.server_name,
            "author":       self.config.get("author", ""),
            "output_dir":   self.config.output_dir,
            "weenie_output_dir": self.config.get("weenie_output_dir", ""),
            "recipe_output_dir": self.config.get("recipe_output_dir", ""),
            "quest_output_dir":  self.config.get("quest_output_dir", ""),
            "event_output_dir":  self.config.get("event_output_dir", ""),
            "clothingbase_output_dir": self.config.get("clothingbase_output_dir", ""),
            "wcid_ranges":  self.config.get_wcid_ranges(),
            "base_wcid_ranges": self.config.get_base_wcid_ranges(),
            "auto_open_folder": self.config.get("auto_open_folder", True),
            "ollama_mode":     self.config.get("ollama_mode", False),
            # Send provider metadata to JS for building the UI
            "known_endpoints": KNOWN_ENDPOINTS,
            "default_models":  DEFAULT_MODELS,
        }

    def save_config(self, data: dict) -> dict:
        try:
            if "provider"    in data: self.config.provider    = data["provider"]
            if "model"       in data: self.config.model       = data["model"]
            if "base_url"    in data: self.config.base_url    = data["base_url"]
            if "server_name" in data: self.config.server_name = data["server_name"]
            if "author"      in data: self.config.set("author", data["author"])
            if "output_dir"  in data: self.config.output_dir  = data["output_dir"]
            for _k in ("weenie_output_dir", "recipe_output_dir",
                       "quest_output_dir", "event_output_dir",
                       "clothingbase_output_dir"):
                if _k in data:
                    self.config.set(_k, str(data[_k] or "").strip())
            if "api_key" in data and data["api_key"]:
                self.config.api_key = data["api_key"]
            if "wcid_ranges" in data:
                self.config.set("wcid_ranges", data["wcid_ranges"])
            if "base_wcid_ranges" in data and isinstance(data["base_wcid_ranges"], list):
                cleaned = []
                for r in data["base_wcid_ranges"]:
                    try:
                        cleaned.append({
                            "key":     str(r.get("key") or "").strip(),
                            "name":    str(r.get("name") or "").strip(),
                            "min":     int(r["min"]),
                            "max":     int(r["max"]),
                            "folder":  str(r.get("folder") or "").strip(),
                            "builtin": bool(r.get("builtin", False)),
                        })
                    except (KeyError, TypeError, ValueError, AttributeError):
                        continue
                if cleaned:
                    self.config.set("base_wcid_ranges", cleaned)

            self.config.save()

            # Refresh the API client with new credentials
            self.api_client.update_credentials(
                api_key=self.config.api_key,
                model=self.config.model,
                provider=self.config.provider,
                base_url=self.config.base_url,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_key(self) -> dict:
        """Test the currently saved API credentials."""
        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )
        ok, err = self.api_client.validate_key()
        return {"valid": ok, "error": err}

    def validate_key_with(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str = "",
    ) -> dict:
        """
        Test credentials passed directly from the Settings form.
        Does NOT require saving first — used by the Test Connection button.
        Uses a temporary client so saved credentials are not affected.
        """
        from .api_client import APIClient
        temp = APIClient(
            api_key=api_key,
            model=model or "gemini-2.0-flash",
            provider=provider,
            base_url=base_url,
        )
        ok, err = temp.validate_key()
        return {"valid": ok, "error": err}

    # ── File Operations ────────────────────────────────────────────────────────

    _gear_data_cache = None

    def _gear_resolve_web_path(self, *parts) -> 'Path':
        """Find a file under aceforge/web/ in any of the places PyInstaller
        might put it — mirrors main.py's get_icon() candidate-search pattern,
        since a single hardcoded Path(__file__).parent guess does not
        reliably resolve inside a one-file PyInstaller bundle."""
        import sys
        candidates = []
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
            candidates += [
                base.joinpath("aceforge", "web", *parts),
                base.joinpath("web", *parts),
            ]
        here = Path(__file__).parent
        candidates += [
            here.joinpath("web", *parts),
            here.parent.joinpath("aceforge", "web", *parts),
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]  # fall back to first candidate so the error message is informative

    def _gear_load_data(self):
        if self._gear_data_cache is not None:
            return self._gear_data_cache
        try:
            here = self._gear_resolve_web_path("gear_data", "gear_full.json")
            with open(here, encoding="utf-8") as f:
                raw = json.load(f)
            by_wcid = {}
            for records in raw.values():
                for r in records:
                    by_wcid[r["wcid"]] = r
            self._gear_data_cache = by_wcid
        except Exception:
            self._gear_data_cache = {}
        return self._gear_data_cache

    _gear_spell_names_cache = None

    def _gear_load_spell_names(self):
        if self._gear_spell_names_cache is not None:
            return self._gear_spell_names_cache
        try:
            here = self._gear_resolve_web_path("spells.json")
            with open(here, encoding="utf-8") as f:
                raw = json.load(f)
            self._gear_spell_names_cache = {row[0]: row[1] for row in raw}
        except Exception:
            self._gear_spell_names_cache = {}
        return self._gear_spell_names_cache

    _GEAR_ARMOR_PIECE_WORDS = [
        'Pair Of', 'Helm', 'Helmet', 'Coif', 'Basinet', 'Cowl', 'Kabuton',
        'Breastplate', 'Cuirass', 'Hauberk', 'Coat', 'Vestment', 'Jerkin', 'Vest', 'Jumpsuit',
        'Shirt', 'Robe', 'Pauldrons', 'Sleeves', 'Bracers', 'Vambraces', 'Gauntlets',
        'Girth', 'Leggings', 'Tassets', 'Greaves', 'Sollerets', 'Boots', 'Shoes', 'Sandals',
    ]
    _GEAR_WEAPON_PIECE_WORDS = [
        'Sword', 'Blade', 'Axe', 'Mace', 'Dagger', 'Spear', 'Staff', 'Stave', 'Fist', 'Lance',
        'Bow', 'Crossbow', 'Atlatl', 'Wand', 'Orb', 'Katar', 'Club', 'Scimitar', 'Kaskara',
        'Quarter Staff', 'War Staff', 'Greatblade', 'Two Handed Blade', 'Tachi', 'Balister',
        'Greatsword', 'Scepter',
    ]

    def _gear_piece_type_word(self, original_name: str) -> str:
        """Extract just the piece-type word (e.g. 'Bracers', 'Axe') from a
        full source item name, wherever it appears — armor piece words sit
        at the end ('Blackfire Shadow Bracers'), but weapon piece words can
        sit at the start ('Axe of the Quiddity') or end ('Acid Axe'). Falls
        back to the full original name if no known piece word is found, so
        a renamed item never ends up with an empty/blank name."""
        words = self._GEAR_ARMOR_PIECE_WORDS + self._GEAR_WEAPON_PIECE_WORDS
        for w in sorted(words, key=len, reverse=True):  # longest match first
            if re.search(r'\b' + re.escape(w) + r'\b', original_name, re.I):
                return w
        return original_name

    def generate_gear_items(self, wcids: list, options: dict) -> dict:
        """
        Clone one or more source armor/weapon weenies into structured,
        editable item data (NOT rendered SQL) — used by GearForge's new
        per-item editor flow. Returns each item's full int/bool/float/
        string/did/spells property dict, same shape as the source data,
        so every field is independently editable before Save.
        """
        try:
            data = self._gear_load_data()
            name_prefix = (options.get("name_prefix") or "").strip()
            start_wcid  = int(options.get("start_wcid") or 0)
            palette     = options.get("palette")
            shade       = options.get("shade")
            value       = options.get("value")
            stat_scale  = options.get("stat_scale")

            if not start_wcid:
                return {"success": False, "error": "Starting WCID is required.", "items": []}

            items = []
            next_wcid = start_wcid
            for src_wcid in wcids:
                src = data.get(int(src_wcid))
                if not src:
                    continue
                new_wcid = next_wcid
                next_wcid += 1
                orig_name = (src.get("string", {}).get("Name", {}) or {}).get("value", "Item")
                if name_prefix:
                    piece_word = self._gear_piece_type_word(orig_name)
                    new_name = f"{name_prefix} {piece_word}".strip()
                else:
                    new_name = orig_name
                item = self._gear_build_item(src, new_wcid, new_name,
                                              palette, shade, value, stat_scale)
                items.append(item)

            if not items:
                return {"success": False, "error": "No matching source items found.", "items": []}

            return {"success": True, "items": items, "error": None, "next_wcid": next_wcid}
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "items": [],
                    "traceback": traceback.format_exc()}

    def render_gear_items_sql(self, items: list) -> dict:
        """
        Serialize a list of (possibly user-edited) structured item dicts —
        same shape as generate_gear_items returns — into final SQL. Called
        by Save, so whatever edits the user made in the per-item editor are
        what actually gets written out, not the original unedited clone.
        """
        try:
            blocks = [self._gear_render_item_sql(item) for item in items]
            return {"success": True, "sql": "\n".join(blocks), "error": None}
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "sql": "",
                    "traceback": traceback.format_exc()}

    def _gear_build_item(self, source: dict, new_wcid: int, new_name: str,
                          palette, shade, value, stat_scale) -> dict:
        """Apply the standard GearForge overrides and return a structured,
        editable item dict (wcid/class_name/weenie_type/int/bool/float/
        string/did/spells) — the shared logic behind both the legacy
        one-shot SQL generator and the new structured item editor."""
        def deep_copy_props(props):
            return {k: dict(v) for k, v in props.items()}

        int_props = deep_copy_props(source.get("int", {}))
        if palette not in (None, ""):
            if "PaletteTemplate" in int_props:
                int_props["PaletteTemplate"]["value"] = str(palette)
            else:
                int_props["PaletteTemplate"] = {"type": 3, "value": str(palette)}
        if value not in (None, "") and "Value" in int_props:
            int_props["Value"]["value"] = str(value)
        if stat_scale not in (None, ""):
            if "ArmorLevel" in int_props:
                int_props["ArmorLevel"]["value"] = str(stat_scale)
            elif "Damage" in int_props:
                int_props["Damage"]["value"] = str(stat_scale)

        float_props = deep_copy_props(source.get("float", {}))
        if shade not in (None, ""):
            if "Shade" in float_props:
                float_props["Shade"]["value"] = str(shade)
            else:
                float_props["Shade"] = {"type": 12, "value": str(shade)}

        bool_props = deep_copy_props(source.get("bool", {}))
        string_props = deep_copy_props(source.get("string", {}))
        name_type = string_props.get("Name", {}).get("type", 1)
        string_props["Name"] = {"type": name_type, "value": new_name}
        did_props = deep_copy_props(source.get("did", {}))
        spells = []  # always start empty — user builds their own spellbook from scratch

        return {
            "wcid": new_wcid,
            # Which catalog weenie this was cloned from. The generated wcid is
            # brand new and absent from the catalog, so without this the Doll
            # can't re-dress (or re-generate) an already-generated set.
            "source_wcid": source.get("wcid"),
            "class_name": re.sub(r"[^a-zA-Z0-9]", "", new_name.lower())[:30] or f"item{new_wcid}",
            "weenie_type": source.get("weenie_type", 1),
            "int": int_props, "bool": bool_props, "float": float_props,
            "string": string_props, "did": did_props, "spells": spells,
        }

    def _gear_render_item_sql(self, item: dict) -> str:
        """Render one structured item dict (from _gear_build_item, possibly
        edited by the user afterward) into a complete weenie SQL block."""
        new_wcid = item["wcid"]

        def emit_block(table, props, fmt):
            if not props:
                return ""
            lines = [f"INSERT INTO `weenie_properties_{table}` (`object_Id`, `type`, `value`)"]
            rows = sorted(props.items(), key=lambda kv: kv[1]["type"])
            for i, (pname, p) in enumerate(rows):
                prefix = "VALUES " if i == 0 else "     , "
                trail = ";" if i == len(rows) - 1 else ""
                lines.append(f"{prefix}({new_wcid}, {p['type']}, {fmt(p['value'])}) /* {pname} */{trail}")
            return "\n".join(lines) + "\n"

        lines = [
            f"DELETE FROM `weenie` WHERE `class_Id` = {new_wcid};\n",
            "INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)",
            f"VALUES ({new_wcid}, '{item['class_name']}', {item.get('weenie_type', 1)}, '{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');\n",
            emit_block("int", item.get("int", {}), lambda v: v),
            emit_block("bool", item.get("bool", {}), lambda v: v),
            emit_block("float", item.get("float", {}), lambda v: v),
            emit_block("string", item.get("string", {}), lambda v: "'" + str(v).replace("'", "''") + "'"),
            emit_block("d_i_d", item.get("did", {}), lambda v: v),
        ]
        spells = item.get("spells") or []
        if spells:
            spell_names = self._gear_load_spell_names()
            spell_lines = ["INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)"]
            for i, sp in enumerate(spells):
                prefix = "VALUES " if i == 0 else "     , "
                trail = ";" if i == len(spells) - 1 else ""
                sp_name = spell_names.get(int(sp["spell_id"]), "")
                comment = f" /* {sp_name} */" if sp_name else ""
                spell_lines.append(f"{prefix}({new_wcid}, {sp['spell_id']}, {sp['probability']}){comment}{trail}")
            lines.append("\n".join(spell_lines))

        return "\n".join(l for l in lines if l)

    def generate_gear_set(self, wcids: list, options: dict) -> dict:
        """
        Clone one or more source armor/weapon weenies into new custom items.
        options: {name_prefix, start_wcid, palette, shade, value, stat_scale}
        Name/Palette/Shade/Value/ArmorLevel-or-Damage are user-editable;
        everything else (ValidLocations, resistances, Setup/Icon/
        PhysicsEffectTable/SoundTable DIDs, spellbook) copies verbatim so the
        clone looks and behaves like the source item.
        """
        try:
            data = self._gear_load_data()
            name_prefix = (options.get("name_prefix") or "").strip()
            start_wcid  = int(options.get("start_wcid") or 0)
            palette     = options.get("palette")
            shade       = options.get("shade")
            value       = options.get("value")
            stat_scale  = options.get("stat_scale")

            if not start_wcid:
                return {"success": False, "error": "Starting WCID is required.", "sql": ""}

            blocks = []
            next_wcid = start_wcid
            for src_wcid in wcids:
                src = data.get(int(src_wcid))
                if not src:
                    continue
                new_wcid = next_wcid
                next_wcid += 1
                orig_name = (src.get("string", {}).get("Name", {}) or {}).get("value", "Item")
                new_name = f"{name_prefix} {orig_name}".strip() if name_prefix else orig_name
                blocks.append(self._gear_clone_one(src, new_wcid, new_name,
                                                    palette, shade, value, stat_scale))

            if not blocks:
                return {"success": False, "error": "No matching source items found.", "sql": ""}

            return {"success": True, "sql": "\n".join(blocks), "error": None,
                    "count": len(blocks), "next_wcid": next_wcid}
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "sql": "",
                    "traceback": traceback.format_exc()}

    def _gear_clone_one(self, source: dict, new_wcid: int, new_name: str,
                         palette, shade, value, stat_scale) -> str:
        def deep_copy_props(props):
            return {k: dict(v) for k, v in props.items()}

        int_props = deep_copy_props(source.get("int", {}))
        if palette not in (None, ""):
            if "PaletteTemplate" in int_props:
                int_props["PaletteTemplate"]["value"] = str(palette)
            else:
                int_props["PaletteTemplate"] = {"type": 3, "value": str(palette)}
        if value not in (None, "") and "Value" in int_props:
            int_props["Value"]["value"] = str(value)
        if stat_scale not in (None, ""):
            if "ArmorLevel" in int_props:
                int_props["ArmorLevel"]["value"] = str(stat_scale)
            elif "Damage" in int_props:
                int_props["Damage"]["value"] = str(stat_scale)

        float_props = deep_copy_props(source.get("float", {}))
        if shade not in (None, ""):
            if "Shade" in float_props:
                float_props["Shade"]["value"] = str(shade)
            else:
                float_props["Shade"] = {"type": 12, "value": str(shade)}

        bool_props = deep_copy_props(source.get("bool", {}))
        string_props = deep_copy_props(source.get("string", {}))
        name_type = string_props.get("Name", {}).get("type", 1)
        string_props["Name"] = {"type": name_type, "value": new_name}
        did_props = deep_copy_props(source.get("did", {}))  # always verbatim

        class_name = re.sub(r"[^a-zA-Z0-9]", "", new_name.lower())[:30] or f"item{new_wcid}"

        def emit_block(table, props, fmt):
            if not props:
                return ""
            lines = [f"INSERT INTO `weenie_properties_{table}` (`object_Id`, `type`, `value`)"]
            rows = sorted(props.items(), key=lambda kv: kv[1]["type"])
            for i, (pname, p) in enumerate(rows):
                prefix = "VALUES " if i == 0 else "     , "
                trail = ";" if i == len(rows) - 1 else ""
                lines.append(f"{prefix}({new_wcid}, {p['type']}, {fmt(p['value'])}) /* {pname} */{trail}")
            return "\n".join(lines) + "\n"

        lines = [
            f"DELETE FROM `weenie` WHERE `class_Id` = {new_wcid};\n",
            "INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)",
            f"VALUES ({new_wcid}, '{class_name}', {source.get('weenie_type', 1)}, '{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');\n",
            emit_block("int", int_props, lambda v: v),
            emit_block("bool", bool_props, lambda v: v),
            emit_block("float", float_props, lambda v: v),
            emit_block("string", string_props, lambda v: "'" + v.replace("'", "''") + "'"),
            emit_block("d_i_d", did_props, lambda v: v),
        ]
        spells = []  # always start empty — user builds their own spellbook from scratch
        if spells:
            spell_lines = ["INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)"]
            for i, sp in enumerate(spells):
                prefix = "VALUES " if i == 0 else "     , "
                trail = ";" if i == len(spells) - 1 else ""
                spell_lines.append(f"{prefix}({new_wcid}, {sp['spell_id']}, {sp['probability']}){trail}")
            lines.append("\n".join(spell_lines))

        return "\n".join(l for l in lines if l)

    @staticmethod
    def _detect_sql_type(sql: str) -> str:
        """Classify an SQL file by its primary target table so it can be routed
        to the matching per-type output directory. Mirrors the JS
        _detectSQLFileType — DELETE FROM is the reliable first-line indicator."""
        s = sql or ""
        if re.search(r"DELETE FROM `?quest`?", s, re.I):
            return "quest"
        if re.search(r"DELETE FROM `?event`?", s, re.I):
            return "event"
        if re.search(r"DELETE FROM `?recipe`?", s, re.I) or \
           re.search(r"INSERT INTO `?recipe`?\b", s, re.I) or \
           re.search(r"INSERT INTO `?cook_book`?", s, re.I):
            return "recipe"
        return "weenie"  # default: creatures, NPCs, items, gear, quest-flag weenies

    @staticmethod
    def _extract_wcid(sql: str):
        """Pull the weenie WCID from SQL — DELETE header first, then the
        weenie INSERT. Returns int or None."""
        m = re.search(r"DELETE\s+FROM\s+`?weenie`?\s+WHERE\s+`?class_Id`?\s*=\s*(\d+)", sql, re.I)
        if not m:
            m = re.search(r"INSERT\s+INTO\s+`?weenie`?\s*\([^)]*\)\s*VALUES\s*\(\s*(\d+)", sql, re.I)
        return int(m.group(1)) if m else None

    def _folder_token_to_dir(self, token: str) -> str:
        """Resolve a base-WCID-range folder value to a directory path.
        '' = unset, 'default' = main output dir, 'weenie'/'recipe'/'quest'/
        'event' = that type's configured dir, anything else = custom path."""
        t = str(token or "").strip()
        if not t:
            return ""
        if t == "default":
            return str(self.config.output_dir or "").strip()
        if t in ("weenie", "recipe", "quest", "event"):
            return str(self.config.output_dir_for(t) or "").strip()
        return t

    def _range_folder_for_wcid(self, wcid: int) -> str:
        """Return the configured output dir for the base WCID range containing
        wcid, or '' if no range matches or the matching range has no folder.
        Generators use their creature's WCID with a leading 1 (+1000000), so
        an unmatched 1xxxxxx WCID retries as xxxxxx — the generator file then
        lands in the same folder as the creature it spawns."""
        candidates = [wcid]
        if wcid > 1000000:
            candidates.append(wcid - 1000000)
        for w in candidates:
            for r in self.config.get_base_wcid_ranges():
                try:
                    if int(r.get("min")) <= w <= int(r.get("max")):
                        return self._folder_token_to_dir(r.get("folder"))
                except (TypeError, ValueError):
                    continue
        return ""

    def _resolve_output_dir(self, sql: str) -> str:
        """Pick the output directory for a piece of SQL, creating it if needed.
        Weenie files whose WCID falls in a base WCID range with a folder
        override go to that folder; everything else routes by file type,
        falling back to the default output dir."""
        ftype = self._detect_sql_type(sql)
        output_dir = ""
        if ftype == "weenie":
            wcid = self._extract_wcid(sql)
            if wcid is not None:
                output_dir = self._range_folder_for_wcid(wcid)
        if not output_dir:
            output_dir = str(self.config.output_dir_for(ftype) or "").strip()
        if not output_dir:
            output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    def save_sql(self, sql_text: str, wcid: int, name: str) -> dict:
        try:
            output_dir = self._resolve_output_dir(sql_text)
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            safe_name = name.lower().replace(" ", "_").replace("'", "")[:40]
            # If name is already a .sql filename (from import), use it directly
            if name.lower().endswith('.sql'):
                filename = name
            else:
                filename = f"{wcid} {name}.sql"
            fpath     = out_path / filename
            fpath.write_text(sql_text, encoding="utf-8")
            self._saved_index_built = False   # invalidate saved-item index
            return {"success": True, "path": str(fpath), "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Searchable saved-item index ────────────────────────────────────────────
    # Weenie types that are NOT items and must never appear in the index.
    _SAVED_SKIP_TYPES = {10, 12}   # 10=Creature, 12=Vendor/NPC
    _SAVED_TYPE_LABEL = {
        1: "Item", 2: "Armor/Clothing", 3: "Weapon", 4: "Ammo", 6: "Weapon",
        8: "Book", 9: "Coin", 18: "Food", 19: "Door", 20: "Chest", 21: "Container",
        22: "Key", 25: "Lifestone", 34: "Scroll", 35: "Caster", 37: "ManaStone",
        38: "Gem", 51: "Stackable",
    }

    def _saved_index_dirs(self):
        dirs, seen = [], set()
        for d in ([self.config.output_dir] +
                  [self.config.get(k, "") for k in (
                      "weenie_output_dir", "recipe_output_dir",
                      "quest_output_dir", "event_output_dir")] +
                  [self._folder_token_to_dir(r.get("folder"))
                   for r in self.config.get_base_wcid_ranges()]):
            d = str(d or "").strip()
            if d and d not in seen:
                seen.add(d); dirs.append(Path(d))
        if not dirs:
            dirs.append(Path.home() / "Documents" / "ACEForge" / "output")
        return dirs

    def _parse_saved_item(self, text: str, filename: str):
        """Extract an indexable item from one SQL file, or None if it isn't an
        item weenie (creature/NPC/generator/quest files are skipped)."""
        m = re.search(r"INSERT\s+INTO\s+`?weenie`?\s*\([^)]*\)\s*VALUES\s*"
                      r"\(\s*(\d+)\s*,\s*'([^']*)'\s*,\s*(\d+)", text, re.I)
        if not m:
            return None
        wtype = int(m.group(3))
        if wtype in self._SAVED_SKIP_TYPES:
            return None
        if re.search(r"weenie_properties_generator", text, re.I):
            return None   # generator weenie, not a referenceable item
        wcid, class_name = int(m.group(1)), m.group(2)
        name = class_name
        nm = re.search(r"weenie_properties_string`[^;]*?VALUES\s*\(\s*\d+\s*,\s*1\s*,\s*'([^']*)'",
                       text, re.I | re.S)
        if nm and nm.group(1).strip():
            name = nm.group(1)
        return {"wcid": wcid, "name": name, "class_name": class_name,
                "type": wtype, "type_label": self._SAVED_TYPE_LABEL.get(wtype, f"Type {wtype}"),
                "file": filename}

    def _build_saved_index(self):
        idx = {}
        for d in self._saved_index_dirs():
            try:
                if not d.exists():
                    continue
                for f in d.glob("*.sql"):
                    try:
                        it = self._parse_saved_item(
                            f.read_text(encoding="utf-8", errors="ignore"), f.name)
                        if it:
                            idx[it["wcid"]] = it   # dedupe by wcid, newest wins
                    except Exception:
                        continue
            except Exception:
                continue
        self._saved_index = list(idx.values())
        self._saved_index_built = True
        return self._saved_index

    def search_saved_items(self, query: str = "", limit: int = 40) -> dict:
        """Search items previously saved to the output folder(s) by WCID or name.
        Only weapons/armor/clothing/jewelry/items are indexed (no creatures/NPCs)."""
        try:
            if not self._saved_index_built:
                self._build_saved_index()
            q = str(query or "").strip().lower()
            items = self._saved_index
            if q:
                items = [it for it in items
                         if q in str(it["wcid"]) or q in it["name"].lower()
                         or q in it["class_name"].lower()]
            items = sorted(items, key=lambda it: it["name"].lower())[:int(limit or 40)]
            return {"items": items, "total": len(self._saved_index)}
        except Exception as e:
            return {"items": [], "error": str(e)}

    def rescan_saved_items(self) -> dict:
        """Force a rescan of the output folders and return the item count."""
        self._build_saved_index()
        return {"count": len(self._saved_index)}

    # ── Emote Parser ──────────────────────────────────────────────────────────

    def convert_emotes(self, emote_text: str, wcid: int) -> dict:
        """
        Convert WeenieFab compact emote text → ACEmulator SQL.
        Called from JS as: window.pywebview.api.convert_emotes(text, wcid)

        Returns:
            {
              success:      bool,
              sql:          str,       # ready-to-paste SQL
              warnings:     [str],     # non-fatal parser warnings
              emote_count:  int,
              action_count: int,
              error:        str|None,
            }
        """
        try:
            if not emote_text or not emote_text.strip():
                return {
                    "success": False, "sql": "", "warnings": [],
                    "emote_count": 0, "action_count": 0,
                    "error": "Emote text is empty.",
                }
            try:
                wcid = int(wcid)
            except (TypeError, ValueError):
                wcid = 850000

            result = parse_emote_text(emote_text, wcid)
            if result["error"]:
                return {
                    "success": False,
                    "sql":          "",
                    "warnings":     result["warnings"],
                    "emote_count":  0,
                    "action_count": 0,
                    "error":        result["error"],
                }
            return {
                "success":      True,
                "sql":          result["sql"],
                "warnings":     result["warnings"],
                "emote_count":  result["emote_count"],
                "action_count": result["action_count"],
                "blocks":       result.get("blocks", []),
                "error":        None,
            }
        except Exception as e:
            import traceback
            return {
                "success":      False,
                "sql":          "",
                "warnings":     [traceback.format_exc()],
                "emote_count":  0,
                "action_count": 0,
                "error":        str(e),
            }

    def start_planning(self, prompt: str, content_type: str, existing_sql: str = '') -> dict:
        """Phase 1: Ask AI to produce a JSON plan of files needed."""
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}

        self._generating = True
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break

        wcid_ranges = self.config.get_wcid_ranges()
        server_name = self.config.server_name or "Shattered Dawn"

        edit_mode = bool(existing_sql and existing_sql.strip())
        system_prompt = f"""You are an ACEmulator content {"editor" if edit_mode else "planner"} for the server "{server_name}".
Analyze the user request and produce a complete JSON file plan.

CRITICAL INSTRUCTIONS — READ CAREFULLY:
1. You MUST list EVERY separate SQL file required to fully implement the request.
2. Do NOT collapse multiple pieces of content into one file. Each distinct weenie, NPC, item, quest, or generator needs its OWN entry.
3. If the user requests 10 monsters, plan 10 creature files PLUS 10 generator files = 20 entries.
4. If the user requests a questline, plan every NPC, every item reward, every kill contract, and every generator needed.
5. Do not summarize or reduce. Be complete. More files is better than fewer.

Respond with ONLY a valid JSON object. No markdown fences, no explanation, no extra text before or after.

JSON format (use exactly this structure):
{{
  "summary": "one sentence describing what will be created",
  "files": [
    {{"index": 0, "name": "WCID DescriptiveName.sql", "type": "creature", "wcid": 800001, "description": "brief description"}},
    {{"index": 1, "name": "WCID DescriptiveName Generator.sql", "type": "generator", "wcid": 810001, "description": "spawner for WCID 800001"}}
  ]
}}

WCID ranges for {server_name}:
- Creatures/Mobs: 800000-809999
- Items/Custom objects: 810000-819999
- Portals: 820000-829999
- Bosses: 840000-849999
- NPCs (quest givers, vendors): 850000-859999
- Kill Contracts: 860000-869999
- Custom Gear/Jewelry: 870000-879999
- Generators: creature_wcid + 10000 (e.g. creature 800001 → generator 810001)

File planning rules:
- One file per weenie (creature, NPC, item, weapon, armor, quest, generator)
- Assign unique WCIDs in the correct range — no duplicates
- Order files: items/rewards first, then creatures/NPCs, then quests, then generators last
- Name format: "WCID DescriptiveName.sql"
- Every creature or NPC MUST have a paired generator file so it spawns in world
- Generator WCID = creature_wcid + 10000 (if that range is taken, use creature_wcid + 5000)

Think step by step before writing JSON:
- What distinct creatures/NPCs does this request need?
- What items or rewards are needed?
- What quests or kill contracts are needed?
- What generators are needed (one per creature/NPC)?
Count all of the above, then write that many entries in the files array."""

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        def _plan_done(text: str):
            self._generating = False
            self._last_plan_text = text
            self._chunk_queue.put({"type": "plan_ready", "text": text})
            print(f"[PLAN] done, {len(text)} chars", flush=True)

        # In edit mode, prepend the existing SQL so AI knows what to modify
        planning_prompt = prompt
        if existing_sql and existing_sql.strip():
            # Store for use by generate_planned_file
            self._editing_sql = existing_sql.strip()
            planning_prompt = (
                f"EXISTING WEENIE SQL (modify this, do not create new):\n```sql\n{existing_sql[:8000]}\n```\n\n"
                f"USER REQUEST: {prompt}"
            )
        else:
            self._editing_sql = ""

        try:
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, planning_prompt, self._on_chunk, _plan_done, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": str(e)}
        return {"success": True}

    def generate_planned_file(self, plan_json: str, file_index: int,
                              original_prompt: str, existing_sql: str = '',
                              gen_mode: str = 'base') -> dict:
        """
        Phase 2: Generate one planned file.
        gen_mode='base'     → direct single-call generation per file (fast, accurate SQL)
        gen_mode='advanced' → AgentLoop with self-review, auto-continuation, context threading
        """
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}

        try:
            plan = json.loads(plan_json)
        except Exception as e:
            return {"success": False, "error": f"Plan parse error: {e}"}

        # Use stored editing SQL from planning phase if not provided
        if not existing_sql:
            existing_sql = getattr(self, "_editing_sql", "")

        # ── Base mode: direct single-call generation per file ─────────────
        # Same plan/approve/save flow, no AgentLoop overhead.
        if gen_mode != 'advanced':
            return self._generate_file_direct(plan_json, file_index, original_prompt, existing_sql)

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        # Create or reuse the AgentLoop for this session.
        # Reuse if plan hasn't changed (same session); reset if new plan.
        current_summary = plan.get("summary", "")
        if (self._agent_loop is None
                or getattr(self._agent_loop, "_last_plan_summary", None) != current_summary
                or file_index == 0):
            def _clear_generating():
                self._generating = False
            self._agent_loop = AgentLoop(
                api_client=self.api_client,
                skill_loader=self.skill_loader,
                config=self.config,
                chunk_queue=self._chunk_queue,
                process_emote_scripts=self._process_emote_scripts,
                save_file=self._save_single_file,
                on_complete=_clear_generating,
            )
            self._agent_loop._last_plan_summary = current_summary

        self._generating = True
        # Clear stale chunks
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break

        # Forward _generating state to the loop (it manages its own flag too)
        started = self._agent_loop.run_file(
            plan=plan,
            file_index=file_index,
            original_prompt=original_prompt,
            editing_sql=existing_sql,
        )
        if not started:
            self._generating = False
            return {"success": False, "error": "Agent loop already running."}

        return {"success": True}

    def _generate_file_direct(self, plan_json: str, file_index: int,
                               original_prompt: str, existing_sql: str) -> dict:
        """Base mode: generate one planned file in a single focused API call."""
        try:
            plan = json.loads(plan_json)
        except Exception as e:
            return {"success": False, "error": f"Plan parse error: {e}"}

        files = plan.get("files", [])
        if file_index >= len(files):
            return {"success": False, "error": "File index out of range."}

        file_entry = files[file_index]
        fname  = file_entry.get("name", f"file_{file_index}.sql")
        ftype  = file_entry.get("type", "creature")
        wcid   = file_entry.get("wcid", 800000)
        fdesc  = file_entry.get("description", "")
        total  = len(files)
        server = self.config.server_name or "Shattered Dawn"
        is_local = (self.config.get('provider','anthropic') in ('ollama',)
                    or bool(self.config.get('ollama_mode', False)))

        # Other files in the plan for cross-reference context
        other_ctx = "\n".join(
            f"  - File {i+1}: WCID {f['wcid']} | {f['name']} | {f['description']}"
            for i, f in enumerate(files) if i != file_index
        ) or "  (none)"

        # JSON schema prompt — replaces the large SKILL.md SQL prompt
        try:
            from pathlib import Path
            import sys
            _base = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(__file__).parent
            _json_schema = (_base / 'references' / 'ai_json_schema.md').read_text(encoding='utf-8')
            _emote_fmt   = (_base / 'references' / 'emote_format.md').read_text(encoding='utf-8')
        except Exception:
            _json_schema = 'Output a JSON object describing the ACE content.'
            _emote_fmt   = ''

        system = (
            f'You are an ACEmulator content generator for the server "{server}".\n'
            f'You output ONLY a JSON object. Never write SQL.\n\n'
            + _json_schema
            + ('\n\n' + _emote_fmt if _emote_fmt else '')
        )

        system += f"""

## File Context
You are generating FILE {file_index + 1} of {total}.
This file: WCID {wcid} | {fname} | {fdesc}

Other files in this generation set (for WCID cross-references):
{other_ctx}

Output raw SQL only — no markdown fences, no explanations.
Start with: /* ===== FILE: {fname} ===== */
"""

        edit_ctx = (
            f"EXISTING SQL TO MODIFY:\n```sql\n{existing_sql[:6000]}\n```\n\n"
            if existing_sql else ""
        )
        user = (
            f"{edit_ctx}"
            f"Generate a JSON object for: {fdesc}\n"
            f"Original request: {original_prompt}\n"
            f"WCID: {wcid} | File: {fname}\n"
            f"Output ONLY the JSON object. No SQL. No explanations."
        )

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        self._generating = True
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break

        def _done(text: str):
            self._generating = False
            try:
                # Convert JSON output to SQL, then run emote YAML conversion
                sql = _json_to_sql(text, fname)
                if not sql.strip():
                    # Fallback: treat as raw SQL if no JSON found
                    sql = text
                sql = self._process_emote_scripts(sql)
                save = self._save_single_file(sql, fname)
            except Exception as e:
                save = {"success": False, "error": str(e)}
            self._chunk_queue.put({
                "type": "file_done",
                "file_index": file_index,
                "file_name": fname,
                "save": save,
                "total": total,
                "review_issues": [],
            })

        def _err(msg: str):
            self._generating = False
            self._chunk_queue.put({"type": "error", "message": msg})

        self._generating = True  # set before thread starts — prevents stall detection gap
        # Use a bare chunk handler that always queues — avoids _on_chunk's _generating guard
        _q = self._chunk_queue
        def _chunk(text: str):
            _q.put({"type": "chunk", "text": text})
        import threading
        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system, user, _chunk, _done, _err, 0.2),  # 0.2 = precise SQL generation
            daemon=True,
        ).start()
        return {"success": True}

    def _save_single_file(self, content: str, suggested_name: str) -> dict:
        """Save one SQL file immediately, routed to the per-type output dir.
        Used by QuestForge's per-file save so quest-flag files land in the
        Quest directory while the creature/item weenies they spawn land in the
        Weenie directory (each file classified by its own content)."""
        try:
            output_dir = self._resolve_output_dir(content)
            written = parse_and_save_files(content, output_dir, subfolder="",
                                           dir_for_content=self._resolve_output_dir)
            if not written:
                # Fallback: save with suggested name
                from aceforge.sql_parser import sanitize_filename, clean_sql
                fname = sanitize_filename(suggested_name)
                fpath = Path(output_dir) / fname
                fpath.write_text(clean_sql(content), encoding="utf-8")
                written = [str(fpath)]
            self._saved_index_built = False   # invalidate saved-item index
            return {
                "success": True,
                "files": [os.path.basename(f) for f in written],
                "folder": os.path.dirname(written[0]) if written else output_dir,
            }
        except Exception as e:
            import traceback
            print(f"[SAVE] error: {traceback.format_exc()}", flush=True)
            return {"success": False, "error": str(e)}


    def continue_generation(self, pass_num: int) -> dict:
        """Continue a truncated generation — appends to _last_ai_response."""
        if self._generating:
            return {"success": False, "error": "Already generating."}

        tail = self._last_ai_response[-600:] if self._last_ai_response else ""
        if not tail:
            return {"success": False, "error": "No previous output to continue from."}

        continuation_prompt = (
            "Continue generating exactly where you left off. "
            "Do NOT restate the file header or any SQL already written. "
            "Do NOT add introductory text. "
            "Begin IMMEDIATELY from after this last line:\n\n"
            f"...{tail}"
        )
        # Minimal system prompt for continuation
        system_prompt = (
            "You are continuing an ACEmulator SQL generation. "
            "Output only raw SQL continuation with /* ===== FILE: name.sql ===== */ "
            "markers for any new files. No markdown fences, no explanations."
        )
        self._generating = True
        self._continuation_pass = pass_num

        def _on_done_continuation(text: str):
            self._generating = False
            text = self._process_emote_scripts(text)   # convert WeenieFab blocks → SQL
            self._last_ai_response = self._last_ai_response + "\n" + text
            stripped = text.rstrip()
            looks_truncated = bool(stripped) and not any(
                stripped.endswith(s) for s in (";", "*/", "---", "```")
            )
            self._chunk_queue.put({
                "type": "done",
                "truncated": looks_truncated,
                "pass": pass_num,
            })
            print(f"[API] continuation pass {pass_num} done, appended {len(text)} chars", flush=True)

        try:
            self.api_client.update_credentials(
                api_key=self.config.api_key,
                model=self.config.model,
                provider=self.config.provider,
                base_url=self.config.base_url,
            )
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, continuation_prompt,
                      self._on_chunk, _on_done_continuation, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": str(e)}
        return {"success": True}


    def save_ai_files(self, content_type: str = "creature") -> dict:
        try:
            full_response = self._last_ai_response
            if not full_response:
                return {"success": False, "error": "No content to save — generate first."}
            output_dir = str(self.config.output_dir or "").strip()
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
            # Ensure output dir exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            written = parse_and_save_files(full_response, output_dir, subfolder="",
                                           dir_for_content=self._resolve_output_dir)
            if not written:
                return {"success": False, "error": "Parser found no SQL content in response. Ensure AI output contains FILE: markers or valid SQL."}
            return {
                "success": True,
                "files":  [os.path.basename(f) for f in written],
                "count":  len(written),
                "folder": os.path.dirname(written[0]),
            }
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied writing to output directory: {e}"}
        except Exception as e:
            import traceback
            print(f"[SAVE] exception: {traceback.format_exc()}", flush=True)
            return {"success": False, "error": str(e)}

    # ── Content Libraries ─────────────────────────────────────────────────────



    def import_sql(self) -> dict:
        """Open a file dialog and return SQL file content for import into the builder.
        Uses pywebview native dialog (works in both dev and EXE mode)."""
        from pathlib import Path
        try:
            if self._window is None:
                return {"error": "Window not ready — call set_window() first."}
            result = self._window.create_file_dialog(
                dialog_type=10,          # OPEN_DIALOG
                allow_multiple=False,
                file_types=("SQL Files (*.sql)", "All Files (*.*)")
            )
            if not result:
                return {"cancelled": True}
            path = result[0] if isinstance(result, (list, tuple)) else result
        except Exception as e:
            # Fallback: tkinter (dev mode without pywebview window)
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                path = filedialog.askopenfilename(
                    title="Import SQL File",
                    filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
                )
                root.destroy()
                if not path:
                    return {"cancelled": True}
            except Exception as e2:
                return {"error": f"File dialog unavailable: {e2}"}
        if not path:
            return {"cancelled": True}
        try:
            content = Path(path).read_text(encoding='utf-8', errors='ignore')
            return {
                "path": str(path),
                "filename": Path(path).name,
                "content": content,
                "size": len(content),
            }
        except Exception as e:
            return {"error": str(e)}

    def import_sql_multi(self) -> dict:
        """Open a multi-select file dialog and return the content of every chosen
        SQL file. Used by GearForge to bulk-import items for editing.
        Returns {"files": [{"filename", "path", "content"}], "cancelled"?}."""
        from pathlib import Path
        paths = []
        try:
            if self._window is None:
                return {"error": "Window not ready — call set_window() first."}
            result = self._window.create_file_dialog(
                dialog_type=10,          # OPEN_DIALOG
                allow_multiple=True,
                file_types=("SQL Files (*.sql)", "All Files (*.*)")
            )
            if not result:
                return {"cancelled": True}
            paths = list(result) if isinstance(result, (list, tuple)) else [result]
        except Exception:
            # Fallback: tkinter (dev mode without a pywebview window)
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                chosen = filedialog.askopenfilenames(
                    title="Import SQL Files",
                    filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
                )
                root.destroy()
                paths = list(chosen)
                if not paths:
                    return {"cancelled": True}
            except Exception as e2:
                return {"error": f"File dialog unavailable: {e2}"}
        if not paths:
            return {"cancelled": True}
        files = []
        for p in paths:
            try:
                files.append({
                    "path": str(p),
                    "filename": Path(p).name,
                    "content": Path(p).read_text(encoding="utf-8", errors="ignore"),
                })
            except Exception as e:
                files.append({"path": str(p), "filename": Path(p).name,
                              "content": "", "error": str(e)})
        return {"files": files}

    def browse_folder(self) -> dict:
        """Open a native folder-selection dialog and return the chosen path.
        Used by the Settings output-directory 'Browse' buttons.
        Returns {"path": str} | {"cancelled": True} | {"error": str}."""
        from pathlib import Path
        try:
            if self._window is None:
                return {"error": "Window not ready — call set_window() first."}
            result = self._window.create_file_dialog(dialog_type=20)  # FOLDER_DIALOG
            if not result:
                return {"cancelled": True}
            path = result[0] if isinstance(result, (list, tuple)) else result
            return {"path": str(path)}
        except Exception:
            # Fallback: tkinter (dev mode without a pywebview window)
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                path = filedialog.askdirectory(title="Select Output Folder")
                root.destroy()
                if not path:
                    return {"cancelled": True}
                return {"path": str(path)}
            except Exception as e2:
                return {"error": f"Folder dialog unavailable: {e2}"}

    # ── Quest Templates ──────────────────────────────────────────────────

    def get_quest_templates(self) -> list:
        """Return list of available quest templates for the UI."""
        return get_all_templates()

    def get_quest_template_fields(self, template_id: str) -> list:
        """Return field definitions for a specific template."""
        return get_template_fields(template_id)

    def generate_quest_template(self, template_id: str, params_json: str) -> dict:
        """
        Deterministically generate all SQL files for a quest template, then
        send every dialogue line (Tell/DirectBroadcast/LocalBroadcast/
        WorldBroadcast/Say/FellowBroadcast) to the AI in a single batched
        request so it can rewrite them in the NPC's stated personality —
        everything else (WCIDs, quest flags, generator rows, structure)
        stays exactly as the deterministic template produced it.
        Returns {success, files: [{filename, sql, type}], error}
        """
        try:
            params = json.loads(params_json)
        except Exception as e:
            return {"success": False, "error": f"Invalid params: {e}", "files": []}

        # Enrich item descriptions with emote hints for the AI
        params = self._enrich_item_descriptions(params)

        try:
            files = run_template(template_id, params, self.config)
            # Process emote scripts in each file
            for f in files:
                f["sql"] = self._process_emote_scripts(f["sql"])
            # Rewrite dialogue lines in each NPC's personality, if given
            files = self._rewrite_dialogue_with_ai(files, params)
            return {"success": True, "files": files, "error": None}
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "files": [],
                    "traceback": traceback.format_exc()}

    # ── "What Do You Want?" — natural-language → structured quest params ──────
    # Creature types the batch/turn-in forms understand, as "Label (int)".
    _CREATURE_TYPES = [
        'Olthoi (1)', 'Banderling (2)', 'Drudge (3)', 'Mosswart (4)',
        'Lugian (5)', 'Tumerok (6)', 'Mite (7)', 'Tusker (8)', 'Golem (13)',
        'Undead (14)', 'Gromnie (15)', 'Reedshark (16)', 'Armoredillo (17)',
        'Fae (18)', 'Virindi (19)', 'Wisp (20)', 'Shadow (22)', 'Mattekar (23)',
        'Monouga (28)', 'Zefir (29)', 'Skeleton (30)', 'Human (31)',
        'Shreth (32)', 'FireElemental (38)', 'Snowman (39)', 'Grievver (44)',
        'Ursuin (46)', 'AcidElemental (60)', 'FrostElemental (61)', 'Burun (75)',
        'GearKnight (99)', 'Gurog (100)', 'Anekshay (101)',
    ]
    _LOOT_TIERS = ['None (0)', 'T4 (3101)', 'T5 (3102)', 'T6 (3103)',
                   'T7 (3104)', 'T8 (3105)']

    def _ct_label(self, name: str) -> str:
        """Map a loose creature-type name ('tumerok', 'Tumerok (6)', 'undead')
        to the canonical 'Label (int)' string. Returns '' if unrecognized."""
        if not name:
            return ''
        key = re.sub(r'\s*\(\d+\)\s*$', '', str(name)).strip().lower()
        for lbl in self._CREATURE_TYPES:
            if lbl.split(' (')[0].lower() == key:
                return lbl
        return ''

    def _lt_label(self, name: str) -> str:
        """Map a loose loot-tier value ('t6', 'tier 8', '8', '3103') → 'Label (int)'."""
        s = str(name or '').strip().lower()
        s = s.replace('lootgen', '').replace('tier', '').strip()
        if not s or s in ('none', '0', 'no', 'false', ''):
            return 'None (0)'
        if s in ('4', '5', '6', '7', '8'):     # bare tier number → t4..t8
            s = 't' + s
        for lbl in self._LOOT_TIERS:
            base = lbl.split(' (')[0].lower()          # 't6'
            num = lbl.split('(')[1].rstrip(')')        # '3103'
            if s == base or s == num or s == '(' + num + ')':
                return lbl
        return 'None (0)'

    def plan_quest_from_prompt(self, prompt: str, quest_kind: str) -> dict:
        """Turn a free-text prompt into structured quest-form parameters.

        The LLM is used ONLY as a parameter extractor — it never writes SQL.
        It reads the prompt and emits a small JSON object of field values, which
        the frontend loads into the existing quest form for review. The proven
        deterministic engine then builds the SQL when the user hits Generate.

        quest_kind: 'kill_task' | 'item_turnin' | 'delivery'
        Returns {success, kind, shared?, rows?, form?, notes, error, raw?}.
        """
        prompt = (prompt or '').strip()
        if not prompt:
            return {"success": False, "error": "Please describe what you want."}
        kind = (quest_kind or 'kill_task').strip()
        if kind not in ('kill_task', 'item_turnin', 'delivery'):
            return {"success": False, "error": f"Unknown quest kind: {kind}"}

        system_prompt = self._build_quest_plan_system_prompt(kind)
        res = self._ai_generate_sync(system_prompt, prompt,
                                     temperature=0.6, timeout=90.0)
        if not res.get("success"):
            return {"success": False, "error": res.get("error", "AI request failed")}

        raw = res.get("text", "")
        data = self._extract_json_object(raw)
        if data is None:
            return {"success": False,
                    "error": "The AI response could not be parsed as JSON.",
                    "raw": raw[:1200]}

        try:
            plan = self._normalize_quest_plan(kind, data)
        except Exception as e:
            return {"success": False, "error": f"Could not build plan: {e}",
                    "raw": raw[:1200]}
        plan.update({"success": True, "error": None})
        return plan

    def _extract_json_object(self, text: str):
        """Best-effort extraction of the first JSON object from an LLM reply
        (tolerates ```json fences and trailing prose)."""
        if not text:
            return None
        cleaned = re.sub(r'```(?:json)?', '', text, flags=re.IGNORECASE).replace('```', '').strip()
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start < 0 or end <= start:
            return None
        try:
            return json.loads(cleaned[start:end + 1])
        except Exception:
            return None

    def _build_quest_plan_system_prompt(self, kind: str) -> str:
        """System prompt instructing the model to emit structured JSON params.
        Encodes the app's default rules (blank reward unless asked, XP/Lum off
        unless asked, random creature types unless specified, creative fill)."""
        types = ", ".join(t.split(' (')[0] for t in self._CREATURE_TYPES)
        rules = (
            "You convert a content builder's request into JSON parameters for an "
            "Asheron's Call quest generator. Follow every rule exactly.\n\n"
            "OUTPUT: Return ONLY one JSON object — no prose, no markdown, no code fences.\n\n"
            "CREATIVITY — whenever a detail is not given, invent a good one in "
            "Asheron's Call style. Be evocative, never generic:\n"
            "- Creature NAMES must be distinctive proper names, NEVER the bare type word. "
            "Do not name a creature \"Mite\", \"Lugian\", \"Mosswart\", or \"Undead\". "
            "Build an epithet + noun (optionally a rank/title). Examples: "
            "Mite -> \"Gloomfang Skitterling\"; Lugian -> \"Ironbrow Marauder\"; "
            "Mosswart -> \"Bogrot Witchdoctor\"; Undead -> \"Ashen Revenant\"; "
            "Golem -> \"Riftborn Sentinel\"; Tumerok -> \"Crimson Warband Reaver\"; "
            "Virindi -> \"Whispering Arbiter\". Every creature gets its OWN distinct name.\n"
            "- NPC names have character: a name plus a fitting title or epithet, e.g. "
            "\"Ulgrim the Unpleasant\", \"Nantesa, Keeper of Relics\", \"Sergeant Boruq\".\n"
            "- ITEM names are flavorful and specific (\"Sealed Tumerok War-Missive\", "
            "not \"Quest Item\").\n"
            "- PERSONALITIES/descriptions are a short vivid phrase (\"gruff, battle-scarred "
            "veteran\"; \"nervous archivist who hoards secrets\").\n\n"
            "CREATURE TYPES: only use names from this list; if the user does not specify, "
            "pick a DIFFERENT fitting type for each creature: " + types + ".\n\n"
            "REWARDS default to OFF unless the user asks:\n"
            "- No reward item mentioned -> leave reward item fields blank.\n"
            "- No XP mentioned -> reward_xp 0, omit xp_type.\n"
            "- No Luminance mentioned -> reward_luminance 0.\n\n"
            "XP AWARD TYPE — infer it from the wording:\n"
            "- A flat XP number (\"5 million xp\") -> xp_type \"AwardXP\", reward_xp = that number.\n"
            "- \"unshared\"/\"no share\"/\"per player\" XP -> xp_type \"AwardNoShareXP\", reward_xp = number.\n"
            "- A PERCENTAGE or \"level proportional\" XP (\"25%\", \"0.25\", \"scale to level\") -> "
            "xp_type \"AwardLevelProportionalXP\" and xp_percent as a DECIMAL (25% -> 0.25); "
            "in this case DO NOT set a flat reward_xp.\n"
        )
        if kind == 'kill_task':
            return rules + (
                "\nTASK: Build one or more KILL TASK quests (one per creature requested; "
                "default 1). Use the item-giver method unless the user clearly wants an NPC "
                "giver. Return JSON of this exact shape:\n"
                "{\n"
                '  "shared": { "repeat_hours": 20 },\n'
                '  "tasks": [\n'
                "    {\n"
                '      "creature_name": "distinctive proper name (NOT the type word)",\n'
                '      "creature_type": "one type name from the list",\n'
                '      "creature_level": 150,\n'
                '      "kill_count": 25,\n'
                '      "spawn_count": 5,                // creatures the generator spawns at once\n'
                '      "giver": "item",                 // "item" or "npc"\n'
                '      "item_name": "giver item name (if giver=item)",\n'
                '      "npc_name": "giver NPC name (if giver=npc)",\n'
                '      "npc_description": "giver personality (optional)",\n'
                '      "loot_tier": "None",             // None or T4..T8\n'
                '      "reward_item": "",               // blank unless user asked\n'
                '      "reward_xp": 0,                  // flat XP; 0 unless asked\n'
                '      "xp_type": "AwardXP",            // AwardXP | AwardNoShareXP | AwardLevelProportionalXP\n'
                '      "xp_percent": 0,                 // DECIMAL, only for AwardLevelProportionalXP (0.25 = 25%)\n'
                '      "reward_luminance": 0            // 0 unless asked\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "PER-TASK VALUES ARE INDEPENDENT. creature_level, kill_count, spawn_count, "
                "loot_tier, xp_percent (or reward_xp), and reward_luminance belong to EACH "
                "task separately — put them ON EACH TASK, never only in \"shared\". When the "
                "user describes groups of tasks with different stats, every task in a group "
                "repeats that group's exact numbers, and different groups keep DIFFERENT "
                "numbers. Do not copy one group's values onto another. This includes "
                "loot_tier: a tier stated for ONE group applies to that group ONLY — every "
                "other group stays \"None\" unless the user gave it a tier too.\n"
                "EXAMPLE — \"3 tasks at level 275, 15% xp, 25000 luminance, kill 50, spawn 5, "
                "loot tier 8; then 3 at level 350, 25% xp, 50000 luminance, kill 1, spawn 1\" "
                "-> 6 tasks: the first three each have creature_level 275, xp_percent 0.15, "
                "reward_luminance 25000, kill_count 50, spawn_count 5, loot_tier \"T8\"; the "
                "next three each have creature_level 350, xp_percent 0.25, reward_luminance "
                "50000, kill_count 1, spawn_count 1, loot_tier \"None\" (no tier was stated "
                "for them).\n\n"
                "NAMING: If the user says the giver items are called e.g. \"Commissions\", set "
                'each item_name to "<Creature Name> Commission".'
            )
        if kind == 'item_turnin':
            return rules + (
                "\nTASK: Build one ITEM TURN-IN quest (collect an item, hand it to an NPC).\n"
                "Return JSON with these fields (omit or blank any not implied):\n"
                "{\n"
                '  "quest_prefix": "ShortNoSpaces",\n'
                '  "npc_name": "quest giver NPC (with a title/epithet)",\n'
                '  "npc_description": "vivid personality phrase",\n'
                '  "item_name": "flavorful item to collect",\n'
                '  "item_description": "one-line lore",\n'
                '  "multi_item_count": 1,\n'
                '  "item_drop_creature": "distinctive creature that drops it (optional)",\n'
                '  "item_drop_creature_type": "type name (optional)",\n'
                '  "item_drop_level": 150,\n'
                '  "item_drop_loot_tier": "None",\n'
                '  "reward_xp": 0,                  // flat XP; 0 unless asked\n'
                '  "xp_type": "AwardXP",            // AwardXP | AwardNoShareXP | AwardLevelProportionalXP\n'
                '  "xp_percent": 0,                 // DECIMAL, only for AwardLevelProportionalXP\n'
                '  "reward_luminance": 0,           // 0 unless asked\n'
                '  "reward_pyreals": 0,\n'
                '  "repeat_hours": 20,\n'
                '  "reward_item_name": "",          // blank unless user asked\n'
                '  "reward_item_description": ""\n'
                "}"
            )
        # delivery
        return rules + (
            "\nTASK: Build one DELIVERY quest (carry an item from NPC A to NPC B, "
            "optionally chaining to C and D).\n"
            "Return JSON with these fields (omit NPC C/D unless a longer chain is implied):\n"
            "{\n"
            '  "quest_prefix": "ShortNoSpaces",\n'
            '  "item_name": "flavorful item to carry",\n'
            '  "item_description": "one-line lore",\n'
            '  "item_count": 1,\n'
            '  "npc_a_name": "quest giver (with title/epithet)",\n'
            '  "npc_a_description": "vivid personality phrase",\n'
            '  "npc_b_name": "recipient (with title/epithet)",\n'
            '  "npc_b_description": "vivid personality phrase",\n'
            '  "npc_c_name": "",\n'
            '  "npc_d_name": "",\n'
            '  "reward_xp": 0,                  // flat XP; 0 unless asked\n'
            '  "xp_type": "AwardXP",            // AwardXP | AwardNoShareXP | AwardLevelProportionalXP\n'
            '  "xp_percent": 0,                 // DECIMAL, only for AwardLevelProportionalXP\n'
            '  "reward_luminance": 0,           // 0 unless asked\n'
            '  "reward_pyreals": 0,\n'
            '  "repeat_hours": 20\n'
            "}"
        )

    @staticmethod
    def _xp_plan(src: dict) -> dict:
        """Resolve XP-reward fields from a dict of LLM values.

        Distinguishes a flat XP award from a level-proportional (percentage) one,
        and normalizes the award type. Returns:
          {use:'yes'|'no', xp_type, reward_xp:str, xp_percent:str}
        """
        def _amt(v):
            try: return int(float(str(v).strip() or 0))
            except Exception: return 0
        def _pct(v):
            try: return float(str(v).strip() or 0)
            except Exception: return 0.0
        raw_type = str(src.get('xp_type') or '').strip().lower()
        pct = _pct(src.get('xp_percent'))
        if pct > 1:                      # "25" meaning 25% -> 0.25
            pct = pct / 100.0
        flat = _amt(src.get('reward_xp'))
        proportional = ('proportion' in raw_type or 'level' in raw_type or pct > 0)
        noshare = ('noshare' in raw_type or 'no share' in raw_type
                   or 'no-share' in raw_type or 'unshared' in raw_type)
        if proportional:
            if pct <= 0:
                pct = 0.25
            return {"use": "yes", "xp_type": "AwardLevelProportionalXP",
                    "reward_xp": "", "xp_percent": f"{pct:g}"}
        if flat > 0:
            return {"use": "yes",
                    "xp_type": "AwardNoShareXP" if noshare else "AwardXP",
                    "reward_xp": str(flat), "xp_percent": ""}
        return {"use": "no", "xp_type": "AwardXP", "reward_xp": "", "xp_percent": ""}

    def _normalize_quest_plan(self, kind: str, data: dict) -> dict:
        """Convert the LLM's JSON into the exact shape the frontend forms load."""
        def _amt(v):
            try:
                n = int(float(str(v).strip() or 0)); return n
            except Exception:
                return 0
        def _prefix(name: str, suffix: str) -> str:
            return re.sub(r'[^A-Za-z0-9]', '', str(name or '')) + suffix

        if kind == 'kill_task':
            shared_in = data.get('shared') or {}
            tasks = data.get('tasks') or data.get('rows') or []
            if isinstance(tasks, dict):
                tasks = list(tasks.values())
            tasks = [t for t in tasks if isinstance(t, dict)]
            if not tasks:
                raise ValueError("no tasks produced")

            # Resolve XP per task (shared XP hints apply to any task that omits them).
            xp_per = [self._xp_plan({**shared_in, **t}) for t in tasks]
            xp_types = [x["xp_type"] for x in xp_per if x["use"] == "yes"]
            if any(x == "AwardLevelProportionalXP" for x in xp_types):
                shared_xp_type = "AwardLevelProportionalXP"
            elif any(x == "AwardNoShareXP" for x in xp_types):
                shared_xp_type = "AwardNoShareXP"
            else:
                shared_xp_type = "AwardXP"
            any_xp = any(x["use"] == "yes" for x in xp_per)
            proportional = (shared_xp_type == "AwardLevelProportionalXP")

            rows = []
            any_lum = False
            for t, xp in zip(tasks, xp_per):
                cname = str(t.get('creature_name') or '').strip() or 'Unknown Creature'
                giver = str(t.get('giver') or 'item').strip().lower()
                giver = 'npc' if giver == 'npc' else 'item'
                rlum = _amt(t.get('reward_luminance'))
                any_lum = any_lum or rlum > 0
                # Batch form: one shared xp_type; per-row reward_xp or xp_percent.
                row_xp = '' if proportional else xp["reward_xp"]
                row_pct = (xp["xp_percent"] or '0.25') if proportional else '0.25'
                rows.append({
                    "prefix": _prefix(cname, "KT"),
                    "giver_type": giver,
                    "item_name": str(t.get('item_name') or '').strip(),
                    "npc_name": str(t.get('npc_name') or '').strip(),
                    "npc_description": str(t.get('npc_description') or '').strip(),
                    "creature_name": cname,
                    "creature_type": self._ct_label(t.get('creature_type')) or 'Tumerok (6)',
                    "creature_level": str(_amt(t.get('creature_level')) or 150),
                    "kill_count": str(_amt(t.get('kill_count')) or 25),
                    "spawn_count": str(_amt(t.get('spawn_count')) or 5),
                    "loot_tier": self._lt_label(t.get('loot_tier')),
                    "reward_xp": row_xp,
                    "xp_percent": row_pct,
                    "reward_luminance": str(rlum) if rlum > 0 else '',
                    "reward_name": str(t.get('reward_item') or '').strip(),
                    "reward_wcid": '',
                })
            shared = {
                "repeat_hours": str(_amt(shared_in.get('repeat_hours')) or 20),
                "xp_type": shared_xp_type,
                "use_reward_xp": "yes" if any_xp else "no",
                "use_reward_lum": "yes" if any_lum else "no",
            }
            return {"kind": "batch_kill_task", "shared": shared, "rows": rows,
                    "notes": f"{len(rows)} kill task(s) drafted — review and Generate."}

        # Simple single-form templates (item_turnin / delivery)
        form = {}
        def put(fid, val):
            v = str(val).strip() if val is not None else ''
            if v:
                form[fid] = v

        # Shared XP + Luminance handling for both simple templates.
        xp = self._xp_plan(data)
        toggles = {"use_reward_xp": xp["use"]}
        if xp["use"] == "yes":
            put('xp_type', xp["xp_type"])          # set BEFORE amount so the
            if xp["reward_xp"]:                     # right field is visible for
                put('reward_xp', xp["reward_xp"])   # collection (showWhen).
            if xp["xp_percent"]:
                put('xp_percent', xp["xp_percent"])
        rlum = _amt(data.get('reward_luminance'))
        if rlum > 0:
            toggles["use_reward_lum"] = "yes"
            put('reward_luminance', rlum)

        if kind == 'item_turnin':
            name = data.get('npc_name') or data.get('item_name') or 'Quest'
            put('quest_prefix', data.get('quest_prefix') or _prefix(name, 'Quest'))
            for fid in ('npc_name', 'npc_description', 'item_name',
                        'item_description', 'multi_item_count',
                        'item_drop_creature', 'item_drop_level',
                        'reward_pyreals', 'repeat_hours',
                        'reward_item_name', 'reward_item_description'):
                put(fid, data.get(fid))
            ct = self._ct_label(data.get('item_drop_creature_type'))
            if ct:
                put('item_drop_creature_type', ct)
            lt = data.get('item_drop_loot_tier')
            if lt:
                put('item_drop_loot_tier', self._lt_label(lt))
            return {"kind": "item_turnin", "form": form, "toggles": toggles,
                    "notes": "Turn-in quest drafted — review and Generate."}

        # delivery
        put('quest_prefix', data.get('quest_prefix') or _prefix(
            data.get('item_name') or 'Delivery', 'Run'))
        for fid in ('item_name', 'item_description', 'item_count',
                    'npc_a_name', 'npc_a_description', 'npc_b_name',
                    'npc_b_description', 'npc_c_name', 'npc_c_description',
                    'npc_d_name', 'reward_pyreals', 'repeat_hours'):
            put(fid, data.get(fid))
        return {"kind": "delivery", "form": form, "toggles": toggles,
                "notes": "Delivery quest drafted — review and Generate."}

    # Dialogue action types whose `message` text should be rewritten in the
    # NPC's personality. Other emote actions (Give, AwardLuminance, Goto,
    # etc.) are structural and never touched.
    _DIALOGUE_TYPES = ("Tell", "DirectBroadcast", "LocalBroadcast",
                        "WorldBroadcast", "Say", "FellowBroadcast")

    def _ai_generate_sync(self, system_prompt: str, user_prompt: str,
                           temperature: float = 0.7, timeout: float = 60.0) -> dict:
        """Blocking wrapper around APIClient.stream_generate for a single
        request/response call (no live UI streaming needed here)."""
        import threading
        done = threading.Event()
        result = {"text": "", "error": None}

        def on_chunk(_chunk): pass
        def on_done(full_text):
            result["text"] = full_text
            done.set()
        def on_error(msg):
            result["error"] = msg
            done.set()

        self.api_client.stream_generate(
            system_prompt, user_prompt, on_chunk, on_done, on_error, temperature
        )
        done.wait(timeout)
        if not done.is_set():
            return {"success": False, "error": "AI request timed out", "text": ""}
        if result["error"]:
            return {"success": False, "error": result["error"], "text": ""}
        return {"success": True, "error": None, "text": result["text"]}

    def _rewrite_dialogue_with_ai(self, files: list, params: dict) -> list:
        """
        Extract every Tell/Broadcast/Say message across all generated files,
        grouped by which NPC speaks them (matched via the generated filename
        slug), and send everything to the AI in one combined batched request
        — each NPC's lines are clearly delineated with that NPC's stated
        personality, so a multi-NPC template (e.g. Delivery's NPC A/B/C/D)
        gets each voice rewritten distinctly in a single call. Every other
        line (WCIDs, quest flags, structure) is untouched. On any failure,
        returns `files` unmodified so the quest still generates with its
        original templated dialogue.
        """
        import re, json as _json

        # QuestForge's "AI-Written Dialogue" toggle. Absent means on, so the
        # default stays "rewrite whenever a personality was supplied" — the UI
        # only sends this key when the user explicitly opts out, in which case
        # every NPC keeps its fast, generic templated dialogue.
        if str(params.get("use_ai_dialogue", "yes")).strip().lower() in ("no", "false", "0"):
            return files

        def _slug(name: str) -> str:
            return re.sub(r'[^a-z0-9]+', '_', (name or '').lower()).strip('_')

        # Discover every NPC name/personality pair present in params:
        # single-NPC templates use npc_name/npc_description; Delivery uses
        # npc_a_name/npc_a_description through npc_d_name/npc_d_description.
        npc_pairs = []  # [(name, personality)]
        if params.get("npc_name"):
            npc_pairs.append((params["npc_name"], (params.get("npc_description") or "").strip()))
        for letter in ("a", "b", "c", "d"):
            name = params.get(f"npc_{letter}_name")
            if name:
                npc_pairs.append((name, (params.get(f"npc_{letter}_description") or "").strip()))

        # Only NPCs with a personality given are worth an AI rewrite — others
        # keep their templated dialogue exactly as-is.
        npc_pairs = [(n, p) for (n, p) in npc_pairs if p]
        if not npc_pairs:
            return files

        msg_pattern = re.compile(
            r"(/\*\s*(?:" + "|".join(self._DIALOGUE_TYPES) + r")\s*\*/"
            r"\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*(?:NULL|0x[0-9A-Fa-f]+|\d+)\s*,\s*)'((?:[^']|'')*)'",
            re.IGNORECASE,
        )

        def _unescape(s):  return s.replace("''", "'")
        def _escape(s):    return s.replace("'", "''")

        # Match each NPC-type file to its (name, personality) pair via the
        # slugified name embedded in the generated filename. Both sides must be
        # slugified: filenames are "800023 Test Giver.sql" (spaces) while _slug
        # yields "test_giver" (underscores), so comparing a slug against the raw
        # lowercased filename never matched and silently disabled every rewrite.
        file_to_npc = {}  # file_idx -> (name, personality)
        for fi, f in enumerate(files):
            if f.get("type") != "npc":
                continue
            fname_slug = _slug(f["filename"])
            for name, personality in npc_pairs:
                if _slug(name) and _slug(name) in fname_slug:
                    file_to_npc[fi] = (name, personality)
                    break

        if not file_to_npc:
            return files  # couldn't confidently match any file to an NPC

        # Collect every dialogue line, grouped by NPC, preserving per-file
        # document order so the splice-back can match occurrences correctly.
        groups = []  # [{npc_name, personality, lines: [{file_idx, original}]}]
        group_by_npc = {}
        for fi, (name, personality) in file_to_npc.items():
            for m in msg_pattern.finditer(files[fi]["sql"]):
                original = _unescape(m.group(2))
                if not original.strip():
                    continue
                if name not in group_by_npc:
                    group_by_npc[name] = {"npc_name": name, "personality": personality, "lines": []}
                    groups.append(group_by_npc[name])
                group_by_npc[name]["lines"].append({"file_idx": fi, "original": original})

        groups = [g for g in groups if g["lines"]]
        if not groups:
            return files

        # Build one combined prompt covering every NPC's lines, clearly
        # delineated so the model applies the right voice to each group.
        prompt_sections = []
        flat_lines = []  # global order, matches the flat JSON array we expect back
        n = 0
        for g in groups:
            prompt_sections.append(f"\n--- NPC: {g['npc_name']} (personality: {g['personality']}) ---")
            for l in g["lines"]:
                n += 1
                prompt_sections.append(f"{n}. {l['original']}")
                flat_lines.append(l)

        system_prompt = (
            "You rewrite Asheron's Call NPC dialogue lines to match each "
            "NPC's stated personality. You will receive dialogue grouped by "
            "NPC, each group labeled with that NPC's name and personality. "
            "Rewrite each numbered line in its own NPC's voice, keeping the "
            "same meaning, similar length, and any game mechanics/numbers/"
            "item names mentioned exactly as given — only tone and phrasing "
            "should change. Reply with ONLY a JSON array of strings, one per "
            "numbered line in the SAME GLOBAL ORDER as given (ignore the "
            "per-NPC grouping when forming the output array — it's just for "
            "your reference). No other text, no markdown fences."
        )
        user_prompt = "Lines to rewrite:\n" + "\n".join(prompt_sections)

        result = self._ai_generate_sync(system_prompt, user_prompt, temperature=0.8)
        if not result["success"]:
            return files  # silent fallback to templated dialogue

        try:
            raw = result["text"].strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            rewritten = _json.loads(raw)
            if not isinstance(rewritten, list) or len(rewritten) != len(flat_lines):
                return files  # shape mismatch — don't risk a bad splice
        except Exception:
            return files  # unparseable — silent fallback

        # Splice rewrites back in per-file, in original document order, so a
        # repeated line maps to its correct occurrence.
        per_file_replacements = {}
        for line, new_text in zip(flat_lines, rewritten):
            if not isinstance(new_text, str) or not new_text.strip():
                continue
            per_file_replacements.setdefault(line["file_idx"], []).append(
                (line["original"], new_text)
            )

        for fi, repls in per_file_replacements.items():
            sql = files[fi]["sql"]
            for original, new_text in repls:
                old_escaped = _escape(original)
                new_escaped = _escape(new_text)
                sql = sql.replace(f"'{old_escaped}'", f"'{new_escaped}'", 1)
            files[fi]["sql"] = sql

        return files

    def _enrich_item_descriptions(self, params: dict) -> dict:
        """
        Scan all reward_N_desc and ms_stageN_reward_M_desc fields.
        If a description contains emote trigger keywords (Use, Wield, Unwield,
        Pickup, Drop), append a structured hint so the AI generates the
        correct WeenieFab emote YAML for that item.
        """
        import re
        EMOTE_KEYWORDS = {
            r'\bon\s+use\b':      'Use',
            r'\bon\s+wield\b':    'Wield',
            r'\bon\s+unwield\b':  'Unwield',
            r'\bon\s+pickup\b':   'Pickup',
            r'\bon\s+drop\b':     'Drop',
            r'\bwhen\s+used\b':   'Use',
            r'\bwhen\s+wielded\b':'Wield',
            r'\bwhen\s+picked\b': 'Pickup',
            r'\bwhen\s+dropped\b':'Drop',
        }
        EMOTE_HINT = (
            ' [ACE EMOTE REQUIRED: Generate a WeenieFab emote YAML block '
            'for trigger {trigger} that implements: {action}. '
            'Use valid ACE emote actions: AwardXP, AwardLuminance, CastSpell, '
            'Tell, Give, TakeItems, DestroyInventoryItem, InqIntStat, InqBoolStat, '
            'SetIntStat, Motion, Sound, Spawn, FinishBarber, or compound sequences. '
            'Output the emote block appended after the item SQL.]'
        )
        enriched = dict(params)
        for key, val in params.items():
            if not key.endswith('_desc') or not isinstance(val, str):
                continue
            val_lower = val.lower()
            for pattern, trigger in EMOTE_KEYWORDS.items():
                if re.search(pattern, val_lower):
                    hint = EMOTE_HINT.format(trigger=trigger, action=val)
                    if hint not in val:
                        enriched[key] = val + hint
                    break  # one hint per item
        return enriched

    def save_quest_file(self, filename: str, sql: str) -> dict:
        """Save a single quest template output file."""
        return self._save_single_file(sql, filename)

    def set_groq_base_url(self) -> dict:
        """Pre-configure the Groq base URL in config — called when user selects Groq provider."""
        self.config.set('base_url', GROQ_BASE_URL)
        return {'ok': True, 'url': GROQ_BASE_URL}

    def download_and_install_update(self, download_url: str) -> dict:
        """
        Download the new release zip, extract it, write a batch installer to
        TEMP, then use Win32 ShellExecuteW("runas") to launch it elevated and
        exit the current process so the batch can overwrite the running exe.

        Previous approaches failed because:
        - PowerShell -NonInteractive blocks UAC dialogs entirely
        - DETACHED_PROCESS disconnects from the desktop session UAC needs
        - The copy-success check used exe existence (always true) not a new file
        The fix uses ctypes ShellExecuteW which is the native Win32 elevation
        path — reliable from PyInstaller bundles, no PowerShell dependency.
        """
        import urllib.request, zipfile, shutil, sys, os, subprocess, threading, time
        from pathlib import Path

        if not download_url:
            return {"success": False, "error": "No download URL provided"}

        try:
            # ── Paths ─────────────────────────────────────────────────────────
            if hasattr(sys, "_MEIPASS"):
                install_root = Path(sys.executable).parent
                exe_path     = Path(sys.executable)
            else:
                install_root = Path(__file__).parent.parent
                exe_path     = Path(sys.executable)

            tmp_zip  = Path(os.environ.get("TEMP", str(Path.home()))) / "ACEForge_update.zip"
            tmp_dir  = Path(os.environ.get("TEMP", str(Path.home()))) / "ACEForge_update_extract"
            bat_path = Path(os.environ.get("TEMP", str(Path.home()))) / "aceforge_update.bat"
            log_path = Path(os.environ.get("TEMP", str(Path.home()))) / "aceforge_update.log"

            # ── Download ──────────────────────────────────────────────────────
            self._ollama_event("download_start", "Downloading update...", 0, 0)

            def on_progress(block, block_size, total):
                if total > 0:
                    pct = min(100, int(block * block_size * 100 / total))
                    mb  = round(block * block_size / 1024 / 1024, 1)
                    mbt = round(total / 1024 / 1024, 1)
                    self._ollama_event("download_progress",
                        "Downloading update... {} MB / {} MB".format(mb, mbt), pct, 100)

            urllib.request.urlretrieve(download_url, str(tmp_zip), on_progress)
            self._ollama_event("download_done", "Download complete. Preparing installer...", 100, 100)

            # ── Extract ───────────────────────────────────────────────────────
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(tmp_dir)
            tmp_zip.unlink(missing_ok=True)

            # Release zip is flat (ACEForge.exe, README.md, VERSION.txt at root).
            # If exactly one subdirectory exists (source zip layout), use it.
            subdirs = [tmp_dir / d for d in os.listdir(tmp_dir)
                       if (tmp_dir / d).is_dir()]
            src_root = subdirs[0] if len(subdirs) == 1 else tmp_dir

            # ── Verify the exe is in src_root before writing the bat ──────────
            src_exe = src_root / exe_path.name
            if not src_exe.exists():
                # Try one level deeper
                deeper = [src_root / d / exe_path.name
                          for d in os.listdir(src_root)
                          if (src_root / d).is_dir()]
                found  = [p for p in deeper if p.exists()]
                if found:
                    src_root = found[0].parent
                else:
                    return {"success": False,
                            "error": "Could not find {} in downloaded zip.".format(exe_path.name)}

            # ── Write batch script ────────────────────────────────────────────
            pid       = os.getpid()
            install_q = str(install_root).replace("/", "\\")
            src_q     = str(src_root).replace("/", "\\")
            tmp_dir_q = str(tmp_dir).replace("/", "\\")
            exe_q     = str(exe_path).replace("/", "\\")
            log_q     = str(log_path).replace("/", "\\")

            lines = []
            lines.append("@echo off")
            lines.append("setlocal enabledelayedexpansion")
            lines.append('echo [%TIME%] ACEForge updater started >> "{}"'.format(log_q))
            lines.append('echo [%TIME%] PID to wait for: {} >> "{}"'.format(pid, log_q))
            lines.append('echo [%TIME%] Source: {} >> "{}"'.format(src_q, log_q))
            lines.append('echo [%TIME%] Destination: {} >> "{}"'.format(install_q, log_q))

            # Wait for the PID to exit
            lines.append(":waitpid")
            lines.append('tasklist /FI "PID eq {}" 2>NUL | find "{}" >NUL'.format(pid, pid))
            lines.append("if errorlevel 1 goto waitpiddone")
            lines.append("timeout /t 1 /nobreak >NUL")
            lines.append("goto waitpid")
            lines.append(":waitpiddone")
            lines.append('echo [%TIME%] PID {} gone >> "{}"'.format(pid, log_q))

            # Wait for image name to clear (PyInstaller bootloader cleanup)
            lines.append("timeout /t 2 /nobreak >NUL")
            lines.append(":waitimg")
            lines.append('tasklist /FI "IMAGENAME eq {}" 2>NUL | find /I "{}" >NUL'.format(
                exe_path.name, exe_path.name))
            lines.append("if errorlevel 1 goto waitimgdone")
            lines.append("timeout /t 1 /nobreak >NUL")
            lines.append("goto waitimg")
            lines.append(":waitimgdone")
            lines.append('echo [%TIME%] Image cleared >> "{}"'.format(log_q))

            # Copy — robocopy 0-7 = success/informational, 8+ = error
            lines.append("set TRIES=0")
            lines.append(":copyloop")
            lines.append("set /a TRIES+=1")
            lines.append('echo [%TIME%] Copy attempt %TRIES% >> "{}"'.format(log_q))
            lines.append('robocopy "{}" "{}" /E /IS /IT /IM /NFL /NDL /NJH /NJS'.format(
                src_q, install_q))
            lines.append("set RC=%ERRORLEVEL%")
            lines.append('echo [%TIME%] robocopy exit %RC% >> "{}"'.format(log_q))
            # robocopy 0-7 = ok
            lines.append("if %RC% LEQ 7 goto copydone")
            # robocopy failed — xcopy fallback
            lines.append('echo [%TIME%] robocopy failed, trying xcopy >> "{}"'.format(log_q))
            lines.append('xcopy /E /Y /I "{}\\*" "{}\\"\n'.format(src_q, install_q))
            lines.append(":copydone")

            # Verify: VERSION.txt is a new file that only lands after a real copy
            lines.append('if exist "{}\\VERSION.txt" goto verified'.format(install_q))
            lines.append("if %TRIES% GEQ 5 goto giveup")
            lines.append('echo [%TIME%] VERSION.txt not found, retry >> "{}"'.format(log_q))
            lines.append("timeout /t 2 /nobreak >NUL")
            lines.append("goto copyloop")

            lines.append(":giveup")
            lines.append('echo [%TIME%] Copy failed after 5 attempts >> "{}"'.format(log_q))
            lines.append("goto relaunch")

            lines.append(":verified")
            lines.append('echo [%TIME%] Copy verified OK >> "{}"'.format(log_q))

            # Relaunch then cleanup
            lines.append(":relaunch")
            lines.append('echo [%TIME%] Relaunching {} >> "{}"'.format(exe_path.name, log_q))
            lines.append('start "" "{}"'.format(exe_q))
            lines.append('rd /s /q "{}" 2>NUL'.format(tmp_dir_q))
            lines.append('del "%~f0"')

            bat_text = "\r\n".join(lines)
            bat_path.write_text(
                bat_text.encode("ascii", errors="replace").decode("ascii"),
                encoding="ascii"
            )

            # ── Signal UI ─────────────────────────────────────────────────────
            self._ollama_event("download_done",
                "Update downloaded. ACEForge will now close and restart with the new version.",
                100, 100)

            # ── Launch batch + exit ───────────────────────────────────────────
            # Use Win32 ShellExecuteW with "runas" verb for elevation.
            # This is the native Windows UAC path — works from PyInstaller
            # bundles, doesn't need PowerShell, shows UAC on the correct desktop.
            # SW_HIDE = 0 keeps the cmd window hidden.
            #
            # If already elevated (ran as admin), ShellExecuteW("runas") still
            # works — it just skips the UAC prompt.
            #
            # We use a non-daemon thread so the thread survives even if the
            # webview main thread exits before the sleep finishes.
            def _launch_and_exit():
                time.sleep(0.8)  # let the UI event render
                try:
                    import ctypes
                    SW_HIDE = 0
                    ctypes.windll.shell32.ShellExecuteW(
                        None,           # hwnd
                        "runas",        # verb — triggers UAC elevation
                        "cmd.exe",      # file
                        '/c "{}"'.format(str(bat_path)),  # params
                        None,           # working dir (use cwd)
                        SW_HIDE,        # nShowCmd — hidden window
                    )
                except Exception:
                    # ctypes not available or not on Windows — fall back to
                    # plain subprocess (no elevation, may fail on Program Files)
                    subprocess.Popen(
                        ["cmd.exe", "/c", str(bat_path)],
                        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                                   | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                    )
                time.sleep(0.3)
                os._exit(0)

            # daemon=False: thread survives main thread exit
            t = threading.Thread(target=_launch_and_exit, daemon=False)
            t.start()
            return {"success": True, "message": "Update ready. Restarting..."}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        """Open a URL in the system default browser."""
        import webbrowser
        webbrowser.open(url)
        return {"success": True}

    def open_output_folder(self) -> dict:
        try:
            path = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
            Path(path).mkdir(parents=True, exist_ok=True)
            os.startfile(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── AI Generation ─────────────────────────────────────────────────────────

    def start_generation(self, prompt: str, content_type: str) -> dict:
        if self._generating:
            return {"success": False, "error": "Already generating."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured. Open Settings and add your API key."}

        self._generating = True
        # Clear any stale chunks from previous run
        while not self._chunk_queue.empty():
            try: self._chunk_queue.get_nowait()
            except: break
        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        # Detect local model — Ollama or compatible with ollama_mode flag
        provider   = self.config.get("provider", "anthropic")
        ollama_mode = self.config.get("ollama_mode", False)
        is_local   = provider == "ollama" or bool(ollama_mode)

        # Extract keywords from prompt and find matching base-game weenies
        try:
            content_type = content_type or "creature"
            weenie_context = self._build_weenie_context(prompt, content_type)
            system_prompt = self.skill_loader.build_system_prompt(
                content_type=content_type,
                server_name=self.config.server_name,
                wcid_ranges=self.config.get_wcid_ranges(),
                author=self.config.get("author", ""),
                weenie_context=weenie_context,
                is_local=is_local,
                base_wcid_ranges=self.config.get_base_wcid_ranges(),
            )
        except Exception as e:
            self._generating = False
            return {"success": False, "error": f"Prompt build error: {e}"}

        try:
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, prompt, self._on_chunk, self._on_done, self._on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._generating = False
            return {"success": False, "error": f"Failed to start generation: {e}"}
        return {"success": True}

    def _build_weenie_context(self, prompt: str, content_type: str) -> str:
        """
        Search the weenie index for base-game weenies relevant to the prompt.
        Injects 2-4 matching weenie SQL files as format/value references.
        """
        try:
            import re
            # Extract likely creature/item names from the prompt
            # Strip common adjectives and focus on noun phrases
            words = re.findall(r"[A-Za-z][a-z]{2,}", prompt)
            # Filter stop words
            STOP = {"level","high","low","with","that","this","from","into","the",
                    "and","for","has","are","can","will","give","make","create",
                    "drop","loot","kill","quest","named","custom","new","about",
                    "like","some","each","them","item","creature","weapon","armor"}
            keywords = [w for w in words if w.lower() not in STOP]

            # Search for each keyword, collect unique results
            seen_wcids = set()
            results = []
            for kw in keywords[:8]:
                matches = self.skill_loader.search_weenies(kw, max_results=2)
                for m in matches:
                    if m["w"] not in seen_wcids:
                        seen_wcids.add(m["w"])
                        results.append(m)
                if len(results) >= 4:
                    break

            if not results:
                return ""

            # Read and concatenate matching SQL files
            parts = []
            for entry in results[:4]:
                sql = self.skill_loader.get_weenie_sql(entry)
                if sql:
                    parts.append(f"/* WCID {entry['w']} — {entry['n']} ({entry['f'].split('/')[0]}) */")
                    parts.append(sql.strip())
                    parts.append("")

            return "\n".join(parts)
        except Exception:
            return ""

    # ── Ollama Setup & Management ─────────────────────────────────────────────

    def check_ollama(self) -> dict:
        """
        Full Ollama status check. Returns:
          installed  — ollama binary found
          running    — localhost:11434 is responding
          models     — list of locally installed model names
          path       — path to ollama binary (or empty)
          recommended — recommended models with name/size/desc
        """
        import shutil, urllib.request, json as _json, os

        RECOMMENDED = [
            {"id": "qwen2.5-coder:7b",  "label": "Qwen 2.5 Coder 7B",  "size": "4.5 GB",
             "desc": "Best for SQL — trained on structured data and code schemas. Recommended."},
            {"id": "codellama:7b",       "label": "CodeLlama 7B",        "size": "3.8 GB",
             "desc": "Meta's code-focused model. Good SQL, reliable formatting."},
            {"id": "llama3.2:3b",        "label": "Llama 3.2 3B",        "size": "2.0 GB",
             "desc": "Fastest, lowest RAM. Less accurate for complex quest chains."},
        ]

        # Find binary
        path = shutil.which("ollama") or ""
        if not path:
            win_path = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
            )
            if os.path.exists(win_path):
                path = win_path

        installed = bool(path)

        # Check if running
        running = False
        models  = []
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = _json.loads(resp.read())
                running = True
                models  = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

        return {
            "installed":    installed,
            "running":      running,
            "models":       models,
            "path":         path,
            "recommended":  RECOMMENDED,
        }

    def launch_ollama(self) -> dict:
        """Start `ollama serve` as a background subprocess, then wait until ready."""
        import subprocess, time, urllib.request, shutil, os

        path = shutil.which("ollama") or os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
        )
        if not path or not os.path.exists(path):
            return {"success": False, "error": "Ollama binary not found. Please install it first."}

        try:
            # Start silently (no console window on Windows)
            flags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                flags = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(
                [path, "serve"],
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            return {"success": False, "error": str(e)}

        # Poll until ready (up to 15 seconds)
        for _ in range(15):
            time.sleep(1)
            try:
                urllib.request.urlopen("http://localhost:11434/", timeout=1)
                return {"success": True, "message": "Ollama started successfully"}
            except Exception:
                pass

        return {"success": False, "error": "Ollama started but did not respond in time. Try again."}

    def install_ollama(self) -> dict:
        """
        Download OllamaSetup.exe and launch the installer.
        Streams download progress via ollama_progress events.
        """
        import urllib.request, tempfile, os, subprocess

        URL  = "https://ollama.com/download/OllamaSetup.exe"
        dest = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")

        self._ollama_event("download_start", "Downloading Ollama installer…", 0, 0)
        try:
            def on_progress(block, block_size, total):
                if total > 0:
                    pct = min(100, int(block * block_size * 100 / total))
                    mb_done = round(block * block_size / 1024 / 1024, 1)
                    mb_total = round(total / 1024 / 1024, 1)
                    self._ollama_event(
                        "download_progress",
                        f"Downloading Ollama… {mb_done} MB / {mb_total} MB",
                        pct, 100
                    )
            urllib.request.urlretrieve(URL, dest, on_progress)
        except Exception as e:
            return {"success": False, "error": f"Download failed: {e}"}

        self._ollama_event("download_done", "Launching installer…", 100, 100)

        try:
            subprocess.Popen([dest], shell=False)
            return {
                "success": True,
                "message": "Installer launched. Complete installation, then click 'Check Again'."
            }
        except Exception as e:
            return {"success": False, "error": f"Could not launch installer: {e}"}

    def pull_ollama_model(self, model: str) -> dict:
        """
        Run `ollama pull MODEL` and stream progress via ollama_progress events.
        Runs in a background thread so the UI stays responsive.
        """
        import subprocess, threading, re, shutil, os

        path = shutil.which("ollama") or os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
        )
        if not path:
            return {"success": False, "error": "Ollama not found."}

        def _run():
            try:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                proc = subprocess.Popen(
                    [path, "pull", model],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=flags,
                    encoding="utf-8",
                    errors="replace",   # swap undecodable bytes with ? instead of crashing
                )
                last_pct = -1
                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    # Parse: "pulling abc123...  42% ▕███▏  1.8 GB/4.5 GB"
                    m = re.search(r"(\d+)%", line)
                    gb = re.search(r"([\d.]+\s*GB/[\d.]+\s*GB)", line)
                    if m:
                        pct = int(m.group(1))
                        size_label = gb.group(1) if gb else ""
                        if pct != last_pct:
                            last_pct = pct
                            self._ollama_event(
                                "pull_progress",
                                f"Downloading {model}… {size_label or str(pct)+'%'}",
                                pct, 100
                            )
                    elif line:
                        self._ollama_event("pull_status", line, last_pct if last_pct >= 0 else 0, 100)

                proc.wait()
                if proc.returncode == 0:
                    self._ollama_event("pull_done", f"{model} installed and ready", 100, 100)
                    # Auto-configure ACEForge to use this model
                    self.config.set("provider",   "compatible")
                    self.config.set("base_url",   "http://localhost:11434/v1")
                    self.config.set("model",       model)
                    self.config.set("ollama_mode", True)
                    self.config.save()
                    self._ollama_event("auto_configured", model, 100, 100)
                else:
                    self._ollama_event("pull_error", f"Pull failed (exit {proc.returncode})", 0, 100)
            except Exception as e:
                self._ollama_event("pull_error", str(e), 0, 100)

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True, "message": f"Pulling {model} — this may take several minutes…"}

    def _ollama_event(self, event: str, message: str, current: int, total: int):
        """Send an ollama_setup event to the UI."""
        if self._window:
            import json as _json
            payload = _json.dumps({
                "event":   event,
                "message": message,
                "current": current,
                "total":   total,
            })
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('ollama_setup',{{detail:{payload}}}))"
            )

    def _lib_progress(self, message: str, current: int, total: int):
        """Push a library installation progress event to the UI."""
        if self._window:
            import json as _json
            payload = _json.dumps({"message": message, "current": current, "total": total})
            self._window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('lib_progress',{{detail:{payload}}}))"
            )

    def stop_generation(self) -> dict:
        if self._agent_loop:
            self._agent_loop.stop()
        self._generating = False
        return {"success": True}


    # ── Emote Script Post-Processor ───────────────────────────────────────────

    def _process_emote_scripts(self, text: str) -> str:
        """
        Scan AI output for WeenieFab emote blocks and convert them to SQL.

        Marker format (written by AI):
            -- EMOTE SCRIPT (WCID: 850000)
            Use:
                - Tell: Hello!
            -- END EMOTE SCRIPT

        Each block is replaced with the converted SQL in-place.
        Conversion errors are left as SQL comments so the file is still usable.
        """
        import re
        pattern = re.compile(
            r'--\s*EMOTE SCRIPT\s*\(WCID:\s*(\d+)\)\s*\n(.*?)\n\s*--\s*END EMOTE SCRIPT',
            re.DOTALL | re.IGNORECASE,
        )

        def _replace(m: re.Match) -> str:
            wcid   = int(m.group(1))
            script = m.group(2).strip()
            if not script:
                return ''
            try:
                result = parse_emote_text(script, wcid)
                if result['error']:
                    return (
                        f'-- EMOTE CONVERSION ERROR: {result["error"]}\n'
                        f'-- Original script preserved below:\n'
                        + m.group(0)
                    )
                # Prefix with summary comment
                header = (
                    f'-- Emote rows: {result["emote_count"]}  '
                    f'Action rows: {result["action_count"]}\n'
                )
                warnings = ''.join(
                    f'-- WARN: {w}\n' for w in result['warnings']
                )
                return header + warnings + result['sql']
            except Exception as exc:
                return (
                    f'-- EMOTE CONVERSION EXCEPTION: {exc}\n'
                    + m.group(0)
                )

        converted = pattern.sub(_replace, text)
        n_blocks   = len(pattern.findall(text))
        if n_blocks:
            print(f'[EMOTE] converted {n_blocks} emote block(s)', flush=True)
        return converted

    def _on_chunk(self, text: str):
        if not self._generating:
            return
        self._chunk_queue.put({"type": "chunk", "text": text})
        print(f"[API] chunk queued: {len(text)} chars, queue size ~{self._chunk_queue.qsize()}", flush=True)

    def _on_done(self, text: str):
        self._generating = False
        text = self._process_emote_scripts(text)   # convert WeenieFab blocks → SQL
        self._last_ai_response = text              # store full text Python-side (avoid bridge size limit)
        stripped = text.rstrip()
        looks_truncated = bool(stripped) and not any(
            stripped.endswith(s) for s in (";", "*/", "---", "```")
        )
        self._chunk_queue.put({"type": "done", "truncated": looks_truncated})
        print(f"[API] done queued, total chars: {len(text)}", flush=True)

    def _on_error(self, message: str):
        self._generating = False
        self._chunk_queue.put({"type": "error", "message": message})
        print(f"[API] error queued: {message}", flush=True)

    def poll_generation(self) -> dict:
        """Called by JS every 100ms — drains the queue and returns all pending items."""
        items = []
        try:
            while True:
                items.append(self._chunk_queue.get_nowait())
        except queue.Empty:
            pass
        if items:
            print(f"[API] poll returning {len(items)} items", flush=True)
        return {"items": items, "generating": self._generating}



    # ── DAT Loader — 3D model preview ────────────────────────────────────────

    # The AC client DAT set. portal is the only one the 3D preview needs today;
    # the rest (cell=landblocks/terrain, highres=hi-res textures, local=UI
    # strings) are discovered too so future features can use them without any
    # extra wiring. Maps the client filename → the config key its path is cached
    # under.
    _DAT_FILES = {
        "portal":  ("client_portal.dat",        "portal_dat"),
        "cell":    ("client_cell_1.dat",         "cell_dat"),
        "highres": ("client_highres.dat",        "highres_dat"),
        "local":   ("client_local_English.dat",  "local_dat"),
    }

    def _dat_search_folders(self) -> list:
        """Conventional local folders that may hold the DAT set, most-likely
        first. Includes the OneDrive-redirected Documents (Known-Folder-Move)
        and a real client install, which is the canonical retail set."""
        repo_root = Path(__file__).resolve().parent.parent
        folders = [
            repo_root / "dat",
            repo_root / "DAT Files",
            Path.home() / "Documents" / "DAT Files",
            Path.home() / "Documents" / "DAT",
            Path.home() / "Desktop" / "DAT Files",
        ]
        onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
        if onedrive:
            folders.insert(0, Path(onedrive) / "Documents" / "DAT Files")
        # A client install is the authoritative retail set — prefer it over
        # loose copies, which are easy to end up with several of.
        for drive in ("C:", "D:", "E:"):
            folders.insert(0, Path(f"{drive}/Turbine/Asheron's Call"))
        # An explicitly chosen DAT folder (e.g. a custom set built in ACME)
        # outranks every convention.
        chosen = self.config.get("dat_folder", "")
        if chosen:
            folders.insert(0, Path(chosen))
        return folders

    def _resolve_dat(self, which: str = "portal") -> str:
        """Return a usable path for one of the client DAT files.

        Prefers the path configured via Settings, else auto-discovers the file
        in conventional local folders and caches the hit back to config. Every
        folder here is gitignored or outside the repo, so the copyrighted DATs
        (~1.3GB for the full set) are never committed.
        """
        filename, cfg_key = self._DAT_FILES.get(which, self._DAT_FILES["portal"])
        configured = self.config.get(cfg_key, "")
        if configured and Path(configured).exists():
            return configured
        for folder in self._dat_search_folders():
            f = folder / filename
            if f.exists():
                self.config.set(cfg_key, str(f))
                self.config.save()
                return str(f)
        return configured

    def _resolve_portal_dat(self) -> str:
        """Back-compat shim — the 3D preview resolves the portal DAT."""
        return self._resolve_dat("portal")

    def get_dat_status(self) -> dict:
        """Discovery status for the whole DAT set — {key: {configured, path}}."""
        out = {}
        for which, (filename, cfg_key) in self._DAT_FILES.items():
            path = self._resolve_dat(which)
            out[which] = {"filename": filename,
                          "path": path,
                          "configured": bool(path and Path(path).exists())}
        return out

    def browse_portal_dat(self) -> dict:
        """Open a file dialog for the user to locate client_portal.dat."""
        try:
            if self._window is None:
                return {"error": "Window not ready"}
            result = self._window.create_file_dialog(
                dialog_type=10,
                allow_multiple=False,
                file_types=("DAT Files (*.dat)", "All Files (*.*)")
            )
            if not result:
                return {"cancelled": True}
            path = result[0] if isinstance(result, (list, tuple)) else result
            return {"path": str(path)}
        except Exception:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw()
                path = filedialog.askopenfilename(
                    title="Select client_portal.dat",
                    filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
                )
                root.destroy()
                if not path:
                    return {"cancelled": True}
                return {"path": str(path)}
            except Exception as e2:
                return {"error": str(e2)}

    def set_portal_dat(self, path: str) -> dict:
        """Save the client_portal.dat path to config and verify it opens."""
        try:
            from aceforge.dat_loader import DatDatabase
            db = DatDatabase(path)
            n  = len(db.files_by_type(0x02))
            db.close()
            self.config.set("portal_dat", path)
            self.config.save()
            return {"success": True, "setup_count": n}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_portal_dat_status(self) -> dict:
        """Return the configured DAT path and whether it's valid."""
        path = self._resolve_portal_dat()
        if not path:
            return {"configured": False, "path": ""}
        from pathlib import Path
        exists = Path(path).exists()
        return {"configured": exists, "path": path}

    def get_model_glb(self, setup_id_hex: str, clothing_id_hex: str = "",
                      motion_id_hex: str = "", palette_template: str = "",
                      shade: str = "") -> dict:
        """
        Return a base64-encoded GLB for the given Setup DID (as hex string).
        Uses the cache — extracts from DAT on first request, cached thereafter.
        clothing_id_hex: optional ClothingBase DID (0x10xxxxxx) — armor/clothing
        weenies point their Setup at base body parts; the clothing table swaps
        in the armor models/textures.
        motion_id_hex: optional MotionTable DID (0x09xxxxxx) — bakes the default
        idle animation into the GLB so the viewer can play it.
        Result: {success, data_b64} or {success: False, error}
        """
        import base64, traceback

        def _parse_did(raw):
            # DIDs may be hex ("0x02000001") or decimal ("33554433"). Auto-
            # detect by the 0x prefix rather than assuming base-16.
            s = str(raw).strip()
            if not s:
                return 0
            return int(s, 16) if s.lower().startswith("0x") else int(s, 10)

        try:
            setup_id = _parse_did(setup_id_hex)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid setup ID"}
        try:
            clothing_id = _parse_did(clothing_id_hex)
        except (ValueError, TypeError):
            clothing_id = 0
        try:
            motion_id = _parse_did(motion_id_hex)
        except (ValueError, TypeError):
            motion_id = 0
        # Only ClothingTable (0x10) / MotionTable (0x09) DIDs make sense here
        if clothing_id and (clothing_id >> 24) != 0x10:
            clothing_id = 0
        if motion_id and (motion_id >> 24) != 0x09:
            motion_id = 0
        # PaletteTemplate int + Shade float drive the clothing dye subpalettes
        try:
            pal_tpl = int(str(palette_template).strip() or "0")
        except (ValueError, TypeError):
            pal_tpl = 0
        try:
            shade_f = float(str(shade).strip() or "0")
        except (ValueError, TypeError):
            shade_f = 0.0
        shade_f = min(max(shade_f, 0.0), 1.0)

        from aceforge.dat_loader import (cached_glb_path, DatDatabase,
                                          get_or_export_glb, export_setup_glb,
                                          parse_setup, parse_gfxobj)
        from pathlib import Path

        cached = cached_glb_path(setup_id, clothing_id, motion_id, pal_tpl, shade_f)
        if cached.exists():
            return {"success": True,
                    "data_b64": base64.b64encode(cached.read_bytes()).decode()}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}

        try:
            db = DatDatabase(path)

            # ── Diagnostics ───────────────────────────────────────────────────
            total_setups  = len(db.files_by_type(0x02))
            total_gfxobjs = len(db.files_by_type(0x01))
            in_index      = setup_id in db.entries
            # Include block_size — if wrong, all file reads produce garbage
            entry_info = ""
            if setup_id in db.entries:
                e = db.entries[setup_id]
                entry_info = f"entry: offset={e.file_offset} size={e.file_size}. "
            diag = (f"DAT indexed {len(db.entries)} total entries, "
                    f"{total_setups} setups (0x02), "
                    f"{total_gfxobjs} gfxobjs (0x01). "
                    f"block_size={db.block_size}. "
                    f"dat_type={db.dat_type}. "
                    f"0x{setup_id:08X} in index: {in_index}. "
                    f"{entry_info}")

            raw = db.read_file(setup_id)
            if raw is None:
                db.close()
                return {"success": False,
                        "error": f"Setup 0x{setup_id:08X} not found in DAT. {diag}"}

            setup = parse_setup(raw)
            if setup is None:
                db.close()
                return {"success": False,
                        "error": f"parse_setup returned None for 0x{setup_id:08X}. "
                                 f"Raw data: {len(raw)} bytes, first 32: {raw[:32].hex()}. {diag}"}

            if not setup.parts:
                db.close()
                return {"success": False,
                        "error": f"Setup 0x{setup_id:08X} has 0 parts. "
                                 f"Flags=0x{raw[4]:02X}{raw[5]:02X}{raw[6]:02X}{raw[7]:02X}. {diag}"}

            # Check first GfxObj
            first_gid = setup.parts[0].gfxobj_id
            gfx_raw   = db.read_file(first_gid)
            if gfx_raw is None:
                db.close()
                return {"success": False,
                        "error": f"GfxObj 0x{first_gid:08X} not found (first part of setup). "
                                 f"Setup has {len(setup.parts)} parts. {diag}"}

            try:
                gfx = parse_gfxobj(gfx_raw)
            except Exception as gfx_err:
                db.close()
                return {"success": False,
                        "error": f"parse_gfxobj error for 0x{first_gid:08X}: {gfx_err}. "
                                 f"Raw: {len(gfx_raw)} bytes, b8-64: {gfx_raw[8:64].hex()}"}
            if gfx is None:
                db.close()
                return {"success": False,
                        "error": f"parse_gfxobj returned None for 0x{first_gid:08X}. "
                                 f"Raw: {len(gfx_raw)} bytes, b8-64: {gfx_raw[8:64].hex()}"}

            gfx_diag = (f"GfxObj 0x{first_gid:08X}: "
                        f"{len(gfx.vertices)} verts, {len(gfx.polygons)} polys, "
                        f"{len(gfx.surfaces)} surfaces. ")
            # ── End diagnostics ───────────────────────────────────────────────

            glb_path = get_or_export_glb(db, setup_id, clothing_id, motion_id,
                                         pal_tpl, shade_f)
            db.close()
            if glb_path is None:
                return {"success": False,
                        "error": f"export_setup_glb returned None. {diag}{gfx_diag}"}
            glb_bytes = glb_path.read_bytes()
            return {"success": True,
                    "data_b64": base64.b64encode(glb_bytes).decode(),
                    "info": f"{len(setup.parts)} parts, {gfx_diag}glb={len(glb_bytes)}B"}
        except Exception as e:
            return {"success": False,
                    "error": f"Exception: {e}\n{traceback.format_exc()[-800:]}"}

    # ── Doll: wearable catalog ────────────────────────────────────────────
    # Only armor + clothing. Weapons are deliberately excluded: they hang off
    # attachment points rather than replacing body parts, so they need
    # different handling than a ClothingBase composite.
    _doll_wearables_cache = None

    _EQUIP_SLOT_NAMES = [
        (0x00000001, "Head"),      (0x00000002, "Chest"),
        (0x00000004, "Abdomen"),   (0x00000008, "Upper Arms"),
        (0x00000010, "Lower Arms"), (0x00000020, "Hands"),
        (0x00000040, "Upper Legs"), (0x00000080, "Lower Legs"),
        (0x00000100, "Feet"),      (0x00000200, "Chest"),
        (0x00000400, "Abdomen"),   (0x00000800, "Upper Arms"),
        (0x00001000, "Lower Arms"), (0x00002000, "Upper Legs"),
        (0x00004000, "Lower Legs"), (0x08000000, "Cloak"),
    ]

    def _doll_slot_label(self, valid_locations: int) -> str:
        if not valid_locations:
            return ""
        seen, out = set(), []
        for bit, name in self._EQUIP_SLOT_NAMES:
            if (valid_locations & bit) and name not in seen:
                seen.add(name)
                out.append(name)
        return " / ".join(out[:3])

    def _doll_load_wearables(self):
        if self._doll_wearables_cache is not None:
            return self._doll_wearables_cache
        out = []
        try:
            path = self._gear_resolve_web_path("gear_data", "gear_full.json")
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            for cat in ("armor", "clothing"):
                for r in raw.get(cat, []):
                    cb = (r.get("did") or {}).get("ClothingBase")
                    if not cb:
                        continue          # nothing to map onto a body
                    def _i(key, sec="int"):
                        v = (r.get(sec) or {}).get(key)
                        try:
                            return int(v["value"]) if v else 0
                        except (ValueError, TypeError, KeyError):
                            return 0
                    tl = (r.get("bool") or {}).get("TopLayerPriority")
                    tlv = None
                    if tl is not None:
                        tlv = str(tl.get("value", "")).strip().lower() in ("1", "true")
                    try:
                        shade = float(((r.get("float") or {})
                                       .get("Shade") or {}).get("value") or 0.0)
                    except (ValueError, TypeError):
                        shade = 0.0
                    vl = _i("ValidLocations")
                    out.append({
                        "wcid":              r["wcid"],
                        "name":              ((r.get("string") or {}).get("Name") or {})
                                                .get("value") or r.get("class_name") or "",
                        "class_name":        r.get("class_name") or "",
                        "category":          cat,
                        "clothing_id":       str(cb["value"]),
                        "palette_template":  _i("PaletteTemplate"),
                        "shade":             min(max(shade, 0.0), 1.0),
                        "item_type":         _i("ItemType"),
                        "valid_locations":   vl,
                        "clothing_priority": _i("ClothingPriority"),
                        "top_layer":         tlv,
                        "slot":              self._doll_slot_label(vl),
                    })
        except Exception:
            out = []
        out.sort(key=lambda x: x["name"].lower())
        self._doll_wearables_cache = out
        return out

    def doll_generate_items(self, pieces: list, options: dict) -> dict:
        """Generate editable gear items from the Doll's worn pieces.

        Unlike generate_gear_items — which applies one palette/shade to the
        whole set — each piece keeps the exact PaletteTemplate + Shade it was
        given in the wardrobe, so what was previewed is what gets written.

        pieces: [{wcid, palette_template, shade}, ...] in worn order.
        """
        try:
            data = self._gear_load_data()
            name_prefix = (options or {}).get("name_prefix") or ""
            name_prefix = str(name_prefix).strip()
            try:
                start_wcid = int((options or {}).get("start_wcid") or 0)
            except (ValueError, TypeError):
                start_wcid = 0
            if not start_wcid:
                return {"success": False, "error": "Starting WCID is required.",
                        "items": []}

            items, skipped = [], []
            next_wcid = start_wcid
            for p in (pieces or []):
                try:
                    src_wcid = int((p or {}).get("wcid") or 0)
                except (ValueError, TypeError):
                    src_wcid = 0
                src = data.get(src_wcid)
                if not src:
                    # Pieces seeded from already-generated items have new WCIDs
                    # that aren't in the source catalog — nothing to clone from.
                    skipped.append({"wcid": src_wcid,
                                    "name": (p or {}).get("name") or ""})
                    continue
                orig_name = (src.get("string", {}).get("Name", {}) or {}).get("value", "Item")
                if name_prefix:
                    new_name = f"{name_prefix} {self._gear_piece_type_word(orig_name)}".strip()
                else:
                    new_name = orig_name
                tpl = (p or {}).get("palette_template")
                shade = (p or {}).get("shade")
                item = self._gear_build_item(
                    src, next_wcid, new_name,
                    tpl if tpl not in (None, "") else None,
                    shade if shade not in (None, "") else None,
                    None, None)
                items.append(item)
                next_wcid += 1

            if not items:
                return {"success": False, "items": [], "skipped": skipped,
                        "error": "None of the worn pieces could be generated — "
                                 "they have no source weenie in the catalog."}
            return {"success": True, "items": items, "skipped": skipped,
                    "next_wcid": next_wcid, "error": None}
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "items": [],
                    "traceback": traceback.format_exc()}

    def doll_items_by_wcid(self, wcids: list) -> dict:
        """Look up wearable gear by WCID, preserving the caller's order.

        Lets the Doll seed itself from the set pieces the user has ticked in
        GearForge, before anything has been generated.
        """
        by_wcid = {i["wcid"]: i for i in self._doll_load_wearables()}
        out, missing = [], []
        for w in (wcids or []):
            try:
                k = int(w)
            except (ValueError, TypeError):
                continue
            if k in by_wcid:
                out.append(by_wcid[k])
            else:
                missing.append(k)      # weapon/jewelry or no ClothingBase
        return {"success": True, "items": out, "missing": missing}

    # Everyday words players use for gear AC names differently — searching
    # "chainmail gloves" should find "Chainmail Gauntlets".
    _DOLL_SYNONYMS = {
        "gloves": "gauntlets", "glove": "gauntlets", "mitts": "gauntlets",
        "boots": "sollerets", "boot": "sollerets", "shoes": "shoes",
        "helmet": "helm", "hat": "helm", "cap": "helm",
        "pants": "leggings", "trousers": "leggings",
        "shirt": "shirt", "gloves/gauntlets": "gauntlets",
        "armour": "armor", "vest": "breastplate", "chest": "breastplate",
        "bracer": "bracers", "sleeves": "bracers",
    }

    def doll_search_items(self, query: str = "", limit: int = 60) -> dict:
        """Search wearable gear by name, class name, or WCID.

        Tokenised AND-match so word order does not matter, with a small
        synonym pass mapping common player vocabulary onto AC's naming.
        """
        items = self._doll_load_wearables()
        q = str(query or "").strip().lower()
        try:
            limit = max(1, min(int(limit), 200))
        except (ValueError, TypeError):
            limit = 60
        if not q:
            return {"success": True, "total": len(items), "items": items[:limit]}

        tokens = [self._DOLL_SYNONYMS.get(t, t) for t in q.split() if t]
        if not tokens:
            return {"success": True, "total": len(items), "items": items[:limit]}

        exact, starts, contains = [], [], []
        for i in items:
            n, c, w = i["name"].lower(), i["class_name"].lower(), str(i["wcid"])
            if q == w:
                exact.append(i)
                continue
            hay = n + " " + c + " " + w
            if all(t in hay for t in tokens):
                (starts if n.startswith(tokens[0]) else contains).append(i)
        hits = exact + starts + contains
        return {"success": True, "total": len(hits), "items": hits[:limit]}

    # Palette data is immutable for a given DAT, and opening the DAT costs far
    # more (~700ms — it walks the B-tree directory and attaches
    # client_highres.dat) than the parse itself (~60ms). So memoize results and
    # let callers batch, rather than holding a shared DatDatabase open: the
    # bridge can run calls concurrently and a shared file handle's seek/read
    # would race.
    _doll_palette_cache = None

    def _doll_parse_cid(self, raw):
        s = str(raw or "").strip()
        try:
            cid = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
        except (ValueError, TypeError):
            return 0
        return cid if cid and (cid >> 24) == 0x10 else 0

    def doll_item_palettes(self, clothing_id_hex: str) -> dict:
        """Dye templates + shade swatches available to one ClothingBase."""
        cid = self._doll_parse_cid(clothing_id_hex)
        if not cid:
            return {"success": False, "error": "Not a ClothingBase DID"}
        r = self.doll_item_palettes_batch([clothing_id_hex])
        if not r.get("success"):
            return r
        return {"success": True,
                "palettes": r["palettes"].get(f"0x{cid:08X}", [])}

    def doll_item_palettes_batch(self, clothing_ids: list) -> dict:
        """Dye options for several ClothingBases, opening the DAT at most once.

        Returns {"palettes": {"0xNNNNNNNN": [...], ...}} keyed by padded hex.
        """
        from pathlib import Path
        if self._doll_palette_cache is None:
            self._doll_palette_cache = {}
        cache = self._doll_palette_cache

        want = []
        for raw in (clothing_ids or []):
            cid = self._doll_parse_cid(raw)
            if cid and cid not in want:
                want.append(cid)
        if not want:
            return {"success": True, "palettes": {}}

        missing = [c for c in want if c not in cache]
        if missing:
            path = self._resolve_portal_dat()
            if not path or not Path(path).exists():
                return {"success": False,
                        "error": "client_portal.dat not configured"}
            db = None
            try:
                from aceforge.dat_loader import DatDatabase, list_clothing_palettes
                db = DatDatabase(path)
                for cid in missing:
                    try:
                        cache[cid] = list_clothing_palettes(db, cid)
                    except Exception:
                        cache[cid] = []
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                if db is not None:
                    try:
                        db.close()
                    except Exception:
                        pass
        return {"success": True,
                "palettes": {f"0x{c:08X}": cache.get(c, []) for c in want}}

    def get_body_setups(self) -> dict:
        """List the body setups the Doll can dress, for the body picker."""
        from aceforge.dat_loader import BODY_SETUPS
        return {"success": True,
                "bodies": [{"id": f"0x{k:08X}", "name": v}
                           for k, v in BODY_SETUPS.items()]}

    def doll_resolve_body(self, setup_hex: str) -> dict:
        """Can this Setup DID be dressed, and which body should the Doll use?

        Lets WeenieForge decide whether to offer the Doll for the creature
        currently in the editor. Alternate setups (Anakshay, barber variants)
        are eligible via the alias map even though no ClothingTable names them.
        """
        from aceforge.dat_loader import BODY_SETUPS, resolve_body_setup
        s = str(setup_hex or "").strip()
        try:
            sid = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
        except (ValueError, TypeError):
            return {"success": True, "eligible": False}
        if not sid or (sid >> 24) != 0x02:
            return {"success": True, "eligible": False}
        if sid in BODY_SETUPS:
            return {"success": True, "eligible": True, "body": f"0x{sid:08X}",
                    "name": BODY_SETUPS[sid], "aliased": False}
        alias = resolve_body_setup(sid)
        if alias in BODY_SETUPS:
            return {"success": True, "eligible": True, "body": f"0x{sid:08X}",
                    "name": BODY_SETUPS[alias], "aliased": True}
        return {"success": True, "eligible": False}

    def doll_base_clothing(self) -> dict:
        """The shirt/pants layer worn under armor.

        Armor and clothing paint DISJOINT palette ranges (verified: Pants
        writes 128 indices with zero overlap against Platemail Leggings), so
        without a clothing layer those ranges keep the texture's default and
        read as white. Applying a shirt+pants underneath colours them.
        """
        by_wcid = {i["wcid"]: i for i in self._doll_load_wearables()}
        out = {}
        for key, wcid in (("shirt", 2588), ("pants", 127)):
            rec = by_wcid.get(wcid)
            if rec:
                out[key] = rec
        return {"success": True, "clothing": out}

    def weenie_palette_options_batch(self, wcids: list) -> dict:
        """weenie_palette_options for several WCIDs, opening the DAT once.

        Returns {"items": {"<wcid>": {clothing_id, palettes}, ...}}. Callers
        with N rows must use this rather than N single calls — each single
        call can re-open the DAT (~700ms) before the memo is warm.
        """
        data = self._gear_load_data()
        want = {}
        for w in (wcids or []):
            try:
                k = int(w)
            except (ValueError, TypeError):
                continue
            src = data.get(k)
            cb = (src.get("did") or {}).get("ClothingBase") if src else None
            want[k] = cb["value"] if cb else None

        cids = [v for v in want.values() if v]
        pal_map = {}
        if cids:
            r = self.doll_item_palettes_batch(cids)
            if not r.get("success"):
                return {"success": False, "error": r.get("error"), "items": {}}
            pal_map = r["palettes"]

        out = {}
        for k, cbv in want.items():
            if not cbv:
                out[str(k)] = {"clothing_id": "", "palettes": []}
                continue
            cid = self._doll_parse_cid(cbv)
            key = f"0x{cid:08X}"
            out[str(k)] = {"clothing_id": key, "palettes": pal_map.get(key, [])}
        return {"success": True, "items": out}

    def weenie_palette_options(self, wcid) -> dict:
        """Dye options for ANY weenie in the catalog (gear or weapon).

        Backs the Create Items palette/shade row, which can reference any
        wieldable — not just the armor/clothing the Doll's wardrobe lists.
        """
        try:
            w = int(wcid)
        except (ValueError, TypeError):
            return {"success": True, "clothing_id": "", "palettes": []}
        src = self._gear_load_data().get(w)
        if not src:
            return {"success": True, "clothing_id": "", "palettes": []}
        cb = (src.get("did") or {}).get("ClothingBase")
        if not cb:
            return {"success": True, "clothing_id": "", "palettes": []}
        r = self.doll_item_palettes_batch([cb["value"]])
        if not r.get("success"):
            return {"success": False, "error": r.get("error"), "palettes": []}
        cid = self._doll_parse_cid(cb["value"])
        return {"success": True, "clothing_id": f"0x{cid:08X}",
                "palettes": r["palettes"].get(f"0x{cid:08X}", [])}

    def _parse_cb_overrides(self, overrides) -> tuple:
        """[CustomClothingBase JSON obj|text] → ({clothing_id: table}, errors).

        The editor's live document is already in the mod's export format, so it
        comes over the wire as-is — preview and export therefore cannot drift.
        """
        from aceforge import clothing_json as cj

        out, errs = {}, []
        for i, o in enumerate(overrides or []):
            try:
                t = (cj.table_from_json(o) if isinstance(o, str)
                     else cj.table_from_obj(o))
            except cj.ClothingJsonError as e:
                errs.append(f"override[{i}]: {e}")
                continue
            if (t["id"] >> 24) != 0x10:
                errs.append(f"override[{i}]: Id 0x{t['id']:08X} is not a "
                            f"ClothingTable")
                continue
            out[t["id"]] = t
        return out, errs

    def clothingbase_load(self, clothing_id_hex: str) -> dict:
        """Read a ClothingBase from the DAT as CustomClothingBase JSON text.

        The editor's "open" — the returned text is a valid mod file as-is, and
        is what the mod's own /clothingbase-export command would write.
        """
        from pathlib import Path
        from aceforge.dat_loader import DatDatabase, parse_clothing_table_full
        from aceforge import clothing_json as cj

        s = str(clothing_id_hex or "").strip()
        try:
            cid = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
        except (ValueError, TypeError):
            return {"success": False, "error": f"Invalid ClothingBase id: {s!r}"}
        if (cid >> 24) != 0x10:
            return {"success": False,
                    "error": f"0x{cid:08X} is not a ClothingTable (0x10......)"}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}

        db = None
        try:
            db = DatDatabase(path)
            table = parse_clothing_table_full(db, cid)
            if table is None:
                return {"success": False,
                        "error": f"ClothingBase 0x{cid:08X} not found in the DAT"}
            return {"success": True,
                    "json": cj.table_to_json(table),
                    "filename": cj.json_filename(cid),
                    "setups": [f"0x{s:08X}" for s in sorted(table["base_effects"])],
                    "templates": sorted(table["subpal_effects"]),
                    "warnings": cj.validate_table(table)}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def _cb_texture_index(self):
        """Memoized texture index — ~0.2s to build, so build it once.

        Holds the clothing-usage index, every SurfaceTexture in the DAT, and
        the named terrain textures.
        """
        if getattr(self, "_cb_tex_idx", None) is None:
            from pathlib import Path
            from aceforge.dat_loader import (DatDatabase, clothing_texture_index,
                                             parse_terrain_textures)
            path = self._resolve_portal_dat()
            if not path or not Path(path).exists():
                return None
            db = None
            try:
                db = DatDatabase(path)
                idx = clothing_texture_index(db)
                idx["every"] = sorted(db.files_by_type(0x05))
                idx["terrain"] = parse_terrain_textures(db)
                self._cb_tex_idx = idx
            finally:
                if db is not None:
                    try:
                        db.close()
                    except Exception:
                        pass
        return self._cb_tex_idx

    def clothingbase_textures_for_part(self, setup_hex: str, part_index: int) -> dict:
        """Textures other armor uses on this (setup, part) — the picker's list.

        The DAT has ~7240 SurfaceTextures, but only ~2038 are used by clothing
        at all, and only a handful on any given part. Offering the part's own
        list first is the difference between a usable picker and a haystack.
        """
        idx = self._cb_texture_index()
        if idx is None:
            return {"success": False, "error": "client_portal.dat not configured"}
        try:
            setup = int(str(setup_hex), 16) if str(setup_hex).lower().startswith("0x") \
                else int(str(setup_hex), 10)
            part = int(part_index)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid setup or part index"}

        here = idx["by_part"].get((setup, part), [])
        # Terrain first among the "fun" sets: they are the only named textures
        # in the DAT, so they are the only ones anyone can go looking for.
        terrain = [{"id": f"0x{t['texture']:08X}", "name": t["name"]}
                   for t in idx["terrain"]]
        return {"success": True,
                "for_part": [f"0x{i:08X}" for i in here],
                "all_clothing": [f"0x{i:08X}" for i in idx["all"]],
                "terrain": terrain,
                "every": [f"0x{i:08X}" for i in idx["every"]],
                "users": {f"0x{i:08X}": idx["users"][i] for i in here}}

    def clothingbase_texture_thumbs(self, ids: list, size: int = 64) -> dict:
        """Batch SurfaceTexture → base64 PNG thumbnails, disk-cached.

        Batched because opening the DAT costs ~700ms; the doll's palette API
        learned the same lesson. Disk-cached because the box filter is ~25ms
        per texture in pure Python and the picker re-renders the same grid.
        """
        import base64
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, get_cache_dir,
                                         render_surface_texture_png)

        try:
            size = max(8, min(int(size), 256))
        except (ValueError, TypeError):
            size = 64

        want = []
        for raw in (ids or []):
            s = str(raw or "").strip()
            try:
                want.append(int(s, 16) if s.lower().startswith("0x") else int(s, 10))
            except (ValueError, TypeError):
                continue

        cdir = get_cache_dir().parent / "tex_cache"
        cdir.mkdir(parents=True, exist_ok=True)
        out, missing = {}, []
        for tid in want:
            p = cdir / f"{tid:08X}_{size}.png"
            if p.exists():
                out[f"0x{tid:08X}"] = base64.b64encode(p.read_bytes()).decode()
            else:
                missing.append((tid, p))

        if missing:
            path = self._resolve_portal_dat()
            if not path or not Path(path).exists():
                return {"success": False, "error": "client_portal.dat not configured"}
            db = None
            try:
                db = DatDatabase(path)
                for tid, p in missing:
                    r = render_surface_texture_png(db, tid, size)
                    if r is None:
                        continue
                    png = r[0]
                    try:
                        p.write_bytes(png)
                    except OSError:
                        pass          # a failed cache write must not fail the render
                    out[f"0x{tid:08X}"] = base64.b64encode(png).decode()
            except Exception as e:
                return {"success": False, "error": f"Exception: {e}"}
            finally:
                if db is not None:
                    try:
                        db.close()
                    except Exception:
                        pass

        return {"success": True, "thumbs": out,
                "missing": [f"0x{t:08X}" for t in want
                            if f"0x{t:08X}" not in out]}

    def clothingbase_parts(self, clothing_id_hex: str, setup_hex: str) -> dict:
        """The editable rows for one (ClothingBase, setup): each part's model
        and its old→new texture effects, plus which bodies the table covers.

        The coverage list matters: a ClothingBase only applies to setups it
        explicitly names, so armor customized for Human Male renders untouched
        on an Umbraen unless that setup gets its own base effect. Surfacing it
        here keeps that from reading as a bug.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, parse_clothing_table_full,
                                         BODY_SETUPS, body_part_name)

        def _id(s, default=0):
            s = str(s or "").strip()
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return default

        cid, setup = _id(clothing_id_hex), _id(setup_hex)
        if (cid >> 24) != 0x10:
            return {"success": False, "error": "Not a ClothingTable id"}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            t = parse_clothing_table_full(db, cid)
            if t is None:
                return {"success": False, "error": f"0x{cid:08X} not found"}
            covers = sorted(t["base_effects"])
            rows = [{
                "part": o["index"],
                "part_name": body_part_name(o["index"]),
                "model_id": f"0x{o['model_id']:08X}",
                "textures": [{"old": f"0x{e['old']:08X}",
                              "new": f"0x{e['new']:08X}",
                              "changed": e["old"] != e["new"]}
                             for e in o.get("tex_effects", [])],
            } for o in t["base_effects"].get(setup, [])]
            return {"success": True,
                    "parts": rows,
                    "covers": [{"setup": f"0x{s:08X}",
                                "name": BODY_SETUPS.get(s, f"Setup 0x{s:08X}"),
                                "is_body": s in BODY_SETUPS} for s in covers],
                    "missing_bodies": [{"setup": f"0x{s:08X}", "name": n}
                                       for s, n in sorted(BODY_SETUPS.items())
                                       if s not in t["base_effects"]]}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clothingbase_synthesize(self, setup_hex: str, new_id_hex: str = "") -> dict:
        """Build an editable ClothingBase from a creature's bare Setup.

        For the ~28% of creatures that have no ClothingBase: read the Setup's
        real parts as identity texture slots so the editor can swap them, then
        export under a new id the weenie's DID 7 will point at. Returns the same
        shape as clothingbase_load so the editor opens it identically.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase,
                                         synthesize_clothing_table_from_setup,
                                         BODY_SETUPS)
        from aceforge import clothing_json as cj

        def _id(s, d=0):
            s = str(s or "").strip()
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return d

        setup = _id(setup_hex)
        if (setup >> 24) != 0x02:
            return {"success": False, "error": "Not a Setup id (0x02......)"}

        # Pick a free custom id unless the caller supplied one.
        new_id = _id(new_id_hex)
        if not new_id:
            sug = self.clothingbase_suggest_id()
            if not sug.get("success"):
                return sug
            new_id = _id(sug["id"])
        if not cj.range_ok(new_id):
            return {"success": False,
                    "error": f"0x{new_id:08X} is outside the ClothingBase range."}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            table = synthesize_clothing_table_from_setup(db, setup, new_id)
            if table is None:
                return {"success": False,
                        "error": f"Setup 0x{setup:08X} has no textured parts."}
            return {"success": True,
                    "json": cj.table_to_json(table),
                    "filename": cj.json_filename(new_id),
                    "id": f"0x{new_id:08X}",
                    "setups": [f"0x{setup:08X}"],
                    "templates": [],
                    "humanoid": setup in BODY_SETUPS,
                    "synthesized": True,
                    "warnings": cj.validate_table(table)}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clothingbase_creature_load(self, setup_hex: str, cb_hex: str = "") -> dict:
        """Load a creature for editing with its WHOLE body reachable.

        A creature's ClothingBase usually covers only a few parts (a Virindi's
        cb touches just the head), so loading the cb alone leaves most of the
        body uneditable. This merges the cb's real effects over the full Setup
        part list — cb parts keep their swaps/dyes, every other part becomes an
        identity slot — so the entire creature is editable, like Derpy's tool.

        Always returns a table the editor seeds directly (no DAT round-trip), so
        a synthesised-id creature can never hit a "not found in the DAT" load.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, parse_clothing_table_full,
                                         synthesize_clothing_table_from_setup,
                                         BODY_SETUPS)
        from aceforge import clothing_json as cj

        def _id(s, d=0):
            s = str(s or "").strip()
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return d

        setup = _id(setup_hex)
        if (setup >> 24) != 0x02:
            return {"success": False, "error": "Not a Setup id (0x02......)"}
        cb = _id(cb_hex)

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            in_dat = cb in set(db.files_by_type(0x10)) if (cb >> 24) == 0x10 else False
            # Synthetic id is derived from the Setup so it's stable per creature
            # (reopening reuses it) and distinct between creatures (no collision).
            cid = cb if (cb and (cb >> 24) == 0x10) else (0x10F00000 | (setup & 0xFFFFF))

            synth = synthesize_clothing_table_from_setup(db, setup, cid)
            if synth is None:
                return {"success": False,
                        "error": "This creature is solid-coloured — its model "
                                 "has no body-part textures to swap. (A handful "
                                 "of creatures like the Knath are flat colours, "
                                 "not textures, so there's nothing to edit here.)"}

            if in_dat:
                table = parse_clothing_table_full(db, cb)
                covered = {o["index"] for o in table["base_effects"].get(setup, [])}
                extra = [o for o in synth["base_effects"][setup]
                         if o["index"] not in covered]
                objs = table["base_effects"].setdefault(setup, [])
                objs.extend(extra)
                objs.sort(key=lambda o: o["index"])
                table["id"] = cid
            else:
                table = synth        # no cb (or cb absent from DAT): pure synthesis

            n = len(table["base_effects"].get(setup, []))
            return {"success": True,
                    "json": cj.table_to_json(table),
                    "filename": cj.json_filename(cid),
                    "id": f"0x{cid:08X}",
                    "has_cb": bool(in_dat),
                    "setup": f"0x{setup:08X}",
                    "part_count": n,
                    "humanoid": setup in BODY_SETUPS,
                    "templates": sorted(table["subpal_effects"]),
                    "warnings": cj.validate_table(table)}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clothingbase_validate(self, text: str) -> dict:
        """Check editor JSON without rendering. Returns parse errors or warnings."""
        from aceforge import clothing_json as cj
        try:
            table = cj.table_from_json(text if isinstance(text, str)
                                       else json.dumps(text))
        except cj.ClothingJsonError as e:
            return {"success": False, "error": str(e)}
        return {"success": True,
                "id": f"0x{table['id']:08X}",
                "filename": cj.json_filename(table["id"]),
                "setups": [f"0x{s:08X}" for s in sorted(table["base_effects"])],
                "templates": sorted(table["subpal_effects"]),
                "warnings": cj.validate_table(table)}

    def clothingbase_part_palette_runs(self, part_textures: dict) -> dict:
        """Which palette indices each body part's texture samples, so the Colors
        tab can say which parts a dye range recolours.

        part_textures: {part_index(str/int): [SurfaceTexture hex, ...]} — the
        NewTextures currently on each part (passed from the live doc so it
        follows texture swaps). Returns {parts: {idx: {name, runs:[[s,e],...]}}}.

        Memoised on the exact texture set: the Colors tab re-renders on every
        dye tweak but the textures rarely change, so this opens the DAT once.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, texture_used_indices,
                                         indices_to_runs, body_part_name)

        def _id(s):
            s = str(s or "").strip()
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return 0

        norm = {}
        for k, texlist in (part_textures or {}).items():
            try:
                idx = int(k)
            except (ValueError, TypeError):
                continue
            ids = tuple(sorted({_id(t) for t in (texlist or []) if _id(t)}))
            if ids:
                norm[idx] = ids

        sig = tuple(sorted(norm.items()))
        cache = getattr(self, "_cb_runs_cache", None)
        if cache is None:
            cache = self._cb_runs_cache = {}
        if sig in cache:
            return cache[sig]

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            tex_cache = {}
            parts = {}
            for idx, ids in norm.items():
                used = set()
                for tid in ids:
                    if tid not in tex_cache:
                        tex_cache[tid] = texture_used_indices(db, tid) or set()
                    used |= tex_cache[tid]
                parts[str(idx)] = {"name": body_part_name(idx),
                                   "runs": indices_to_runs(used)}
            result = {"success": True, "parts": parts}
            cache[sig] = result
            return result
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clothingbase_palette_strips(self, entries: list, shade: float = 0.0) -> dict:
        """Swatch strips for subpalette rows / the dye picker.

        entries: [{"paletteset": hex, "offset": int, "num_colors": int}] —
        offset/num_colors matter because a subpalette only paints that slice,
        so the swatch has to come from the same slice or it lies about the dye.
        Batched: one DAT open (~700ms) per call, not per swatch.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, palette_strip,
                                         PALETTE_TEMPLATE_NAMES)

        def _id(s, d=0):
            s = str(s or "").strip()
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return d

        try:
            shade = min(max(float(shade or 0.0), 0.0), 1.0)
        except (ValueError, TypeError):
            shade = 0.0

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            out = []
            for e in (entries or []):
                ps = _id((e or {}).get("paletteset"))
                off = int((e or {}).get("offset") or 0)
                num = int((e or {}).get("num_colors") or 0)
                out.append({"paletteset": f"0x{ps:08X}",
                            "colors": palette_strip(db, ps, shade, off, num, 24)})
            return {"success": True, "strips": out}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clothingbase_dye_options(self, shade: float = 0.0, offset: int = 0,
                                 num_colors: int = 0) -> dict:
        """The named dye palettes for the PaletteSet picker, plus every
        PaletteSet clothing uses as a fallback list.

        The 94 canonical 0x0F0000NN palettes are the only ones with real names
        (Blue, Red, Forest Green…), which is what someone recolouring armor is
        actually shopping for. They are *not* what most tables reference — only
        13% of retail primaries follow that convention — so this is a curated
        starter set, not a filter, and "all" stays available.
        """
        from pathlib import Path
        from aceforge.dat_loader import (DatDatabase, palette_strip,
                                         clothing_paletteset_index,
                                         PALETTE_TEMPLATE_NAMES)
        try:
            shade = min(max(float(shade or 0.0), 0.0), 1.0)
            offset = int(offset or 0)
            num_colors = int(num_colors or 0)
        except (ValueError, TypeError):
            shade, offset, num_colors = 0.0, 0, 0

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            named = []
            for tpl, name in sorted(PALETTE_TEMPLATE_NAMES.items()):
                ps = 0x0F000000 | tpl
                cols = palette_strip(db, ps, shade, offset, num_colors, 12)
                if cols:
                    named.append({"paletteset": f"0x{ps:08X}", "name": name,
                                  "template": tpl, "colors": cols})
            idx = clothing_paletteset_index(db)
            return {"success": True, "named": named,
                    "all": [f"0x{i:08X}" for i in idx["all"]]}
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    # Retail ClothingTables stop at 0x100012AE. Custom ids start well clear of
    # that block so a glance at an id says whether it is ours, and so the mod's
    # stub path (which only fires for ids absent from the DAT) always applies.
    CB_CUSTOM_BASE = 0x10F00000

    def _cb_usage(self):
        """{clothing_id: [wcid, ...]} across the gear catalog. Memoized."""
        if getattr(self, "_cb_usage_cache", None) is None:
            out = {}
            for w in self._doll_load_wearables():
                # gear_full.json stores ClothingBase as a hex string ("0x100004E2").
                cid = self._doll_parse_cid(w.get("clothing_id"))
                if cid:
                    out.setdefault(cid, []).append(w.get("wcid"))
            self._cb_usage_cache = out
        return self._cb_usage_cache

    def clothingbase_id_info(self, clothing_id_hex: str) -> dict:
        """Is this id in the DAT, and which weenies point at it?

        Editing a retail id in place is a merge, so it silently restyles every
        item that shares it — which for a common ClothingBase can be dozens.
        The editor needs to say so before the user saves, not after.
        """
        from pathlib import Path
        from aceforge.dat_loader import DatDatabase
        from aceforge import clothing_json as cj

        s = str(clothing_id_hex or "").strip()
        try:
            cid = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
        except (ValueError, TypeError):
            return {"success": False, "error": f"Invalid id: {s!r}"}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            in_dat = cid in set(db.files_by_type(0x10))
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

        wcids = self._cb_usage().get(cid, [])
        return {"success": True, "id": f"0x{cid:08X}", "in_dat": in_dat,
                "wcids": wcids[:200], "wcid_count": len(wcids),
                "legal": cj.range_ok(cid)}

    def clothingbase_suggest_id(self) -> dict:
        """The next free custom ClothingBase id."""
        from pathlib import Path
        from aceforge.dat_loader import DatDatabase

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}
        db = None
        try:
            db = DatDatabase(path)
            used = set(db.files_by_type(0x10))
        except Exception as e:
            return {"success": False, "error": f"Exception: {e}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

        # Skip ids already exported to the output folder, so two custom pieces
        # made in one sitting don't collide on the same number.
        out_dir = self._cb_output_dir()
        if out_dir:
            for f in Path(out_dir).glob("*.json"):
                try:
                    used.add(int(f.stem, 16))
                except ValueError:
                    pass

        cid = self.CB_CUSTOM_BASE
        while cid in used and cid <= 0x10FFFFFF:
            cid += 1
        if cid > 0x10FFFFFF:
            return {"success": False, "error": "No free ClothingBase ids left"}
        return {"success": True, "id": f"0x{cid:08X}"}

    def _cb_output_dir(self) -> str:
        return (self.config.get("clothingbase_output_dir", "")
                or str(self.config.output_dir or "")).strip()

    def clothingbase_get_output_dir(self) -> dict:
        """Where exports go, and whether it's a dedicated setting or a fallback.

        Falls back to the general output_dir so the tool isn't dead before the
        user sets a folder, but the UI should say which it is — a fallback drops
        the JSON somewhere unexpected for a server mod.
        """
        explicit = (self.config.get("clothingbase_output_dir", "") or "").strip()
        return {"success": True,
                "path": self._cb_output_dir(),
                "explicit": bool(explicit)}

    def clothingbase_set_output_dir(self, path: str) -> dict:
        """Persist the ClothingBase JSON output folder. Blank clears it."""
        from pathlib import Path
        p = str(path or "").strip()
        if p:
            try:
                Path(p).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return {"success": False, "error": f"Cannot use that folder: {e}"}
        self.config.set("clothingbase_output_dir", p)
        self.config.save()
        return {"success": True, "path": p}

    def clothingbase_browse_output_dir(self) -> dict:
        """Native folder picker → persist as the ClothingBase output folder."""
        r = self.browse_folder()
        if not r.get("path"):
            return r
        return self.clothingbase_set_output_dir(r["path"])

    def _cb_weenie_sql(self, wcids: list, cid: int) -> str:
        """SQL patching weenies to point at a ClothingBase (DID 7).

        A patch, not a full weenie dump: the item already exists and only its
        appearance changes. DELETE-then-INSERT so re-running is safe.
        """
        from datetime import datetime
        # ASCII only: this file gets fed to whatever MySQL client the user has,
        # with whatever charset settings, and a stray em-dash in a comment is a
        # pointless thing to lose an import over.
        lines = [
            f"/* ACEForge - point {len(wcids)} weenie(s) at "
            f"ClothingBase 0x{cid:08X} */",
            f"/* Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            f"Requires the CustomClothingBase mod and 0x{cid:08X}.json "
            f"in its json/ folder. */",
            "",
        ]
        for w in wcids:
            lines.append(f"DELETE FROM `weenie_properties_d_i_d` "
                         f"WHERE `object_Id` = {w} AND `type` = 7;")
            lines.append("INSERT INTO `weenie_properties_d_i_d` "
                         "(`object_Id`, `type`, `value`)")
            lines.append(f"VALUES ({w}, 7, 0x{cid:08X}) /* ClothingBase */;")
            lines.append("")
        return "\n".join(lines)

    def clothingbase_export(self, clothing_id_hex: str, text: str,
                            save_as: str = "", wcids: list = None) -> dict:
        """Write an edited ClothingBase as a CustomClothingBase mod file, and
        optionally the weenie SQL that points items at it.

        Named {id:X}.json to match what the mod looks for (PatchClass.GetFilename)
        — the name is load-bearing, not cosmetic.

        save_as: write under a different (new) ClothingBase id instead of the
        one the table was loaded from. A new id has no DAT entry, so the mod
        stubs an empty table and the JSON must stand alone — which it does,
        because the editor always loads the whole table.

        wcids: emit a .sql alongside pointing these weenies at the id. Only
        meaningful with save_as; editing a retail id in place needs no SQL,
        since the weenies already reference it.
        """
        from pathlib import Path
        from aceforge import clothing_json as cj

        try:
            table = cj.table_from_json(text if isinstance(text, str)
                                       else json.dumps(text))
        except cj.ClothingJsonError as e:
            return {"success": False, "error": str(e)}

        if save_as:
            s = str(save_as).strip()
            try:
                new_id = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return {"success": False, "error": f"Invalid new id: {save_as!r}"}
            if not cj.range_ok(new_id):
                return {"success": False,
                        "error": f"0x{new_id:08X} is outside the ClothingBase "
                                 f"range 0x10000001–0x10FFFFFF."}
            table["id"] = new_id

        out_dir = self._cb_output_dir()
        if not out_dir:
            return {"success": False,
                    "error": "No output folder configured — set one in Settings."}

        clean = []
        for w in (wcids or []):
            try:
                clean.append(int(str(w).strip()))
            except (ValueError, TypeError):
                continue

        try:
            d = Path(out_dir)
            d.mkdir(parents=True, exist_ok=True)
            p = d / cj.json_filename(table["id"])
            p.write_text(cj.table_to_json(table), encoding="utf-8")
            sql_path = None
            if clean:
                sql_path = d / f"{table['id']:X}_weenies.sql"
                sql_path.write_text(self._cb_weenie_sql(clean, table["id"]),
                                    encoding="utf-8")
        except OSError as e:
            return {"success": False, "error": f"Could not write file: {e}"}

        return {"success": True, "path": str(p), "filename": p.name,
                "sql_path": str(sql_path) if sql_path else None,
                "sql_filename": sql_path.name if sql_path else None,
                "wcids": clean,
                "id": f"0x{table['id']:08X}",
                "warnings": cj.validate_table(table)}

    def get_doll_glb(self, body_setup_hex: str, outfit: list,
                     motion_id_hex: str = "", overrides: list = None) -> dict:
        """Return a base64 GLB of a body setup wearing an outfit.

        outfit: list of dicts, one per equipped item, each with
          clothing_id (hex/dec str), and optionally palette_template, shade,
          item_type, valid_locations, clothing_priority, top_layer.
        Items are ordered and composited the way ACE's CalculateObjDesc does,
        so overlapping pieces layer the same way they would in game.

        overrides: optional list of edited ClothingTables in CustomClothingBase
        JSON form. Each is merged over the DAT entry the way the server mod
        merges it, so the preview matches what players would see. Renders with
        an override skip the disk cache — live editing would otherwise leave a
        ~1MB GLB behind per keystroke.
        """
        import base64, traceback
        from pathlib import Path

        def _did(raw, default=0):
            s = str(raw or "").strip()
            if not s:
                return default
            try:
                return int(s, 16) if s.lower().startswith("0x") else int(s, 10)
            except (ValueError, TypeError):
                return default

        def _num(raw, default=0):
            try:
                return int(str(raw).strip())
            except (ValueError, TypeError, AttributeError):
                return default

        setup_id = _did(body_setup_hex)
        if not setup_id or (setup_id >> 24) != 0x02:
            return {"success": False, "error": "Invalid body setup ID"}
        motion_id = _did(motion_id_hex)
        if motion_id and (motion_id >> 24) != 0x09:
            motion_id = 0

        clean = []
        for it in (outfit or []):
            cid = _did((it or {}).get("clothing_id"))
            if not cid or (cid >> 24) != 0x10:
                continue          # only real ClothingTables can dress a body
            tl = (it or {}).get("top_layer")
            if isinstance(tl, str):
                tl = {"true": True, "false": False}.get(tl.strip().lower())
            try:
                shade = min(max(float((it or {}).get("shade") or 0.0), 0.0), 1.0)
            except (ValueError, TypeError):
                shade = 0.0
            clean.append({
                "clothing_id":       cid,
                "palette_template":  _num(it.get("palette_template")),
                "shade":             shade,
                "item_type":         _num(it.get("item_type")),
                "valid_locations":   _num(it.get("valid_locations")),
                "clothing_priority": _num(it.get("clothing_priority")),
                "top_layer":         tl if isinstance(tl, bool) else None,
            })

        from aceforge.dat_loader import (cached_glb_path, DatDatabase,
                                         export_setup_glb, get_or_export_glb,
                                         order_outfit)

        ov, ov_errs = self._parse_cb_overrides(overrides)
        if ov_errs:
            return {"success": False, "error": "; ".join(ov_errs)}

        # "pieces" is always present; "layers" only when the order was actually
        # computed (a cache hit skips the DB, and re-opening it just to derive
        # the order would defeat the cache). Edited tables are never cached, so
        # they always take the render path below.
        if not ov:
            cached = cached_glb_path(setup_id, motion_id=motion_id, outfit=clean)
            if cached.exists():
                return {"success": True,
                        "data_b64": base64.b64encode(cached.read_bytes()).decode(),
                        "pieces": len(clean),
                        "info": f"{len(clean)} piece(s), cached"}

        path = self._resolve_portal_dat()
        if not path or not Path(path).exists():
            return {"success": False, "error": "client_portal.dat not configured"}

        db = None
        try:
            db = DatDatabase(path)
            layers = [f"0x{i['clothing_id']:08X}" for i in order_outfit(db, clean)]
            if ov:
                glb = export_setup_glb(db, setup_id, motion_id=motion_id,
                                       outfit=clean, overrides=ov)
            else:
                glb_path = get_or_export_glb(db, setup_id, motion_id=motion_id,
                                             outfit=clean)
                glb = glb_path.read_bytes() if glb_path is not None else None
            if glb is None:
                return {"success": False,
                        "error": "Could not build the doll — the body setup "
                                 "has no renderable geometry."}
            edited = (f", {len(ov)} edited" if ov else "")
            return {"success": True,
                    "data_b64": base64.b64encode(glb).decode(),
                    "pieces": len(clean),
                    "info": f"{len(clean)} piece(s){edited}, glb={len(glb):,}B",
                    "layers": layers}
        except Exception as e:
            return {"success": False,
                    "error": f"Exception: {e}\n{traceback.format_exc()[-800:]}"}
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    def clear_model_cache(self) -> dict:
        """Delete all cached GLB files."""
        try:
            from aceforge.dat_loader import get_cache_dir
            d = get_cache_dir()
            count = 0
            for f in d.glob("*.glb"):
                f.unlink()
                count += 1
            return {"success": True, "deleted": count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    APP_VERSION = "0.3.09"

    def get_version(self) -> str:
        """
        Return the running version. Prefers VERSION.txt next to the exe so the
        version display updates immediately after an auto-update overwrites the
        file — no recompile needed. Falls back to the hardcoded APP_VERSION if
        VERSION.txt is absent (dev mode, first run before any update).
        """
        import sys
        from pathlib import Path

        try:
            if hasattr(sys, "_MEIPASS"):
                # PyInstaller onefile: exe lives at sys.executable
                ver_file = Path(sys.executable).parent / "VERSION.txt"
            else:
                # Dev mode: look next to the repo root
                ver_file = Path(__file__).parent.parent / "VERSION.txt"

            if ver_file.exists():
                first_line = ver_file.read_text(encoding="utf-8").splitlines()[0]
                # Expected: "ACEForge v1.2.3"
                token = first_line.strip().split()[-1].lstrip("vV")
                if token and all(c.isdigit() or c == "." for c in token):
                    return token
        except Exception:
            pass

        return self.APP_VERSION

    def get_seen_update_version(self) -> str:
        """Return the last update version the user was notified about.
        Stored in the config file (not localStorage) so it survives app updates."""
        return self.config.get("seen_update_version", "")

    def set_seen_update_version(self, version: str) -> dict:
        """Persist the dismissed update version so the user isn't re-notified
        about the same release on every launch."""
        try:
            self.config.set("seen_update_version", version)
            self.config.save()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_for_update(self) -> dict:
        """Check GitHub releases for a newer version of ACEForge."""
        import urllib.request, json as _json
        try:
            url = "https://api.github.com/repos/shemtar-90/aceforge/releases/latest"
            req = urllib.request.Request(url,
                headers={"User-Agent": "ACEForge/" + self.APP_VERSION,
                         "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = _json.loads(r.read().decode())
            latest    = data.get("tag_name", "").lstrip("v")
            notes     = data.get("body", "")
            published = data.get("published_at", "")  # ISO timestamp e.g. "2025-06-22T10:00:00Z"
            assets    = data.get("assets", [])
            dl_url    = next((a["browser_download_url"] for a in assets
                              if a["name"].endswith(".zip")), "")

            def _ver(v):
                """
                Parse a version string into a comparable tuple of ints.
                Each segment is compared numerically so that e.g.
                (0,3,13) < (0,3,122) — but this means 0.3.13 reads as
                OLDER than 0.3.122.

                To handle non-monotonic version numbering (where the dev
                may reset or reuse segment values), we also accept a
                published_at ISO timestamp as a tiebreaker: if the latest
                release was published after the app was built, it wins
                regardless of version tuple ordering.
                """
                try:
                    return tuple(int(x) for x in str(v).split("."))
                except Exception:
                    return (0,)

            current     = self.get_version()
            ver_newer   = bool(latest) and _ver(latest) > _ver(current)

            # Fallback: if tag-based comparison says "not newer", check the
            # release publish date against the build date from VERSION.txt.
            # This covers cases where version numbering is non-monotonic
            # (e.g. 0.3.13 released after 0.3.122).
            date_newer = False
            if not ver_newer and published:
                try:
                    import sys
                    from pathlib import Path
                    if hasattr(sys, "_MEIPASS"):
                        ver_file = Path(sys.executable).parent / "VERSION.txt"
                    else:
                        ver_file = Path(__file__).parent.parent / "VERSION.txt"
                    if ver_file.exists():
                        lines = ver_file.read_text(encoding="utf-8").splitlines()
                        # VERSION.txt line 2: "Built: 2025-06-22 10:00 UTC"
                        built_line = next((l for l in lines if l.startswith("Built:")), "")
                        built_str  = built_line.replace("Built:", "").strip().replace(" UTC", "Z").replace(" ", "T")
                        if built_str and published > built_str:
                            date_newer = True
                except Exception:
                    pass

            has_update = ver_newer or date_newer
            return {"has_update": has_update,
                    "latest_version": latest,
                    "current_version": current,
                    "release_notes": notes,
                    "download_url": dl_url}
        except Exception as e:
            return {"has_update": False, "error": str(e),
                    "current_version": self.get_version()}

    def save_converter_output(self, content: str, base_name: str, ext: str) -> dict:
        """Save JSON<->SQL converter output to the configured Output folder."""
        try:
            output_dir = str(self.config.output_dir or "").strip()
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            name = (base_name or "converted").strip() or "converted"
            for ch in r'\/:*?"<>|':
                name = name.replace(ch, "")
            name = name.strip() or "converted"
            ext = (ext or "txt").lstrip(".").lower()

            fpath = Path(output_dir) / f"{name}.{ext}"
            fpath.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(fpath), "folder": output_dir}
        except Exception as e:
            return {"error": str(e)}

    def convert_json_to_sql(self, json_text: str, filename: str = "") -> dict:
        """Convert ACE JSON weenie data to ACE-World SQL."""
        try:
            from aceforge.json_to_sql import extract_and_convert
            sql = extract_and_convert(json_text, filename)
            if not sql:
                return {"error": "No SQL generated — check JSON format."}
            return {"sql": sql}
        except Exception as e:
            return {"error": str(e)}

    def convert_sql_to_json(self, sql_text: str) -> dict:
        """Convert ACE-World SQL weenie INSERT statements back to ACE JSON format."""
        import re, json as _json
        try:
            sql = sql_text.strip()

            def _clean_val(v):
                v = v.strip()
                if v.upper() == "NULL": return None
                if v.upper() == "TRUE": return True
                if v.upper() == "FALSE": return False
                if v.startswith("'") and v.endswith("'"): return v[1:-1].replace("''", "'")
                try: return int(v)
                except ValueError: pass
                try: return float(v)
                except ValueError: pass
                return v

            def _split_value_rows(values_block):
                """Split a VALUES (...) , (...) , (...) block into individual
                row strings, respecting quoted strings and skipping over
                /* comments */ so a stray paren inside a comment can't break
                row boundaries."""
                rows, depth, buf, in_str = [], 0, '', False
                i, n = 0, len(values_block)
                while i < n:
                    ch = values_block[i]
                    if in_str:
                        if ch == "'" and i+1 < n and values_block[i+1] == "'":
                            buf += "''"; i += 2; continue
                        buf += ch
                        if ch == "'": in_str = False
                        i += 1; continue
                    if ch == "'":
                        in_str = True; buf += ch; i += 1; continue
                    if ch == '/' and i+1 < n and values_block[i+1] == '*':
                        end = values_block.find('*/', i+2)
                        i = end + 2 if end >= 0 else n
                        continue
                    if ch == '(':
                        depth += 1
                        if depth == 1:
                            buf = ''
                            i += 1; continue
                    if ch == ')':
                        depth -= 1
                        if depth == 0:
                            rows.append(buf)
                            i += 1; continue
                    if depth >= 1: buf += ch
                    i += 1
                return rows

            def _split_row_values(raw):
                """Quote-aware, comment-aware CSV split of one row's values."""
                vals, cur, in_q = [], '', False
                i, n = 0, len(raw)
                while i < n:
                    ch = raw[i]
                    if in_q:
                        if ch == "'" and i+1 < n and raw[i+1] == "'":
                            cur += "''"; i += 2; continue
                        cur += ch
                        if ch == "'": in_q = False
                        i += 1; continue
                    if ch == "'":
                        in_q = True; cur += ch; i += 1; continue
                    if ch == '/' and i+1 < n and raw[i+1] == '*':
                        end = raw.find('*/', i+2)
                        i = end + 2 if end >= 0 else n
                        continue
                    if ch == ',':
                        vals.append(cur.strip()); cur = ''
                        i += 1; continue
                    cur += ch; i += 1
                if cur.strip(): vals.append(cur.strip())
                return vals

            def _parse_insert(sql_block):
                """Parse an INSERT statement into a list of {col: val} dicts —
                one per VALUES row tuple, since ACE-World SQL commonly writes
                many rows per statement (e.g. one INSERT for all of a
                weenie's int properties)."""
                col_m = re.search(r"INSERT INTO `[^`]+`\s*\(([^)]+)\)", sql_block, re.I)
                val_m = re.search(r"VALUES\s*([\s\S]+?);\s*$", sql_block, re.I)
                if not col_m or not val_m: return []
                cols = [c.strip().strip('`') for c in col_m.group(1).split(',')]
                out = []
                for row_raw in _split_value_rows(val_m.group(1)):
                    vals = _split_row_values(row_raw)
                    out.append({cols[i]: _clean_val(vals[i]) for i in range(min(len(cols), len(vals)))})
                return out

            # Parse all INSERT statements
            all_rows = {}
            for m in re.finditer(r"INSERT INTO `([^`]+)`([^;]+);", re.sub(r"--[^\n]*","",sql), re.I|re.S):
                table = m.group(1).lower()
                rows = _parse_insert("INSERT INTO `" + m.group(1) + "`" + m.group(2) + ";")
                if table not in all_rows: all_rows[table] = []
                all_rows[table].extend(rows)

            # Build JSON structure
            weenie_row = (all_rows.get("weenie") or [{}])[0]
            wcid = weenie_row.get("class_Id") or weenie_row.get("class_id") or 0
            name = ""
            desc = ""

            result = {
                "wcid": wcid,
                "weenieType": weenie_row.get("type") or weenie_row.get("weenie_Type") or 0,
                "intStats": {},  "boolStats": {}, "floatStats": {},
                "stringStats": {}, "didStats": {},
                "positions": {}, "attributes": {}, "skills": [], "spells": []
            }

            for row in all_rows.get("weenie_properties_int", []):
                k = str(row.get("type",""))
                v = row.get("value")
                if k and v is not None: result["intStats"][k] = v

            for row in all_rows.get("weenie_properties_bool", []):
                k = str(row.get("type",""))
                v = row.get("value")
                if k and v is not None: result["boolStats"][k] = bool(int(v))

            for row in all_rows.get("weenie_properties_float", []):
                k = str(row.get("type",""))
                v = row.get("value")
                if k and v is not None: result["floatStats"][k] = v

            for row in all_rows.get("weenie_properties_string", []):
                k = str(row.get("type",""))
                v = row.get("value") or ""
                if k: result["stringStats"][k] = v
                if k == "1": name = v
                if k == "15": desc = v

            for row in all_rows.get("weenie_properties_d_i_d", []):
                k = str(row.get("type",""))
                v = row.get("value")
                if k and v is not None:
                    result["didStats"][k] = f"0x{int(v):08x}" if isinstance(v, int) else str(v)

            for row in all_rows.get("weenie_properties_spell_book", []):
                sp = row.get("spell") or row.get("spell_Id")
                if sp: result["spells"].append({"id": sp, "prob": row.get("probability", 1.0)})

            result["name"] = name
            result["description"] = desc
            return {"json": _json.dumps(result, indent=2)}
        except Exception as e:
            import traceback
            return {"error": str(e), "trace": traceback.format_exc()}


    def generate_item_sql(self, params: dict) -> dict:
        """Generate drop-in SQL for a wieldable, sellable, or droppable item."""
        try:
            from aceforge.json_to_sql import (
                _emit_header, _emit_int_props, _emit_bool_props,
                _emit_float_props, _emit_str_props, _emit_did_props, _slug
            )

            def _si(v, default=0):
                try: return int(str(v).strip()) if str(v).strip() else default
                except: return default
            def _sf(v, default=0.0):
                try: return float(str(v).strip()) if str(v).strip() else default
                except: return default

            name      = params.get("name","New Item").strip() or "New Item"
            slug      = _slug(name)
            wcid      = _si(params.get("wcid",""), 810000)
            item_type = _si(params.get("item_type",""), 6)
            icon_raw  = params.get("icon","0x06001036").strip() or "0x06001036"
            icon_int  = int(icon_raw, 16) if icon_raw.startswith("0x") else _si(icon_raw, 0x06001036)
            value     = _si(params.get("value",""), 0)
            encumb    = _si(params.get("encumb",""), 100)
            desc      = params.get("description","").strip()
            long_desc = params.get("long_desc","").strip() or desc
            preset    = params.get("preset","droppable")

            # Core int props
            int_rows = [(1, item_type, "ItemType")]
            bool_rows = []
            float_rows = []
            str_rows  = [(1, name, "Name"), (15, desc or name, "ShortDesc")]
            if long_desc: str_rows.append((16, long_desc, "LongDesc"))
            did_rows  = [
                (1,  0x02000155, "Setup"),
                (3,  0x20000014, "SoundTable"),
                (8,  icon_int,   "Icon"),
                (22, 0x3400002B, "PhysicsEffectTable"),
            ]

            if preset == "wieldable":
                damage   = _si(params.get("damage",""), 20)
                dmg_type = _si(params.get("damage_type",""), 2)
                variance = _sf(params.get("damage_variance",""), 0.25)
                wskill   = _si(params.get("weapon_skill",""), 36)
                wtime    = _si(params.get("weapon_time",""), 50)
                valid_loc= _si(params.get("valid_locations",""), 32768)
                max_stack= _si(params.get("max_stack",""), 1)
                palette_raw = params.get("palette","").strip()
                int_rows += [
                    (9,  damage,    "Damage"),
                    (10, dmg_type,  "DamageType"),
                    (19, value,     "Value"),
                    (5,  encumb,    "EncumbranceVal"),
                    (8,  max_stack, "MaxStackSize"),
                    (26, valid_loc, "ValidLocations"),
                    (74, wskill,    "WeaponSkill"),
                    (80, wtime,     "WeaponTime"),
                ]
                float_rows += [(19, variance, "DamageVariance")]
                bool_rows  += [(93, True, "Inscribable")]
                if palette_raw and palette_raw.startswith("0x"):
                    did_rows.append((4, int(palette_raw, 16), "PaletteBase"))

            elif preset == "sellable":
                burden   = _si(params.get("burden",""), 100)
                buy_mult = _sf(params.get("buy_price",""), 1.0)
                sell_mult= _sf(params.get("sell_price",""), 0.75)
                max_stack= _si(params.get("max_stack",""), 1)
                int_rows += [
                    (5,  burden,    "EncumbranceVal"),
                    (19, value,     "Value"),
                    (8,  max_stack, "MaxStackSize"),
                ]
                float_rows += [
                    (20, buy_mult,  "SellPrice"),
                ]
                bool_rows  += [
                    (11, True, "Inscribable"),
                    (14, True, "Bonded"),
                ]

            else:  # droppable
                burden    = _si(params.get("burden",""), 100)
                max_stack = _si(params.get("max_stack",""), 1)
                stackable = _si(params.get("stackable",""), 0)
                int_rows += [
                    (5,  burden,    "EncumbranceVal"),
                    (8,  max_stack, "MaxStackSize"),
                    (19, value,     "Value"),
                ]
                if stackable:
                    int_rows.append((256, max_stack, "StackSize"))
                bool_rows += [(93, True, "Inscribable")]

            int_rows  += [(93, 1044, "PhysicsState")]

            lines = [
                f"/* ===== FILE: {wcid}_{slug}.sql ===== */", "",
                f"DELETE FROM `weenie` WHERE `class_Id` = {wcid};", "",
                _emit_header(wcid, name, item_type),
                "", _emit_int_props(wcid, [(r[0], r[1], r[2]) for r in int_rows]),
            ]
            if bool_rows:
                lines += ["", _emit_bool_props(wcid, [(r[0], r[1], r[2]) for r in bool_rows])]
            if float_rows:
                lines += ["", _emit_float_props(wcid, [(r[0], r[1], r[2]) for r in float_rows])]
            if str_rows:
                lines += ["", _emit_str_props(wcid, [(r[0], r[1], r[2]) for r in str_rows])]
            if did_rows:
                lines += ["", _emit_did_props(wcid, [(r[0], r[1], r[2]) for r in did_rows])]
            lines.append("")

            return {"sql": "\n".join(lines)}
        except Exception as e:
            import traceback
            return {"error": str(e), "trace": traceback.format_exc()}


    def ping(self) -> dict:
        """Connectivity test — confirms new code is loaded."""
        return {"ok": True, "version": "2.1.polling", "queue_ready": hasattr(self, "_chunk_queue")}


    # ── World Placement — put weenies in the world ───────────────────────────
    #
    # Thin delegation to aceforge.world_api; the terrain comes from cell.dat
    # (landblock_dat) and placements are written to the server's per-landblock
    # SQL files (landblock). Every method returns {"error": …} rather than
    # raising so a failure surfaces in the panel instead of killing the bridge.

    def _world_paths(self) -> tuple:
        """(cell.dat, portal.dat, landblock SQL folder) as currently configured."""
        from . import world_api
        sql_dir = self.config.get(world_api.SQL_DIR_KEY, "")
        return (self._resolve_dat("cell"), self._resolve_dat("portal"), sql_dir)

    def world_status(self) -> dict:
        """Whether the editor has everything it needs, and what's missing."""
        try:
            from . import world_api
            cell, portal, sql_dir = self._world_paths()
            # A stored folder with no landblock files in it is never useful —
            # fall back to discovery rather than leaving the panel stuck.
            replaced_from = ""
            if sql_dir and not world_api.describe_sql_dir(sql_dir)["ok"]:
                replaced_from, sql_dir = sql_dir, ""
            if not sql_dir:
                # Desktop/Documents may be OneDrive-redirected (Known Folder
                # Move), same as the DAT search in _dat_search_folders.
                # Walk up from the weenie folder first: a server-content repo
                # usually holds weenies and landblocks as sibling subtrees, so
                # its root is the highest-signal place to look.
                hints = []
                for start in (self.config.output_dir_for("weenie"),
                              self.config.output_dir):
                    if not start:
                        continue
                    p = Path(start)
                    hints.append(str(p))
                    hints += [str(a) for a in list(p.parents)[:5]]
                roots = [Path.home()]
                onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
                if onedrive:
                    roots.insert(0, Path(onedrive))
                for root in roots:
                    hints += [str(root / "Documents" / "GitHub"),
                              str(root / "Desktop"), str(root / "Documents")]
                sql_dir = world_api.guess_sql_dir(hints)
                if sql_dir:
                    self.config.set(world_api.SQL_DIR_KEY, sql_dir)
                    self.config.save()
                elif replaced_from:
                    sql_dir = replaced_from        # nothing better — keep theirs
            # A folder that exists isn't necessarily a *landblock* folder —
            # report what's actually in it so a wrong pick explains itself.
            desc = world_api.describe_sql_dir(sql_dir)
            if replaced_from and desc["ok"]:
                desc = dict(desc, reason=desc["reason"] + " (auto-corrected — the "
                            "previous folder held no landblock files)")
            return {
                "cellDat": cell, "cellDatOk": bool(cell and Path(cell).exists()),
                "portalDat": portal, "portalDatOk": bool(portal and Path(portal).exists()),
                "sqlDir": sql_dir, "sqlDirOk": desc["ok"],
                "sqlDirReason": desc["reason"],
                "sqlDirCount": desc.get("count", 0),
                "sqlDirSuggestions": desc.get("suggestions", []),
                "ready": all([cell and Path(cell).exists(),
                              portal and Path(portal).exists(),
                              desc["ok"]]),
            }
        except Exception as e:
            return {"error": str(e)}

    def world_browse_sql_dir(self) -> dict:
        """Folder picker for the landblock SQL folder."""
        try:
            from . import world_api
            if self._window is None:
                return {"error": "Window not ready"}
            result = self._window.create_file_dialog(dialog_type=20)  # FOLDER_DIALOG
            if not result:
                return {"cancelled": True}
            path = str(result[0] if isinstance(result, (list, tuple)) else result)
            desc = world_api.describe_sql_dir(path)
            # If they picked a parent (a repo root, say), accept the landblock
            # folder underneath rather than making them browse again.
            if not desc["ok"] and desc.get("suggestions"):
                path = desc["suggestions"][0]
                desc = world_api.describe_sql_dir(path)
            self.config.set(world_api.SQL_DIR_KEY, path)
            self.config.save()
            return {"path": path, "ok": desc["ok"], "reason": desc["reason"],
                    "count": desc.get("count", 0)}
        except Exception as e:
            return {"error": str(e)}

    def world_set_sql_dir(self, path: str) -> dict:
        try:
            from . import world_api
            self.config.set(world_api.SQL_DIR_KEY, str(path or "").strip())
            self.config.save()
            return {"ok": True, "path": self.config.get(world_api.SQL_DIR_KEY, "")}
        except Exception as e:
            return {"error": str(e)}

    def world_list_weenies(self) -> dict:
        """The user's authored weenies, for the placement picker."""
        try:
            from . import world_api
            # output_dir_for() applies the per-type overrides and falls back to
            # the default; config.get("output_dir") would miss that default.
            folders = [self.config.output_dir]
            folders += [self.config.output_dir_for(t)
                        for t in ("weenie", "quest", "event")]
            seen, unique = set(), []
            for f in folders:
                if f and f not in seen:
                    seen.add(f); unique.append(f)
            return {"weenies": world_api.scan_weenies(unique), "folders": unique}
        except Exception as e:
            return {"error": str(e)}

    def world_load_landblock(self, landblock: str) -> dict:
        """Terrain mesh + existing placements for one landblock."""
        try:
            from . import world_api
            cell, portal, sql_dir = self._world_paths()
            if not (cell and Path(cell).exists()):
                return {"error": "client_cell_1.dat not found — set it in Settings"}
            if not (portal and Path(portal).exists()):
                return {"error": "client_portal.dat not found — set it in Settings"}
            lb = world_api.parse_landblock_id(landblock)
            if lb is None:
                return {"error": f"'{landblock}' is not a landblock id (try C6A9)"}
            return world_api.load_landblock(cell, portal, sql_dir, lb)
        except Exception as e:
            return {"error": str(e)}

    def world_is_enabled(self) -> dict:
        """Whether the WorldForge tab should be shown at all."""
        try:
            return {"enabled": bool(self.config.get("worldforge_enabled", False))}
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def world_set_enabled(self, on: bool) -> dict:
        """
        Show or hide the WorldForge tab, persisted to config.

        Kept as an explicit toggle rather than a build flag so the same binary
        can ship with the feature dark and still be exercised in place.
        """
        try:
            self.config.set("worldforge_enabled", bool(on))
            self.config.save()
            return {"enabled": bool(on)}
        except Exception as e:
            return {"error": str(e)}

    def world_dat_info(self) -> dict:
        """
        Which DAT set is in use and what's in it.

        The counts let a user tell sets apart — a custom set built in ACME will
        differ from retail in landblock/cell totals, and several byte-identical
        copies of retail are easy to accumulate.
        """
        try:
            from . import world_api
            cell, portal, _sql = self._world_paths()
            info = {"cellDat": cell, "portalDat": portal,
                    "folder": self.config.get("dat_folder", ""),
                    "landblocks": 0, "cells": 0, "sizeMB": 0}
            if cell and Path(cell).exists():
                info["sizeMB"] = round(Path(cell).stat().st_size / 1048576)
                db = world_api._dat(cell)
                info["landblocks"] = sum(1 for f in db.entries if (f & 0xFFFF) == 0xFFFF)
                info["cells"] = sum(1 for f in db.entries
                                    if 0x0100 <= (f & 0xFFFF) < 0xFF00)
            return info
        except Exception as e:
            return {"error": str(e)}

    def world_browse_dat_folder(self) -> dict:
        """
        Choose the folder holding the DAT set — a client install, or a custom
        set built in ACME.
        """
        try:
            from . import world_api
            if self._window is None:
                return {"error": "Window not ready"}
            result = self._window.create_file_dialog(dialog_type=20)  # FOLDER_DIALOG
            if not result:
                return {"cancelled": True}
            folder = Path(result[0] if isinstance(result, (list, tuple)) else result)
            missing = [name for name, _key in self._DAT_FILES.values()
                       if name in ("client_cell_1.dat", "client_portal.dat")
                       and not (folder / name).exists()]
            if missing:
                return {"error": f"{folder.name} is missing {', '.join(missing)}"}
            self.config.set("dat_folder", str(folder))
            # Drop the resolved per-file paths so they re-resolve from the new
            # folder, and release open handles or we'd keep reading the old set.
            for _name, key in self._DAT_FILES.values():
                self.config.set(key, "")
            self.config.save()
            world_api.close_dats()
            return dict({"path": str(folder)}, **self.world_dat_info())
        except Exception as e:
            return {"error": str(e)}

    def world_terrain_atlas(self) -> dict:
        """
        The 32 terrain textures as one base64 PNG sheet.

        Fetched once per session — the sheet is the same for every landblock.
        Building it decodes 32 DXT textures (~6 s), so it is cached on disk;
        subsequent calls are effectively free.
        """
        try:
            from . import world_api
            from .landblock_dat import build_terrain_atlas, ATLAS_COLS, ATLAS_ROWS
            _cell, portal, _sql = self._world_paths()
            if not (portal and Path(portal).exists()):
                return {"error": "client_portal.dat not found"}
            png = build_terrain_atlas(world_api._dat(portal), portal)
            if png is None:
                return {"error": "Pillow not installed — terrain textures "
                                 "unavailable, falling back to flat colours"}
            import base64 as _b64
            return {"png": _b64.b64encode(png).decode("ascii"),
                    "cols": ATLAS_COLS, "rows": ATLAS_ROWS,
                    "bytes": len(png)}
        except Exception as e:
            return {"error": str(e)}

    def world_resolve_cell(self, params: dict) -> dict:
        """Shortlist the interior cells that could contain a point."""
        try:
            from . import world_api
            cell, portal, _sql = self._world_paths()
            lb = world_api.parse_landblock_id(params.get("landblock"))
            if lb is None:
                return {"error": "Missing or invalid landblock"}
            return world_api.resolve_cell(
                cell, portal, lb,
                float(params.get("x")), float(params.get("y")),
                float(params.get("z")),
            )
        except Exception as e:
            return {"error": str(e)}

    def world_place(self, params: dict) -> dict:
        """Write a placement into the landblock's SQL file."""
        try:
            from . import world_api
            cell, portal, sql_dir = self._world_paths()
            lb = world_api.parse_landblock_id(params.get("landblock"))
            if lb is None:
                return {"error": "Missing or invalid landblock"}
            z = params.get("z")
            return world_api.place_weenie(
                sql_dir=sql_dir, landblock=lb,
                wcid=int(params.get("wcid")),
                x=float(params.get("x")), y=float(params.get("y")),
                z=None if z in (None, "") else float(z),
                heading=float(params.get("heading") or 0.0),
                name=str(params.get("name") or ""),
                cell=int(params.get("cell") or 0),
                cell_dat=cell, portal_dat=portal,
            )
        except Exception as e:
            return {"error": str(e)}

    def world_move(self, params: dict) -> dict:
        """Reposition an existing placement."""
        try:
            from . import world_api
            cell, portal, sql_dir = self._world_paths()
            lb = world_api.parse_landblock_id(params.get("landblock"))
            if lb is None:
                return {"error": "Missing or invalid landblock"}
            z, heading = params.get("z"), params.get("heading")
            return world_api.move_instance(
                sql_dir=sql_dir, landblock=lb,
                guid=int(params.get("guid")),
                x=float(params.get("x")), y=float(params.get("y")),
                z=None if z in (None, "") else float(z),
                heading=None if heading in (None, "") else float(heading),
                cell_dat=cell, portal_dat=portal,
            )
        except Exception as e:
            return {"error": str(e)}

    def world_remove(self, params: dict) -> dict:
        """Delete a placement from the landblock's SQL file."""
        try:
            from . import world_api
            _cell, _portal, sql_dir = self._world_paths()
            lb = world_api.parse_landblock_id(params.get("landblock"))
            if lb is None:
                return {"error": "Missing or invalid landblock"}
            return world_api.remove_instance(sql_dir, lb, int(params.get("guid")))
        except Exception as e:
            return {"error": str(e)}
