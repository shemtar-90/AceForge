"""
ACEForge SQL Builder
Converts a WeenieModel to valid ACE-World-16PY MySQL INSERT statements.
Produces the same format as the AI mode output — one /* ===== FILE: ... ===== */
block per weenie, using /* */ inline comments, no -- comments.
"""

from .weenie_model import WeenieModel
from .enums_data import (
    PROPERTY_INT_NAMES, PROPERTY_BOOL_NAMES, PROPERTY_FLOAT_NAMES,
    PROPERTY_STRING_NAMES, PROPERTY_DID_NAMES,
    PROPERTY_ATTRIBUTE_NAMES, PROPERTY_ATTRIBUTE2ND_NAMES,
    SKILL_TYPES, SKILL_SAC, BODY_PART_KEYS,
    WEENIE_TYPES, EMOTE_CATEGORY, EMOTE_TYPE,
)

EMOTE_ACTION_COLUMNS = (
    "emote_Id", "order", "type", "delay", "extent", "motion", "message",
    "test_String", "min", "max", "min_64", "max_64", "min_Dbl", "max_Dbl",
    "stat", "display", "amount", "amount_64", "hero_X_P_64", "percent",
    "spell_Id", "wealth_Rating", "treasure_Class", "treasure_Type",
    "p_Script", "sound", "destination_Type", "weenie_Class_Id", "stack_Size",
    "palette", "shade", "try_To_Bond", "obj_Cell_Id",
    "origin_X", "origin_Y", "origin_Z",
    "angles_W", "angles_X", "angles_Y", "angles_Z",
)


def _v(val) -> str:
    """Format a value for SQL."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, str):
        escaped = val.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(val, float):
        return f"{val:g}"
    return str(val)


def build_sql(weenie: WeenieModel, file_label: str = "") -> str:
    """Build complete SQL for one weenie."""
    wid = weenie.class_id
    lines = []

    if file_label:
        lines.append(f"/* ===== FILE: {file_label} ===== */")
        lines.append("")

    # weenie row
    type_name = WEENIE_TYPES.get(weenie.weenie_type, str(weenie.weenie_type))
    lines.append(f"DELETE FROM `weenie` WHERE `class_Id` = {wid};")
    lines.append("")
    lines.append("INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)")
    lines.append(f"VALUES ({wid}, '{weenie.class_name}', {weenie.weenie_type}, NOW()) /* {type_name} - Shattered Dawn custom content */;")

    # Int properties
    if weenie.int_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)")
        rows = []
        for p in sorted(weenie.int_props, key=lambda x: x["type"]):
            name = PROPERTY_INT_NAMES.get(p["type"], f"type_{p['type']}")
            rows.append(f"VALUES ({wid}, {p['type']:>4}, {str(p['value']):>12}) /* {name} */")
        for i, r in enumerate(rows):
            prefix = "     , " if i > 0 else ""
            lines.append(f"{prefix}{r}" if i > 0 else f"{r}")
        lines[-len(rows)] = rows[0]
        # Redo as multi-row format
        lines = lines[:-(len(rows))]
        for i, r in enumerate(rows):
            if i == 0:
                lines.append(r)
            else:
                lines.append(f"     , {r[7:]}")  # strip leading VALUES
        lines.append(";")

    # Bool properties
    if weenie.bool_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)")
        rows = []
        for p in sorted(weenie.bool_props, key=lambda x: x["type"]):
            name = PROPERTY_BOOL_NAMES.get(p["type"], f"type_{p['type']}")
            val = "True " if p["value"] else "False"
            rows.append(f"({wid}, {p['type']:>4}, {val}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # Float properties
    if weenie.float_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)")
        rows = []
        for p in sorted(weenie.float_props, key=lambda x: x["type"]):
            name = PROPERTY_FLOAT_NAMES.get(p["type"], f"type_{p['type']}")
            rows.append(f"({wid}, {p['type']:>4}, {_v(p['value'])}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # String properties
    if weenie.string_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)")
        rows = []
        for p in sorted(weenie.string_props, key=lambda x: x["type"]):
            name = PROPERTY_STRING_NAMES.get(p["type"], f"type_{p['type']}")
            rows.append(f"({wid}, {p['type']:>4}, {_v(p['value'])}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # DID properties
    if weenie.did_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)")
        rows = []
        for p in sorted(weenie.did_props, key=lambda x: x["type"]):
            name = PROPERTY_DID_NAMES.get(p["type"], f"type_{p['type']}")
            rows.append(f"({wid}, {p['type']:>4}, {p['value']}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # Int64 properties
    if weenie.int64_props:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_int64` (`object_Id`, `type`, `value`)")
        rows = [f"({wid}, {p['type']}, {p['value']})" for p in weenie.int64_props]
        _write_multirow(lines, "VALUES", rows)

    # Attributes
    if weenie.attributes:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)")
        rows = []
        for p in sorted(weenie.attributes, key=lambda x: x["type"]):
            name = PROPERTY_ATTRIBUTE_NAMES.get(p["type"], f"attr_{p['type']}")
            rows.append(f"({wid}, {p['type']}, {p['init_Level']}, {p['level_From_C_P']}, {p['c_P_Spent']}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # Attribute 2nd (vitals)
    if weenie.attribute2nd:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)")
        rows = []
        for p in sorted(weenie.attribute2nd, key=lambda x: x["type"]):
            name = PROPERTY_ATTRIBUTE2ND_NAMES.get(p["type"], f"vital_{p['type']}")
            rows.append(f"({wid}, {p['type']}, {p['init_Level']}, {p['level_From_C_P']}, {p['c_P_Spent']}, {p['current_Level']}) /* {name} */")
        _write_multirow(lines, "VALUES", rows)

    # Skills
    if weenie.skills:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)")
        rows = []
        for p in sorted(weenie.skills, key=lambda x: x["type"]):
            sname = SKILL_TYPES.get(p["type"], f"skill_{p['type']}")
            sac_name = SKILL_SAC.get(p.get("s_a_c", 2), "Trained")
            rows.append(
                f"({wid}, {p['type']:>3}, {p.get('level_From_P_P',0)}, {p.get('s_a_c',2)}, "
                f"{p.get('p_p',0)}, {p.get('init_Level',0)}, "
                f"{p.get('resistance_At_Last_Check',0)}, {p.get('last_Used_Time',0)}) "
                f"/* {sname} — {sac_name} */"
            )
        _write_multirow(lines, "VALUES", rows)

    # Body parts
    if weenie.body_parts:
        lines.append("")
        lines.append(
            "INSERT INTO `weenie_properties_body_part` "
            "(`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, "
            "`armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, "
            "`armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, "
            "`b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, "
            "`h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)"
        )
        rows = []
        for p in sorted(weenie.body_parts, key=lambda x: x["key"]):
            part_name = BODY_PART_KEYS.get(p["key"], f"key_{p['key']}")
            row = (
                f"({wid}, {p['key']:>3}, {p['d_Type']:>3}, {p['d_Val']:>4}, {_v(p['d_Var'])}, "
                f"{p['base_Armor']:>4}, "
                f"{p['armor_Vs_Slash']:>4}, {p['armor_Vs_Pierce']:>4}, {p['armor_Vs_Bludgeon']:>4}, "
                f"{p['armor_Vs_Cold']:>4}, {p['armor_Vs_Fire']:>4}, {p['armor_Vs_Acid']:>4}, "
                f"{p['armor_Vs_Electric']:>4}, {p.get('armor_Vs_Nether',0):>4}, "
                f"{p['b_h']}, "
                f"{_v(p['h_l_f'])}, {_v(p['m_l_f'])}, {_v(p['l_l_f'])}, "
                f"{_v(p['h_r_f'])}, {_v(p['m_r_f'])}, {_v(p['l_r_f'])}, "
                f"{_v(p['h_l_b'])}, {_v(p['m_l_b'])}, {_v(p['l_l_b'])}, "
                f"{_v(p['h_r_b'])}, {_v(p['m_r_b'])}, {_v(p['l_r_b'])}) "
                f"/* {part_name} */"
            )
            rows.append(row)
        _write_multirow(lines, "VALUES", rows)

    # Spell book
    if weenie.spell_book:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)")
        rows = []
        for p in sorted(weenie.spell_book, key=lambda x: x["probability"]):
            rows.append(f"({wid}, {p['spell']:>5}, {_v(p['probability'])})")
        _write_multirow(lines, "VALUES", rows)

    # Event filters
    if weenie.event_filters:
        lines.append("")
        lines.append("INSERT INTO `weenie_properties_event_filter` (`object_Id`, `event`)")
        rows = [f"({wid}, {ev})" for ev in weenie.event_filters]
        _write_multirow(lines, "VALUES", rows)

    # Emotes
    for emote in weenie.emotes:
        cat_name = EMOTE_CATEGORY.get(emote.get("category"), str(emote.get("category")))
        wcid_filter = emote.get("weenie_Class_Id", "NULL")
        quest_filter = _v(emote.get("quest"))
        style = _v(emote.get("style"))
        substyle = _v(emote.get("substyle"))
        vendor_type = _v(emote.get("vendor_Type"))
        min_hp = _v(emote.get("min_Health"))
        max_hp = _v(emote.get("max_Health"))

        lines.append("")
        lines.append(
            f"INSERT INTO `weenie_properties_emote` "
            f"(`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, "
            f"`quest`, `vendor_Type`, `min_Health`, `max_Health`)"
        )
        lines.append(
            f"VALUES ({wid}, {emote['category']} /* {cat_name} */, "
            f"{_v(emote.get('probability', 1))}, "
            f"{wcid_filter if wcid_filter != 'NULL' else 'NULL'}, "
            f"{style}, {substyle}, {quest_filter}, {vendor_type}, {min_hp}, {max_hp});"
        )
        lines.append("")
        lines.append("SET @parent_id = LAST_INSERT_ID();")

        actions = emote.get("actions", [])
        if actions:
            cols = ", ".join(f"`{c}`" for c in EMOTE_ACTION_COLUMNS)
            lines.append(f"INSERT INTO `weenie_properties_emote_action` ({cols})")
            action_rows = []
            for ai, action in enumerate(actions):
                type_name_e = EMOTE_TYPE.get(action.get("type"), str(action.get("type", 0)))
                vals = ["@parent_id", str(ai)]
                vals.append(f"{action.get('type', 0)} /* {type_name_e} */")
                vals.append(_v(action.get("delay", 0)))
                vals.append(_v(action.get("extent", 1)))
                for col in EMOTE_ACTION_COLUMNS[5:]:
                    vals.append(_v(action.get(col)))
                action_rows.append(f"({', '.join(vals)})")
            _write_multirow(lines, "VALUES", action_rows)

    # Create list
    if weenie.create_list:
        lines.append("")
        lines.append(
            "INSERT INTO `weenie_properties_create_list` "
            "(`object_Id`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)"
        )
        rows = []
        for p in weenie.create_list:
            rows.append(
                f"({wid}, {p.get('destination_Type',9)}, {p.get('weenie_Class_Id',0)}, "
                f"{p.get('stack_Size',1)}, {p.get('palette',0)}, {_v(p.get('shade',1.0))}, "
                f"{'True' if p.get('try_To_Bond') else 'False'})"
            )
        _write_multirow(lines, "VALUES", rows)

    # Generator
    if weenie.generator:
        lines.append("")
        lines.append(
            "INSERT INTO `weenie_properties_generator` "
            "(`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, "
            "`when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, "
            "`origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)"
        )
        rows = []
        for g in weenie.generator:
            rows.append(
                f"({wid}, {_v(g.get('probability',-1))}, {g.get('weenie_Class_Id',0)}, "
                f"{g.get('delay',1800)}, {g.get('init_Create',1)}, {g.get('max_Create',1)}, "
                f"{g.get('when_Create',1)}, {g.get('where_Create',4)}, {g.get('stack_Size',-1)}, "
                f"{g.get('palette_Id',0)}, {_v(g.get('shade',0.0))}, {g.get('obj_Cell_Id',0)}, "
                f"{_v(g.get('origin_X',0.0))}, {_v(g.get('origin_Y',0.0))}, {_v(g.get('origin_Z',0.0))}, "
                f"{_v(g.get('angles_W',1.0))}, {_v(g.get('angles_X',0.0))}, "
                f"{_v(g.get('angles_Y',0.0))}, {_v(g.get('angles_Z',0.0))})"
            )
        _write_multirow(lines, "VALUES", rows)

    return "\n".join(lines) + "\n"


def _write_multirow(lines: list, keyword: str, rows: list):
    """Write multi-row INSERT VALUES block."""
    for i, row in enumerate(rows):
        if i == 0:
            lines.append(f"{keyword} {row}")
        else:
            lines.append(f"     , {row}")
    lines.append(";")
