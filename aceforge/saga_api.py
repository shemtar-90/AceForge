"""
saga_api.py — SagaForge Backend Mixin

Three-stage pipeline:
  1. saga_build_bible()     — AI produces a Story Bible JSON from a prompt
  2. (approval in JS)       — user reviews and confirms before generation
  3. saga_generate_file()   — generates one file at a time, streams via poll_generation

The AI never touches quest flag names, WCIDs, trigger types, or emote structure.
All of that is handled by saga_templates.py.  The AI's only creative job is
supplying dialogue strings for [PLACEHOLDER] slots.
"""

from __future__ import annotations
import json
import os
import re
import threading
from pathlib import Path


# ── System prompts ────────────────────────────────────────────────────────────

_BIBLE_SYSTEM = """You are an Asheron's Call quest designer for the private server "{server}".
Your job is to read a quest idea and output a structured Story Bible as JSON.

CRITICAL: Output ONLY a valid JSON object. No markdown fences. No explanation text.
No SQL. No WeenieFab. Just the raw JSON object.

The JSON must follow this exact schema — do NOT add extra fields, do NOT omit required ones:

{{
  "title": "Short quest chain title",
  "summary": "2-3 sentence description of the full chain",
  "saga_type": "one of: kill_task_chain | item_turnin_chain | multi_npc_story | mixed",
  "npcs": [
    {{
      "id": "npc_0",
      "name": "Full NPC Name",
      "role": "One sentence: what this NPC does in the chain",
      "dialogue_notes": "Personality, tone, speech style — brief",
      "quest_flags": ["PrimaryFlagName", "PrimaryFlagNameDone"],
      "gives_item_id": "item_0 OR null",
      "takes_item_id": "item_1 OR null",
      "kill_task_flag": "KillFlagName OR null"
    }}
  ],
  "creatures": [
    {{
      "id": "creature_0",
      "name": "Creature Name",
      "creature_type": "Human|Tumerok|Virindi|Drudge|Undead|Mosswart|Lugian|Olthoi|Shadow|Golem",
      "level": 100,
      "kill_task_flag": "FlagNameKT",
      "kill_count": 10,
      "respawn_delay": 300,
      "init_create": 3,
      "max_create": 5
    }}
  ],
  "items": [
    {{
      "id": "item_0",
      "name": "Item Name",
      "purpose": "What this item is for in the chain",
      "description": "Flavor text for the item",
      "stackable": false
    }}
  ],
  "quest_flags": [
    {{
      "name": "ExactFlagName",
      "min_delta": 0,
      "max_solves": 1,
      "message": "quest complete",
      "purpose": "What this flag tracks"
    }}
  ],
  "flow": [
    {{"step": 1, "actor": "npc_0", "action": "Brief description of what happens at this step"}}
  ],
  "rewards": [
    {{"type": "xp", "value": "5%"}},
    {{"type": "luminance", "value": 2000000}},
    {{"type": "item", "wcid": 51954, "name": "Durable Legendary Key"}}
  ]
}}

RULES:
- Quest flag names must be PascalCase, no spaces, globally unique within this chain
- Kill task flags end with "KT" (e.g. VirindStrikerKT)
- Completion flags end with "Done" (e.g. VethMissionDone)
- Every NPC must have at least 2 quest_flags: ["MainFlag", "MainFlagDone"]
- If an NPC checks kills, set kill_task_flag to the creature's kill_task_flag
- gives_item_id and takes_item_id reference item "id" fields
- Kill task creatures must have a quest_flags entry with max_solves=100 and message="kill counter"
- Do NOT include "wcid", "generator_wcid", or "quest_id" fields — those are assigned by the app
- Flow steps must reference NPC or creature "id" values in the "actor" field
- Keep it realistic for an AC private server — 1 to 4 NPCs, 0 to 2 creature types
"""

_CREATURE_SYSTEM = """You are an Asheron's Call creature stat designer for the server "{server}".
Output ONLY a JSON object with these fields. No SQL. No explanation.

{{
  "name": "exact name from context",
  "creature_type": "Human|Tumerok|Virindi|Drudge|Undead|Mosswart|Lugian|Olthoi|Shadow|Golem",
  "level": 100,
  "health": 800,
  "stamina": 500,
  "mana": 200,
  "strength": 200,
  "endurance": 180,
  "quickness": 160,
  "coordination": 170,
  "focus": 80,
  "self": 80,
  "melee_defense": 150,
  "attack_skill_name": "HeavyWeapons",
  "attack_skill": 180,
  "armor": 60,
  "scale": 1.0,
  "visual_range": 20.0,
  "loot_tier": 3101,
  "attackable": true,
  "treasure_corpse": true
}}

Scale stats appropriate to the level. loot_tier: 3101=T4, 3102=T5, 3103=T6, 3104=T7, 3105=T8.
"""

_DIALOGUE_SYSTEM = """You are writing NPC dialogue for an Asheron's Call quest for the server "{server}".

You will receive:
- The NPC's name, role, and personality notes
- A list of dialogue slot names and their context
- The full Story Bible for context

Output ONLY a JSON object mapping slot names to dialogue strings.
No markdown. No explanation. Just the JSON.

Rules:
- Keep each line of dialogue under 180 characters
- Match the NPC's personality from dialogue_notes
- Reference lore, other NPCs, or items by name where appropriate
- ALREADY_DONE_DIALOGUE should be polite but firm
- KILL_PROGRESS_DIALOGUE should be encouraging
- REWARD_DIALOGUE should feel satisfying and complete the story beat
- WRONG_ITEM_DIALOGUE should be confused/dismissive but not mean
- Do not use modern slang — this is a fantasy MMO
- All strings must be plain text — no quotes inside, no special characters
"""


class SagaMixin:
    """
    Mixin for AceForgeAPI providing all SagaForge backend methods.
    Mixed in via class inheritance — shares self.config, self.api_client,
    self._chunk_queue, self._generating, and self._process_emote_scripts().
    """

    # ── Stage 1: Build Story Bible ────────────────────────────────────────────

    def saga_build_bible(self, prompt: str, saga_type: str) -> dict:
        """
        Phase 1: AI produces a Story Bible JSON from the user's prompt.
        WCIDs are then assigned deterministically by allocate_wcids().
        Returns {success, bible_json (str)} or {success: False, error}.
        """
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}
        if self._generating:
            return {"success": False, "error": "Generation already in progress."}

        server = self.config.server_name or "Shattered Dawn"
        wcid_ranges = self.config.get_wcid_ranges()

        # Build WCID preview table so AI understands the ranges (it won't assign them)
        range_summary = "\n".join(
            f"  {k}: next available = {v.get('next', v.get('start', 0))}"
            for k, v in wcid_ranges.items()
        )

        system = _BIBLE_SYSTEM.format(server=server)
        user   = (
            f"Server: {server}\n"
            f"Saga type: {saga_type}\n\n"
            f"Quest idea:\n{prompt}\n\n"
            "Output ONLY the JSON Story Bible."
        )

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        self._generating = True
        result_holder = {}

        def _done(text: str):
            self._generating = False
            try:
                # Strip any accidental markdown fences
                clean = re.sub(r"^```[a-z]*\n?|```$", "", text.strip(), flags=re.MULTILINE).strip()
                bible_draft = json.loads(clean)

                # Assign WCIDs deterministically
                from aceforge.saga_templates import allocate_wcids
                bible = allocate_wcids(bible_draft, self.config)

                result_holder["bible"] = bible
                self._chunk_queue.put({
                    "type": "saga_bible_ready",
                    "bible": bible,
                })
            except Exception as e:
                self._chunk_queue.put({
                    "type": "error",
                    "message": f"Story Bible parse error: {e}\n\nRaw output:\n{text[:800]}",
                })

        def _chunk(text: str):
            self._chunk_queue.put({"type": "chunk", "text": text})

        def _err(msg: str):
            self._generating = False
            self._chunk_queue.put({"type": "error", "message": msg})

        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system, user, _chunk, _done, _err, 0.7),
            daemon=True,
        ).start()

        return {"success": True}

    # ── Stage 3: Generate one file ────────────────────────────────────────────

    def saga_generate_file(self, bible_json: str, file_index: int) -> dict:
        """
        Phase 3: Generate one file from the Story Bible.

        Routing by file type:
          item      → deterministic SQL (saga_templates.quest_item_sql)
          generator → deterministic SQL (saga_templates.generator_sql)
          quests    → deterministic SQL (saga_templates.quest_flags_sql)
          creature  → AI for stats, deterministic for SQL structure
          npc       → AI for dialogue only, deterministic for emote structure
        """
        if self._generating:
            return {"success": False, "error": "Generation already in progress."}
        if not self.config.api_key:
            return {"success": False, "error": "No API key configured."}

        try:
            bible = json.loads(bible_json)
        except Exception as e:
            return {"success": False, "error": f"Bible parse error: {e}"}

        files = bible.get("files", [])
        if file_index >= len(files):
            return {"success": False, "error": "File index out of range."}

        file_entry = files[file_index]
        ftype      = file_entry.get("type", "")
        fname      = file_entry.get("name", f"file_{file_index}.sql")
        ref        = file_entry.get("ref", "")
        total      = len(files)

        # ── Fully deterministic types ─────────────────────────────────────────
        from aceforge.saga_templates import (
            quest_flags_sql, generator_sql, quest_item_sql,
            npc_weeniefab_skeleton, extract_placeholders, splice_dialogue,
        )

        if ftype == "quests":
            sql = quest_flags_sql(bible)
            return self._saga_save_and_emit(sql, fname, file_index, total)

        if ftype == "generator":
            sql = generator_sql(bible, ref)
            return self._saga_save_and_emit(sql, fname, file_index, total)

        if ftype == "item":
            sql = quest_item_sql(bible, ref)
            return self._saga_save_and_emit(sql, fname, file_index, total)

        # ── Creature: AI for stats, deterministic SQL structure ───────────────
        if ftype == "creature":
            return self._saga_generate_creature(bible, ref, fname, file_index, total)

        # ── NPC: deterministic skeleton + AI dialogue only ────────────────────
        if ftype == "npc":
            return self._saga_generate_npc(bible, ref, fname, file_index, total)

        return {"success": False, "error": f"Unknown file type: {ftype}"}

    # ── Creature generation ───────────────────────────────────────────────────

    def _saga_generate_creature(self, bible: dict, ref: str, fname: str,
                                 file_index: int, total: int) -> dict:
        creatures = {c["id"]: c for c in bible.get("creatures", [])}
        c = creatures.get(ref)
        if not c:
            return {"success": False, "error": f"Creature ref '{ref}' not found in Bible."}

        server = self.config.server_name or "Shattered Dawn"
        system = _CREATURE_SYSTEM.format(server=server)
        user   = (
            f"Design stats for this creature:\n"
            f"Name: {c['name']}\n"
            f"Type: {c.get('creature_type', 'Human')}\n"
            f"Level: {c.get('level', 100)}\n"
            f"Role: Kill task target for {c.get('kill_task_flag', 'unknown')} "
            f"(player must kill {c.get('kill_count', 10)})\n\n"
            f"Full Story Bible for context:\n{json.dumps(bible, indent=2)[:3000]}"
        )

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        self._generating = True

        def _done(text: str):
            self._generating = False
            try:
                clean  = re.sub(r"^```[a-z]*\n?|```$", "", text.strip(), flags=re.MULTILINE).strip()
                stats  = json.loads(clean)

                # Build creature SQL via json_to_sql
                from aceforge.json_to_sql import json_to_sql as _j2s
                stats["wcid"]         = c["wcid"]
                stats["content_type"] = "creature"
                stats["class_name"]   = stats.get("name", c["name"])
                stats["kill_quest"]   = c.get("kill_task_flag", "")
                sql = _j2s(stats, fname)
                self._saga_save_and_emit(sql, fname, file_index, total, _sync=True)
            except Exception as e:
                self._chunk_queue.put({
                    "type": "saga_file_error",
                    "file_index": file_index,
                    "file_name": fname,
                    "error": str(e),
                    "total": total,
                })

        def _chunk(t: str):
            self._chunk_queue.put({"type": "chunk", "text": t})

        def _err(msg: str):
            self._generating = False
            self._chunk_queue.put({"type": "error", "message": msg})

        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system, user, _chunk, _done, _err, 0.3),
            daemon=True,
        ).start()
        return {"success": True}

    # ── NPC generation ────────────────────────────────────────────────────────

    def _saga_generate_npc(self, bible: dict, ref: str, fname: str,
                            file_index: int, total: int) -> dict:
        npcs = {n["id"]: n for n in bible.get("npcs", [])}
        npc  = npcs.get(ref)
        if not npc:
            return {"success": False, "error": f"NPC ref '{ref}' not found in Bible."}

        from aceforge.saga_templates import (
            npc_weeniefab_skeleton, extract_placeholders, splice_dialogue,
        )

        # Build the structural skeleton — AI cannot get this wrong
        skeleton     = npc_weeniefab_skeleton(bible, ref)
        placeholders = extract_placeholders(skeleton)

        server = self.config.server_name or "Shattered Dawn"
        system = _DIALOGUE_SYSTEM.format(server=server)

        # Give AI exactly what it needs: personality + slot list + Bible summary
        slot_ctx = "\n".join(
            f'  "{p}": "<dialogue for this slot>"'
            for p in placeholders
        )
        user = (
            f"NPC: {npc['name']}\n"
            f"Role: {npc.get('role', '')}\n"
            f"Personality: {npc.get('dialogue_notes', 'Friendly and helpful')}\n\n"
            f"Story Bible summary:\n"
            f"  Title: {bible.get('title', '')}\n"
            f"  Summary: {bible.get('summary', '')}\n"
            f"  Flow: {json.dumps(bible.get('flow', []))}\n\n"
            f"Fill in these dialogue slots:\n{{\n{slot_ctx}\n}}\n\n"
            f"Output ONLY the JSON object. Each value is a plain dialogue string."
        )

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        self._generating = True

        def _done(text: str):
            self._generating = False
            try:
                clean    = re.sub(r"^```[a-z]*\n?|```$", "", text.strip(), flags=re.MULTILINE).strip()
                dialogue = json.loads(clean)

                # Splice dialogue into the deterministic skeleton
                completed_script = splice_dialogue(skeleton, dialogue)

                # Build the NPC base SQL (no emotes yet)
                npc_sql = self._saga_npc_base_sql(npc, bible, fname)

                # Append emote block and convert via existing emote parser
                full_text = npc_sql + "\n\n" + completed_script
                sql       = self._process_emote_scripts(full_text)

                self._saga_save_and_emit(sql, fname, file_index, total, _sync=True)
            except Exception as e:
                import traceback
                self._chunk_queue.put({
                    "type": "saga_file_error",
                    "file_index": file_index,
                    "file_name": fname,
                    "error": f"{e}\n{traceback.format_exc()}",
                    "total": total,
                })

        def _chunk(t: str):
            self._chunk_queue.put({"type": "chunk", "text": t})

        def _err(msg: str):
            self._generating = False
            self._chunk_queue.put({"type": "error", "message": msg})

        threading.Thread(
            target=self.api_client.stream_generate,
            args=(system, user, _chunk, _done, _err, 0.75),
            daemon=True,
        ).start()
        return {"success": True}

    # ── NPC base SQL (structure only, no emotes) ──────────────────────────────

    def _saga_npc_base_sql(self, npc: dict, bible: dict, fname: str) -> str:
        """
        Emit the weenie table rows for an NPC.
        Emotes are handled separately via WeenieFab skeleton.
        """
        from aceforge.saga_templates import _slug, _esc, TIMESTAMP

        wcid = npc["wcid"]
        name = npc["name"]

        lines = [
            f"/* ===== FILE: {fname} ===== */",
            f"/* Generated by SagaForge — {TIMESTAMP} */",
            "",
            f"DELETE FROM `weenie` WHERE `class_Id` = {wcid};",
            "",
            "INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)",
            f"VALUES ({wcid}, '{_slug(name)}', 10, '{TIMESTAMP}') /* Creature */;",
            "",
            "INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)",
            f"VALUES ({wcid},   1,         16) /* ItemType - Creature */",
            f"     , ({wcid},   2,         31) /* CreatureType - Human */",
            f"     , ({wcid},   6,         -1) /* ItemsCapacity */",
            f"     , ({wcid},   7,         -1) /* ContainersCapacity */",
            f"     , ({wcid},  16,         32) /* ItemUseable - Remote */",
            f"     , ({wcid},  25,        100) /* Level */",
            f"     , ({wcid},  93,    6292504) /* PhysicsState */",
            f"     , ({wcid},  95,          8) /* RadarBlipColor - Yellow */",
            f"     , ({wcid}, 113,          1) /* Gender - Male */",
            f"     , ({wcid}, 133,          4) /* ShowableOnRadar - ShowAlways */",
            f"     , ({wcid}, 134,         16) /* PlayerKillerStatus - RubberGlue */",
            f"     , ({wcid}, 146,          0) /* XpOverride */;",
            "",
            "INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)",
            f"VALUES ({wcid},   1, True ) /* Stuck */",
            f"     , ({wcid},   8, True ) /* AllowGive */",
            f"     , ({wcid},  19, False) /* Attackable */",
            f"     , ({wcid},  52, True ) /* AiImmobile */;",
            "",
            "INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)",
            f"VALUES ({wcid},   1,       5) /* HeartbeatInterval */",
            f"     , ({wcid},   2,       0) /* HeartbeatTimestamp */",
            f"     , ({wcid},   3,    0.16) /* HealthRate */",
            f"     , ({wcid},   4,       5) /* StaminaRate */",
            f"     , ({wcid},   5,       1) /* ManaRate */",
            f"     , ({wcid},  54,       3) /* UseRadius */;",
            "",
            "INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)",
            f"VALUES ({wcid},   1, '{_esc(name)}') /* Name */;",
            "",
            "INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)",
            f"VALUES ({wcid},   1, 0x02000001) /* Setup */",
            f"     , ({wcid},   2, 0x09000001) /* MotionTable */",
            f"     , ({wcid},   3, 0x20000001) /* SoundTable */",
            f"     , ({wcid},   4, 0x30000000) /* CombatTable */",
            f"     , ({wcid},   8, 0x06001036) /* Icon */;",
            "",
            "INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)",
            f"VALUES ({wcid},   1, 180, 0, 0) /* Strength */",
            f"     , ({wcid},   2, 180, 0, 0) /* Endurance */",
            f"     , ({wcid},   3, 180, 0, 0) /* Quickness */",
            f"     , ({wcid},   4, 180, 0, 0) /* Coordination */",
            f"     , ({wcid},   5, 150, 0, 0) /* Focus */",
            f"     , ({wcid},   6, 150, 0, 0) /* Self */;",
            "",
            "INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)",
            f"VALUES ({wcid},   1,   100, 0, 0,  190) /* MaxHealth */",
            f"     , ({wcid},   3,   100, 0, 0,  280) /* MaxStamina */",
            f"     , ({wcid},   5,   100, 0, 0,  250) /* MaxMana */;",
        ]

        return "\n".join(lines)

    # ── Save helper ───────────────────────────────────────────────────────────

    def _saga_save_and_emit(self, sql: str, fname: str, file_index: int,
                             total: int, _sync: bool = False) -> dict:
        """
        Save SQL to the output folder and push a saga_file_done event to the queue.
        _sync=True: called from inside a thread (already off main thread).
        _sync=False: called directly (deterministic files, no threading needed).
        """
        save = self._save_single_file(sql, fname)
        self._chunk_queue.put({
            "type":       "saga_file_done",
            "file_index": file_index,
            "file_name":  fname,
            "save":       save,
            "total":      total,
        })
        if not _sync:
            return {"success": True}
        return save

    # ── Open output folder ────────────────────────────────────────────────────

    def saga_open_output(self) -> dict:
        """Open the output folder after generation completes."""
        return self.open_output_folder()
