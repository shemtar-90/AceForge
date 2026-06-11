"""
json_to_sql.py — ACEForge JSON → SQL converter

Converts the structured JSON output from AI generation into correct
ACE-World-Database SQL. The AI never touches SQL structure — it only
provides semantic content. This module handles all table names, column
orders, NULL padding, formatting, and enum lookups.

Supported top-level JSON keys per content type:
  All:        wcid, class_name, weenie_type, name, short_desc, long_desc, icon, setup,
              motion_table, sound_table, physics_effect_table, palette_base, physics_state
  Creature:   level, xp, creature_type, health, stamina, mana, strength, endurance,
              quickness, coordination, focus, self, melee_defense, attack_skill,
              attack_skill_name, scale, treasure_type, loot_tier, stuck, attackable,
              treasure_corpse, visual_range, heartbeat, health_rate, armor, resist_*,
              body_parts, create_list, kill_quest
  NPC:        (creature fields minus combat + vendor_type, sell_items)
  Item:       item_type, encumbrance, mass, value, useable, max_stack, inscribable
  Quest:      quest_name, min_delta, max_solves, message
  Generator:  target_wcid, delay, init_create, max_create, when_create, where_create
"""

from __future__ import annotations
import json
import re
from datetime import datetime
from typing import Any

TIMESTAMP = "2025-01-01 00:00:00"

# ── Enum lookup tables ────────────────────────────────────────────────────────

WEENIE_TYPE = {
    "creature": 10, "npc": 10, "vendor": 10, "boss": 10,
    "item": 6, "generic": 6,
    "food": 7, "gem": 9, "key": 10,
    "melee_weapon": 16, "missile_weapon": 17, "caster": 18,
    "clothing": 19, "armor": 20, "scroll": 21,
    "stackable": 22, "container": 2,
    "generator": 35, "portal": 7,
    "quest_item": 6,
}

CREATURE_TYPE = {
    "human": 1, "lugian": 2, "tumerok": 3, "mosswart": 4,
    "drudge": 5, "shadow": 6, "undead": 7, "skeleton": 7, "zombie": 7,
    "olthoi": 8, "cow": 9, "golem": 10, "virindi": 11,
    "monouga": 12, "tusker": 13, "banderling": 14, "zefir": 15,
    "phyntos_wasp": 16, "grievver": 17, "gurog": 18, "moarsman": 19,
    "mite": 20, "mukkir": 21, "carenzi": 22, "doll": 23,
    "wisp": 24, "gotrok": 25, "slith": 26, "reed_shark": 27,
    "rat": 28, "remoran": 29, "shreth": 30, "silifi": 31,
    "fennk": 32, "reedshark": 27,
}

DAMAGE_TYPE = {
    "slash": 1, "pierce": 2, "bludgeon": 4, "cold": 8,
    "fire": 16, "acid": 32, "electric": 64, "nether": 128,
    "health": 256, "stamina": 512, "mana": 1024,
}

SKILL_ID = {
    "alchemy": 1, "arcane_lore": 2, "armor_tinkering": 3, "assess_creature": 4,
    "assess_person": 5, "cooking": 6, "creature_enchantment": 7, "fletching": 8,
    "healing": 9, "item_enchantment": 10, "item_tinkering": 11, "jump": 12,
    "leadership": 13, "life_magic": 14, "loyalty": 15, "mana_conversion": 16,
    "melee_defense": 6, "missile_defense": 17, "missile_weapons": 18,
    "salvaging": 19, "shield": 20, "spell_research": 21, "summoning": 22,
    "swim": 23, "thrown_weapons": 24, "two_handed_combat": 25, "unarmed_combat": 26,
    "void_magic": 27, "war_magic": 28, "weapon_tinkering": 29,
    "finesse_weapons": 30, "heavy_weapons": 44, "light_weapons": 45, "magic_defense": 46,
}

ITEM_TYPE = {
    "none": 0, "melee_weapon": 1, "armor": 2, "clothing": 4,
    "jewelry": 8, "creature": 16, "container": 32, "food": 64,
    "money": 128, "misc": 256, "missile_weapon": 512, "caster": 1024,
    "mana_stone": 2048, "craft_tool": 4096, "key": 8192,
    "writable": 8192, "book": 8192,
    "gem": 16384, "spell_component": 32768, "service": 65536,
}

PHYSICS_STATE = {
    "default":   1044,   # Ethereal, IgnoreCollisions, Gravity (most items)
    "creature":  3080,   # Ethereal, Gravity, Missile
    "npc":       3076,   # Ethereal, Gravity
    "generator": 4,      # Ethereal
}

# DID defaults by content type
DID_DEFAULTS = {
    "creature": {
        "setup":               0x020002A5,
        "motion_table":        0x09000010,
        "sound_table":         0x20000009,
        "icon":                0x0600108A,
        "physics_effect_table":0x34000026,
    },
    "npc": {
        "setup":               0x0200010D,
        "motion_table":        0x09000001,
        "sound_table":         0x20000001,
        "icon":                0x06001F2E,
        "physics_effect_table":0x34000004,
    },
    "item": {
        "setup":               0x02000155,
        "sound_table":         0x20000014,
        "icon":                0x06001310,
        "physics_effect_table":0x3400002B,
    },
    "generator": {
        "setup":               0x02000001,
        "motion_table":        0x09000001,
        "sound_table":         0x20000001,
        "icon":                0x06001F2E,
        "physics_effect_table":0x34000004,
    },
}

BODY_PART_KEYS = [
    "head", "chest", "abdomen", "upper_arm", "lower_arm",
    "hand", "upper_leg", "lower_leg", "foot"
]

# ── Formatting helpers ────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    """Convert display name to ACE class_name slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s_]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s[:64]

def _int_val(d: dict, key: str, default: int = 0) -> int:
    return int(d.get(key, default) or default)

def _float_val(d: dict, key: str, default: float = 0.0) -> float:
    return float(d.get(key, default) or default)

def _str_val(d: dict, key: str, default: str = "") -> str:
    return str(d.get(key, default) or default)

def _lookup(table: dict, key: Any, default: int = 0) -> int:
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        return table.get(key.lower().replace(" ", "_"), default)
    return default

def _fmt_int(v: int, width: int = 9) -> str:
    return str(v).rjust(width)

def _fmt_float(v: float) -> str:
    if v == int(v):
        return str(int(v)).rjust(7)
    return f"{v:>7g}"

def _fmt_hex(v: int) -> str:
    return f"0x{v:08X}"

def _escape_sql(s: str) -> str:
    return s.replace("'", "''")


# ── Per-table emitters ────────────────────────────────────────────────────────

def _emit_header(wcid: int, class_name: str, weenie_type: int) -> str:
    ts = TIMESTAMP
    lines = [
        f"DELETE FROM `weenie` WHERE `class_Id` = {wcid};",
        "",
        f"INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)",
        f"VALUES ({wcid}, '{class_name}', {weenie_type}, '{ts}');",
    ]
    return "\n".join(lines)


def _emit_int_props(wcid: int, rows: list[tuple[int, int, str]]) -> str:
    """rows = [(type_id, value, comment), ...]"""
    if not rows:
        return ""
    lines = [f"INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        comment = f" /* {c} */" if c else ""
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {_fmt_int(v)}){comment}{end}")
    return "\n".join(lines)


def _emit_bool_props(wcid: int, rows: list[tuple[int, bool, str]]) -> str:
    if not rows:
        return ""
    lines = [f"INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        comment = f" /* {c} */" if c else ""
        end = ";" if i == len(rows) - 1 else ""
        bv = "True " if v else "False"
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {bv}){comment}{end}")
    return "\n".join(lines)


def _emit_float_props(wcid: int, rows: list[tuple[int, float, str]]) -> str:
    if not rows:
        return ""
    lines = [f"INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        comment = f" /* {c} */" if c else ""
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {_fmt_float(v)}){comment}{end}")
    return "\n".join(lines)


def _emit_str_props(wcid: int, rows: list[tuple[int, str, str]]) -> str:
    if not rows:
        return ""
    lines = [f"INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        comment = f" /* {c} */" if c else ""
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, '{_escape_sql(v)}'){comment}{end}")
    return "\n".join(lines)


def _emit_did_props(wcid: int, rows: list[tuple[int, int, str]]) -> str:
    if not rows:
        return ""
    lines = [f"INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        comment = f" /* {c} */" if c else ""
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {_fmt_hex(v)}){comment}{end}")
    return "\n".join(lines)


def _emit_attributes(wcid: int, attrs: dict) -> str:
    ORDER = [
        (1, "strength", "Strength"),
        (2, "endurance", "Endurance"),
        (3, "quickness", "Quickness"),
        (4, "coordination", "Coordination"),
        (5, "focus", "Focus"),
        (6, "self", "Self"),
    ]
    rows = [(tid, _int_val(attrs, key, 100), label) for tid, key, label in ORDER]
    if not any(r[1] for r in rows):
        return ""
    lines = ["INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {_fmt_int(v, 4)}, 0, 0) /* {c} */{end}")
    return "\n".join(lines)


def _emit_vitals(wcid: int, health: int, stamina: int, mana: int) -> str:
    rows = [(1, health, "MaxHealth"), (3, stamina, "MaxStamina"), (5, mana, "MaxMana")]
    lines = ["INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)"]
    for i, (t, v, c) in enumerate(rows):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, {_fmt_int(v, 5)}, 0, 0, {_fmt_int(v, 5)}) /* {c} */{end}")
    return "\n".join(lines)


def _emit_skills(wcid: int, skill_rows: list[tuple[int, int, str]]) -> str:
    """skill_rows = [(skill_id, init_level, comment), ...]  s_a_c=2 (Trained)"""
    if not skill_rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)"]
    for i, (t, v, c) in enumerate(skill_rows):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(skill_rows) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {str(t).rjust(3)}, 0, 2, 0, {_fmt_int(v, 4)}, 0, 0) /* {c} */{end}")
    return "\n".join(lines)


def _emit_body_parts(wcid: int, armor: int = 80, damage_type: int = 4) -> str:
    parts = [
        (0, "Head"), (1, "Chest"), (2, "Abdomen"),
        (3, "UpperArm"), (4, "LowerArm"), (5, "Hand"),
        (6, "UpperLeg"), (7, "LowerLeg"), (8, "Foot"),
    ]
    a = armor
    cols = "(`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)"
    lines = [f"INSERT INTO `weenie_properties_body_part` {cols}"]
    for i, (key, label) in enumerate(parts):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(parts) - 1 else ""
        lines.append(
            f"{prefix} ({wcid}, {key}, {damage_type}, 0, 0, {a}, {a}, {a}, {a}, {a}, {a}, {a}, {a}, 0, "
            f"1, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0) /* {label} */{end}"
        )
    return "\n".join(lines)


def _emit_create_list(wcid: int, items: list[dict]) -> str:
    """items = [{"wcid": int, "qty": int, "destination": int}]"""
    if not items:
        return ""
    lines = ["INSERT INTO `weenie_properties_create_list` (`object_Id`, `destination`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)"]
    dest_map = {"contain": 1, "corpse_drop": 2, "shop": 3, "treasure": 4, "wield": 6}
    for i, item in enumerate(items):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(items) - 1 else ""
        dest_raw = item.get("destination", "corpse_drop")
        dest = dest_raw if isinstance(dest_raw, int) else dest_map.get(str(dest_raw).lower(), 2)
        qty = _int_val(item, "qty", 1)
        iwcid = _int_val(item, "wcid", 0)
        comment = item.get("comment", "")
        cmt = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {dest}, {iwcid}, {qty}, 0, 0, False){cmt}{end}")
    return "\n".join(lines)


def _emit_generator(wcid: int, g: dict) -> str:
    target = _int_val(g, "target_wcid", 0)
    delay = _float_val(g, "delay", 300.0)
    init = _int_val(g, "init_create", 1)
    maxc = _int_val(g, "max_create", 1)
    when = _int_val(g, "when_create", 1)
    where = _int_val(g, "where_create", 1)
    cols = "(`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)"
    return (
        f"INSERT INTO `weenie_properties_generator` {cols}\n"
        f"VALUES ({wcid}, 1.0, {target}, {delay}, {init}, {maxc}, {when}, {where}, -1, 0, 0.0, 0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0);"
    )


def _emit_position(wcid: int, pos: dict) -> str:
    cell = pos.get("cell", 0)
    if isinstance(cell, str) and cell.startswith("0x"):
        cell = int(cell, 16)
    cell = int(cell)
    ox = _float_val(pos, "x", 0.0)
    oy = _float_val(pos, "y", 0.0)
    oz = _float_val(pos, "z", 0.0)
    aw = _float_val(pos, "angles_w", 1.0)
    ax = _float_val(pos, "angles_x", 0.0)
    ay = _float_val(pos, "angles_y", 0.0)
    az = _float_val(pos, "angles_z", 0.0)
    return (
        f"INSERT INTO `weenie_properties_position` (`object_Id`, `position_Type`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)\n"
        f"VALUES ({wcid}, 1, {_fmt_hex(cell)}, {ox}, {oy}, {oz}, {aw}, {ax}, {ay}, {az});"
    )


def _emit_quest_entry(q: dict) -> str:
    name = _escape_sql(_str_val(q, "quest_name", "MyQuestFlag"))
    delta = _int_val(q, "min_delta", 86400)
    solves = _int_val(q, "max_solves", 1)
    msg = _escape_sql(_str_val(q, "message", ""))
    return (
        f"DELETE FROM `quest` WHERE `name` = '{name}';\n\n"
        f"INSERT INTO `quest` (`name`, `min_Delta`, `max_Solves`, `message`, `last_Modified`)\n"
        f"VALUES ('{name}', {delta}, {solves}, '{msg}', '{TIMESTAMP}');"
    )


# ── Main converter ────────────────────────────────────────────────────────────

def json_to_sql(data: dict | str, filename: str = "") -> str:
    """
    Convert a JSON dict (or JSON string) describing a weenie into complete ACE SQL.
    Returns the full SQL string ready to save.
    """
    if isinstance(data, str):
        data = json.loads(data)

    ctype = data.get("content_type", data.get("type", "creature")).lower()
    wcid = int(data.get("wcid", 800000))
    name = _str_val(data, "name", "Unknown")
    class_name = _str_val(data, "class_name", "") or _slug(name)

    # Resolve weenie_type integer
    wtype_raw = data.get("weenie_type", ctype)
    if isinstance(wtype_raw, int):
        weenie_type = wtype_raw
    else:
        weenie_type = WEENIE_TYPES_INT.get(str(wtype_raw).lower(), WEENIE_TYPE.get(ctype, 10))

    sections = []
    file_comment = filename or f"{wcid}_{_slug(name)}.sql"
    sections.append(f"/* ===== FILE: {file_comment} ===== */")
    sections.append("")
    sections.append(_emit_header(wcid, class_name, weenie_type))

    # ── Quest table (standalone quest flags) ──────────────────────────────────
    if ctype == "quest":
        sections.append("")
        sections.append(_emit_quest_entry(data))
        return "\n".join(sections)

    # ── Generator (standalone spawner weenie) ─────────────────────────────────
    if ctype == "generator":
        did_defaults = DID_DEFAULTS.get("generator", {})
        did_rows = _build_did_rows(data, did_defaults)
        if did_rows:
            sections.append("")
            sections.append(_emit_did_props(wcid, did_rows))
        gen_data = data.get("generator", data)
        sections.append("")
        sections.append(_emit_generator(wcid, gen_data))
        return "\n".join(sections)

    # ── INT properties ────────────────────────────────────────────────────────
    int_rows = []

    if ctype in ("creature", "npc", "vendor", "boss"):
        # Creature-type int properties
        creature_type = _lookup(CREATURE_TYPE, data.get("creature_type", "human"), 1)
        int_rows.append((1,  16,  "ItemType - Creature"))
        int_rows.append((2,  creature_type, f"CreatureType - {data.get('creature_type', 'Human')}"))
        level = _int_val(data, "level", 100)
        int_rows.append((25, level, "Level"))
        int_rows.append((93, _int_val(data, "physics_state",
                         PHYSICS_STATE.get("npc" if ctype == "npc" else "creature", 3080)), "PhysicsState"))
        int_rows.append((133, 4, "ShowableOnRadar"))
        xp = _int_val(data, "xp", level * 1000)
        int_rows.append((146, xp, "XpOverride"))
        if data.get("kill_quest"):
            pass  # handled in string props
        loot = data.get("loot_tier", data.get("treasure_type", 0))
        # loot handled in DID

    elif ctype in ("item", "quest_item"):
        item_type = _lookup(ITEM_TYPE, data.get("item_type", "misc"), 256)
        int_rows.append((1,  item_type, f"ItemType"))
        int_rows.append((5,  _int_val(data, "encumbrance", 10), "EncumbranceVal"))
        int_rows.append((8,  _int_val(data, "mass", 5), "Mass"))
        int_rows.append((9,  0, "Locations"))
        int_rows.append((16, _int_val(data, "useable", 8), "ItemUseable"))
        int_rows.append((19, _int_val(data, "value", 100), "Value"))
        int_rows.append((93, _int_val(data, "physics_state",
                         PHYSICS_STATE.get("default", 1044)), "PhysicsState"))
        if data.get("max_stack"):
            int_rows.append((25, _int_val(data, "max_stack", 1), "MaxStackSize"))

    # Append any extra int props from JSON
    for ep in data.get("extra_int", []):
        int_rows.append((_int_val(ep, "type"), _int_val(ep, "value"), ep.get("comment", "")))

    if int_rows:
        sections.append("")
        sections.append(_emit_int_props(wcid, int_rows))

    # ── BOOL properties ───────────────────────────────────────────────────────
    bool_rows = []
    if ctype in ("creature", "npc", "vendor", "boss"):
        bool_rows.append((1,  True,  "Stuck"))
        attackable = bool(data.get("attackable", ctype != "npc"))
        bool_rows.append((19, attackable, "Attackable"))
        bool_rows.append((120, bool(data.get("treasure_corpse", True)), "TreasureCorpse"))
    elif ctype in ("item", "quest_item"):
        bool_rows.append((22, bool(data.get("inscribable", False)), "Inscribable"))
    for ep in data.get("extra_bool", []):
        bool_rows.append((_int_val(ep, "type"), bool(ep.get("value", False)), ep.get("comment", "")))
    if bool_rows:
        sections.append("")
        sections.append(_emit_bool_props(wcid, bool_rows))

    # ── FLOAT properties ──────────────────────────────────────────────────────
    float_rows = []
    if ctype in ("creature", "npc", "vendor", "boss"):
        float_rows.append((1,  _float_val(data, "heartbeat", 5.0),  "HeartbeatInterval"))
        float_rows.append((3,  _float_val(data, "health_rate", 0.5), "HealthRate"))
        float_rows.append((31, _float_val(data, "visual_range", 20.0), "VisualAwarenessRange"))
        float_rows.append((39, _float_val(data, "scale", 1.0), "DefaultScale"))
        # Armor resists
        for t, key, label in [
            (13, "resist_slash",    "ArmorModVsSlash"),
            (14, "resist_pierce",   "ArmorModVsPierce"),
            (15, "resist_bludgeon", "ArmorModVsBludgeon"),
            (16, "resist_cold",     "ArmorModVsCold"),
            (17, "resist_fire",     "ArmorModVsFire"),
            (18, "resist_acid",     "ArmorModVsAcid"),
            (19, "resist_electric", "ArmorModVsElectric"),
        ]:
            v = _float_val(data, key, 1.0)
            float_rows.append((t, v, label))
    elif ctype in ("item", "quest_item"):
        float_rows.append((54, _float_val(data, "use_radius", 1.0), "UseRadius"))
    for ep in data.get("extra_float", []):
        float_rows.append((_int_val(ep, "type"), _float_val(ep, "value"), ep.get("comment", "")))
    if float_rows:
        sections.append("")
        sections.append(_emit_float_props(wcid, float_rows))

    # ── STRING properties ─────────────────────────────────────────────────────
    str_rows = [(1, name, "Name")]
    short_desc = _str_val(data, "short_desc", "")
    long_desc  = _str_val(data, "long_desc", "")
    if short_desc:
        str_rows.append((15, short_desc, "ShortDesc"))
    if long_desc:
        str_rows.append((16, long_desc, "LongDesc"))
    kill_quest = _str_val(data, "kill_quest", "")
    if kill_quest:
        str_rows.append((45, kill_quest, "KillQuest"))
    for ep in data.get("extra_string", []):
        str_rows.append((_int_val(ep, "type"), _str_val(ep, "value"), ep.get("comment", "")))
    sections.append("")
    sections.append(_emit_str_props(wcid, str_rows))

    # ── DID properties ────────────────────────────────────────────────────────
    did_defaults = DID_DEFAULTS.get(ctype if ctype in DID_DEFAULTS else "item", {})
    did_rows = _build_did_rows(data, did_defaults)
    # Add loot tier for creatures
    if ctype in ("creature", "npc", "vendor", "boss"):
        loot_tier = data.get("loot_tier", data.get("treasure_type"))
        if loot_tier:
            loot_val = int(loot_tier) if str(loot_tier).isdigit() else 3101
            did_rows.append((35, loot_val, "DeathTreasureType"))
    if did_rows:
        sections.append("")
        sections.append(_emit_did_props(wcid, did_rows))

    # ── Attributes + Vitals + Skills (creatures only) ─────────────────────────
    if ctype in ("creature", "npc", "vendor", "boss"):
        attrs = {k: data.get(k, 150) for k in
                 ["strength", "endurance", "quickness", "coordination", "focus", "self"]}
        attr_sql = _emit_attributes(wcid, attrs)
        if attr_sql:
            sections.append("")
            sections.append(attr_sql)

        health  = _int_val(data, "health",  500)
        stamina = _int_val(data, "stamina", 400)
        mana    = _int_val(data, "mana",    300)
        sections.append("")
        sections.append(_emit_vitals(wcid, health, stamina, mana))

        # Skills — melee defense always, plus attack skill if specified
        skill_rows = [(6, _int_val(data, "melee_defense", 180), "MeleeDefense")]
        atk_name = data.get("attack_skill_name", "HeavyWeapons")
        atk_id   = _lookup(SKILL_ID, atk_name, 44)
        atk_val  = _int_val(data, "attack_skill", 200)
        skill_rows.append((atk_id, atk_val, atk_name))
        for ep in data.get("extra_skills", []):
            sid = _lookup(SKILL_ID, ep.get("name", ""), 0)
            if sid:
                skill_rows.append((sid, _int_val(ep, "level", 150), ep.get("name", "")))
        sections.append("")
        sections.append(_emit_skills(wcid, skill_rows))

        # Body parts
        armor = _int_val(data, "armor", 80)
        sections.append("")
        sections.append(_emit_body_parts(wcid, armor))

    # ── Create list ───────────────────────────────────────────────────────────
    create_list = data.get("create_list", [])
    if create_list:
        sections.append("")
        sections.append(_emit_create_list(wcid, create_list))

    # ── Position ──────────────────────────────────────────────────────────────
    position = data.get("position")
    if position:
        sections.append("")
        sections.append(_emit_position(wcid, position))

    # ── Emote block (pass-through — handled by emote_parser) ─────────────────
    emote_yaml = _str_val(data, "emotes", "")
    if emote_yaml.strip():
        sections.append("")
        sections.append(f"-- EMOTE SCRIPT (WCID: {wcid})")
        sections.append(emote_yaml.strip())
        sections.append(f"-- END EMOTE SCRIPT")

    sections.append("")  # trailing newline
    return "\n".join(sections)


def _build_did_rows(data: dict, defaults: dict) -> list[tuple[int, int, str]]:
    DID_FIELD_MAP = {
        "setup":                (1,  "Setup"),
        "motion_table":         (2,  "MotionTable"),
        "sound_table":          (3,  "SoundTable"),
        "palette_base":         (6,  "PaletteBase"),
        "icon":                 (8,  "Icon"),
        "physics_effect_table": (22, "PhysicsEffectTable"),
    }
    rows = []
    seen = set()
    # JSON-specified values first
    for key, (tid, label) in DID_FIELD_MAP.items():
        raw = data.get(key)
        if raw is not None:
            v = int(raw, 16) if isinstance(raw, str) and raw.startswith("0x") else int(raw)
            rows.append((tid, v, label))
            seen.add(tid)
    # Fill defaults for missing
    for key, (tid, label) in DID_FIELD_MAP.items():
        if tid not in seen and key in defaults:
            rows.append((tid, defaults[key], label))
            seen.add(tid)
    rows.sort(key=lambda r: r[0])
    # Extra DID props
    for ep in data.get("extra_did", []):
        t = _int_val(ep, "type")
        raw = ep.get("value", 0)
        v = int(raw, 16) if isinstance(raw, str) and raw.startswith("0x") else int(raw)
        rows.append((t, v, ep.get("comment", "")))
    return rows


WEENIE_TYPES_INT = {
    "creature": 10, "npc": 10, "vendor": 10, "boss": 10,
    "item": 6, "generic": 6, "quest_item": 6,
    "food": 7, "gem": 9,
    "melee_weapon": 16, "missile_weapon": 17, "caster": 18,
    "clothing": 19, "armor": 20, "scroll": 21,
    "stackable": 22, "container": 2,
    "generator": 35,
}


# ── Entry point for processing AI output ─────────────────────────────────────

def extract_and_convert(ai_output: str, filename: str = "") -> str:
    """
    Find a JSON block in AI output, convert it to SQL, and return the result.
    Also handles EMOTE SCRIPT blocks (passed through to emote_parser).
    Returns the full SQL string, or empty string if no JSON found.
    """
    # Try to find ```json ... ``` block first
    m = re.search(r'```json\s*([\s\S]+?)\s*```', ai_output, re.IGNORECASE)
    if not m:
        # Try bare { ... } JSON object
        m = re.search(r'(\{[\s\S]+\})', ai_output)
    if not m:
        return ""

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return ""

    return json_to_sql(data, filename)
