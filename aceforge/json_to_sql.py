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


# ── Formatting helpers ────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    """Convert a display name to a lowercase underscore slug."""
    import re as _re
    return _re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def _fmt_val(v) -> str:
    """Format a Python value for SQL output."""
    if isinstance(v, bool):
        return "True " if v else "False"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, int):
        return str(v)
    # string
    escaped = str(v).replace("'", "''")
    return f"'{escaped}'"


def _emit_header(wcid: int, name: str, weenie_type: int) -> str:
    """Emit DELETE + INSERT INTO weenie header row."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    TYPE_COMMENT = {
        2: "Container", 6: "Generic", 7: "Food", 9: "Gem", 10: "Creature",
        12: "Vendor", 16: "MeleeWeapon", 17: "MissileWeapon", 18: "Caster",
        19: "Clothing", 20: "Armor", 21: "Scroll", 22: "Stackable",
        35: "Generator", 38: "Gem", 51: "Stackable",
    }
    comment = TYPE_COMMENT.get(weenie_type, f"type={weenie_type}")
    # class_name: use slug of name
    class_name = _slug(name)
    return (
        f"DELETE FROM `weenie` WHERE `class_Id` = {wcid};\n\n"
        f"INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)\n"
        f"VALUES ({wcid}, '{name}', {weenie_type}, '{ts}') /* {comment} */;"
    )


def _emit_int_props(wcid: int, rows: list) -> str:
    """rows = [(type_id, value, comment), ...]"""
    if not rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)"]
    for i, row in enumerate(rows):
        tid, val, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        c = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {tid:4d}, {val:10}){c}{end}")
    return "\n".join(lines)


def _emit_bool_props(wcid: int, rows: list) -> str:
    """rows = [(type_id, bool_val, comment), ...]"""
    if not rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)"]
    for i, row in enumerate(rows):
        tid, val, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        v = "True " if val else "False"
        c = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {tid:3d}, {v}){c}{end}")
    return "\n".join(lines)


def _emit_float_props(wcid: int, rows: list) -> str:
    """rows = [(type_id, float_val, comment), ...]"""
    if not rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)"]
    for i, row in enumerate(rows):
        tid, val, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        fv = f"{val:g}" if isinstance(val, float) else str(val)
        c = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {tid:4d}, {fv:>8}){c}{end}")
    return "\n".join(lines)


def _emit_str_props(wcid: int, rows: list) -> str:
    """rows = [(type_id, str_val, comment), ...]"""
    if not rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)"]
    for i, row in enumerate(rows):
        tid, val, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        escaped = str(val).replace("'", "''")
        c = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {tid:3d}, '{escaped}'){c}{end}")
    return "\n".join(lines)


def _emit_did_props(wcid: int, rows: list) -> str:
    """rows = [(type_id, hex_or_int_val, comment), ...]"""
    if not rows:
        return ""
    lines = ["INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)"]
    for i, row in enumerate(rows):
        tid, val, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        # Format as hex if >= 0x01000000, else decimal
        if isinstance(val, int) and val >= 0x01000000:
            vs = f"0x{val:08X}"
        else:
            vs = str(val)
        c = f" /* {comment} */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {tid:4d}, {vs}){c}{end}")
    return "\n".join(lines)


def _emit_attributes(wcid: int, attrs: dict) -> str:
    """attrs = {name: init_level, ...} for the 6 primary attributes."""
    ATTR_IDS = {
        "strength": 1, "endurance": 2, "quickness": 3,
        "coordination": 4, "focus": 5, "self": 6,
    }
    ATTR_NAMES = {1: "Strength", 2: "Endurance", 3: "Quickness",
                  4: "Coordination", 5: "Focus", 6: "Self"}
    cols = "(`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)"
    lines = [f"INSERT INTO `weenie_properties_attribute` {cols}"]
    items = [(ATTR_IDS[k], v) for k, v in attrs.items() if k in ATTR_IDS]
    items.sort(key=lambda x: x[0])
    for i, (tid, val) in enumerate(items):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(items) - 1 else ""
        name = ATTR_NAMES.get(tid, f"attr{tid}")
        lines.append(f"{prefix} ({wcid}, {tid:4d}, {val:5d}, 0, 0) /* {name} */{end}")
    return "\n".join(lines)


def _emit_vitals(wcid: int, health: int, stamina: int, mana: int) -> str:
    """Emit weenie_properties_attribute_2nd for MaxHealth/MaxStamina/MaxMana."""
    cols = "(`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)"
    lines = [f"INSERT INTO `weenie_properties_attribute_2nd` {cols}"]
    vitals = [
        (1, health,  "MaxHealth"),
        (3, stamina, "MaxStamina"),
        (5, mana,    "MaxMana"),
    ]
    for i, (tid, val, name) in enumerate(vitals):
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(vitals) - 1 else ""
        init = max(0, val - 100)  # init_Level approximation
        lines.append(f"{prefix} ({wcid}, {tid:4d}, {init:6d}, 0, 0, {val:5d}) /* {name} */{end}")
    return "\n".join(lines)


def _emit_skills(wcid: int, rows: list) -> str:
    """rows = [(skill_id, init_level, comment), ...]
    s_a_c=2 means Trained."""
    if not rows:
        return ""
    cols = "(`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)"
    lines = [f"INSERT INTO `weenie_properties_skill` {cols}"]
    for i, row in enumerate(rows):
        sid, init, comment = row[0], row[1], row[2] if len(row) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end = ";" if i == len(rows) - 1 else ""
        pad = f"{comment:<22}" if comment else ""
        c = f" /* {pad}Trained */" if comment else ""
        lines.append(f"{prefix} ({wcid}, {sid:2d}, 0, 2, 0, {init:4d}, 0, 0){c}{end}")
    return "\n".join(lines)


def _int_val(d: dict, key: str, default: int = 0) -> int:
    try:
        return int(d.get(key, default))
    except (TypeError, ValueError):
        return default


def _float_val(d: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(d.get(key, default))
    except (TypeError, ValueError):
        return default


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

# Creature type int IDs matching ACE World DB (authoritative from WeenieForge CREATURE_TYPES)
CREATURE_TYPE = {
    "none":          0,
    "olthoi":        1,
    "banderling":    2,
    "drudge":        3,
    "mosswart":      4,
    "lugian":        5,
    "tumerok":       6,
    "mite":          7,
    "tusker":        8,
    "golem":         13,
    "undead":        14, "skeleton": 14, "zombie": 14,
    "gromnie":       15,
    "reedshark":     16,
    "armoredillo":   17,
    "fae":           18,
    "virindi":       19,
    "wisp":          20,
    "shadow":        22,
    "mattekar":      23,
    "monouga":       28,
    "zefir":         29,
    "shreth":        32,
    "fireelemental": 38,
    "snowman":       39,
    "grievver":      44,
    "ursuin":        46,
    "hollowminion":  48,
    "acidelemental": 60,
    "frostelemental":61,
    "burun":         75,
    "gearknight":    99,
    "gurog":         100,
    "anekshay":      101,
    "human":         31,  # default
}

# Body part keys per creature type (from WeenieForge CREATURE_BP_MAP)
CREATURE_BP_MAP = {
    0:  [0,1,2,3,4,5,6,7,8],
    1:  [0,9,14,16,17,18,20],           # Olthoi
    2:  [0,1,2,3,4,5,6,7,8,9],          # Banderling
    3:  [0,1,2,3,4,5,6,7,8,9],          # Drudge
    4:  [0,1,2,3,4,5,6,7,8,9],          # Mosswart
    5:  [0,1,2,3,4,5,6,7,8],            # Lugian
    6:  [0,1,2,3,4,5,6,7,8,9],          # Tumerok
    7:  [0,1,2,3,4,5,6,7,8],            # Mite
    8:  [0,1,2,3,4,5,6,7,8,9],          # Tusker
    13: [0,1,2,3,4,5,6,7,8,9],          # Golem
    14: [0,1,2,3,4,5,6,7,8,9],          # Undead
    15: [0,1,2,3,4,5,6,7,8,9,20],       # Gromnie
    16: [0,9,10,12,14],                  # Reedshark
    17: [0,9,14,15,17],                  # Armoredillo
    18: [0,1,2,3,4,5,6,7,8],            # Fae
    19: [0,1,2,3,4,5,9,15],             # Virindi
    20: [0,9,14,15,19],                  # Wisp
    22: [0,1,2,3,4,5,6,7,8,9],          # Shadow
    23: [0,9,10,12,14],                  # Mattekar
    28: [0,1,2,3,4,5,6,7,8,9],          # Monouga
    29: [0,9,14,15,19],                  # Zefir
    30: [0,1,2,3,4,5,6,7,8,9],          # Skeleton
    31: [0,1,2,3,4,5,6,7,8],            # Human (default)
    32: [0,1,2,3,4,5,6,7,8,9],          # Shreth
    38: [0,1,2,3,4,5,6,7,8],            # FireElemental
    39: [0,1,2,3,4,5,6,7,8],            # Snowman
    44: [0,9,14,16,17,18,20],           # Grievver
    46: [0,9,10,12,14],                  # Ursuin
    48: [0,1,2,3,4,5,9,15],             # HollowMinion
    60: [0,1,2,3,4,5,6,7,8],            # AcidElemental
    61: [0,1,2,3,4,5,6,7,8],            # FrostElemental
    75: [0,1,2,3,4,5,6,7,8,9,18],       # Burun
    99: [0,1,2,3,4,5,6,7,8,9,10],       # GearKnight
    100:[0,1,2,3,4,5,6,7,8,9],          # Gurog
    101:[0,1,2,3,4,5,6,7,8,9],          # Anekshay
}

# Body part key → name (from WeenieForge BP_KEY_NAMES)
BP_KEY_NAMES = {
    0:'Head',    1:'Chest',     2:'Abdomen',   3:'UpperArm',    4:'LowerArm',
    5:'Hand',    6:'UpperLeg',  7:'LowerLeg',  8:'Foot',        9:'Horn',
    10:'FrontLeg',11:'FrontFoot',12:'RearLeg', 13:'RearFoot',  14:'Torso',
    15:'Tail',   16:'Arm',      17:'Leg',      18:'Claw',       19:'Wings',
    20:'Breath', 21:'Tentacle', 22:'UpperTentacle', 23:'LowerTentacle', 24:'Cloak',
}


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


def _emit_body_parts_ref(wcid: int, parts=None, armor: int = 100,
                         creature_type_int: int = None) -> str:
    """Emit body_part rows.
    - If `parts` is an int (creature_type_int), auto-build from CREATURE_BP_MAP.
    - If `parts` is a list of tuples (explicit), emit as-is.
      Tuple format: (key, d_Type, d_Val, d_Var, base_Armor,
                     vs_Slash, vs_Pierce, vs_Bludgeon, vs_Cold, vs_Fire, vs_Acid, vs_Electric, vs_Nether,
                     b_h, hlf, mlf, llf, hrf, mrf, lrf, hlb, mlb, llb, hrb, mrb, lrb)
    Supports all 35 creature types via CREATURE_BP_MAP.
    """
    # Hit-location fractions per key
    _BP_FRACS = {
        0:  (1, 0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0   ),  # Head
        1:  (2, 0.44, 0.17, 0,    0.44, 0.17, 0,    0.44, 0.17, 0,    0.44, 0.17, 0   ),  # Chest
        2:  (3, 0,    0.17, 0,    0,    0.17, 0,    0,    0.17, 0,    0,    0.17, 0   ),  # Abdomen
        3:  (1, 0.23, 0.03, 0,    0.23, 0.03, 0,    0.23, 0.03, 0,    0.23, 0.03, 0   ),  # UpperArm
        4:  (2, 0,    0.3,  0,    0,    0.3,  0,    0,    0.3,  0,    0,    0.3,  0   ),  # LowerArm
        5:  (2, 0,    0.2,  0,    0,    0.2,  0,    0,    0.2,  0,    0,    0.2,  0   ),  # Hand
        6:  (3, 0,    0.13, 0.18, 0,    0.13, 0.18, 0,    0.13, 0.18, 0,    0.13, 0.18),  # UpperLeg
        7:  (3, 0,    0,    0.6,  0,    0,    0.6,  0,    0,    0.6,  0,    0,    0.6 ),  # LowerLeg
        8:  (3, 0,    0,    0.22, 0,    0,    0.22, 0,    0,    0.22, 0,    0,    0.22),  # Foot
        9:  (2, 0.5,  0.5,  0,    0.5,  0.5,  0,    0,    0,    0,    0,    0,    0   ),  # Horn
        10: (2, 0.2,  0.4,  0.5,  0.2,  0.4,  0.5,  0,    0,    0,    0,    0,    0   ),  # FrontLeg
        11: (3, 0,    0,    0.25, 0,    0,    0.25, 0,    0,    0,    0,    0,    0   ),  # FrontFoot (old key)
        12: (3, 0,    0,    0.25, 0,    0,    0.25, 0,    0,    0,    0,    0,    0   ),  # RearLeg
        13: (3, 0,    0,    0.25, 0,    0,    0.25, 0,    0,    0,    0,    0,    0   ),  # RearFoot (old key)
        14: (2, 0.3,  0.4,  0.25, 0.3,  0.4,  0.25, 0.6,  0.5,  0.25, 0.6,  0.5,  0.25),  # Torso
        15: (3, 0,    0,    0.5,  0,    0,    0.5,  0,    0,    0,    0,    0,    0   ),  # Tail
        16: (1, 0.25, 0.5,  0,    0.25, 0.5,  0,    0,    0,    0,    0,    0,    0   ),  # Arm
        17: (2, 0,    0.25, 0.5,  0,    0.25, 0.5,  0,    0,    0,    0,    0,    0   ),  # Leg
        18: (2, 0.5,  0.5,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0   ),  # Claw
        19: (1, 0.5,  0,    0,    0,    0,    0,    0.5,  0,    0,    0,    0,    0   ),  # Wings
        20: (2, 0.1,  0.1,  0,    0.1,  0.1,  0,    0.1,  0.1,  0,    0.1,  0.1,  0   ),  # Breath
        21: (2, 0.3,  0.3,  0.3,  0.3,  0.3,  0.3,  0,    0,    0,    0,    0,    0   ),  # Tentacle
        22: (2, 0.5,  0.5,  0,    0.5,  0.5,  0,    0,    0,    0,    0,    0,    0   ),  # UpperTentacle
        23: (3, 0,    0,    0.5,  0,    0,    0.5,  0,    0,    0,    0,    0,    0   ),  # LowerTentacle
        24: (1, 0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0,    0.33, 0,    0   ),  # Cloak
    }
    # d_Val/d_Var per key (damage type 4 = Bludgeoning for most)
    _BP_DVAL = {5: (2, 0.75), 8: (2, 0.75), 9: (4, 0.75),
                10: (4, 0), 12: (4, 0), 13: (4, 0),
                15: (4, 0), 17: (4, 0), 18: (4, 0.75), 20: (64, 0.75)}

    if parts is None:
        parts = creature_type_int if creature_type_int is not None else 31
    if isinstance(parts, int):
        creature_type_int = parts
        keys = CREATURE_BP_MAP.get(creature_type_int, CREATURE_BP_MAP[31])
        parts = []
        for key in keys:
            fracs = _BP_FRACS.get(key, _BP_FRACS[0])
            dval_pair = _BP_DVAL.get(key, (4, 0))
            d_Type, d_Val, d_Var = 4, dval_pair[0], dval_pair[1]
            a = armor
            vs = a  # armor_Vs_* = base_Armor for creatures
            parts.append((key, d_Type, d_Val, d_Var, a, vs, vs, vs, vs, vs, vs, vs, 0) + fracs)

    cols = ("(`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, "
            "`armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, "
            "`armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, "
            "`armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, "
            "`h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, "
            "`h_r_b`, `m_r_b`, `l_r_b`)")
    lines = [f"INSERT INTO `weenie_properties_body_part` {cols}"]
    for i, p in enumerate(parts):
        key = p[0]
        label = BP_KEY_NAMES.get(key, f"key{key}")
        prefix = "VALUES" if i == 0 else "     ,"
        end    = ";" if i == len(parts) - 1 else ""
        def _f(v):
            return f"{v:g}" if isinstance(v, float) else str(v)
        vals = ", ".join(_f(x) for x in p)
        lines.append(f"{prefix} ({wcid}, {vals}) /* {label} */{end}")
    return "\n".join(lines)



def _emit_spellbook(wcid: int, spells: list) -> str:
    """Emit spellbook rows.
    spells = [(spell_id, probability, comment), ...]
    """
    cols = "(`object_Id`, `spell`, `probability`)"
    lines = [f"INSERT INTO `weenie_properties_spell_book` {cols}"]
    for i, entry in enumerate(spells):
        sid, prob = entry[0], entry[1]
        comment = f" /* {entry[2]} */" if len(entry) > 2 else ""
        prefix = "VALUES" if i == 0 else "     ,"
        end    = ";" if i == len(spells) - 1 else ""
        lines.append(f"{prefix} ({wcid}, {sid:5d}, {prob:8}){comment}{end}")
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
    """Emit generator weenie using the correct Shattered Dawn format.
    Uses int props 81/82 for counts, float props 41/43 for timing/radius,
    and weenie_properties_generator with probability=-1 (always spawn)."""
    target = _int_val(g, "target_wcid", 0)
    delay  = _float_val(g, "delay", 300.0)
    init   = _int_val(g, "init_create", 1)
    maxc   = _int_val(g, "max_create", 1)
    when   = _int_val(g, "when_create", 1)
    where  = _int_val(g, "where_create", 2)  # 2=Scatter default
    radius = _float_val(g, "radius", 50.0)

    # Int properties: MaxGeneratedObjects(81), InitGeneratedObjects(82), PhysicsState(93)
    int_rows = [
        (81, maxc,  "MaxGeneratedObjects"),
        (82, init,  "InitGeneratedObjects"),
        (93, 1044,  "PhysicsState - Ethereal, IgnoreCollisions, Gravity"),
    ]
    # Bool properties
    bool_rows = [
        (1,  True, "Stuck"),
        (11, True, "IgnoreCollisions"),
        (18, True, "Visibility"),
    ]
    # Float properties: RegenerationInterval(41), GeneratorRadius(43)
    float_rows = [
        (41, delay,  "RegenerationInterval"),
        (43, radius, "GeneratorRadius"),
    ]
    # Generator table row: probability=-1 means always spawn
    gen_cols = "(`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)"
    gen_comment = f"/* Generate {target} (x{init} up to max of {maxc}) - Regenerate upon Destruction */"

    parts = [
        _emit_int_props(wcid, int_rows),
        _emit_bool_props(wcid, bool_rows),
        _emit_float_props(wcid, float_rows),
        f"INSERT INTO `weenie_properties_generator` {gen_cols}\n"
        f"VALUES ({wcid}, -1, {target}, 1, {init}, {maxc}, {when}, {where}, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) {gen_comment};",
    ]
    return "\n\n".join(p for p in parts if p)



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
    name   = _escape_sql(_str_val(q, "quest_name", "MyQuestFlag"))
    quest_id = _int_val(q, "quest_id", 0)
    delta  = _int_val(q, "min_delta", 0)
    solves = _int_val(q, "max_solves", 100)
    msg    = _escape_sql(_str_val(q, "message", "kill counter"))
    id_part = f"id = '{quest_id}' OR " if quest_id else ""
    return (
        f"DELETE FROM quest WHERE {id_part}name = '{name}';\n\n"
        f"INSERT INTO quest (id, name, min_Delta, max_Solves, message)\n"
        f"VALUES ('{quest_id}', '{name}', '{delta}', '{solves}', '{msg}');"
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

    # Emotes are generated separately by AgentLoop._generate_emotes()
    # and appended after JSON→SQL conversion — not embedded in JSON.

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
