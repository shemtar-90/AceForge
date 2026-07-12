"""Build aceforge/web/creature_setups.json — a map of CreatureType int →
every Setup DID used by base-game creatures of that type.

Scrapes the bundled weenie database (aceforge/references/weenie_index.json +
weenies/*.sql). For each creature type, collects one entry per unique *visual identity*
(Setup + PaletteBase + ClothingBase + PaletteTemplate) so same-Setup variants
with different armor/color schemes are all kept, not collapsed onto the first.
Keeps the companion DIDs (MotionTable, SoundTable, PaletteBase, ClothingBase,
PhysicsEffectTable, CombatTable) so the UI can auto-fill the whole DATA ID
section when a model is picked. Each entry gets a unique key "k" (the select
value): the Setup hex, or Setup hex + ".N" when several variants share a Setup.

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
from typing import Optional

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


def _segment(word: str, vocab: set) -> Optional[list]:
    """Greedy-longest DP segmentation of a compound lowercase name into known
    vocabulary words ("riftquiddity" → ["rift", "quiddity"])."""
    n = len(word)
    best = [None] * (n + 1)
    best[0] = []
    for i in range(1, n + 1):
        # prefer longer words: scan from longest candidate down
        for j in range(max(0, i - 20), i - 2):   # words are >= 3 chars
            if best[j] is not None and word[j:i] in vocab:
                cand = best[j] + [word[j:i]]
                if best[i] is None or len(cand) < len(best[i]):
                    best[i] = cand
    return best[n]


def _prettify(name: str, ct: int, vocab: set) -> str:
    """Turn internal class names into readable labels: strip variant suffixes
    ("-nofall-xp"), split off the creature-type prefix ("zefirdusk" →
    "Zefir Dusk") or segment via the display-name vocabulary
    ("riftquiddity" → "Rift Quiddity"), and capitalize."""
    n = re.sub(r"-.*$", "", name).strip()
    if not n:
        n = name
    if " " in n:               # already a display name
        return n
    label = CT_LABELS.get(ct, "")
    low = n.lower()
    if label and low.startswith(label.lower()) and len(n) > len(label):
        rest = n[len(label):]
        seg = _segment(rest.lower(), vocab)
        if seg and all(len(w) >= 3 for w in seg):
            return label + " " + " ".join(w.capitalize() for w in seg)
        return f"{label} {rest[:1].upper()}{rest[1:]}"
    if label and low == label.lower():
        return label
    seg = _segment(low, vocab)
    if seg and len(seg) >= 2 and all(len(w) >= 3 for w in seg):
        return " ".join(w.capitalize() for w in seg)
    return n[:1].upper() + n[1:]


def main():
    idx = json.loads((REFS / "weenie_index.json").read_text(encoding="utf-8"))
    creatures = [e for e in idx if e.get("t") == 10]

    # Vocabulary of words seen in real display names ("Rift Quiddity" ...) —
    # used to segment compound class names like "riftquiddity".
    vocab = set()
    for e in idx:
        nm = e.get("n") or ""
        if " " in nm:
            for w in re.split(r"[^A-Za-z]+", nm):
                if len(w) >= 3:
                    vocab.add(w.lower())
    for lbl in CT_LABELS.values():
        vocab.add(lbl.lower())
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
        # Int PaletteTemplate (weenie_properties_int type 3) — recolors a shared
        # Setup (e.g. Shadow creatures reuse a human Setup, tinted Black via 39).
        # Part of the visual identity, so scrape it and keep it distinct.
        pal_tmpl = None
        int_sec = re.search(r"weenie_properties_int\b[^;]+;", text)
        if int_sec:
            mi = re.search(r"\(\d+,\s*3,\s*(-?\d+)\)", int_sec.group(0))
            if mi:
                pal_tmpl = int(mi.group(1))
        def _name_score(n: str) -> int:
            # Prefer clean display names ("Olthoi Soldier") over internal
            # variant names ("boygrubinfestedpraetorian-nofall-xp").
            s = len(n)
            if "-" in n or "_" in n: s += 50
            if any(c.isdigit() for c in n): s += 30
            if " " not in n: s += 20
            if not n[:1].isupper(): s += 20
            return s

        # Dedup by *visual identity* — Setup plus the fields that change how the
        # creature actually looks (PaletteBase, ClothingBase, PaletteTemplate DID,
        # and the int PaletteTemplate tint) — so same-Setup variants with
        # different armor/color schemes are all kept, not collapsed onto the
        # first one seen.
        vkey = (setup, dids.get(6), dids.get(7), dids.get(22), pal_tmpl)
        by_key = out.setdefault(ct, {})
        pretty = _prettify(e["n"], ct, vocab)
        if vkey not in by_key:
            ent = {"s": f"0x{setup:08X}", "n": pretty}
            for key, did_type in (("mt", 2), ("st", 3), ("ct4", 4), ("pb", 6),
                                  ("cb", 7), ("pt", 22)):
                v = dids.get(did_type)
                if v:
                    ent[key] = f"0x{v:08X}"
            if pal_tmpl is not None:
                ent["pi"] = pal_tmpl
            if bp_keys:
                ent["bp"] = bp_keys
            by_key[vkey] = ent
        else:
            cur = by_key[vkey]
            if _name_score(pretty) < _name_score(cur["n"]):
                cur["n"] = pretty
            if bp_keys and "bp" not in cur:
                cur["bp"] = bp_keys
        n_ok += 1

    # dict-of-dict → dict-of-sorted-list (by name). Assign each entry a unique
    # key "k" (the UI/generator select value): the Setup hex when it alone is
    # unique within the type, else the Setup hex plus a ".N" suffix. Same-name
    # variants also get a " (N)" label suffix so the dropdown stays legible.
    final = {}
    for ct, by_key in sorted(out.items()):
        ents = sorted(by_key.values(), key=lambda x: x["n"].lower())
        setup_seen: dict[str, int] = {}
        name_seen: dict[str, int] = {}
        for ent in ents:
            s = ent["s"]
            n = setup_seen.get(s, 0)
            setup_seen[s] = n + 1
            ent["k"] = s if n == 0 else f"{s}.{n}"
            base = ent["n"]
            c = name_seen.get(base, 0)
            name_seen[base] = c + 1
            if c:
                ent["n"] = f"{base} ({c + 1})"
        final[str(ct)] = ents
    OUT.write_text(json.dumps(final, separators=(",", ":")), encoding="utf-8")

    total_setups = sum(len(v) for v in final.values())
    print(f"scraped {n_ok} creatures ({n_skip} skipped) -> "
          f"{len(final)} creature types, {total_setups} unique models")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    for ct in list(final)[:6]:
        print(f"  type {ct}: {len(final[ct])} models, e.g. {final[ct][0]['n']}")


if __name__ == "__main__":
    main()
