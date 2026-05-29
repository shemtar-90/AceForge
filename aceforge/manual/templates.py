"""
ACEForge Templates
Pre-built default values for each content type.
Returns a populated WeenieModel ready for the editor.
"""

from .weenie_model import WeenieModel


def apply_creature_template(m: WeenieModel, level: int = 150):
    m.weenie_type = 10
    # Int props
    m.int_props = [
        {"type": 1,   "value": 16},       # ItemType - Creature
        {"type": 2,   "value": 31},       # CreatureType - Human (change as needed)
        {"type": 3,   "value": 20},       # PaletteTemplate - Silver
        {"type": 6,   "value": -1},       # ItemsCapacity
        {"type": 7,   "value": -1},       # ContainersCapacity
        {"type": 16,  "value": 1},        # ItemUseable - No
        {"type": 25,  "value": level},    # Level
        {"type": 40,  "value": 2},        # CombatMode - Melee
        {"type": 67,  "value": 0},        # Tolerance - None
        {"type": 68,  "value": 5},        # TargetingTactic - Random+LastDamager
        {"type": 69,  "value": 4},        # CombatTactic
        {"type": 93,  "value": 3080},     # PhysicsState - Standard Creature
        {"type": 101, "value": 2},        # AiAllowedCombatStyle - OneHanded
        {"type": 133, "value": 4},        # ShowableOnRadar - Always
        {"type": 140, "value": 0},        # AiOptions
        {"type": 146, "value": 8500000},  # XpOverride
        {"type": 332, "value": 8000},     # LuminanceAward
    ]
    m.bool_props = [
        {"type": 1,   "value": True},     # Stuck
        {"type": 11,  "value": False},    # IgnoreCollisions
        {"type": 12,  "value": True},     # ReportCollisions
        {"type": 13,  "value": False},    # Ethereal
        {"type": 14,  "value": True},     # GravityStatus
        {"type": 15,  "value": True},     # LightsStatus
        {"type": 19,  "value": True},     # Attackable
        {"type": 120, "value": False},    # TreasureCorpse
    ]
    m.float_props = [
        {"type": 1,  "value": 5.0},   # HeartbeatInterval
        {"type": 2,  "value": 0.0},   # HeartbeatTimestamp
        {"type": 3,  "value": 0.4},   # HealthRate
        {"type": 4,  "value": 0.4},   # StaminaRate
        {"type": 5,  "value": 1.5},   # ManaRate
        {"type": 12, "value": 1.0},   # Shade
        {"type": 13, "value": 1.0},   # ArmorModVsSlash
        {"type": 14, "value": 1.0},   # ArmorModVsPierce
        {"type": 15, "value": 1.0},   # ArmorModVsBludgeon
        {"type": 16, "value": 1.0},   # ArmorModVsCold
        {"type": 17, "value": 1.0},   # ArmorModVsFire
        {"type": 18, "value": 1.0},   # ArmorModVsAcid
        {"type": 19, "value": 1.0},   # ArmorModVsElectric
        {"type": 31, "value": 16.0},  # VisualAwarenessRange
        {"type": 34, "value": 1.0},   # PowerupTime
        {"type": 39, "value": 1.0},   # DefaultScale
        {"type": 64, "value": 1.0},   # ResistSlash
        {"type": 65, "value": 1.0},   # ResistPierce
        {"type": 66, "value": 1.0},   # ResistBludgeon
        {"type": 67, "value": 1.0},   # ResistFire
        {"type": 68, "value": 1.0},   # ResistCold
        {"type": 69, "value": 1.0},   # ResistAcid
        {"type": 70, "value": 1.0},   # ResistElectric
        {"type": 104,"value": 10.0},  # ObviousRadarRange
        {"type": 125,"value": 1.0},   # ResistHealthDrain
        {"type": 165,"value": 1.0},   # ArmorModVsNether
        {"type": 166,"value": 1.0},   # ResistNether
    ]
    m.string_props = [{"type": 1, "value": "New Creature"}]
    m.did_props = [
        {"type": 1,  "value": "0x02000178"},   # Setup - human placeholder
        {"type": 2,  "value": "0x09000008"},   # MotionTable
        {"type": 3,  "value": "0x20000008"},   # SoundTable
        {"type": 4,  "value": "0x30000006"},   # CombatTable
        {"type": 6,  "value": "0x04000BEF"},   # PaletteBase
        {"type": 8,  "value": "0x06001036"},   # Icon
        {"type": 22, "value": "0x34000026"},   # PhysicsEffectTable
        {"type": 35, "value": 3000},           # DeathTreasureType
    ]
    m.attributes = [
        {"type": 1, "init_Level": 260, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 2, "init_Level": 260, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 3, "init_Level": 220, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 4, "init_Level": 240, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 5, "init_Level": 180, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 6, "init_Level": 180, "level_From_C_P": 0, "c_P_Spent": 0},
    ]
    m.attribute2nd = [
        {"type": 1, "init_Level": 1200, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 1200},
        {"type": 3, "init_Level": 1200, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 1200},
        {"type": 5, "init_Level": 800,  "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 800},
    ]
    m.skills = [
        {"type": 6,  "level_From_P_P": 0, "s_a_c": 2, "p_p": 0, "init_Level": 240, "resistance_At_Last_Check": 0, "last_Used_Time": 0},
        {"type": 7,  "level_From_P_P": 0, "s_a_c": 2, "p_p": 0, "init_Level": 240, "resistance_At_Last_Check": 0, "last_Used_Time": 0},
        {"type": 15, "level_From_P_P": 0, "s_a_c": 2, "p_p": 0, "init_Level": 220, "resistance_At_Last_Check": 0, "last_Used_Time": 0},
        {"type": 44, "level_From_P_P": 0, "s_a_c": 2, "p_p": 0, "init_Level": 290, "resistance_At_Last_Check": 0, "last_Used_Time": 0},
    ]
    m.body_parts = [
        _body_part(0, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 1, 0.33,0,0,0.33,0,0,0.33,0,0,0.33,0,0),
        _body_part(1, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 2, 0.44,0.17,0,0.44,0.17,0,0.44,0.17,0,0.44,0.17,0),
        _body_part(2, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 3, 0,0.17,0,0,0.17,0,0,0.17,0,0,0.17,0),
        _body_part(3, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 1, 0.23,0.03,0,0.23,0.03,0,0.23,0.03,0,0.23,0.03,0),
        _body_part(4, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 2, 0,0.3,0,0,0.3,0,0,0.3,0,0,0.3,0),
        _body_part(5, 4, 50, 0.75, 175, 175, 175, 175, 175, 175, 175, 0, 2, 0,0.2,0,0,0.2,0,0,0.2,0,0,0.2,0),
        _body_part(6, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 3, 0,0.13,0.18,0,0.13,0.18,0,0.13,0.18,0,0.13,0.18),
        _body_part(7, 4, 0, 0.0,  175, 175, 175, 175, 175, 175, 175, 0, 3, 0,0,0.6,0,0,0.6,0,0,0.6,0,0,0.6),
        _body_part(8, 4, 20, 0.75, 100, 100, 100, 100, 100, 100, 100, 0, 3, 0,0,0.22,0,0,0.22,0,0,0.22,0,0,0.22),
    ]


def apply_npc_template(m: WeenieModel):
    m.weenie_type = 10
    m.int_props = [
        {"type": 1,   "value": 16},
        {"type": 2,   "value": 31},       # CreatureType - Human
        {"type": 6,   "value": -1},
        {"type": 7,   "value": -1},
        {"type": 16,  "value": 32},       # ItemUseable - Remote
        {"type": 25,  "value": 275},      # Level
        {"type": 93,  "value": 6292504},  # PhysicsState - NPC
        {"type": 95,  "value": 8},        # RadarBlipColor - Yellow
        {"type": 133, "value": 4},
        {"type": 134, "value": 16},       # PlayerKillerStatus - RubberGlue
        {"type": 146, "value": 0},
    ]
    m.bool_props = [
        {"type": 1,  "value": True},   # Stuck
        {"type": 8,  "value": True},   # AllowGive
        {"type": 12, "value": True},   # ReportCollisions
        {"type": 13, "value": False},  # Ethereal
        {"type": 14, "value": True},   # GravityStatus
        {"type": 19, "value": False},  # Attackable
        {"type": 29, "value": True},   # NoCorpse
        {"type": 41, "value": True},   # ReportCollisionsAsEnvironment
        {"type": 42, "value": True},   # AllowEdgeSlide
        {"type": 52, "value": True},   # AiImmobile
    ]
    m.float_props = [
        {"type": 1,  "value": 60.0},
        {"type": 2,  "value": 0.0},
        {"type": 3,  "value": 0.16},
        {"type": 4,  "value": 5.0},
        {"type": 5,  "value": 1.0},
        {"type": 39, "value": 1.0},
        {"type": 54, "value": 3.0},   # UseRadius
    ]
    m.string_props = [
        {"type": 1,  "value": "New NPC"},
        {"type": 15, "value": ""},   # ShortDesc
    ]
    m.did_props = [
        {"type": 1,  "value": "0x02000178"},
        {"type": 2,  "value": "0x09000008"},
        {"type": 3,  "value": "0x20000008"},
        {"type": 6,  "value": "0x04000F90"},
        {"type": 7,  "value": "0x10000001"},
        {"type": 8,  "value": "0x06001036"},
        {"type": 22, "value": "0x3400001A"},
    ]
    m.attributes = [
        {"type": 1, "init_Level": 290, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 2, "init_Level": 260, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 3, "init_Level": 290, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 4, "init_Level": 290, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 5, "init_Level": 200, "level_From_C_P": 0, "c_P_Spent": 0},
        {"type": 6, "init_Level": 200, "level_From_C_P": 0, "c_P_Spent": 0},
    ]
    m.attribute2nd = [
        {"type": 1, "init_Level": 500, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 500},
        {"type": 3, "init_Level": 500, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 500},
        {"type": 5, "init_Level": 500, "level_From_C_P": 0, "c_P_Spent": 0, "current_Level": 500},
    ]
    m.body_parts = [
        _body_part(k, 4, 0, 0.0, 250,125,125,125,125,125,125,0, bh, *bfr)
        for k, bh, bfr in [
            (0, 1, [0.33,0,0,0.33,0,0,0.33,0,0,0.33,0,0]),
            (1, 2, [0.44,0.17,0,0.44,0.17,0,0.44,0.17,0,0.44,0.17,0]),
            (2, 3, [0,0.17,0,0,0.17,0,0,0.17,0,0,0.17,0]),
            (3, 1, [0.23,0.03,0,0.23,0.03,0,0.23,0.03,0,0.23,0.03,0]),
            (4, 2, [0,0.3,0,0,0.3,0,0,0.3,0,0,0.3,0]),
            (5, 2, [0,0.2,0,0,0.2,0,0,0.2,0,0,0.2,0]),
            (6, 3, [0,0.13,0.18,0,0.13,0.18,0,0.13,0.18,0,0.13,0.18]),
            (7, 3, [0,0,0.6,0,0,0.6,0,0,0.6,0,0,0.6]),
            (8, 3, [0,0,0.22,0,0,0.22,0,0,0.22,0,0,0.22]),
        ]
    ]


def apply_item_template(m: WeenieModel):
    m.weenie_type = 38  # Gem
    m.int_props = [
        {"type": 1,   "value": 2048},
        {"type": 5,   "value": 25},
        {"type": 8,   "value": 25},
        {"type": 11,  "value": 1},
        {"type": 12,  "value": 1},
        {"type": 13,  "value": 25},
        {"type": 14,  "value": 25},
        {"type": 15,  "value": 250},
        {"type": 16,  "value": 1},   # ItemUseable - No
        {"type": 19,  "value": 250},
        {"type": 93,  "value": 1044},
    ]
    m.bool_props = [{"type": 23, "value": True}]  # DestroyOnSell
    m.float_props = [{"type": 39, "value": 1.0}]
    m.string_props = [
        {"type": 1,  "value": "New Item"},
        {"type": 15, "value": ""},
    ]
    m.did_props = [
        {"type": 1,  "value": "0x02000155"},
        {"type": 3,  "value": "0x20000014"},
        {"type": 8,  "value": "0x0600141A"},
        {"type": 22, "value": "0x3400002B"},
    ]


def apply_generator_template(m: WeenieModel, spawns_wcid: int = 0):
    m.weenie_type = 1  # Generic
    m.int_props = [
        {"type": 81,  "value": 1},
        {"type": 82,  "value": 1},
        {"type": 93,  "value": 1044},
        {"type": 133, "value": 4},
    ]
    m.bool_props = [
        {"type": 1,  "value": True},
        {"type": 11, "value": True},
        {"type": 18, "value": False},
    ]
    m.float_props = [
        {"type": 39, "value": 1.0},
        {"type": 41, "value": 1.0},
        {"type": 43, "value": 3.0},
    ]
    m.string_props = [{"type": 1, "value": "NewGen"}]
    m.did_props = [
        {"type": 1,  "value": "0x020006FD"},
        {"type": 2,  "value": "0x09000091"},
        {"type": 3,  "value": "0x20000058"},
        {"type": 8,  "value": "0x060016C5"},
        {"type": 22, "value": "0x34000072"},
    ]
    if spawns_wcid:
        m.generator = [{
            "probability": -1, "weenie_Class_Id": spawns_wcid,
            "delay": 1800, "init_Create": 1, "max_Create": 1,
            "when_Create": 1, "where_Create": 4, "stack_Size": -1,
            "palette_Id": 0, "shade": 0.0, "obj_Cell_Id": 0,
            "origin_X": 0.0, "origin_Y": 0.0, "origin_Z": 0.0,
            "angles_W": 1.0, "angles_X": 0.0, "angles_Y": 0.0, "angles_Z": 0.0,
        }]


def apply_weapon_template(m: WeenieModel):
    m.weenie_type = 6  # MeleeWeapon
    m.int_props = [
        {"type": 1,  "value": 1},        # ItemType - MeleeWeapon
        {"type": 3,  "value": 20},        # PaletteTemplate - Silver
        {"type": 5,  "value": 800},
        {"type": 8,  "value": 320},
        {"type": 9,  "value": 1048576},   # ValidLocations - MeleeWeapon
        {"type": 16, "value": 1},
        {"type": 19, "value": 360},
        {"type": 44, "value": 11},        # Damage
        {"type": 45, "value": 1},         # DamageType - Slash
        {"type": 46, "value": 2},         # DefaultCombatStyle - OneHanded
        {"type": 47, "value": 4},         # AttackType - Slash
        {"type": 48, "value": 44},        # WeaponSkill - HeavyWeapons
        {"type": 49, "value": 45},        # WeaponTime
        {"type": 51, "value": 1},         # CombatUse - Melee
        {"type": 93, "value": 1044},
    ]
    m.bool_props = [{"type": 22, "value": True}]  # Inscribable
    m.float_props = [
        {"type": 21, "value": 0.75},  # WeaponLength
        {"type": 22, "value": 0.5},   # DamageVariance
        {"type": 29, "value": 1.0},   # WeaponDefense
        {"type": 62, "value": 1.0},   # WeaponOffense
    ]
    m.string_props = [{"type": 1, "value": "New Weapon"}]
    m.did_props = [
        {"type": 1,  "value": "0x02000125"},
        {"type": 3,  "value": "0x20000014"},
        {"type": 6,  "value": "0x04000BEF"},
        {"type": 7,  "value": "0x10000143"},
        {"type": 8,  "value": "0x06001639"},
        {"type": 22, "value": "0x3400002B"},
    ]


def apply_armor_template(m: WeenieModel):
    m.weenie_type = 2  # Clothing
    m.int_props = [
        {"type": 1,  "value": 2},       # ItemType - Armor
        {"type": 3,  "value": 20},
        {"type": 4,  "value": 512},     # ClothingPriority - ChestArmor
        {"type": 5,  "value": 320},
        {"type": 8,  "value": 160},
        {"type": 9,  "value": 512},     # ValidLocations - ChestArmor
        {"type": 16, "value": 1},
        {"type": 19, "value": 433},
        {"type": 27, "value": 3},       # ArmorType - Metal
        {"type": 28, "value": 100},     # ArmorLevel
        {"type": 93, "value": 1044},
    ]
    m.bool_props = [
        {"type": 22, "value": True},    # Inscribable
    ]
    m.float_props = [
        {"type": 12, "value": 0.66},
        {"type": 13, "value": 1.0},    # ArmorModVsSlash
        {"type": 14, "value": 1.0},
        {"type": 15, "value": 1.0},
        {"type": 16, "value": 1.0},
        {"type": 17, "value": 1.0},
        {"type": 18, "value": 1.0},
        {"type": 19, "value": 1.0},
    ]
    m.string_props = [{"type": 1, "value": "New Armor"}]
    m.did_props = [
        {"type": 1,  "value": "0x02000268"},
        {"type": 3,  "value": "0x20000014"},
        {"type": 6,  "value": "0x0400007E"},
        {"type": 7,  "value": "0x1000003A"},
        {"type": 8,  "value": "0x06000FCF"},
        {"type": 22, "value": "0x3400002B"},
    ]


TEMPLATE_FUNCS = {
    "creature":  apply_creature_template,
    "boss":      apply_creature_template,
    "npc":       apply_npc_template,
    "item":      apply_item_template,
    "generator": apply_generator_template,
    "weapon":    apply_weapon_template,
    "armor":     apply_armor_template,
}


def _body_part(key, d_type, d_val, d_var,
               base_armor,
               armor_slash, armor_pierce, armor_bludgeon,
               armor_cold, armor_fire, armor_acid, armor_electric, armor_nether,
               bh, h_l_f, m_l_f, l_l_f, h_r_f, m_r_f, l_r_f,
               h_l_b, m_l_b, l_l_b, h_r_b, m_r_b, l_r_b) -> dict:
    return {
        "key": key, "d_Type": d_type, "d_Val": d_val, "d_Var": d_var,
        "base_Armor": base_armor,
        "armor_Vs_Slash": armor_slash, "armor_Vs_Pierce": armor_pierce,
        "armor_Vs_Bludgeon": armor_bludgeon, "armor_Vs_Cold": armor_cold,
        "armor_Vs_Fire": armor_fire, "armor_Vs_Acid": armor_acid,
        "armor_Vs_Electric": armor_electric, "armor_Vs_Nether": armor_nether,
        "b_h": bh,
        "h_l_f": h_l_f, "m_l_f": m_l_f, "l_l_f": l_l_f,
        "h_r_f": h_r_f, "m_r_f": m_r_f, "l_r_f": l_r_f,
        "h_l_b": h_l_b, "m_l_b": m_l_b, "l_l_b": l_l_b,
        "h_r_b": h_r_b, "m_r_b": m_r_b, "l_r_b": l_r_b,
    }
