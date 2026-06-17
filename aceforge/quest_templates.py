"""
quest_templates.py — ACEForge Deterministic Quest Template Generator

Generates complete, structurally correct ACE SQL for standard quest types
without AI involvement in file structure or cross-references. AI is only
called for NPC dialogue (emotes).

Quest flag names, WCID cross-references, and file ordering are all handled
deterministically by this module. Zero schema errors are possible.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime
from aceforge.json_to_sql import (
    _emit_header, _emit_int_props, _emit_bool_props, _emit_float_props,
    _emit_str_props, _emit_did_props, _emit_attributes, _emit_vitals,
    _emit_skills, _emit_body_parts, _emit_body_parts_ref, _emit_spellbook,
    _emit_create_list, _emit_generator, _emit_quest_entry, _slug, TIMESTAMP,
)

TIMESTAMP = "2025-01-01 00:00:00"


def _quest_sql(quest_id: int, name: str, min_delta: int, max_solves: int,
               message: str = "kill counter") -> str:
    """
    Emit correct ACE quest table SQL matching Shattered Dawn reference format:
        DELETE FROM quest WHERE id = 'N' OR name = 'FlagName';
        INSERT INTO quest (id, name, min_Delta, max_Solves, message)
        VALUES ('N', 'FlagName', 'delta', 'solves', 'message');
    - No backtick quoting on quest table
    - id included as quoted string
    - All values quoted as strings
    - No last_Modified column
    - KT flags: max_solves='100', message='kill counter'
    - Completion flags: max_solves='1', min_delta=repeat_seconds
    - Permanent flags: max_solves='-1', min_delta='0'
    """
    id_clause = f"id = '{quest_id}' OR " if quest_id else ""
    return (
        f"DELETE FROM quest WHERE {id_clause}name = '{name}';\n\n"
        f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
        f"VALUES ('{quest_id}', '{name}', '{min_delta}', '{max_solves}', '{message}');"
    )



# ── WCID allocator ────────────────────────────────────────────────────────────

def alloc_wcids(config, ranges: list[tuple[str, int]]) -> dict[str, list[int]]:
    """
    Allocate WCIDs from config ranges.
    ranges = [('campaign_creatures', 2), ('custom_npcs', 1), ...]
    Duplicate keys are summed — ('kill_contracts',1),('kill_contracts',1) → 2 allocated.
    Returns {range_key: [wcid1, wcid2, ...]}
    """
    # Consolidate duplicate keys
    totals: dict[str, int] = {}
    order: list[str] = []
    for key, count in ranges:
        if key not in totals:
            order.append(key)
        totals[key] = totals.get(key, 0) + count

    wcid_ranges = config.get_wcid_ranges()
    result: dict[str, list[int]] = {}
    for key in order:
        count = totals[key]
        r     = wcid_ranges.get(key, {})
        if not r:
            # Per reference files: kill_tasks use 1000000+ range
            default_start = 1000000 if key == "kill_tasks" else 800000
            wcid_ranges[key] = {"start": default_start, "next": default_start, "label": key}
            r = wcid_ranges[key]
        start = r.get("next", r.get("start", 800000))
        result[key] = list(range(start, start + count))
        wcid_ranges[key]["next"] = start + count
    config.set("wcid_ranges", wcid_ranges)
    return result


# ── Shared SQL helpers ────────────────────────────────────────────────────────

def _file_header(filename: str) -> str:
    return f"/* ===== FILE: {filename} ===== */"


def _creature_sql(wcid: int, data: dict, filename: str) -> str:
    """Generate creature weenie SQL matching Shattered Dawn reference format.
    Based on Rift Stabil (800003) and Rift Anchora (800011) reference files.
    """
    name       = data["name"]
    class_name = data.get("class_name", _slug(name))
    level      = data.get("level", 275)
    xp         = data.get("xp", level * 5000)
    health     = data.get("health", level * 9)
    stamina    = data.get("stamina", level * 4)
    mana       = data.get("mana", level * 4)
    armor      = data.get("armor", 100)
    scale      = data.get("scale", 1.0)
    kill_quest = data.get("kill_quest", "")
    loot_tier  = data.get("loot_tier", 3101)
    luminance  = data.get("luminance_award", 25000)
    creature_type_int   = data.get("creature_type_int", 1)
    creature_type_label = data.get("creature_type_label", "Human")
    atk_skill_id   = data.get("attack_skill_id", 44)
    atk_skill_name = data.get("attack_skill_name", "HeavyWeapons")
    atk_skill_val  = data.get("attack_skill", level + 50)
    def_skill_val  = data.get("melee_defense", level + 30)
    is_caster      = data.get("is_caster", False)

    attrs = {
        "strength":     data.get("strength",     level),
        "endurance":    data.get("endurance",     level),
        "quickness":    data.get("quickness",     level - 25),
        "coordination": data.get("coordination",  level - 25),
        "focus":        data.get("focus",         level - 50),
        "self":         data.get("self",          level - 50),
    }

    sections = [_file_header(filename), ""]
    sections.append(_emit_header(wcid, name, 10))

    int_rows = [
        (1,   16,               "ItemType - Creature"),
        (2,   creature_type_int, f"CreatureType - {creature_type_label}"),
        (6,   -1,               "ItemsCapacity"),
        (7,   -1,               "ContainersCapacity"),
        (16,  1,                "ItemUseable - No"),
        (25,  level,            "Level"),
        (27,  0,                "ArmorType - None"),
        (40,  2,                "CombatMode - Melee"),
        (68,  5,                "TargetingTactic - Random, LastDamager"),
        (69,  4,                "CombatTactic - LastDamager"),
        (93,  3080,             "PhysicsState - ReportCollisions, Gravity, LightingOn"),
        (133, 4,                "ShowableOnRadar - ShowAlways"),
        (146, xp,               "XpOverride"),
        (332, luminance,        "LuminanceAward"),
    ]

    bool_rows = [
        (1,   True,      "Stuck"),
        (6,   is_caster, "AiUsesMana"),
        (11,  False,     "IgnoreCollisions"),
        (12,  True,      "ReportCollisions"),
        (13,  False,     "Ethereal"),
        (14,  True,      "GravityStatus"),
        (15,  True,      "LightsStatus"),
        (19,  True,      "Attackable"),
        (50,  is_caster, "NeverFailCasting"),
        (120, True,      "TreasureCorpse"),
    ]

    shade = data.get("shade", 0.667)
    fire_resist   = data.get("resist_fire", 0.4)
    acid_resist   = data.get("resist_acid", 0.4)
    nether_resist = data.get("resist_nether", 0.1)

    float_rows = [
        (1,   5,            "HeartbeatInterval"),
        (2,   0,            "HeartbeatTimestamp"),
        (3,   0.6,          "HealthRate"),
        (4,   0.5,          "StaminaRate"),
        (5,   2,            "ManaRate"),
        (12,  shade,        "Shade"),
        (13,  0.9,          "ArmorModVsSlash"),
        (14,  1,            "ArmorModVsPierce"),
        (15,  1,            "ArmorModVsBludgeon"),
        (16,  1,            "ArmorModVsCold"),
        (17,  0.9,          "ArmorModVsFire"),
        (18,  1,            "ArmorModVsAcid"),
        (19,  1,            "ArmorModVsElectric"),
        (31,  18,           "VisualAwarenessRange"),
        (34,  1,            "PowerupTime"),
        (36,  1,            "ChargeSpeed"),
        (64,  1,            "ResistSlash"),
        (65,  1,            "ResistPierce"),
        (66,  1,            "ResistBludgeon"),
        (67,  fire_resist,  "ResistFire"),
        (68,  1,            "ResistCold"),
        (69,  acid_resist,  "ResistAcid"),
        (70,  1,            "ResistElectric"),
        (80,  3,            "AiUseMagicDelay"),
        (104, 10,           "ObviousRadarRange"),
        (122, 2,            "AiAcquireHealth"),
        (125, 1,            "ResistHealthDrain"),
        (165, 1,            "ArmorModVsNether"),
        (166, nether_resist,"ResistNether"),
    ]
    if scale != 1.0:
        float_rows.append((39, scale, "DefaultScale"))

    str_rows = [(1, name, "Name")]
    if kill_quest:
        str_rows.append((45, kill_quest, "KillQuest"))

    did_rows = [
        (1,  data.get("setup",          0x020009F6), "Setup"),
        (2,  data.get("motion_table",   0x09000028), "MotionTable"),
        (3,  data.get("sound_table",    0x20000012), "SoundTable"),
        (4,  data.get("combat_table",   0x3000000D), "CombatTable"),
        (6,  data.get("palette_base",   0x040009B2), "PaletteBase"),
        (7,  data.get("clothing_base",  0x100000C1), "ClothingBase"),
        (8,  data.get("icon",           0x06001227), "Icon"),
        (22, data.get("physics_effect", 0x34000029), "PhysicsEffectTable"),
        (35, loot_tier,                              "DeathTreasureType"),
    ]

    # Body parts: auto-build from creature_type_int using CREATURE_BP_MAP
    # Supports all 35 creature types; explicit list in data["body_parts"] overrides
    body_parts = data.get("body_parts", creature_type_int)

    # Skill set: full list matching reference
    skill_rows = [
        (6,  def_skill_val, "MeleeDefense"),
        (7,  def_skill_val, "MissileDefense"),
        (15, def_skill_val, "MagicDefense"),
        (16, def_skill_val, "ManaConversion"),
        (31, def_skill_val, "CreatureEnchantment"),
        (33, def_skill_val, "LifeMagic"),
        (34, def_skill_val, "WarMagic"),
        (41, atk_skill_val, "TwoHandedCombat"),
        (43, def_skill_val, "VoidMagic"),
        (44, atk_skill_val, "HeavyWeapons"),
        (45, atk_skill_val, "LightWeapons"),
        (46, atk_skill_val, "FinesseWeapons"),
    ]

    spells = data.get("spells", [])

    sections.append(""); sections.append(_emit_int_props(wcid, int_rows))
    sections.append(""); sections.append(_emit_bool_props(wcid, bool_rows))
    sections.append(""); sections.append(_emit_float_props(wcid, float_rows))
    sections.append(""); sections.append(_emit_str_props(wcid, str_rows))
    sections.append(""); sections.append(_emit_did_props(wcid, did_rows))
    sections.append(""); sections.append(_emit_body_parts_ref(wcid, body_parts, armor=armor))
    sections.append(""); sections.append(_emit_attributes(wcid, attrs))
    sections.append(""); sections.append(_emit_vitals(wcid, health, stamina, mana))
    sections.append(""); sections.append(_emit_skills(wcid, skill_rows))
    if spells:
        sections.append(""); sections.append(_emit_spellbook(wcid, spells))
    if data.get("create_list"):
        sections.append(""); sections.append(_emit_create_list(wcid, data["create_list"]))
    sections.append("")
    return "\n".join(s for s in sections)



def _generator_sql(gen_wcid: int, creature_wcid: int,
                   creature_class: str, filename: str,
                   spawn_count: int = 5, delay: float = 300.0) -> str:
    """Generate generator weenie SQL.
    Block order matches reference: header → int → bool → float → string → did → generator
    No string/did blocks in the weenie header area.
    """
    sections = [_file_header(filename), ""]
    gen_display_name = creature_class.replace('_', ' ').title() + ' Generator'
    sections.append(_emit_header(gen_wcid, gen_display_name, 35))
    sections.append("")

    int_rows = [
        (81, spawn_count, "MaxGeneratedObjects"),
        (82, spawn_count, "InitGeneratedObjects"),
        (93, 1044,        "PhysicsState - Ethereal, IgnoreCollisions, Gravity"),
    ]
    bool_rows = [
        (1,  True, "Stuck"),
        (11, True, "IgnoreCollisions"),
        (18, True, "Visibility"),
    ]
    float_rows = [
        (41, int(delay), "RegenerationInterval"),
        (43, 50,         "GeneratorRadius"),
    ]
    str_rows = [(1, gen_display_name, "Name")]
    did_rows = [
        (1, 0x0200026B, "Setup"),
        (8, 0x06001066, "Icon"),
    ]
    gen_comment = f"/* Generate {creature_wcid} (x{spawn_count} up to max of {spawn_count}) - Regenerate upon Destruction */"
    gen_cols = ("(`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`,"
                " `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`,"
                " `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)")
    gen_row = (f"INSERT INTO `weenie_properties_generator` {gen_cols}\n"
               f"VALUES ({gen_wcid}, -1, {creature_wcid}, 1, {spawn_count}, {spawn_count},"
               f" 1, 2, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) {gen_comment};")

    sections.append(_emit_int_props(gen_wcid, int_rows))
    sections.append("")
    sections.append(_emit_bool_props(gen_wcid, bool_rows))
    sections.append("")
    sections.append(_emit_float_props(gen_wcid, float_rows))
    sections.append("")
    sections.append(_emit_str_props(gen_wcid, str_rows))
    sections.append("")
    sections.append(_emit_did_props(gen_wcid, did_rows))
    sections.append("")
    sections.append(gen_row)
    sections.append("")
    return "\n".join(sections)


def _npc_base_sql(wcid: int, name: str, class_name: str, filename: str) -> str:
    """Generate NPC weenie SQL matching Shattered Dawn reference format.
    Based on Lucius Athenos (850000) and Marson Riftrider (850003) reference files.
    """
    sections = [_file_header(filename), ""]
    sections.append(_emit_header(wcid, name, 10))

    int_rows = [
        (1,   16,       "ItemType - Creature"),
        (2,   31,       "CreatureType - Human"),
        (6,   -1,       "ItemsCapacity"),
        (7,   -1,       "ContainersCapacity"),
        (16,  32,       "ItemUseable - Remote"),
        (25,  275,      "Level"),
        (93,  6292504,  "PhysicsState - ReportCollisions, IgnoreCollisions, Gravity, ReportCollisionsAsEnvironment, EdgeSlide"),
        (95,  8,        "RadarBlipColor - Yellow"),
        (113, 1,        "Gender - Male"),
        (133, 4,        "ShowableOnRadar - ShowAlways"),
        (134, 16,       "PlayerKillerStatus - RubberGlue"),
        (146, 0,        "XpOverride"),
        (188, 1,        "HeritageGroup - Aluvian"),
    ]
    bool_rows = [
        (1,   True,  "Stuck"),
        (19,  False, "Attackable"),
    ]
    float_rows = [
        (1,   60,   "HeartbeatInterval"),
        (2,   0,    "HeartbeatTimestamp"),
        (3,   2,    "HealthRate"),
        (4,   5,    "StaminaRate"),
        (5,   1,    "ManaRate"),
        (13,  1,    "ArmorModVsSlash"),
        (14,  1,    "ArmorModVsPierce"),
        (15,  1,    "ArmorModVsBludgeon"),
        (16,  1,    "ArmorModVsCold"),
        (17,  1,    "ArmorModVsFire"),
        (18,  1,    "ArmorModVsAcid"),
        (19,  1,    "ArmorModVsElectric"),
        (31,  18,   "VisualAwarenessRange"),
        (39,  1,    "DefaultScale"),
        (54,  3,    "UseRadius"),
        (64,  1,    "ResistSlash"),
        (65,  1,    "ResistPierce"),
        (66,  1,    "ResistBludgeon"),
        (67,  1,    "ResistFire"),
        (68,  1,    "ResistCold"),
        (69,  1,    "ResistAcid"),
        (70,  1,    "ResistElectric"),
        (80,  2,    "AiUseMagicDelay"),
        (104, 10,   "ObviousRadarRange"),
        (122, 2,    "AiAcquireHealth"),
        (125, 1,    "ResistHealthDrain"),
    ]
    str_rows = [(1, name, "Name")]
    did_rows = [
        (1,  0x02000001, "Setup"),
        (2,  0x09000001, "MotionTable"),
        (3,  0x20000001, "SoundTable"),
        (6,  0x0400007E, "PaletteBase"),
        (8,  0x06001036, "Icon"),
        (31, 1595,       "LinkedPortalOne - Abandoned Mine"),
    ]
    # Body parts: Human 9-part matching reference (base_Armor=250, armor_Vs_*=125)
    body_parts = [
        (0, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 1, 0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0   ),  # Head
        (1, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 2, 0.44, 0.17, 0,    0.44, 0.17, 0,    0.44, 0.17, 0,    0.44, 0.17, 0   ),  # Chest
        (2, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 3, 0,    0.17, 0,    0,    0.17, 0,    0,    0.17, 0,    0,    0.17, 0   ),  # Abdomen
        (3, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 1, 0.23, 0.03, 0,    0.23, 0.03, 0,    0.23, 0.03, 0,    0.23, 0.03, 0   ),  # UpperArm
        (4, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 2, 0,    0.3,  0,    0,    0.3,  0,    0,    0.3,  0,    0,    0.3,  0   ),  # LowerArm
        (5, 4, 4, 0.75, 250, 125, 125, 125, 125, 125, 125, 125, 0, 2, 0,    0.2,  0,    0,    0.2,  0,    0,    0.2,  0,    0,    0.2,  0   ),  # Hand
        (6, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 3, 0,    0.13, 0.18, 0,    0.13, 0.18, 0,    0.13, 0.18, 0,    0.13, 0.18),  # UpperLeg
        (7, 4, 0, 0,    250, 125, 125, 125, 125, 125, 125, 125, 0, 3, 0,    0,    0.6,  0,    0,    0.6,  0,    0,    0.6,  0,    0,    0.6 ),  # LowerLeg
        (8, 4, 8, 0.75, 250, 125, 125, 125, 125, 125, 125, 125, 0, 3, 0,    0,    0.22, 0,    0,    0.22, 0,    0,    0.22, 0,    0,    0.22),  # Foot
    ]
    # Attributes matching reference (Str=290, End=260, Qui=290, Coo=290, Foc=200, Self=200)
    attrs = {
        "strength": 290, "endurance": 260, "quickness": 290,
        "coordination": 290, "focus": 200, "self": 200,
    }
    # Skills: full 13-skill list matching reference
    skill_rows = [
        (6,  132, "MeleeDefense"),
        (7,  149, "MissileDefense"),
        (15, 170, "MagicDefense"),
        (16, 149, "ManaConversion"),
        (31, 149, "CreatureEnchantment"),
        (32, 200, "ItemEnchantment"),
        (33, 149, "LifeMagic"),
        (34, 149, "WarMagic"),
        (41, 132, "TwoHandedCombat"),
        (43, 149, "VoidMagic"),
        (44, 132, "HeavyWeapons"),
        (45, 132, "LightWeapons"),
        (46, 132, "FinesseWeapons"),
    ]

    sections.append(_emit_int_props(wcid, int_rows))
    sections.append(""); sections.append(_emit_bool_props(wcid, bool_rows))
    sections.append(""); sections.append(_emit_float_props(wcid, float_rows))
    sections.append(""); sections.append(_emit_str_props(wcid, str_rows))
    sections.append(""); sections.append(_emit_did_props(wcid, did_rows))
    sections.append(""); sections.append(_emit_body_parts_ref(wcid, body_parts, armor=250))
    sections.append(""); sections.append(_emit_attributes(wcid, attrs))
    sections.append(""); sections.append(_emit_vitals(wcid, 326, 456, 396))
    sections.append(""); sections.append(_emit_skills(wcid, skill_rows))
    sections.append("")
    return "\n".join(s for s in sections)





def _parse_grant_flag(params: dict) -> dict | None:
    """Parse grant_flag params. Returns None if toggle is off or name is blank."""
    if params.get("use_grant_flag","").strip().lower() != "yes":
        return None
    name = params.get("grant_flag_name","").strip().replace(" ","")
    if not name:
        return None
    desc = params.get("grant_flag_desc","").strip() or f"access granted"
    return {"name": name, "desc": desc}


def _grant_flag_file(flag_name: str) -> dict:
    """Generate a permanent quest flag SQL file for a grant flag."""
    sql = (
        f"DELETE FROM quest WHERE name = '{flag_name}';\n\n"
        f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
        f"VALUES ('0', '{flag_name}', '0', '-1', 'permanent access flag');"
    )
    return {
        "filename": f"Quest_{flag_name}.sql",
        "sql":      f"/* ===== FILE: Quest_{flag_name}.sql ===== */\n\n{sql}",
        "type":     "quest_flag",
    }

# ── TEMPLATE 1: Kill Task ─────────────────────────────────────────────────────

def generate_kill_task(params: dict, config) -> list[dict]:
    """
    Generate all SQL files for a Kill Task quest.

    Required params:
        quest_prefix        str  — short unique prefix e.g. "UlgrimTumerok"
        npc_name            str  — e.g. "Ulgrim the Unpleasant"
        npc_description     str  — short desc for AI emote generation
        creature_name       str  — e.g. "Tumerok Berserker"
        creature_level      int  — e.g. 150
        creature_type       str  — e.g. "Tumerok"
        kill_count          int  — e.g. 50
        reward_xp           int  — e.g. 5000000
        reward_pyreals      int  — e.g. 10000
        repeat_hours        int  — repeat timer in hours (0 = one-time)
        loot_tier           int  — 3101-3105 (T4-T8), 0 = no loot
        spawn_count         int  — generator spawn count (default 5)
        spawn_delay         float— respawn seconds (default 300)
        creature_xp         int  — XP from killing creature
        original_prompt     str  — user's original description for AI emotes

    Optional:
        boss_name           str  — if set, adds a named boss variant
        boss_level          int  — boss level (default creature_level * 1.5)
        boss_kill_count     int  — kills needed (default 1)
        reward_item_wcid    int  — WCID of a reward item (0 = none)

    Returns list of {"filename": str, "sql": str} dicts.
    """
    prefix       = params["quest_prefix"].replace(" ", "")
    npc_name     = params["npc_name"]
    npc_desc     = params.get("npc_description", npc_name)
    c_name       = params["creature_name"]
    # Safe conversion helpers — handle empty strings and placeholder text
    def _si(val, default):
        try: s=str(val).strip(); return int(s) if s and s.lstrip('-').isdigit() else default
        except: return default
    def _sf(val, default):
        try: s=str(val).strip(); return float(s) if s else default
        except: return default

    c_level      = _si(params.get("creature_level", ""), 100)
    c_type_label = params.get("creature_type", "Human")
    kill_count   = _si(params.get("kill_count", ""), 25)
    # reward_xp / reward_lum: JS sends these only when toggle is 'yes'
    # Default to 0 when absent (toggle off)
    reward_xp   = _si(params.get("reward_xp", ""), 0)
    reward_lum  = _si(params.get("reward_luminance", ""), 0)
    reward_pyre = _si(params.get("reward_pyreals", ""), 5000)
    repeat_sec   = _si(params.get("repeat_hours", ""), 20) * 3600
    loot_tier    = _si(params.get("loot_tier", ""), 3101)
    # XP award type: 'AwardXP' | 'AwardNoShareXP' | 'AwardLevelProportionalXP'
    xp_type      = params.get("xp_type", "AwardXP").strip() or "AwardXP"
    xp_pct       = _sf(params.get("xp_percent", ""), 0.25)  # for AwardLevelProportionalXP
    grant_flag   = _parse_grant_flag(params)  # optional extra flag on completion
    spawn_count  = _si(params.get("spawn_count", ""), 5)
    spawn_delay  = _sf(params.get("spawn_delay", ""), 300.0)
    c_xp         = _si(params.get("creature_xp", ""), c_level * 3000)
    orig_prompt  = params.get("original_prompt", "")

    # Mob/Boss toggle — "Boss" means single spawn, 1.8x scale, 3x HP, 900s respawn
    is_boss_mode = "Boss" in params.get("is_boss", "")
    has_boss     = False  # old optional named boss field removed
    boss_name    = ""
    boss_level   = int(c_level * 1.5)
    boss_kills   = 1
    # Adjust generator/creature for boss mode
    if is_boss_mode:
        spawn_count = 1
        spawn_delay = 900.0

    # Reward items — multi-item support with optional existing WCIDs
    reward_items = []
    for _i in range(1, 5):
        _rn = params.get(f"reward_{_i}_name", "").strip()
        if not _rn: break
        _rw = params.get(f"reward_{_i}_wcid", "").strip()
        _rq = _si(params.get(f"reward_{_i}_qty", ""), 1)
        _rd = params.get(f"reward_{_i}_desc", "").strip()
        reward_items.append({"name":_rn,"wcid_raw":_rw,"qty":_rq,"desc":_rd,"is_existing":bool(_rw and _rw.isdigit())})
    new_reward_count = sum(1 for r in reward_items if not r["is_existing"])

    # Quest flag names — derived deterministically from prefix
    kt_flag     = f"{prefix}KT"          # kill task progress flag
    kt_timer    = f"{prefix}KTTimer"     # daily/repeat cooldown timer flag
    kt_done     = f"{prefix}KTCompleted" # completion stamp flag
    boss_flag   = f"{prefix}BossKT"      # boss kill flag (if boss exists)

    # Allocate WCIDs
    needed = [
        ("custom_npcs",        1),
        ("campaign_creatures", 1 + (1 if has_boss else 0)),
        ("kill_contracts",     1 + (1 if has_boss else 0)),
    ]
    if new_reward_count > 0:
        needed.append(("custom_items", new_reward_count))
    wcids = alloc_wcids(config, needed)
    # Assign WCIDs to generated reward items
    _ri_pool = list(wcids.get("custom_items", []))
    for r in reward_items:
        r["wcid"] = int(r["wcid_raw"]) if r["is_existing"] else _ri_pool.pop(0)

    npc_wcid        = wcids["custom_npcs"][0]
    creature_wcid   = wcids["campaign_creatures"][0]
    boss_wcid       = wcids["campaign_creatures"][1] if has_boss else None
    gen_wcid        = wcids["kill_contracts"][0]
    boss_gen_wcid   = wcids["kill_contracts"][1] if has_boss else None

    c_slug          = _slug(c_name)
    npc_slug        = _slug(npc_name)
    boss_slug       = _slug(boss_name) if has_boss else ""

    files = []

    # ── Quest Flag Files — one file per flag ──────────────────────────────────
    n_kt_ids = 2 if has_boss else 1
    kt_quest_ids     = alloc_wcids(config, [("kill_tasks", n_kt_ids)])
    kt_quest_id      = kt_quest_ids["kill_tasks"][0]
    max_solves_timer = 1 if repeat_sec > 0 else -1

    def _qf(flag_name, quest_id, min_delta, max_solves, message):
        sql = (
            f"DELETE FROM quest WHERE name = '{flag_name}';\n\n"
            f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
            f"VALUES ('{quest_id}', '{flag_name}', '{min_delta}', '{max_solves}', '{message}');"
        )
        return {"filename": f"Quest_{flag_name}.sql",
                "sql": f"/* ===== FILE: Quest_{flag_name}.sql ===== */\n\n{sql}",
                "type": "quest_flag"}

    files.append(_qf(kt_flag,  kt_quest_id, '0', '100',              'kill counter'))
    files.append(_qf(kt_timer, '0',          repeat_sec, max_solves_timer, 'kill task timer'))
    files.append(_qf(kt_done,  '0',          '0', '-1',              'kill task completed'))
    if has_boss:
        boss_quest_id = kt_quest_ids["kill_tasks"][1]
        files.append(_qf(boss_flag, boss_quest_id, '0', '100', 'boss kill counter'))
    if grant_flag:
        files.append(_grant_flag_file(grant_flag["name"]))

    # ── File 2: Creature ──────────────────────────────────────────────────────
    from aceforge.json_to_sql import CREATURE_TYPE
    # Prefer pre-parsed int from JS (from "Tumerok (6)" → creature_type_int=6)
    # Parse int from pre-parsed JS field OR extract from '(N)' suffix OR dict lookup
    _cti_str = params.get("creature_type_int", params.get("c_type_int", ""))
    if _cti_str:
        c_type_int = int(_cti_str)
    else:
        import re as _re
        _m = _re.search(r'\((\d+)\)', params.get('creature_type', ''))
        if _m:
            c_type_int = int(_m.group(1))
        else:
            c_type_int = CREATURE_TYPE.get(c_type_label.lower().replace(' ','_').replace('-','_'), 31)
    creature_data = {
        "name":               c_name,
        "class_name":         c_slug,
        "level":              c_level,
        "xp":                 c_xp,
        "health":             c_level * 8,
        "stamina":            c_level * 6,
        "mana":               c_level * 2,
        "armor":              max(40, c_level // 2),
        "creature_type_int":  c_type_int,
        "creature_type_label":c_type_label,
        "attack_skill_id":    44,
        "attack_skill_name":  "HeavyWeapons",
        "attack_skill":       c_level + (100 if is_boss_mode else 50),
        "melee_defense":      c_level + (80 if is_boss_mode else 30),
        "kill_quest":         kt_flag,
        "loot_tier":          loot_tier,
        "scale":              1.8 if is_boss_mode else 1.0,
        "health":             c_level * (24 if is_boss_mode else 8),
        "stamina":            c_level * (18 if is_boss_mode else 6),
        "mana":               c_level * (6 if is_boss_mode else 2),
    }
    fname2 = f"{creature_wcid}_{c_slug}.sql"
    files.append({
        "filename": fname2,
        "sql":      _creature_sql(creature_wcid, creature_data, fname2),
        "type":     "creature",
        "wcid":     creature_wcid,
    })

    # ── File 3: Creature Generator ────────────────────────────────────────────
    fname3 = f"{gen_wcid}_{c_slug}_generator.sql"
    files.append({
        "filename": fname3,
        "sql":      _generator_sql(gen_wcid, creature_wcid, c_slug, fname3,
                                   spawn_count, spawn_delay),
        "type":     "generator",
        "wcid":     gen_wcid,
    })

    # ── File 4 (optional): Boss creature ─────────────────────────────────────
    if has_boss and boss_wcid:
        boss_data = {
            "name":               boss_name,
            "class_name":         boss_slug,
            "level":              boss_level,
            "xp":                 boss_level * 8000,
            "health":             boss_level * 20,
            "stamina":            boss_level * 12,
            "mana":               boss_level * 5,
            "armor":              max(80, boss_level // 2),
            "creature_type_int":  c_type_int,
            "creature_type_label":c_type_label,
            "attack_skill_id":    44,
            "attack_skill_name":  "HeavyWeapons",
            "attack_skill":       boss_level + 75,
            "melee_defense":      boss_level + 50,
            "kill_quest":         boss_flag,
            "loot_tier":          min(loot_tier + 1, 3105),
            "scale":              1.5,
        }
        fname4 = f"{boss_wcid}_{boss_slug}.sql"
        files.append({
            "filename": fname4,
            "sql":      _creature_sql(boss_wcid, boss_data, fname4),
            "type":     "boss",
            "wcid":     boss_wcid,
        })
        fname4g = f"{boss_gen_wcid}_{boss_slug}_generator.sql"
        files.append({
            "filename": fname4g,
            "sql":      _generator_sql(boss_gen_wcid, boss_wcid, boss_slug,
                                       fname4g, 1, 600.0),
            "type":     "generator",
            "wcid":     boss_gen_wcid,
        })

    # ── Reward Item Files ─────────────────────────────────────────────────────
    for r in reward_items:
        if r["is_existing"]: continue
        ri_wcid = r["wcid"]; ri_name = r["name"]; ri_slug = _slug(ri_name)
        ri_int  = [(1,256,"ItemType"),(5,10,"EncumbranceVal"),(8,5,"Mass"),(19,0,"Value"),(93,1044,"PhysicsState")]
        ri_desc_text = r.get("desc","").strip() or ri_name
        ri_str  = [(1,ri_name,"Name"),(15,ri_desc_text,"ShortDesc")]
        ri_did  = [(1,0x02000155,"Setup"),(3,0x20000014,"SoundTable"),(8,0x06001310,"Icon"),(22,0x3400002B,"PhysicsEffectTable")]
        fname_ri = f"{ri_wcid}_{ri_slug}.sql"
        files.append({"filename":fname_ri,"sql":"\n".join([f"/* ===== FILE: {fname_ri} ===== */","",_emit_header(ri_wcid,ri_name,6),"",_emit_int_props(ri_wcid,ri_int),"",_emit_str_props(ri_wcid,ri_str),"",_emit_did_props(ri_wcid,ri_did),""]),"type":"item","wcid":ri_wcid})

    # ── File 5: NPC Quest Giver (base SQL — emotes added by AI call) ──────────
    fname5 = f"{npc_wcid}_{npc_slug}.sql"
    npc_base = _npc_base_sql(npc_wcid, npc_name, npc_slug, fname5)

    # Build the emote script deterministically — exact quest flags guaranteed
    boss_check = ""
    if has_boss:
        boss_check = (
            f"        QuestFailure:\n"
            f"            - Goto: NeedBoss\n"
            f"\nGotoSet: NeedBoss\n"
            f"    - Tell: You must also defeat {boss_name} to complete this task.\n"
        )

    # ── Build XP award action matching selected type ─────────────────────────
    # AwardLevelProportionalXP needs percent in min_64/max_64=0, percent col
    # AwardXP / AwardNoShareXP use amount_64 col
    XP_TYPE_ID = {"AwardXP": 2, "AwardNoShareXP": 62, "AwardLevelProportionalXP": 49}
    xp_action_id = XP_TYPE_ID.get(xp_type, 2)

    def _emote_null_row(wcid, parent_var="@parent_id"):
        """Return the long NULL-padded emote action column list."""
        return (f"`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                f" `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                f" `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                f" `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                f" `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                f" `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                f" `origin_X`, `origin_Y`, `origin_Z`,"
                f" `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")

    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")
    NULL40 = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"

    EMO_COLS = ("`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`,"
                " `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`")

    def emo_hdr(cat_id, cat_name, prob=1, quest=None):
        q = f"'{quest}'" if quest else "NULL"
        return (f"INSERT INTO `weenie_properties_emote` ({EMO_COLS})\n"
                f"VALUES ({npc_wcid}, {cat_id} /* {cat_name} */, {prob}, NULL, NULL, NULL, {q}, NULL, NULL, NULL);\n"
                f"\nSET @parent_id = LAST_INSERT_ID();\n")

    def act_row(order, type_id, type_name, *,
                message=None, min_val=None, max_val=None,
                min_64=None, max_64=None, percent=None,
                amount=None, amount_64=None, hero_xp_64=None,
                dest_type=None, wcid=None, stack=None, prefix_kw="VALUES", suffix=""):
        msg  = f"'{message}'" if message is not None else "NULL"
        mn   = str(min_val)   if min_val   is not None else "NULL"
        mx   = str(max_val)   if max_val   is not None else "NULL"
        m64  = str(min_64)    if min_64    is not None else "NULL"
        mx64 = str(max_64)    if max_64    is not None else "NULL"
        pct  = str(percent)   if percent   is not None else "NULL"
        amt  = str(amount)    if amount    is not None else "NULL"
        amt64= str(amount_64) if amount_64 is not None else "NULL"
        hxp  = str(hero_xp_64) if hero_xp_64 is not None else "NULL"
        dt   = str(dest_type) if dest_type is not None else "NULL"
        wc   = str(wcid)      if wcid      is not None else "NULL"
        sk   = str(stack)     if stack     is not None else "NULL"
        return (f"{prefix_kw} (@parent_id, {order}, {type_id} /* {type_name} */, 0, 1, NULL,"
                f" {msg}, NULL, {mn}, {mx}, {m64}, {mx64}, NULL, NULL, NULL, NULL,"
                f" {amt}, {amt64}, {hxp}, {pct},"
                f" NULL, NULL, NULL, NULL, NULL, NULL,"
                f" {dt}, {wc}, {sk},"
                f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL){suffix}")

    def xp_act_row(order, prefix_kw="     ,", suffix=""):
        """Emit the correct XP award row based on xp_type."""
        if xp_type == "AwardLevelProportionalXP":
            return act_row(order, 49, "AwardLevelProportionalXP",
                           min_64=0, max_64=0, percent=xp_pct,
                           prefix_kw=prefix_kw, suffix=suffix)
        elif xp_type == "AwardNoShareXP":
            return act_row(order, 62, "AwardNoShareXP",
                           amount_64=reward_xp,
                           prefix_kw=prefix_kw, suffix=suffix)
        else:  # AwardXP
            return act_row(order, 2, "AwardXP",
                           amount_64=reward_xp,
                           prefix_kw=prefix_kw, suffix=suffix)

    # Build reward action rows (XP, Luminance, items, pyreals)
    # These go inside the KillTaskCompleted QuestSuccess block
    def _reward_actions(start_order):
        """Build reward action rows — all as a single multi-row VALUES block."""
        rows = []
        o = start_order

        def _ar(order, *args, **kwargs):
            # First row uses VALUES, rest use ,
            kwargs["prefix_kw"] = "VALUES" if order == start_order else "     ,"
            return act_row(order, *args, **kwargs)

        rows.append(_ar(o, 18, "DirectBroadcast",
                        message="You have completed this Kill Task."))
        o += 1
        # XP award — only if XP toggle was on (reward_xp > 0 or proportional)
        if reward_xp or xp_type == "AwardLevelProportionalXP":
            rows.append(xp_act_row(o, prefix_kw="     ,"))
            o += 1
        if reward_lum:
            rows.append(_ar(o, 113, "AwardLuminance", hero_xp_64=reward_lum))
            o += 1
        for r in reward_items:
            if r.get("wcid"):  # only emit Give if wcid is set
                rows.append(_ar(o, 3, "Give", dest_type=None, wcid=r["wcid"], stack=None))
                o += 1
        rows.append(_ar(o, 22, "StampQuest", message=kt_timer))
        o += 1
        rows.append(_ar(o, 31, "EraseQuest", message=kt_flag))
        o += 1
        rows.append(_ar(o, 31, "EraseQuest", message=kt_done))
        o += 1
        rows.append(_ar(o, 22, "StampQuest",  message=kt_done))
        o += 1
        if grant_flag:
            rows.append(_ar(o, 22, "StampQuest", message=grant_flag["name"]))
            o += 1
            rows.append(_ar(o, 10, "Tell",
                           message=f"You are now flagged for {grant_flag['desc']}.",
                           suffix=";"))
        else:
            rows[-1] = rows[-1].rstrip(";") + ";"  # close last row
        return rows
    reward_rows = _reward_actions(0)
    reward_sql  = "\n".join(reward_rows)

    # ── Direct SQL emote generation ───────────────────────────────────────────
    # Matches reference exactly:
    # Use → InqQuest(Timer) → QS=DirectBroadcast(cooldown)
    #                       → QF → InqQuestSolves(KT@KillTaskInProgress, 1, MAX)
    #                                → QS → InqQuest(KT@KillTaskCompleted)
    #                                         → QS: rewards + stamp/erase
    #                                         → QF: DirectBroadcast(not finished)
    #                                → QF: DirectBroadcast(kill msg) + SetQuestCompletions(KT,0)

    emote_sql_parts = []

    # ── Block 1: Use → InqQuest(KTTimer) ────────────────────────────────────
    emote_sql_parts.append(emo_hdr(7, "Use"))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 21, "InqQuest", message=kt_timer, prefix_kw="VALUES", suffix=";")
    )

    # ── Block 2: QuestSuccess(KTTimer) → DirectBroadcast(cooldown) ──────────
    emote_sql_parts.append("\n" + emo_hdr(12, "QuestSuccess", quest=kt_timer))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 18, "DirectBroadcast",
                  message="You have completed this daily task too recently.",
                  prefix_kw="VALUES", suffix=";")
    )

    # ── Block 3: QuestFailure(KTTimer) → InqQuestSolves(KT@KillTaskInProgress) ──
    emote_sql_parts.append("\n" + emo_hdr(13, "QuestFailure", quest=kt_timer))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 30, "InqQuestSolves",
                  message=f"{kt_flag}@KillTaskInProgress",
                  min_val=1, max_val=2147483647,
                  prefix_kw="VALUES", suffix=";")
    )

    # ── Block 4: QuestSuccess(KT@KillTaskInProgress) → InqQuest(KT@KillTaskCompleted) ──
    emote_sql_parts.append("\n" + emo_hdr(12, "QuestSuccess", quest=f"{kt_flag}@KillTaskInProgress"))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 21, "InqQuest",
                  message=f"{kt_flag}@KillTaskCompleted",
                  prefix_kw="VALUES", suffix=";")
    )

    # ── Block 5: QuestSuccess(KT@KillTaskCompleted) → rewards ───────────────
    emote_sql_parts.append("\n" + emo_hdr(12, "QuestSuccess", quest=f"{kt_flag}@KillTaskCompleted"))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + reward_sql
    )

    # ── Block 6: QuestFailure(KT@KillTaskCompleted) → not finished ──────────
    emote_sql_parts.append("\n" + emo_hdr(13, "QuestFailure", quest=f"{kt_flag}@KillTaskCompleted"))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 18, "DirectBroadcast",
                  message="You are not quite finished with this task.",
                  prefix_kw="VALUES", suffix=";")
    )

    # ── Block 7: QuestFailure(KT@KillTaskInProgress) → kill msg + reset counter ──
    emote_sql_parts.append("\n" + emo_hdr(13, "QuestFailure", quest=f"{kt_flag}@KillTaskInProgress"))
    emote_sql_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + act_row(0, 18, "DirectBroadcast",
                  message=f"Kill {kill_count} {c_name}s to complete this task.",
                  prefix_kw="VALUES")
        + "\n"
        + act_row(1, 70, "SetQuestCompletions", message=kt_flag, amount=0, suffix=";")
    )

    emote_sql = "\n".join(emote_sql_parts)
    npc_sql_full = npc_base + "\n" + emote_sql + "\n"

    files.append({
        "filename":       fname5,
        "sql":            npc_sql_full,
        "type":           "npc",
        "wcid":           npc_wcid,
        "npc_name":       npc_name,
        "npc_desc":       npc_desc,
        "quest_flag":     kt_flag,
        "kill_count":     kill_count,
        "creature_name":  c_name,
        "reward_xp":      reward_xp,
        "reward_pyreals": reward_pyre,
        "original_prompt":orig_prompt,
    })

    return files




def _parse_reward_params(params: dict, _si) -> dict:
    """Parse reward params consistently across all templates.
    Handles toggle-aware XP/Lum (absent = toggle off = 0).
    """
    xp_type = params.get("xp_type", "AwardXP").strip() or "AwardXP"
    xp_pct  = float(params.get("xp_percent", "0.25") or "0.25")
    try: xp_pct = float(xp_pct)
    except: xp_pct = 0.25
    reward_xp  = _si(params.get("reward_xp", ""), 0)   # 0 when toggle off
    reward_lum = _si(params.get("reward_luminance", ""), 0)
    reward_pyre= _si(params.get("reward_pyreals", ""), 0)

    reward_items = []
    for i in range(1, 5):
        rname = params.get(f"reward_{i}_name", "").strip()
        if not rname: break
        rwcid_raw = params.get(f"reward_{i}_wcid", "").strip()
        rdesc = params.get(f"reward_{i}_desc", f"A quest reward.").strip()
        rqty  = _si(params.get(f"reward_{i}_qty", ""), 1)
        reward_items.append({
            "name":        rname,
            "wcid_raw":    rwcid_raw,
            "desc":        rdesc,
            "qty":         rqty,
            "is_existing": bool(rwcid_raw and rwcid_raw.isdigit()),
        })
    new_reward_count = sum(1 for r in reward_items if not r["is_existing"])
    return {
        "xp_type":         xp_type,
        "xp_pct":          xp_pct,
        "reward_xp":       reward_xp,
        "reward_lum":      reward_lum,
        "reward_pyre":     reward_pyre,
        "reward_items":    reward_items,
        "new_reward_count":new_reward_count,
    }


def _build_reward_actions(npc_wcid: int, reward: dict, extra_before: list = None) -> str:
    """Build direct SQL emote action rows for quest reward delivery.
    Returns the full INSERT ... VALUES (...), ...; block.
    extra_before = [(type_id, type_name, kwargs), ...] rows to prepend (e.g. TakeItems).
    Handles AwardXP, AwardNoShareXP, AwardLevelProportionalXP.
    """
    XP_IDS = {"AwardXP": 2, "AwardNoShareXP": 62, "AwardLevelProportionalXP": 49}
    xp_type = reward["xp_type"]
    xp_id   = XP_IDS.get(xp_type, 2)
    xp_pct  = reward["xp_pct"]
    reward_xp   = reward["reward_xp"]
    reward_lum  = reward["reward_lum"]
    reward_pyre = reward["reward_pyre"]
    reward_items= reward["reward_items"]

    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")

    def _row(order, type_id, type_name, *,
             message=None, min_val=None, max_val=None,
             min_64=None, max_64=None, percent=None,
             amount=None, amount_64=None, hero_xp_64=None,
             dest_type=None, wcid=None, stack=None, is_first=False, is_last=False):
        pfx = "VALUES" if is_first else "     ,"
        sfx = ";" if is_last else ""
        msg  = f"'{message}'" if message is not None else "NULL"
        mn   = str(min_val)   if min_val   is not None else "NULL"
        mx   = str(max_val)   if max_val   is not None else "NULL"
        m64  = str(min_64)    if min_64    is not None else "NULL"
        mx64 = str(max_64)    if max_64    is not None else "NULL"
        pct  = str(percent)   if percent   is not None else "NULL"
        amt  = str(amount)    if amount    is not None else "NULL"
        amt64= str(amount_64) if amount_64 is not None else "NULL"
        hxp  = str(hero_xp_64) if hero_xp_64 is not None else "NULL"
        dt   = str(dest_type) if dest_type is not None else "NULL"
        wc   = str(wcid)      if wcid      is not None else "NULL"
        sk   = str(stack)     if stack     is not None else "NULL"
        return (f"{pfx} (@parent_id, {order}, {type_id} /* {type_name} */, 0, 1, NULL,"
                f" {msg}, NULL, {mn}, {mx}, {m64}, {mx64}, NULL, NULL, NULL, NULL,"
                f" {amt}, {amt64}, {hxp}, {pct},"
                f" NULL, NULL, NULL, NULL, NULL, NULL,"
                f" {dt}, {wc}, {sk},"
                f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL){sfx}")

    rows = []
    o = 0

    # Prepend extra rows (e.g. TakeItems)
    if extra_before:
        for (tid, tname, kwargs) in extra_before:
            rows.append((o, tid, tname, kwargs))
            o += 1

    # XP
    if reward_xp or xp_type == "AwardLevelProportionalXP":
        if xp_type == "AwardLevelProportionalXP":
            rows.append((o, xp_id, "AwardLevelProportionalXP", {"min_64": 0, "max_64": 0, "percent": xp_pct}))
        elif xp_type == "AwardNoShareXP":
            rows.append((o, xp_id, "AwardNoShareXP", {"amount_64": reward_xp}))
        else:
            rows.append((o, xp_id, "AwardXP", {"amount_64": reward_xp}))
        o += 1

    # Luminance
    if reward_lum:
        rows.append((o, 113, "AwardLuminance", {"hero_xp_64": reward_lum}))
        o += 1

    # Pyreals via Give(273)
    if reward_pyre:
        rows.append((o, 3, "Give", {"dest_type": None, "wcid": 273, "stack": reward_pyre}))
        o += 1

    # Reward items
    for r in reward_items:
        if r.get("wcid"):
            rows.append((o, 3, "Give", {"dest_type": None, "wcid": r["wcid"], "stack": r["qty"]}))
            o += 1

    if not rows:
        return ""

    out_lines = [f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})"]
    for idx, (order, type_id, type_name, kwargs) in enumerate(rows):
        is_first = (idx == 0)
        is_last  = (idx == len(rows) - 1)
        out_lines.append(_row(order, type_id, type_name,
                              is_first=is_first, is_last=is_last, **kwargs))
    return "\n".join(out_lines)


def _emit_emote_block(npc_wcid: int, category: int, cat_name: str,
                      probability: float = 1, quest: str = None) -> str:
    """Emit a weenie_properties_emote row + SET @parent_id."""
    q = f"'{quest}'" if quest else "NULL"
    return (
        f"INSERT INTO `weenie_properties_emote` "
        f"(`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, "
        f"`substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)\n"
        f"VALUES ({npc_wcid}, {category} /* {cat_name} */, {probability}, "
        f"NULL, NULL, NULL, {q}, NULL, NULL, NULL);\n"
        f"\nSET @parent_id = LAST_INSERT_ID();\n"
    )


def _emit_simple_action(type_id: int, type_name: str, message: str = None,
                        min_val=None, max_val=None, amount=None,
                        amount_64=None, hero_xp_64=None,
                        dest_type=None, wcid=None, stack=None) -> str:
    """Emit a single emote action as VALUES(...);"""
    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")
    msg  = f"'{message}'" if message is not None else "NULL"
    mn   = str(min_val)   if min_val   is not None else "NULL"
    mx   = str(max_val)   if max_val   is not None else "NULL"
    amt  = str(amount)    if amount    is not None else "NULL"
    amt64= str(amount_64) if amount_64 is not None else "NULL"
    hxp  = str(hero_xp_64) if hero_xp_64 is not None else "NULL"
    dt   = str(dest_type) if dest_type is not None else "NULL"
    wc   = str(wcid)      if wcid      is not None else "NULL"
    sk   = str(stack)     if stack     is not None else "NULL"
    return (
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        f"VALUES (@parent_id, 0, {type_id} /* {type_name} */, 0, 1, NULL,"
        f" {msg}, NULL, {mn}, {mx}, NULL, NULL, NULL, NULL, NULL, NULL,"
        f" {amt}, {amt64}, {hxp}, NULL,"
        f" NULL, NULL, NULL, NULL, NULL, NULL,"
        f" {dt}, {wc}, {sk},"
        f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);"
    )

# ── TEMPLATE 2: Item Turn-In ──────────────────────────────────────────────────

def generate_item_turnin(params: dict, config) -> list[dict]:
    """
    Generate all SQL files for an Item Turn-In quest.

    The player loots or finds a specific item, then returns it to an NPC
    for XP and/or a reward item in exchange.

    Required params:
        quest_prefix        str  — unique short prefix, no spaces
        npc_name            str  — quest giver display name
        npc_description     str  — personality hint for AI dialogue
        item_name           str  — the turn-in item name
        item_description    str  — short desc shown on item
        reward_xp           int  — XP awarded on turn-in
        reward_pyreals      int  — pyreals awarded (0 = none)
        repeat_hours        int  — repeat timer in hours (0 = one-time)

    Optional:
        item_drop_creature      str  — creature that drops the item (name)
        item_drop_creature_type str  — creature type for the dropper
        item_drop_level         int  — level of drop creature
        item_drop_loot_tier     int  — loot tier for drop creature
        spawn_count             int  — generator spawn count (default 5)
        spawn_delay             float— respawn seconds (default 300)
        reward_item_name        str  — name of item given as reward
        reward_item_description str  — description of reward item
        multi_item_count        int  — how many copies of turn-in item needed (default 1)
    """
    def _si(val, default):
        try: s=str(val).strip(); return int(s) if s and s.lstrip('-').isdigit() else default
        except: return default
    def _sf(val, default):
        try: s=str(val).strip(); return float(s) if s else default
        except: return default

    prefix       = params["quest_prefix"].replace(" ", "")
    npc_name     = params["npc_name"]
    npc_desc     = params.get("npc_description", npc_name)
    item_name    = params["item_name"]
    item_desc    = params.get("item_description", f"A {item_name}.")
    repeat_sec  = _si(params.get("repeat_hours", ""), 20) * 3600
    multi_count = _si(params.get("multi_item_count", ""), 1)
    grant_flag  = _parse_grant_flag(params)

    has_dropper  = bool(params.get("item_drop_creature", "").strip())
    drop_name    = params.get("item_drop_creature", "").strip()
    drop_type    = params.get("item_drop_creature_type", "Human")
    drop_level   = _si(params.get("item_drop_level", ""), 100)
    drop_loot    = _si(params.get("item_drop_loot_tier", ""), 3101)
    spawn_count  = _si(params.get("spawn_count", ""), 5)
    spawn_delay  = _sf(params.get("spawn_delay", ""), 300.0)

    # Quest flags
    qt_flag    = f"{prefix}QT"           # turn-in progress flag (unused in new flow)
    qt_timer   = f"{prefix}QTTimer"      # repeat cooldown timer
    qt_done    = f"{prefix}QTCompleted"  # completion stamp
    qt_started = f"{prefix}QTStarted"    # NPC has explained task (gating flag)

    # Reward params (toggle-aware — absent = off = 0)
    _rp = _parse_reward_params(params, _si)
    reward_xp    = _rp["reward_xp"];    reward_lum  = _rp["reward_lum"]
    reward_pyre  = _rp["reward_pyre"];  reward_items= _rp["reward_items"]
    xp_type      = _rp["xp_type"];      xp_pct      = _rp["xp_pct"]
    new_reward_count = _rp["new_reward_count"]

    # WCID allocation — turn-in item + generated reward items
    total_items = 1 + new_reward_count
    needed = [("custom_npcs", 1), ("custom_items", total_items)]
    if has_dropper:
        needed += [("campaign_creatures", 1), ("kill_contracts", 1)]

    wcids = alloc_wcids(config, needed)

    item_pool    = list(wcids["custom_items"])
    npc_wcid     = wcids["custom_npcs"][0]
    item_wcid    = item_pool.pop(0)  # turn-in item always first
    drop_wcid    = wcids["campaign_creatures"][0] if has_dropper else None
    gen_wcid     = wcids["kill_contracts"][0] if has_dropper else None

    # Assign WCIDs to reward items
    for r in reward_items:
        if r["is_existing"]:
            r["wcid"] = int(r["wcid_raw"])
        else:
            r["wcid"] = item_pool.pop(0)


    npc_slug     = _slug(npc_name)
    item_slug    = _slug(item_name)
    drop_slug    = _slug(drop_name) if has_dropper else ""

    files = []

    # ── Quest Flag Files — one file per flag ──────────────────────────────────
    max_solves_timer = 1 if repeat_sec > 0 else -1

    def _qf(flag_name, quest_id, min_delta, max_solves, message):
        sql = (
            f"DELETE FROM quest WHERE name = '{flag_name}';\n\n"
            f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
            f"VALUES ('{quest_id}', '{flag_name}', '{min_delta}', '{max_solves}', '{message}');"
        )
        return {"filename": f"Quest_{flag_name}.sql",
                "sql": f"/* ===== FILE: Quest_{flag_name}.sql ===== */\n\n{sql}",
                "type": "quest_flag"}

    files.append(_qf(qt_timer,   '0', repeat_sec,    max_solves_timer, 'item turn-in timer'))
    files.append(_qf(qt_done,    '0', '0',            '-1',             'item turn-in completed'))
    files.append(_qf(qt_started, '0', '0',            '-1',             'task explained by npc'))
    if grant_flag:
        files.append(_grant_flag_file(grant_flag["name"]))

    # ── File 2: Turn-In Item ──────────────────────────────────────────────────
    item_int_rows = [
        (1,   8192, "ItemType - Writable/Quest"),
        (5,   10,   "EncumbranceVal"),
        (8,   5,    "Mass"),
        (16,  8,    "ItemUseable - Contained"),
        (19,  0,    "Value"),
        (93,  1044, "PhysicsState"),
    ]
    item_bool_rows = [(22, False, "Inscribable")]
    item_str_rows  = [
        (1,  item_name, "Name"),
        (15, item_desc, "ShortDesc"),
    ]
    item_did_rows  = [
        (1,  0x02000155, "Setup"),
        (3,  0x20000014, "SoundTable"),
        (8,  0x06001310, "Icon"),
        (22, 0x3400002B, "PhysicsEffectTable"),
    ]
    fname_item = f"{item_wcid}_{item_slug}.sql"
    item_sections = [
        f"/* ===== FILE: {fname_item} ===== */", "",
        _emit_header(item_wcid, item_name, 6),  # includes DELETE + INSERT weenie
        "", _emit_int_props(item_wcid, item_int_rows),
        "", _emit_bool_props(item_wcid, item_bool_rows),
        "", _emit_str_props(item_wcid, item_str_rows),
        "", _emit_did_props(item_wcid, item_did_rows), "",
    ]
    files.append({
        "filename": fname_item,
        "sql":      "\n".join(item_sections),
        "type":     "item",
        "wcid":     item_wcid,
    })

    # ── File 3 (optional): Drop Creature ─────────────────────────────────────
    if has_dropper and drop_wcid:
        from aceforge.json_to_sql import CREATURE_TYPE
        drop_type_int = CREATURE_TYPE.get(drop_type.lower().replace(" ", "_"), 1)
        drop_data = {
            "name":               drop_name,
            "class_name":         drop_slug,
            "level":              drop_level,
            "xp":                 drop_level * 3000,
            "health":             drop_level * 8,
            "stamina":            drop_level * 6,
            "mana":               drop_level * 2,
            "armor":              max(40, drop_level // 2),
            "creature_type_int":  drop_type_int,
            "creature_type_label":drop_type,
            "attack_skill_id":    44,
            "attack_skill_name":  "HeavyWeapons",
            "attack_skill":       drop_level + 50,
            "melee_defense":      drop_level + 30,
            "loot_tier":          drop_loot,
            # Item drops from create_list on corpse
            "create_list": [
                {"wcid": item_wcid, "qty": 1,
                 "destination": "corpse_drop",
                 "comment": f"{item_name} trophy drop"},
            ],
        }
        fname_drop = f"{drop_wcid}_{drop_slug}.sql"
        files.append({
            "filename": fname_drop,
            "sql":      _creature_sql(drop_wcid, drop_data, fname_drop),
            "type":     "creature",
            "wcid":     drop_wcid,
        })

        # ── File 4: Drop Creature Generator ──────────────────────────────────
        fname_gen = f"{gen_wcid}_{drop_slug}_generator.sql"
        files.append({
            "filename": fname_gen,
            "sql":      _generator_sql(gen_wcid, drop_wcid, drop_slug,
                                       fname_gen, spawn_count, spawn_delay),
            "type":     "generator",
            "wcid":     gen_wcid,
        })

    # ── Reward Item Files (generated items only — existing WCIDs skip file gen) ──
    for r in reward_items:
        if r["is_existing"]:
            continue  # user supplied an existing WCID — no file needed
        ri_wcid = r["wcid"]
        ri_name = r["name"]
        ri_desc = r["desc"]
        ri_slug = _slug(ri_name)
        ri_int  = [(1,256,"ItemType - Misc"),(5,10,"EncumbranceVal"),
                   (8,5,"Mass"),(19,0,"Value"),(93,1044,"PhysicsState")]
        ri_str  = [(1,ri_name,"Name"),(15,ri_desc,"ShortDesc")]
        ri_did  = [(1,0x02000155,"Setup"),(3,0x20000014,"SoundTable"),
                   (8,0x06001310,"Icon"),(22,0x3400002B,"PhysicsEffectTable")]
        fname_ri = f"{ri_wcid}_{ri_slug}.sql"
        ri_secs  = [
            f"/* ===== FILE: {fname_ri} ===== */", "",
            _emit_header(ri_wcid, ri_name, 6),
            "", _emit_int_props(ri_wcid, ri_int),
            "", _emit_str_props(ri_wcid, ri_str),
            "", _emit_did_props(ri_wcid, ri_did), "",
        ]
        files.append({
            "filename": fname_ri,
            "sql":      "\n".join(ri_secs),
            "type":     "item",
            "wcid":     ri_wcid,
        })

    # ── NPC Quest Giver — direct SQL emotes ───────────────────────────────────
    fname_npc = f"{npc_wcid}_{npc_slug}.sql"
    npc_base  = _npc_base_sql(npc_wcid, npc_name, npc_slug, fname_npc)

    rp = _rp  # reward dict from _parse_reward_params
    qty_check = f"{item_wcid} {multi_count}"

    # ── Emote chain matching target YAML / SQL exactly ────────────────────────
    # Use → InqQuest(Timer)
    #   QS(Timer)  → DirectBroadcast(cooldown)
    #   QF(Timer)  → InqQuest(QTStarted)
    #     QS(QTStarted) → InqOwnsItems(item, qty)
    #       TS(OwnsItem) → TakeItems + StampQuest(Timer) + StampQuest(Done)
    #                       + EraseQuest(Started) + XP + Lum + Give(rewards)
    #       TF(OwnsItem) → DirectBroadcast(need item msg)
    #     QF(QTStarted) → Tell(task description) + StampQuest(QTStarted)
    emote_parts = []

    # Block 1: Use → InqQuest(timer)
    emote_parts.append(_emit_emote_block(npc_wcid, 7, "Use"))
    emote_parts.append(_emit_simple_action(21, "InqQuest", message=qt_timer))

    # Block 2: QuestSuccess(timer) → cooldown
    emote_parts.append(_emit_emote_block(npc_wcid, 12, "QuestSuccess", quest=qt_timer))
    emote_parts.append(_emit_simple_action(18, "DirectBroadcast",
                        message="You have completed this task too recently."))

    # Block 3: QuestFailure(timer) → InqQuest(QTStarted)
    emote_parts.append(_emit_emote_block(npc_wcid, 13, "QuestFailure", quest=qt_timer))
    emote_parts.append(_emit_simple_action(21, "InqQuest", message=qt_started))

    # Block 4: QuestSuccess(QTStarted) → InqOwnsItems
    emote_parts.append(_emit_emote_block(npc_wcid, 12, "QuestSuccess", quest=qt_started))
    emote_parts.append(_emit_simple_action(76, "InqOwnsItems",
                        message=f"OwnsItem-{item_wcid}",
                        dest_type=None, wcid=item_wcid, stack=multi_count))

    # Block 5: TestSuccess(OwnsItem) → TakeItems + stamps + erase + XP + Lum + Give
    _it_extras = [
        (74, "TakeItems",   {"dest_type": None, "wcid": item_wcid, "stack": multi_count}),
        (22, "StampQuest",  {"message": qt_timer}),
        (22, "StampQuest",  {"message": qt_done}),
        (31, "EraseQuest",  {"message": qt_started}),
    ]
    if grant_flag:
        _it_extras.append((22, "StampQuest", {"message": grant_flag["name"]}))
        _it_extras.append((10, "Tell", {"message": f"You are now flagged for {grant_flag['desc']}.\n"}))
    reward_actions = _build_reward_actions(npc_wcid, rp, extra_before=_it_extras)
    emote_parts.append(_emit_emote_block(npc_wcid, 22, "TestSuccess",
                                         quest=f"OwnsItem-{item_wcid}"))
    emote_parts.append(reward_actions)

    # Block 6: TestFailure(OwnsItem) → need item message
    emote_parts.append(_emit_emote_block(npc_wcid, 23, "TestFailure",
                                         quest=f"OwnsItem-{item_wcid}"))
    emote_parts.append(_emit_simple_action(18, "DirectBroadcast",
                        message=f"You need {multi_count} {item_name} to complete this task."))

    # Block 7: QuestFailure(QTStarted) → explain task + stamp started
    #   npc_desc contains the personality/task description — use item_desc as fallback
    task_intro = params.get("npc_description", "") or f"I am in need of {multi_count} {item_name}! Bring one to me and I will reward you well!"
    emote_parts.append(_emit_emote_block(npc_wcid, 13, "QuestFailure", quest=qt_started))
    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")
    def _null_row(order, type_id, type_name, message=None, dest_type=None,
                  wcid=None, stack=None, amount_64=None, is_first=False, is_last=False):
        pfx = "VALUES" if is_first else "     ,"
        sfx = ";" if is_last else ""
        msg = f"'{message}'" if message else "NULL"
        dt  = str(dest_type) if dest_type is not None else "NULL"
        wc  = str(wcid)      if wcid      is not None else "NULL"
        sk  = str(stack)     if stack     is not None else "NULL"
        a64 = str(amount_64) if amount_64 is not None else "NULL"
        return (f"{pfx} (@parent_id, {order}, {type_id} /* {type_name} */, 0, 1, NULL,"
                f" {msg}, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,"
                f" NULL, {a64}, NULL, NULL,"
                f" NULL, NULL, NULL, NULL, NULL, NULL,"
                f" {dt}, {wc}, {sk},"
                f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL){sfx}")

    emote_parts.append(
        f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
        + _null_row(0, 10, "Tell", message=task_intro, is_first=True)
        + "\n"
        + _null_row(1, 22, "StampQuest", message=qt_started, is_last=True)
    )

    emote_sql = "\n\n".join(p for p in emote_parts if p)

    files.append({
        "filename": fname_npc,
        "sql": npc_base + "\n" + emote_sql + "\n",
        "type":     "npc",
        "wcid":     npc_wcid,
    })

    return files


# ── TEMPLATE 5: Delivery Quest ────────────────────────────────────────────────

def generate_delivery(params: dict, config) -> list[dict]:
    """
    Generate all SQL files for a Delivery Quest.

    Player receives an item from NPC A and delivers it to NPC B.
    Optionally chains through NPC C and NPC D for multi-hop deliveries.
    Each NPC checks the previous flag before accepting the delivery.

    Required params:
        quest_prefix        str  — unique short prefix, no spaces
        item_name           str  — name of the delivery item
        item_description    str  — short desc on the item
        npc_a_name          str  — first NPC (quest giver, gives the item)
        npc_a_description   str  — personality hint for NPC A
        npc_b_name          str  — second NPC (first recipient)
        npc_b_description   str  — personality hint for NPC B
        reward_xp           int  — XP given at final delivery
        reward_pyreals      int  — pyreals given at final delivery
        repeat_hours        int  — repeat timer (0 = one-time)

    Optional:
        npc_c_name          str  — third NPC in chain (leave blank to stop at B)
        npc_c_description   str  — personality hint for NPC C
        npc_d_name          str  — fourth NPC in chain
        npc_d_description   str  — personality hint for NPC D
        intermediate_xp     int  — XP given at each intermediate handoff
        reward_item_name    str  — item given at final delivery
        reward_item_desc    str  — description of reward item
        item_count          int  — how many copies of item required (default 1)
    """
    def _si(val, default):
        try: s=str(val).strip(); return int(s) if s and s.lstrip('-').isdigit() else default
        except: return default

    prefix       = params["quest_prefix"].replace(" ", "")
    item_name    = params["item_name"]
    item_desc    = params.get("item_description", f"A delivery item from {params.get('npc_a_name','an NPC')}.")
    repeat_sec   = _si(params.get("repeat_hours", ""), 20) * 3600
    item_count  = _si(params.get("item_count", ""), 1)
    grant_flag  = _parse_grant_flag(params)  # optional extra flag on completion

    # Reward params (toggle-aware)
    _rp = _parse_reward_params(params, _si)
    reward_xp    = _rp["reward_xp"];   reward_lum   = _rp["reward_lum"]
    reward_pyre  = _rp["reward_pyre"]; reward_items = _rp["reward_items"]
    xp_type      = _rp["xp_type"];     xp_pct       = _rp["xp_pct"]
    new_reward_count = _rp["new_reward_count"]
    has_reward_item  = bool(reward_items)

    # Delivery is Quest Giver (A) → Item Recipient (B) only
    npc_defs = []
    for letter in ["a", "b"]:
        name = params.get(f"npc_{letter}_name", "").strip()
        if not name:
            raise ValueError(f"NPC {letter.upper()} name is required for delivery quest.")
        npc_defs.append({
            "letter":      letter.upper(),
            "name":        name,
            "description": params.get(f"npc_{letter}_description", name),
            "slug":        _slug(name),
            "flag_done":   f"{prefix}Del{letter.upper()}",
        })

    n_npcs      = len(npc_defs)
    item_slug   = _slug(item_name)
    final_done  = f"{prefix}Done"

    # WCID allocation
    needed = [
        ("custom_npcs",  n_npcs),
        ("custom_items", 1 + new_reward_count),  # delivery item + reward items
    ]
    wcids = alloc_wcids(config, needed)

    npc_wcid_list = wcids["custom_npcs"]
    item_wcids    = list(wcids["custom_items"])
    item_wcid     = item_wcids.pop(0)

    # Assign WCIDs to new reward items
    for r in _rp["reward_items"]:
        if r["is_existing"]:
            r["wcid"] = int(r["wcid_raw"])
        elif item_wcids:
            r["wcid"] = item_wcids.pop(0)
    reward_wcid = None  # legacy single-item path unused

    for i, npc in enumerate(npc_defs):
        npc["wcid"] = npc_wcid_list[i]

    files = []

    # ── Quest Flag Files — one file per flag ──────────────────────────────────
    def _qf(flag_name, quest_id, min_delta, max_solves_val, message):
        sql = (
            f"DELETE FROM quest WHERE name = '{flag_name}';\n\n"
            f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
            f"VALUES ('{quest_id}', '{flag_name}', '{min_delta}', '{max_solves_val}', '{message}');"
        )
        return {"filename": f"Quest_{flag_name}.sql",
                "sql": f"/* ===== FILE: Quest_{flag_name}.sql ===== */\n\n{sql}",
                "type": "quest_flag"}

    for npc in npc_defs:
        files.append(_qf(npc["flag_done"], '0', '0', '-1', 'delivery flag'))
    max_solves_final = -1
    files.append(_qf(final_done, '0', repeat_sec, max_solves_final, 'delivery complete'))
    if grant_flag:
        files.append(_grant_flag_file(grant_flag["name"]))

    # ── Delivery Item ─────────────────────────────────────────────────────────
    di_int  = [
        (1,   8192, "ItemType - Writable/Quest"),
        (5,   5,    "EncumbranceVal"),
        (8,   2,    "Mass"),
        (16,  8,    "ItemUseable - Contained"),
        (19,  0,    "Value"),
        (93,  1044, "PhysicsState"),
    ]
    di_bool = [(22, False, "Inscribable")]
    di_str  = [
        (1,  item_name, "Name"),
        (15, item_desc, "ShortDesc"),
    ]
    di_did  = [
        (1,  0x02000155, "Setup"),
        (3,  0x20000014, "SoundTable"),
        (8,  0x06001310, "Icon"),
        (22, 0x3400002B, "PhysicsEffectTable"),
    ]
    fname_item = f"{item_wcid}_{item_slug}.sql"
    item_secs  = [
        f"/* ===== FILE: {fname_item} ===== */", "",
        f"DELETE FROM `weenie` WHERE `class_Id` = {item_wcid};", "",
        _emit_header(item_wcid, item_slug, 6),
        "", _emit_int_props(item_wcid, di_int),
        "", _emit_bool_props(item_wcid, di_bool),
        "", _emit_str_props(item_wcid, di_str),
        "", _emit_did_props(item_wcid, di_did), "",
    ]
    files.append({
        "filename": fname_item,
        "sql":      "\n".join(item_secs),
        "type":     "item",
        "wcid":     item_wcid,
    })

    # ── Reward Item Files (generated items only) ────────────────────────────
    for r in _rp["reward_items"]:
        if r.get("is_existing") or not r.get("wcid"):
            continue
        ri_slug = _slug(r["name"])
        ri_int  = [(1,256,"ItemType"),(5,10,"EncumbranceVal"),
                   (8,5,"Mass"),(19,0,"Value"),(93,1044,"PhysicsState")]
        ri_str  = [(1,r["name"],"Name"),(15,r.get("desc",r["name"]),"ShortDesc")]
        ri_did  = [(1,0x02000155,"Setup"),(3,0x20000014,"SoundTable"),
                   (8,0x06001310,"Icon"),(22,0x3400002B,"PhysicsEffectTable")]
        fname_ri = f"{r['wcid']}_{ri_slug}.sql"
        ri_secs  = [
            f"/* ===== FILE: {fname_ri} ===== */","",
            _emit_header(r["wcid"], r["name"], 6),
            "", _emit_int_props(r["wcid"], ri_int),
            "", _emit_str_props(r["wcid"], ri_str),
            "", _emit_did_props(r["wcid"], ri_did),"",
        ]
        files.append({
            "filename": fname_ri,
            "sql":      "\n".join(ri_secs),
            "type":     "item",
            "wcid":     r["wcid"],
        })

    # ── NPC Files — direct SQL emotes ────────────────────────────────────────
    npc_a    = npc_defs[0]
    npc_b    = npc_defs[1]
    del_flag = npc_a["flag_done"]   # PackDeliveryDelA
    npc_b_desc = npc_b.get("description", npc_b["name"])

    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")

    def _emo(wcid, cat_id, cat_name, quest=None):
        q = f"'{quest}'" if quest else "NULL"
        return (f"INSERT INTO `weenie_properties_emote` ({_EMO_COLS})\n"
                f"VALUES ({wcid}, {cat_id} /* {cat_name} */, 1, NULL, NULL, NULL,"
                f" {q}, NULL, NULL, NULL);\n\nSET @parent_id = LAST_INSERT_ID();\n")

    _EMO_COLS = ("`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`,"
                 " `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`")

    def _act(order, type_id, type_name, *,
             message=None, wcid=None, stack=None,
             amount_64=None, hero_xp_64=None, percent=None, min_64=None, max_64=None,
             is_first=False, is_last=False):
        pfx = "VALUES" if is_first else "     ,"
        sfx = ";" if is_last else ""
        msg  = f"'{message}'" if message is not None else "NULL"
        wc   = str(wcid)      if wcid      is not None else "NULL"
        sk   = str(stack)     if stack     is not None else "NULL"
        a64  = str(amount_64) if amount_64 is not None else "NULL"
        hxp  = str(hero_xp_64) if hero_xp_64 is not None else "NULL"
        pct  = str(percent)   if percent   is not None else "NULL"
        m64  = str(min_64)    if min_64    is not None else "NULL"
        mx64 = str(max_64)    if max_64    is not None else "NULL"
        return (f"{pfx} (@parent_id, {order}, {type_id} /* {type_name} */, 0, 1, NULL,"
                f" {msg}, NULL, NULL, NULL, {m64}, {mx64}, NULL, NULL, NULL, NULL,"
                f" NULL, {a64}, {hxp}, {pct},"
                f" NULL, NULL, NULL, NULL, NULL, NULL,"
                f" NULL, {wc}, {sk},"
                f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL){sfx}")

    def _single(wcid, cat_id, cat_name, quest, type_id, type_name, **kwargs):
        return (_emo(wcid, cat_id, cat_name, quest)
                + f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                + _act(0, type_id, type_name, is_first=True, is_last=True, **kwargs))

    # ── NPC A: Quest Giver ────────────────────────────────────────────────────
    # Use → InqQuest(Done)
    #   QS(Done) → Tell(already done / timer)
    #   QF(Done) → InqQuest(DelA)
    #     QS(DelA) → Tell(reminder: take it to B)
    #     QF(DelA) → Tell(task intro) + Give(item) + StampQuest(DelA)
    npc_a_wcid = npc_a["wcid"]
    npc_b_name = npc_b["name"]
    intro_msg  = params.get("npc_a_description", "").strip() or f"I need you to deliver this {item_name} to {npc_b_name}."

    npc_a_parts = []

    # Block 1: Use → InqQuest(Done)
    npc_a_parts.append(_emo(npc_a_wcid, 7, "Use"))
    npc_a_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 21, "InqQuest", message=final_done, is_first=True, is_last=True))

    # Block 2: QS(Done) → Tell(already done)
    npc_a_parts.append(_emo(npc_a_wcid, 12, "QuestSuccess", quest=final_done))
    npc_a_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell",
                              message="You have already completed this delivery. Return when the timer resets.",
                              is_first=True, is_last=True))

    # Block 3: QF(Done) → InqQuest(DelA)
    npc_a_parts.append(_emo(npc_a_wcid, 13, "QuestFailure", quest=final_done))
    npc_a_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 21, "InqQuest", message=del_flag, is_first=True, is_last=True))

    # Block 4: QS(DelA) → Tell(reminder)
    npc_a_parts.append(_emo(npc_a_wcid, 12, "QuestSuccess", quest=del_flag))
    npc_a_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell",
                              message=f"Take the {item_name} to {npc_b_name}.",
                              is_first=True, is_last=True))

    # Block 5: QF(DelA) → Tell(intro) + Give(item) + StampQuest(DelA)
    npc_a_parts.append(_emo(npc_a_wcid, 13, "QuestFailure", quest=del_flag))
    npc_a_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell", message=intro_msg, is_first=True)
                       + "\n"
                       + _act(1, 3, "Give", wcid=item_wcid, stack=item_count)
                       + "\n"
                       + _act(2, 22, "StampQuest", message=del_flag, is_last=True))

    npc_a_emote_sql = "\n\n".join(npc_a_parts)

    fname_a = f"{npc_a_wcid}_{npc_a['slug']}.sql"
    npc_a_base = _npc_base_sql(npc_a_wcid, npc_a["name"], npc_a["slug"], fname_a)
    files.append({"filename": fname_a, "sql": npc_a_base + "\n" + npc_a_emote_sql + "\n",
                  "type": "npc", "wcid": npc_a_wcid})

    # ── NPC B: Item Recipient ─────────────────────────────────────────────────
    # Use → InqQuest(Done)
    #   QS(Done) → Tell(already done)
    #   QF(Done) → InqQuest(DelA)
    #     QS(DelA) → InqOwnsItems(item,qty)
    #       TS → TakeItems + rewards + StampQuest(Done) + Tell(thanks)
    #       TF → Tell(missing item)
    #     QF(DelA) → Tell(no task)
    npc_b_wcid   = npc_b["wcid"]
    already_msg  = npc_b_desc if npc_b_desc != npc_b["name"] else "You have already made your delivery. My thanks!"
    notask_msg   = f"I have nothing for you at this time."
    missing_msg  = f"You do not have the {item_name}! Bring it to me!"
    thanks_msg   = f"Excellent. This is exactly what I needed. You have my thanks!"
    owns_key     = f"OwnsItem-{item_wcid}"

    # Build reward rows for Accept block
    XP_TYPE = _rp["xp_type"]; XP_PCT = _rp["xp_pct"]
    XP_IDS  = {"AwardXP":2,"AwardNoShareXP":62,"AwardLevelProportionalXP":49}
    xp_id   = XP_IDS.get(XP_TYPE, 2)

    accept_rows = []
    o = 0
    accept_rows.append(_act(o, 74, "TakeItems", wcid=item_wcid, stack=item_count, is_first=True)); o+=1
    if reward_xp or XP_TYPE=="AwardLevelProportionalXP":
        if XP_TYPE=="AwardLevelProportionalXP":
            accept_rows.append(_act(o, xp_id, "AwardLevelProportionalXP", min_64=0, max_64=0, percent=XP_PCT)); o+=1
        else:
            accept_rows.append(_act(o, xp_id, XP_TYPE, amount_64=reward_xp)); o+=1
    if reward_lum:
        accept_rows.append(_act(o, 113, "AwardLuminance", hero_xp_64=reward_lum)); o+=1
    if reward_pyre:
        accept_rows.append(_act(o, 3, "Give", wcid=273, stack=reward_pyre)); o+=1
    for _r in _rp["reward_items"]:
        if _r.get("wcid"):
            accept_rows.append(_act(o, 3, "Give", wcid=_r["wcid"], stack=_r["qty"])); o+=1
    accept_rows.append(_act(o, 22, "StampQuest", message=final_done)); o+=1
    if grant_flag:
        accept_rows.append(_act(o, 22, "StampQuest", message=grant_flag["name"])); o+=1
        accept_rows.append(_act(o, 10, "Tell",
                               message=f"You are now flagged for {grant_flag['desc']}.",
                               is_last=True))
    else:
        accept_rows.append(_act(o, 10, "Tell", message=thanks_msg, is_last=True))

    npc_b_parts = []

    # Block 1: Use → InqQuest(Done)
    npc_b_parts.append(_emo(npc_b_wcid, 7, "Use"))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 21, "InqQuest", message=final_done, is_first=True, is_last=True))

    # Block 2: QS(Done) → Tell(already done)
    npc_b_parts.append(_emo(npc_b_wcid, 12, "QuestSuccess", quest=final_done))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell", message=already_msg, is_first=True, is_last=True))

    # Block 3: QF(Done) → InqQuest(DelA)
    npc_b_parts.append(_emo(npc_b_wcid, 13, "QuestFailure", quest=final_done))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 21, "InqQuest", message=del_flag, is_first=True, is_last=True))

    # Block 4: QS(DelA) → InqOwnsItems
    npc_b_parts.append(_emo(npc_b_wcid, 12, "QuestSuccess", quest=del_flag))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 76, "InqOwnsItems", message=owns_key,
                              wcid=item_wcid, stack=item_count, is_first=True, is_last=True))

    # Block 5: TS(OwnsItem) → rewards
    npc_b_parts.append(_emo(npc_b_wcid, 22, "TestSuccess", quest=owns_key))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + "\n".join(accept_rows))

    # Block 6: TF(OwnsItem) → missing item
    npc_b_parts.append(_emo(npc_b_wcid, 23, "TestFailure"))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell", message=missing_msg, is_first=True, is_last=True))

    # Block 7: QF(DelA) → no task
    npc_b_parts.append(_emo(npc_b_wcid, 13, "QuestFailure", quest=del_flag))
    npc_b_parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                       + _act(0, 10, "Tell", message=notask_msg, is_first=True, is_last=True))

    npc_b_emote_sql = "\n\n".join(npc_b_parts)

    fname_b = f"{npc_b_wcid}_{npc_b['slug']}.sql"
    npc_b_base = _npc_base_sql(npc_b_wcid, npc_b["name"], npc_b["slug"], fname_b)
    files.append({"filename": fname_b, "sql": npc_b_base + "\n" + npc_b_emote_sql + "\n",
                  "type": "npc", "wcid": npc_b_wcid})

    return files


# ── TEMPLATE 6: Flagging Quest ────────────────────────────────────────────────

def generate_flagging(params: dict, config) -> list[dict]:
    """
    Generate all SQL files for a Flagging Quest.

    Completing this quest permanently (or repeatably) flags the player,
    unlocking something they couldn't access before. The gate can be
    enforced by any NPC that checks the flag before granting access.

    Common uses:
      - Unlock a dungeon or area (guardian NPC checks flag to open path)
      - Unlock a vendor's stock tier (vendor checks flag before selling)
      - Unlock a buff or augmentation grant
      - Prerequisite for another quest chain
      - Society/faction reputation gate

    Required params:
        quest_prefix        str  — unique short prefix, no spaces
        npc_name            str  — quest giver NPC name
        npc_description     str  — personality hint for AI dialogue
        quest_name          str  — display name of the quest (used in dialogue)
        unlock_description  str  — what gets unlocked (e.g. "access to the Vault of Ages")
        requirement_type    str  — "kill_task", "item_turnin", "none"
        reward_xp           int  — XP at completion
        reward_pyreals      int  — pyreals at completion
        repeat_hours        int  — repeat timer (0 = permanent flag)

    Requirement-specific params:
        If requirement_type == "kill_task":
            req_creature        str  — creature to kill
            req_creature_type   str  — creature type
            req_creature_level  int  — level
            req_kill_count      int  — how many
            req_loot_tier       str  — loot tier
            req_spawn_count     int  — spawn count (default 5)
            req_spawn_delay     float— respawn delay (default 300)

        If requirement_type == "item_turnin":
            req_item_name       str  — item to collect and turn in
            req_item_desc       str  — item description
            req_item_count      int  — quantity needed (default 1)
            req_item_creature   str  — creature that drops it (optional)
            req_item_ctype      str  — drop creature type
            req_item_level      int  — drop creature level
            req_item_loot       str  — drop creature loot tier

    Optional:
        reward_item_name    str  — item granted on completion
        reward_item_desc    str  — description of reward item
    """
    def _si(val, default):
        try: s=str(val).strip(); return int(s) if s and s.lstrip('-').isdigit() else default
        except: return default
    def _sf(val, default):
        try: s=str(val).strip(); return float(s) if s else default
        except: return default

    prefix       = params["quest_prefix"].replace(" ", "")
    npc_name     = params["npc_name"]
    npc_desc     = params.get("npc_description", npc_name)
    quest_name   = params.get("quest_name", f"{npc_name}'s Test")
    unlock_desc  = params.get("unlock_description", "access to restricted content")
    req_type     = params.get("requirement_type", "none").strip().lower()
    repeat_sec   = _si(params.get("repeat_hours", ""), 0) * 3600

    # Reward params (toggle-aware)
    _rp = _parse_reward_params(params, _si)
    reward_xp    = _rp["reward_xp"];   reward_lum  = _rp["reward_lum"]
    reward_pyre  = _rp["reward_pyre"]; reward_items= _rp["reward_items"]
    xp_type      = _rp["xp_type"];     xp_pct      = _rp["xp_pct"]
    new_reward_count = _rp["new_reward_count"]

    has_reward_item  = bool(reward_items)

    # Quest flags
    req_flag   = f"{prefix}Req"       # requirement progress (kill/item)
    done_flag  = f"{prefix}Flagged"   # the permanent unlock flag

    # WCID allocation
    needed = [("custom_npcs", 1)]
    if req_type == "kill_task":
        needed += [("campaign_creatures", 1), ("kill_contracts", 1)]
    elif req_type == "item_turnin":
        needed.append(("custom_items", 1))
        if params.get("req_item_creature", "").strip():
            needed += [("campaign_creatures", 1), ("kill_contracts", 1)]
    if new_reward_count:
        needed.append(("custom_items", new_reward_count))

    wcids = alloc_wcids(config, needed)

    npc_wcid      = wcids["custom_npcs"][0]
    cc_pool = list(wcids.get("campaign_creatures", []))
    kc_pool = list(wcids.get("kill_contracts", []))
    ci_pool = list(wcids.get("custom_items", []))

    req_creature_wcid = None
    req_gen_wcid      = None
    req_item_wcid     = None

    if req_type == "kill_task":
        req_creature_wcid = cc_pool.pop(0) if cc_pool else None
        req_gen_wcid      = kc_pool.pop(0) if kc_pool else None
    elif req_type == "item_turnin":
        req_item_wcid = ci_pool.pop(0) if ci_pool else None
        if params.get("req_item_creature", "").strip():
            req_creature_wcid = cc_pool.pop(0) if cc_pool else None
            req_gen_wcid      = kc_pool.pop(0) if kc_pool else None

    # Assign WCIDs to generated reward items
    for r in reward_items:
        if r["is_existing"]:
            r["wcid"] = int(r["wcid_raw"])
        elif ci_pool:
            r["wcid"] = ci_pool.pop(0)

    npc_slug      = _slug(npc_name)

    files = []

    # ── Quest Flag Files — one file per flag ──────────────────────────────────
    def _qf(flag_name, quest_id, min_delta, max_solves_val, message):
        sql = (
            f"DELETE FROM quest WHERE name = '{flag_name}';\n\n"
            f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
            f"VALUES ('{quest_id}', '{flag_name}', '{min_delta}', '{max_solves_val}', '{message}');"
        )
        return {"filename": f"Quest_{flag_name}.sql",
                "sql": f"/* ===== FILE: Quest_{flag_name}.sql ===== */\n\n{sql}",
                "type": "quest_flag"}

    if req_type == "kill_task":
        files.append(_qf(req_flag,  '0', '0', '-1', 'kill requirement progress'))
    files.append(_qf(done_flag, '0', repeat_sec, '-1', 'flagging quest'))

    # ── Requirement: Kill Task ────────────────────────────────────────────────
    if req_type == "kill_task" and req_creature_wcid:
        from aceforge.json_to_sql import CREATURE_TYPE
        c_name  = params.get("req_creature", "Enemy")
        c_type  = params.get("req_creature_type", "Human")
        c_level = _si(params.get("req_creature_level", ""), 150)
        k_count = _si(params.get("req_kill_count", ""), 25)
        lt_raw  = params.get("req_loot_tier", "T4 (3101)")
        lt_m    = __import__("re").search(r"\((\d+)\)", str(lt_raw))
        loot_t  = int(lt_m.group(1)) if lt_m else 3101
        c_slug  = _slug(c_name)
        c_tint  = CREATURE_TYPE.get(c_type.lower().replace(" ","_"), 1)

        c_data = {
            "name":                c_name, "class_name": c_slug,
            "level":               c_level, "xp": c_level * 3000,
            "health":              c_level * 8, "stamina": c_level * 6,
            "mana":                c_level * 2,
            "armor":               max(40, c_level // 2),
            "creature_type_int":   c_tint, "creature_type_label": c_type,
            "attack_skill_id":     44, "attack_skill_name": "HeavyWeapons",
            "attack_skill":        c_level + 50, "melee_defense": c_level + 30,
            "kill_quest":          req_flag, "loot_tier": loot_t,
        }
        fname_c = f"{req_creature_wcid}_{c_slug}.sql"
        files.append({
            "filename": fname_c,
            "sql":      _creature_sql(req_creature_wcid, c_data, fname_c),
            "type":     "creature", "wcid": req_creature_wcid,
        })
        fname_g = f"{req_gen_wcid}_{c_slug}_generator.sql"
        sc = _si(params.get("req_spawn_count",""), 5)
        sd = _sf(params.get("req_spawn_delay",""), 300.0)
        files.append({
            "filename": fname_g,
            "sql":      _generator_sql(req_gen_wcid, req_creature_wcid, c_slug,
                                       fname_g, sc, sd),
            "type":     "generator", "wcid": req_gen_wcid,
        })

    # ── Requirement: Item Turn-In ─────────────────────────────────────────────
    elif req_type == "item_turnin" and req_item_wcid:
        ri_name = params.get("req_item_name", "Required Item")
        ri_desc = params.get("req_item_desc", f"An item needed for {quest_name}.")
        ri_slug = _slug(ri_name)
        ri_count= _si(params.get("req_item_count",""), 1)

        ri_int  = [(1,8192,"ItemType"),(5,5,"EncumbranceVal"),
                   (8,2,"Mass"),(16,8,"ItemUseable"),(19,0,"Value"),(93,1044,"PhysicsState")]
        ri_bool = [(22,False,"Inscribable")]
        ri_str  = [(1,ri_name,"Name"),(15,ri_desc,"ShortDesc")]
        ri_did  = [(1,0x02000155,"Setup"),(3,0x20000014,"SoundTable"),
                   (8,0x06001310,"Icon"),(22,0x3400002B,"PhysicsEffectTable")]
        fname_ri = f"{req_item_wcid}_{ri_slug}.sql"
        ri_secs  = [
            f"/* ===== FILE: {fname_ri} ===== */","",
            f"DELETE FROM `weenie` WHERE `class_Id` = {req_item_wcid};","",
            _emit_header(req_item_wcid, ri_slug, 6),
            "", _emit_int_props(req_item_wcid, ri_int),
            "", _emit_bool_props(req_item_wcid, ri_bool),
            "", _emit_str_props(req_item_wcid, ri_str),
            "", _emit_did_props(req_item_wcid, ri_did),"",
        ]
        files.append({
            "filename": fname_ri,
            "sql":      "\n".join(ri_secs),
            "type":     "item", "wcid": req_item_wcid,
        })

        # Drop creature for the item
        if req_creature_wcid and params.get("req_item_creature","").strip():
            from aceforge.json_to_sql import CREATURE_TYPE
            dc_name  = params["req_item_creature"].strip()
            dc_type  = params.get("req_item_ctype","Human")
            dc_level = _si(params.get("req_item_level",""), 150)
            dc_lt_raw= params.get("req_item_loot","T4 (3101)")
            dc_lt_m  = __import__("re").search(r"\((\d+)\)", str(dc_lt_raw))
            dc_loot  = int(dc_lt_m.group(1)) if dc_lt_m else 3101
            dc_slug  = _slug(dc_name)
            dc_tint  = CREATURE_TYPE.get(dc_type.lower().replace(" ","_"), 1)

            dc_data = {
                "name": dc_name, "class_name": dc_slug,
                "level": dc_level, "xp": dc_level * 3000,
                "health": dc_level * 8, "stamina": dc_level * 6,
                "mana": dc_level * 2, "armor": max(40, dc_level // 2),
                "creature_type_int": dc_tint, "creature_type_label": dc_type,
                "attack_skill_id": 44, "attack_skill_name": "HeavyWeapons",
                "attack_skill": dc_level + 50, "melee_defense": dc_level + 30,
                "loot_tier": dc_loot,
                "create_list": [{"wcid": req_item_wcid, "qty": 1,
                                 "destination":"corpse_drop","comment": ri_name}],
            }
            fname_dc = f"{req_creature_wcid}_{dc_slug}.sql"
            files.append({
                "filename": fname_dc,
                "sql":      _creature_sql(req_creature_wcid, dc_data, fname_dc),
                "type":     "creature", "wcid": req_creature_wcid,
            })
            fname_dg = f"{req_gen_wcid}_{dc_slug}_generator.sql"
            files.append({
                "filename": fname_dg,
                "sql":      _generator_sql(req_gen_wcid, req_creature_wcid,
                                           dc_slug, fname_dg, 5, 300.0),
                "type":     "generator", "wcid": req_gen_wcid,
            })

    # ── Reward Item Files (generated items only) ────────────────────────────
    for r in reward_items:
        if r.get("is_existing") or not r.get("wcid"):
            continue
        ri_slug = _slug(r["name"])
        ri_int  = [(1,256,"ItemType"),(5,10,"EncumbranceVal"),
                   (8,5,"Mass"),(19,0,"Value"),(93,1044,"PhysicsState")]
        ri_str  = [(1,r["name"],"Name"),(15,r.get("desc",r["name"]),"ShortDesc")]
        ri_did  = [(1,0x02000155,"Setup"),(3,0x20000014,"SoundTable"),
                   (8,0x06001310,"Icon"),(22,0x3400002B,"PhysicsEffectTable")]
        fname_ri = f"{r['wcid']}_{ri_slug}.sql"
        ri_secs  = [
            f"/* ===== FILE: {fname_ri} ===== */","",
            _emit_header(r["wcid"], r["name"], 6),
            "", _emit_int_props(r["wcid"], ri_int),
            "", _emit_str_props(r["wcid"], ri_str),
            "", _emit_did_props(r["wcid"], ri_did),"",
        ]
        files.append({
            "filename": fname_ri,
            "sql":      "\n".join(ri_secs),
            "type":     "item", "wcid": r["wcid"],
        })

    # ── NPC Quest Giver — direct SQL emotes ─────────────────────────────────
    fname_npc = f"{npc_wcid}_{npc_slug}.sql"
    npc_base  = _npc_base_sql(npc_wcid, npc_name, npc_slug, fname_npc)

    ACT_COLS = ("`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`,"
                " `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,"
                " `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`,"
                " `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`,"
                " `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`,"
                " `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`,"
                " `origin_X`, `origin_Y`, `origin_Z`,"
                " `angles_W`, `angles_X`, `angles_Y`, `angles_Z`")

    _EMO_COLS = ("`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`,"
                 " `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`")

    def _emo(cat_id, cat_name, quest=None):
        q = f"'{quest}'" if quest else "NULL"
        return (f"INSERT INTO `weenie_properties_emote` ({_EMO_COLS})\n"
                f"VALUES ({npc_wcid}, {cat_id} /* {cat_name} */, 1, NULL, NULL, NULL,"
                f" {q}, NULL, NULL, NULL);\n\nSET @parent_id = LAST_INSERT_ID();\n")

    def _act(order, type_id, type_name, *,
             message=None, min_val=None, max_val=None,
             wcid=None, stack=None, amount_64=None, hero_xp_64=None,
             percent=None, min_64=None, max_64=None,
             is_first=False, is_last=False):
        pfx = "VALUES" if is_first else "     ,"
        sfx = ";" if is_last else ""
        msg  = f"'{message}'" if message is not None else "NULL"
        mn   = str(min_val)   if min_val   is not None else "NULL"
        mx   = str(max_val)   if max_val   is not None else "NULL"
        wc   = str(wcid)      if wcid      is not None else "NULL"
        sk   = str(stack)     if stack     is not None else "NULL"
        a64  = str(amount_64) if amount_64 is not None else "NULL"
        hxp  = str(hero_xp_64) if hero_xp_64 is not None else "NULL"
        pct  = str(percent)   if percent   is not None else "NULL"
        m64  = str(min_64)    if min_64    is not None else "NULL"
        mx64 = str(max_64)    if max_64    is not None else "NULL"
        return (f"{pfx} (@parent_id, {order}, {type_id} /* {type_name} */, 0, 1, NULL,"
                f" {msg}, NULL, {mn}, {mx}, {m64}, {mx64}, NULL, NULL, NULL, NULL,"
                f" NULL, {a64}, {hxp}, {pct},"
                f" NULL, NULL, NULL, NULL, NULL, NULL,"
                f" NULL, {wc}, {sk},"
                f" NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL){sfx}")

    # Build reward rows (shared by Grant block across all req types)
    XP_TYPE = xp_type; XP_PCT = xp_pct
    XP_IDS  = {"AwardXP":2,"AwardNoShareXP":62,"AwardLevelProportionalXP":49}
    xp_id   = XP_IDS.get(XP_TYPE, 2)

    already_msg = f"You are already flagged for {unlock_desc}."
    granted_msg = f"You are now flagged for {unlock_desc}. The way is open to you."
    refuse_msg  = params.get("npc_description","").strip() or "Earn the right first. Then we will speak."

    # Grant block rows: erase req (if any) + stamp done + rewards + tell
    def _grant_rows(start_o, erase_req_flag=None, take_item_wcid=None, take_item_qty=1):
        rows = []; o = start_o
        if take_item_wcid:
            rows.append(_act(o, 74, "TakeItems", wcid=take_item_wcid, stack=take_item_qty,
                             is_first=(o==start_o))); o+=1
        if erase_req_flag:
            rows.append(_act(o, 31, "EraseQuest", message=erase_req_flag,
                             is_first=(o==start_o))); o+=1
        rows.append(_act(o, 22, "StampQuest", message=done_flag,
                         is_first=(o==start_o))); o+=1
        # XP
        if reward_xp or XP_TYPE=="AwardLevelProportionalXP":
            if XP_TYPE=="AwardLevelProportionalXP":
                rows.append(_act(o, xp_id, "AwardLevelProportionalXP",
                                 min_64=0, max_64=0, percent=XP_PCT)); o+=1
            else:
                rows.append(_act(o, xp_id, XP_TYPE, amount_64=reward_xp)); o+=1
        if reward_lum:
            rows.append(_act(o, 113, "AwardLuminance", hero_xp_64=reward_lum)); o+=1
        if reward_pyre:
            rows.append(_act(o, 3, "Give", wcid=273, stack=reward_pyre)); o+=1
        for _fr in reward_items:
            if _fr.get("wcid"):
                rows.append(_act(o, 3, "Give", wcid=_fr["wcid"], stack=_fr["qty"])); o+=1
        rows.append(_act(o, 10, "Tell", message=granted_msg, is_last=True))
        return rows

    parts = []

    # ── Block 1: Use → InqQuest(done_flag) ───────────────────────────────────
    parts.append(_emo(7, "Use"))
    parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                 + _act(0, 21, "InqQuest", message=done_flag, is_first=True, is_last=True))

    # ── Block 2: QS(done_flag) → Tell(already flagged) ───────────────────────
    parts.append(_emo(12, "QuestSuccess", quest=done_flag))
    parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                 + _act(0, 10, "Tell", message=already_msg, is_first=True, is_last=True))

    if req_type == "kill_task":
        c_name  = params.get("req_creature", "enemies")
        k_count = _si(params.get("req_kill_count",""), 25)
        task_msg  = f"To gain {unlock_desc}, you must slay {k_count} {c_name}s."
        task_msg2 = "Return when it is done."

        # Block 3: QF(done_flag) → InqQuestSolves(req_flag, 1, MAX)
        parts.append(_emo(13, "QuestFailure", quest=done_flag))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + _act(0, 30, "InqQuestSolves", message=req_flag,
                            min_val=1, max_val=2147483647, is_first=True, is_last=True))

        # Block 4: QS(req_flag) → Grant
        grant_rows = _grant_rows(0, erase_req_flag=req_flag)
        parts.append(_emo(12, "QuestSuccess", quest=req_flag))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + "\n".join(grant_rows))

        # Block 5: QF(req_flag) → Tell(task instructions x2)
        parts.append(_emo(13, "QuestFailure", quest=req_flag))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + _act(0, 10, "Tell", message=task_msg, is_first=True)
                     + "\n"
                     + _act(1, 10, "Tell", message=task_msg2, is_last=True))

    elif req_type == "item_turnin":
        ri_name  = params.get("req_item_name", "the required item")
        ri_count = _si(params.get("req_item_count",""), 1)
        task_msg = f"Bring me {ri_count} {ri_name} to earn {unlock_desc}."
        owns_key = f"OwnsItem-{req_item_wcid}"

        # Block 3: QF(done_flag) → InqOwnsItems
        parts.append(_emo(13, "QuestFailure", quest=done_flag))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + _act(0, 76, "InqOwnsItems", message=owns_key,
                            wcid=req_item_wcid, stack=ri_count, is_first=True, is_last=True))

        # Block 4: TS(OwnsItem) → TakeItems + Grant
        grant_rows = _grant_rows(0, take_item_wcid=req_item_wcid, take_item_qty=ri_count)
        parts.append(_emo(22, "TestSuccess", quest=owns_key))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + "\n".join(grant_rows))

        # Block 5: TF(OwnsItem) → Tell(need item)
        parts.append(_emo(23, "TestFailure"))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + _act(0, 10, "Tell", message=task_msg, is_first=True, is_last=True))

    else:
        # No requirement — grant immediately on QF(done_flag)
        grant_rows = _grant_rows(0)
        parts.append(_emo(13, "QuestFailure", quest=done_flag))
        parts.append(f"INSERT INTO `weenie_properties_emote_action` ({ACT_COLS})\n"
                     + "\n".join(grant_rows))

    emote_sql = "\n\n".join(parts)

    files.append({
        "filename": fname_npc,
        "sql":      npc_base + "\n" + emote_sql + "\n",
        "type":     "npc", "wcid": npc_wcid,
    })

    return files

# ── Registry ──────────────────────────────────────────────────────────────────

QUEST_TEMPLATES = {
    "kill_task": {
        "label":       "Kill Task",
        "description": "NPC sends player to kill X of a creature type. Optional named boss.",
        "generator":   generate_kill_task,
        "fields": [
            {"id":"quest_prefix",    "label":"Quest Prefix",       "type":"text",   "placeholder":"e.g. UlgrimTumerok",     "required":True,  "help":"Unique short prefix — used for quest flag names. No spaces."},
            {"id":"npc_name",        "label":"NPC Name",           "type":"text",   "placeholder":"e.g. Ulgrim the Unpleasant","required":True, "help":"Display name of the quest giver NPC."},
            {"id":"npc_description", "label":"NPC Personality",    "type":"text",   "placeholder":"e.g. Gruff warrior, dismissive","required":False,"help":"Used by AI to write dialogue in the right voice."},
            {"id":"creature_name",   "label":"Creature Name",      "type":"text",   "placeholder":"e.g. Tumerok Berserker",  "required":True,  "help":"Name of the creature to kill."},
            {"id":"creature_type",   "label":"Creature Type",      "type":"select", "options":["Human","Tumerok","Drudge","Mosswart","Shadow","Undead","Olthoi","Virindi","Lugian","Golem","Tusker","Banderling","Zefir","Grievver","Mukkir"], "required":True},
            {"id":"creature_level",  "label":"Creature Level",     "type":"number", "placeholder":"150",                    "required":True,  "help":"Determines stats, XP, and armor values."},
            {"id":"kill_count",      "label":"Kill Count",         "type":"number", "placeholder":"50",                     "required":True,  "help":"How many the player must kill."},
            {"id":"loot_tier",       "label":"Loot Tier",          "type":"select", "options":["None (0)","T4 (3101)","T5 (3102)","T6 (3103)","T7 (3104)","T8 (3105)"], "required":True},
            {"id":"spawn_count",     "label":"Spawn Count",        "type":"number", "placeholder":"5",                     "required":False, "help":"How many spawn at once from the generator."},
            {"id":"spawn_delay",     "label":"Respawn Delay (sec)","type":"number", "placeholder":"300",                   "required":False},
            {"id":"reward_xp",       "label":"Reward XP",          "type":"number", "placeholder":"5000000",               "required":True},
            {"id":"reward_pyreals",  "label":"Reward Pyreals",     "type":"number", "placeholder":"10000",                 "required":False},
            {"id":"repeat_hours",    "label":"Repeat Timer (hrs)", "type":"number", "placeholder":"20",                    "required":False, "help":"0 = one-time quest."},
            {"id":"boss_name",       "label":"Boss Name (optional)","type":"text",  "placeholder":"e.g. Grak-Nosh the Chieftain","required":False,"help":"Leave blank for a simple kill task without a boss."},
            {"id":"boss_level",      "label":"Boss Level",         "type":"number", "placeholder":"auto",                  "required":False, "help":"Defaults to 1.5× creature level."},
        ],
    },
    "item_turnin": {
        "label":       "Item Turn-In",
        "description": "Player collects an item and turns it in to an NPC for a reward.",
        "generator":   generate_item_turnin,
        "fields": [
            {"id":"quest_prefix",          "label":"Quest Prefix",           "type":"text",   "placeholder":"e.g. UlgrimRelic",      "required":True,  "help":"Unique short prefix for quest flags. No spaces."},
            {"id":"npc_name",              "label":"NPC Name",               "type":"text",   "placeholder":"e.g. Ulgrim the Unpleasant","required":True},
            {"id":"npc_description",       "label":"NPC Personality",        "type":"text",   "placeholder":"e.g. Gruff, impatient",  "required":False, "help":"Used by AI to write dialogue."},
            {"id":"item_name",             "label":"Turn-In Item Name",      "type":"text",   "placeholder":"e.g. Intact Brood Queen Carapace","required":True, "help":"Name of the item the player must collect."},
            {"id":"item_description",      "label":"Item Description",       "type":"text",   "placeholder":"e.g. A carapace from the Brood Queen.","required":False},
            {"id":"multi_item_count",      "label":"Quantity Required",      "type":"number", "placeholder":"1",                     "required":False, "help":"How many copies of the item to turn in."},
            {"id":"item_drop_creature",    "label":"Drop Creature (optional)","type":"text",  "placeholder":"e.g. Brood Queen",       "required":False, "help":"Leave blank if item is found in a chest or already exists."},
            {"id":"item_drop_creature_type","label":"Drop Creature Type",    "type":"select", "options":["Human","Tumerok","Drudge","Mosswart","Shadow","Undead","Olthoi","Virindi","Lugian","Golem","Tusker","Banderling","Zefir","Grievver","Mukkir"], "required":False},
            {"id":"item_drop_level",       "label":"Drop Creature Level",    "type":"number", "placeholder":"150",                   "required":False},
            {"id":"item_drop_loot_tier",   "label":"Drop Creature Loot Tier","type":"select", "options":["None (0)","T4 (3101)","T5 (3102)","T6 (3103)","T7 (3104)","T8 (3105)"], "required":False},
            {"id":"spawn_count",           "label":"Spawn Count",            "type":"number", "placeholder":"5",                     "required":False},
            {"id":"spawn_delay",           "label":"Respawn Delay (sec)",    "type":"number", "placeholder":"300",                   "required":False},
            {"id":"reward_xp",             "label":"Reward XP",              "type":"number", "placeholder":"2000000",               "required":True},
            {"id":"reward_pyreals",        "label":"Reward Pyreals",         "type":"number", "placeholder":"5000",                  "required":False},
            {"id":"repeat_hours",          "label":"Repeat Timer (hrs)",     "type":"number", "placeholder":"20",                    "required":False, "help":"0 = one-time quest."},
            {"id":"reward_item_name",      "label":"Reward Item (optional)", "type":"text",   "placeholder":"e.g. Brood Queen Trophy","required":False, "help":"Leave blank for XP/pyreal reward only."},
            {"id":"reward_item_description","label":"Reward Item Description","type":"text",  "placeholder":"e.g. A trophy of your victory.","required":False},
        ],
    },
    "delivery": {
        "label":       "Delivery Quest",
        "description": "Carry an item from NPC A to NPC B. Optionally chains through C and D.",
        "generator":   generate_delivery,
        "fields": [
            {"id":"quest_prefix",        "label":"Quest Prefix",              "type":"text",   "placeholder":"e.g. MerchantRun",      "required":True,  "help":"Unique short prefix. No spaces."},
            {"id":"item_name",           "label":"Delivery Item Name",        "type":"text",   "placeholder":"e.g. Trade Proposal",   "required":True},
            {"id":"item_description",    "label":"Item Description",          "type":"text",   "placeholder":"e.g. A sealed trade proposal document.","required":False},
            {"id":"item_count",          "label":"Quantity Required",         "type":"number", "placeholder":"1",                     "required":False, "help":"How many copies of the item to deliver."},
            {"id":"npc_a_name",          "label":"NPC A — Quest Giver",       "type":"text",   "placeholder":"e.g. Merchant Anton",   "required":True,  "help":"Gives the item and starts the delivery."},
            {"id":"npc_a_description",   "label":"NPC A — Personality",       "type":"text",   "placeholder":"e.g. Anxious merchant", "required":False},
            {"id":"npc_b_name",          "label":"NPC B — First Recipient",   "type":"text",   "placeholder":"e.g. Guildmaster Renald","required":True,  "help":"First NPC to receive the delivery."},
            {"id":"npc_b_description",   "label":"NPC B — Personality",       "type":"text",   "placeholder":"e.g. Stern guildmaster","required":False},
            {"id":"npc_c_name",          "label":"NPC C — Second Recipient",  "type":"text",   "placeholder":"e.g. Elder Gonjoku",    "required":False, "help":"Leave blank to end chain at NPC B."},
            {"id":"npc_c_description",   "label":"NPC C — Personality",       "type":"text",   "placeholder":"",                      "required":False},
            {"id":"npc_d_name",          "label":"NPC D — Third Recipient",   "type":"text",   "placeholder":"",                      "required":False, "help":"Leave blank to end chain at NPC C."},
            {"id":"npc_b_name",          "label":"NPC B — Item Recipient",    "type":"text",   "placeholder":"e.g. Guildmaster Renald","required":True,  "help":"NPC who receives the delivery."},
            {"id":"npc_b_description",   "label":"NPC B — Personality",       "type":"text",   "placeholder":"e.g. Stern guildmaster","required":False},
            {"id":"reward_xp",           "label":"Final Reward XP",           "type":"number", "placeholder":"2000000",               "required":True},
            {"id":"reward_pyreals",      "label":"Final Reward Pyreals",      "type":"number", "placeholder":"5000",                  "required":False},
            {"id":"repeat_hours",        "label":"Repeat Timer (hours)",      "type":"number", "placeholder":"20",                    "required":False, "help":"0 = one-time."},
        ],
    },
}


def run_template(template_id: str, params: dict, config) -> list[dict]:
    """Run a quest template generator and return the file list."""
    tmpl = QUEST_TEMPLATES.get(template_id)
    if not tmpl:
        raise ValueError(f"Unknown template: {template_id}")
    return tmpl["generator"](params, config)


def get_all_templates() -> list[dict]:
    """Return summary info for all registered templates."""
    return [
        {"id": tid, "label": t["label"], "description": t.get("description", "")}
        for tid, t in QUEST_TEMPLATES.items()
    ]


def get_template_fields(template_id: str) -> list[dict]:
    """Return the field definitions for a specific template."""
    tmpl = QUEST_TEMPLATES.get(template_id)
    if not tmpl:
        return []
    return tmpl.get("fields", [])
