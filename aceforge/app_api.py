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
            "wcid_ranges":  self.config.get_wcid_ranges(),
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
            if "api_key" in data and data["api_key"]:
                self.config.api_key = data["api_key"]
            if "wcid_ranges" in data:
                self.config.set("wcid_ranges", data["wcid_ranges"])

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
            f"VALUES ({new_wcid}, '{item['class_name']}', {item.get('weenie_type', 1)}, NOW());\n",
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
            f"VALUES ({new_wcid}, '{class_name}', {source.get('weenie_type', 1)}, NOW());\n",
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

    def save_sql(self, sql_text: str, wcid: int, name: str) -> dict:
        try:
            output_dir = self.config.output_dir or str(
                Path.home() / "Documents" / "ACEForge" / "output"
            )
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
            return {"success": True, "path": str(fpath), "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
        """Save one AI-generated SQL file immediately."""
        try:
            output_dir = str(self.config.output_dir or "").strip()
            if not output_dir:
                output_dir = str(Path.home() / "Documents" / "ACEForge" / "output")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            written = parse_and_save_files(content, output_dir, subfolder="")
            if not written:
                # Fallback: save with suggested name
                from aceforge.sql_parser import sanitize_filename, clean_sql
                fname = sanitize_filename(suggested_name)
                fpath = Path(output_dir) / fname
                fpath.write_text(clean_sql(content), encoding="utf-8")
                written = [str(fpath)]
            return {
                "success": True,
                "files": [os.path.basename(f) for f in written],
                "folder": output_dir,
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
            written = parse_and_save_files(full_response, output_dir, subfolder="")
            if not written:
                return {"success": False, "error": "Parser found no SQL content in response. Ensure AI output contains FILE: markers or valid SQL."}
            return {
                "success": True,
                "files":  [os.path.basename(f) for f in written],
                "count":  len(written),
                "folder": output_dir,
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
        # slugified name embedded in the generated filename.
        file_to_npc = {}  # file_idx -> (name, personality)
        for fi, f in enumerate(files):
            if f.get("type") != "npc":
                continue
            fname_slug = f["filename"].lower()
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
        Download the new release zip, then hand off installation to a
        temporary batch script that runs after ACEForge exits — avoiding
        the Windows file-lock on the running ACEForge.exe.
        """
        import urllib.request, zipfile, shutil, sys, os, subprocess, threading, time
        from pathlib import Path

        if not download_url:
            return {"success": False, "error": "No download URL provided"}

        try:
            # Determine install root (where ACEForge.exe or main.py lives)
            if hasattr(sys, "_MEIPASS"):
                install_root = Path(sys.executable).parent
                exe_path     = Path(sys.executable)
            else:
                install_root = Path(__file__).parent.parent
                exe_path     = Path(sys.executable)

            tmp_zip = Path(os.environ.get("TEMP", str(Path.home()))) / "ACEForge_update.zip"
            tmp_dir = Path(os.environ.get("TEMP", str(Path.home()))) / "ACEForge_update_extract"

            # ── Download ──────────────────────────────────────────────────────
            self._ollama_event("download_start", "Downloading update…", 0, 0)

            def on_progress(block, block_size, total):
                if total > 0:
                    pct = min(100, int(block * block_size * 100 / total))
                    mb  = round(block * block_size / 1024 / 1024, 1)
                    mbt = round(total / 1024 / 1024, 1)
                    self._ollama_event("download_progress",
                        f"Downloading update… {mb} MB / {mbt} MB", pct, 100)

            urllib.request.urlretrieve(download_url, str(tmp_zip), on_progress)
            self._ollama_event("download_done", "Download complete. Preparing installer…", 100, 100)

            # ── Extract to temp dir ───────────────────────────────────────────
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(tmp_dir)
            tmp_zip.unlink(missing_ok=True)

            # Zip has ACEForge/ at its root — find the inner folder
            src_root = next(
                (tmp_dir / d for d in os.listdir(tmp_dir)
                 if (tmp_dir / d).is_dir()), tmp_dir
            )

            # ── Write a batch script that runs AFTER we exit ──────────────────
            # Windows locks the running .exe, so we can't copy over it while
            # it's alive.  The batch script waits for our PID to disappear,
            # then copies every file from the extracted zip into the install
            # root, relaunches ACEForge, and cleans up after itself.
            pid       = os.getpid()
            bat_path  = Path(os.environ.get("TEMP", str(Path.home()))) / "aceforge_update.bat"
            install_q = str(install_root).replace("/", "\\")
            src_q     = str(src_root).replace("/", "\\")
            tmp_dir_q = str(tmp_dir).replace("/", "\\")
            exe_q     = str(exe_path).replace("/", "\\")

            bat_lines = [
                "@echo off",
                "setlocal enabledelayedexpansion",
                f"echo Waiting for ACEForge to close...",
                # Wait for the visible child process PID to exit first.
                # Every if/goto here is a single top-level statement, never
                # nested inside parentheses — a goto jumping out of an open
                # if(...) block corrupts the batch parser's bracket-tracking
                # state, a documented Windows batch quirk.
                f":waitloop",
                f"tasklist /FI \"PID eq {pid}\" 2>NUL | find \"{pid}\" >NUL",
                f"if errorlevel 1 goto waitloopdone",
                f"timeout /t 1 /nobreak >NUL",
                f"goto waitloop",
                f":waitloopdone",
                # PyInstaller onefile builds run a separate bootloader parent
                # process under the same exe name, which can hold a lock on
                # the .exe for a short window after the visible child PID
                # exits (it has its own temp-dir cleanup to finish). Give it
                # a moment, then also wait until no process with this image
                # name is running at all before attempting to copy.
                f"timeout /t 1 /nobreak >NUL",
                f":waitimage",
                f"tasklist /FI \"IMAGENAME eq {exe_path.name}\" 2>NUL | find /I \"{exe_path.name}\" >NUL",
                f"if errorlevel 1 goto waitimagedone",
                f"timeout /t 1 /nobreak >NUL",
                f"goto waitimage",
                f":waitimagedone",
                f"echo Copying update files...",
                # Retry the copy a few times in case the file is still
                # transiently locked (antivirus scan, slow handle release).
                # The goto below is intentionally OUTSIDE any parenthetical
                # block — a goto from inside nested if(...) parens corrupts
                # the batch parser's bracket-tracking state.
                f"set COPY_TRIES=0",
                f":copyretry",
                f"set /a COPY_TRIES+=1",
                # Robocopy: source → install root, all files/subdirs, quiet
                f"robocopy \"{src_q}\" \"{install_q}\" /E /IS /IT /IM /NFL /NDL /NJH /NJS >NUL 2>&1",
                # Fall back to xcopy if robocopy isn't available
                f"if errorlevel 8 xcopy /E /Y /I \"{src_q}\\*\" \"{install_q}\\\"",
                # Verify the exe actually landed before declaring success —
                # if the copy silently failed (file still locked), retry up
                # to 5 times with a short pause. Each check/goto is a single
                # top-level statement, never nested inside parentheses.
                f"if exist \"{exe_q}\" goto copyok",
                f"if !COPY_TRIES! GEQ 5 goto copyok",
                f"timeout /t 2 /nobreak >NUL",
                f"goto copyretry",
                f":copyok",
                f"echo Relaunching ACEForge...",
                f"start \"\" \"{exe_q}\"",
                # Self-delete and clean up extracted temp dir
                f"rd /s /q \"{tmp_dir_q}\" 2>NUL",
                f"del \"%~f0\"",
            ]

            # Encode defensively: strip/replace anything outside ASCII rather
            # than crashing the whole update on a single stray character —
            # the exact failure mode that motivated this fix in the first
            # place (a literal "…" in an echo string broke ascii encoding).
            bat_text = "\r\n".join(bat_lines)
            bat_path.write_text(bat_text.encode("ascii", errors="replace").decode("ascii"), encoding="ascii")

            # ── Launch the batch detached, then exit ─────────────────────────
            self._ollama_event("download_done",
                "Update ready. ACEForge will restart automatically.", 100, 100)

            def _launch_and_exit():
                time.sleep(0.8)   # let the UI message render
                subprocess.Popen(
                    ["cmd.exe", "/c", str(bat_path)],
                    creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                               | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                    close_fds=True,
                )
                time.sleep(0.4)   # give cmd.exe time to detach
                os._exit(0)       # hard exit so the batch can replace the exe

            threading.Thread(target=_launch_and_exit, daemon=True).start()
            return {"success": True, "message": "Update ready. Restarting…"}

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


    APP_VERSION = "0.3.09"

    def get_version(self) -> str:
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
            latest = data.get("tag_name", "").lstrip("v")
            notes  = data.get("body", "")
            assets = data.get("assets", [])
            dl_url = next((a["browser_download_url"] for a in assets
                           if a["name"].endswith(".zip")), "")
            def _ver(v):
                try: return tuple(int(x) for x in v.split("."))
                except: return (0,)
            has_update = bool(latest) and _ver(latest) > _ver(self.APP_VERSION)
            return {"has_update": has_update,
                    "latest_version": latest,
                    "current_version": self.APP_VERSION,
                    "release_notes": notes,
                    "download_url": dl_url}
        except Exception as e:
            return {"has_update": False, "error": str(e),
                    "current_version": self.APP_VERSION}

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
