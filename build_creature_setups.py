"""Build aceforge/web/creature_setups.json — a map of CreatureType int →
every Setup DID used by base-game creatures of that type.

Scrapes the bundled weenie database (aceforge/references/weenie_index.json +
weenies/*.sql). For each creature type, collects one entry per unique Setup,
keeping the companion DIDs (MotionTable, SoundTable, PaletteBase, ClothingBase,
PhysicsEffectTable, CombatTable) from the first weenie seen with that Setup so
the UI can auto-fill the whole DATA ID section when a model is picked.

Output format:
{ "<ctype_int>": [ {"s": "0x02000038", "n": "Olthoi Soldier",
                    "mt": "0x09000078", "st": "0x20000012", "pb": "0x04000BEF",
                    "cb": "0x10000330", "pt": "0x3400002B", "ct4": "0x30000000"},
                   ... ], ... }

Run from the repo root: python build_creature_setups.py
"""
import json
import re
from pathlib import Path

REFS = Path("aceforge/references")
OUT = Path("aceforge/web/creature_setups.json")

VAL = r"(0x[0-9A-Fa-f]+|\d+)"
DID_ROW = re.compile(r"\((\d+),\s*(\d+),\s*" + VAL + r"\)")
CT_ROW = re.compile(r"\(\d+,\s*2,\s*(\d+)\)\s*/\* CreatureType")

# ACE CreatureType labels — used to split compound class names into words
# ("zefirdusk" → "Zefir Dusk").
CT_LABELS = {
    1: "Olthoi", 2: "Banderling", 3: "Drudge", 4: "Mosswart", 5: "Lugian",
    6: "Tumerok", 7: "Mite", 8: "Tusker", 9: "AunTumerok", 10: "HeaTumerok",
    11: "Ruschk", 13: "Golem", 14: "Undead", 15: "Gromnie", 16: "Reedshark",
    17: "Armoredillo", 18: "Fae", 19: "Virindi", 20: "Wisp", 21: "Knathtead",
    22: "Shadow", 23: "Mattekar", 24: "Mumiyah", 25: "Rabbit", 26: "Sclavus",
    27: "ShallowsShark", 28: "Monouga", 29: "Zefir", 30: "Skeleton",
    31: "Human", 32: "Shreth", 33: "Chittick", 34: "Moarsman",
    35: "OlthoiLarvae", 36: "Slithis", 37: "Deru", 38: "FireElemental",
    39: "Snowman", 41: "Bunny", 42: "LightningElemental", 43: "Grievver",
    44: "Grievver", 45: "Niffis", 46: "Ursuin", 47: "Crystal",
    48: "HollowMinion", 49: "Scarecrow", 50: "Idol", 51: "Empyrean",
    52: "Hopeslayer", 53: "Doll", 54: "Marionette", 55: "Carenzi",
    56: "Siraluun", 57: "AunTumerok", 58: "HeaTumerok", 59: "Sleech",
    60: "AcidElemental", 61: "FrostElemental", 62: "Elemental",
    63: "Statue", 64: "Wall", 65: "AlteredHuman", 66: "Device",
    67: "Harbinger", 68: "DarkSarcophagus", 69: "Chicken", 70: "GotrokLugian",
    71: "Margul", 72: "BleachedRabbit", 73: "NastyRabbit", 74: "GrimacingRabbit",
    75: "Burun", 76: "Target", 77: "Ghost", 78: "Fiun", 79: "Eater",
    80: "Penguin", 81: "Ruschk", 82: "Thrungus", 83: "ViamontianKnight",
    84: "Remoran", 85: "Swarm", 86: "Moar", 87: "EnchantedArms",
    88: "Sleech", 89: "Mukkir", 90: "Merwart", 91: "Food", 92: "ParadoxOlthoi",
    93: "Harvest", 94: "Energy", 95: "Apparition", 96: "Aerbax",
    97: "Touched", 98: "BlightedMoarsman", 99: "GearKnight", 100: "Gurog",
    101: "Anekshay",
}


def _i(v: str) -> int:
    return int(v, 16) if v.lower().startswith("0x") else int(v)


def _prettify(name: str, ct: int) -> str:
    """Turn internal class names into readable labels: strip variant suffixes
    ("-nofall-xp"), split off the creature-type prefix ("zefirdusk" →
    "Zefir Dusk"), and capitalize."""
    n = re.sub(r"-.*$", "", name).strip()
    if not n:
        n = name
    if " " in n:               # already a display name
        return n
    label = CT_LABELS.get(ct, "")
    low = n.lower()
    if label and low.startswith(label.lower()) and len(n) > len(label):
        rest = n[len(label):]
        return f"{label} {rest[:1].upper()}{rest[1:]}"
    if label and low == label.lower():
        return label
    return n[:1].upper() + n[1:]


def main():
    idx = json.loads((REFS / "weenie_index.json").read_text(encoding="utf-8"))
    creatures = [e for e in idx if e.get("t") == 10]
    wd = REFS / "weenies"

    out: dict[int, dict[int, dict]] = {}
    n_ok = n_skip = 0
    for e in creatures:
        f = wd / e["f"]
        if not f.exists():
            n_skip += 1
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = CT_ROW.search(text)
        if not m:
            n_skip += 1
            continue
        ct = int(m.group(1))
        sec = re.search(r"weenie_properties_d_i_d[^;]+;", text)
        if not sec:
            n_skip += 1
            continue
        dids = {}
        for mm in DID_ROW.finditer(sec.group(0)):
            dids[int(mm.group(2))] = _i(mm.group(3))
        setup = dids.get(1)
        if not setup:
            n_skip += 1
            continue
        # Body-part keys — actual per-creature data beats any static map
        bp_keys = []
        bp_sec = re.search(r"weenie_properties_body_part[^;]+;", text)
        if bp_sec:
            bp_keys = sorted({int(m2.group(1)) for m2 in
                              re.finditer(r"\((?:\d+),\s*(\d+),", bp_sec.group(0))})
        def _name_score(n: str) -> int:
            # Prefer clean display names ("Olthoi Soldier") over internal
            # variant names ("boygrubinfestedpraetorian-nofall-xp").
            s = len(n)
            if "-" in n or "_" in n: s += 50
            if any(c.isdigit() for c in n): s += 30
            if " " not in n: s += 20
            if not n[:1].isupper(): s += 20
            return s

        by_setup = out.setdefault(ct, {})
        pretty = _prettify(e["n"], ct)
        if setup not in by_setup:
            ent = {"s": f"0x{setup:08X}", "n": pretty}
            for key, did_type in (("mt", 2), ("st", 3), ("ct4", 4), ("pb", 6),
                                  ("cb", 7), ("pt", 22)):
                v = dids.get(did_type)
                if v:
                    ent[key] = f"0x{v:08X}"
            if bp_keys:
                ent["bp"] = bp_keys
            by_setup[setup] = ent
        else:
            cur = by_setup[setup]
            if _name_score(pretty) < _name_score(cur["n"]):
                cur["n"] = pretty
            if bp_keys and "bp" not in cur:
                cur["bp"] = bp_keys
        n_ok += 1

    # dict-of-dict → dict-of-sorted-list (by name)
    final = {str(ct): sorted(by_setup.values(), key=lambda x: x["n"].lower())
             for ct, by_setup in sorted(out.items())}
    OUT.write_text(json.dumps(final, separators=(",", ":")), encoding="utf-8")

    total_setups = sum(len(v) for v in final.values())
    print(f"scraped {n_ok} creatures ({n_skip} skipped) -> "
          f"{len(final)} creature types, {total_setups} unique setups")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    for ct in list(final)[:6]:
        print(f"  type {ct}: {len(final[ct])} setups, e.g. {final[ct][0]['n']}")


if __name__ == "__main__":
    main()
