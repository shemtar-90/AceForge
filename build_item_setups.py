"""Build aceforge/web/item_setups.json — a map of WeenieType int → every
distinct visual model used by base-game *items* of that type (armor/clothing,
weapons, portals, books, casters, gems, food, scrolls, chests, keys, doors …).

This is the item-world companion to build_creature_setups.py. Where creatures
key their model catalog off CreatureType, items key off WeenieType, and within
a type the list is further tagged with a *subtype* so the editor can show only
the relevant models (e.g. only Sword models when editing a sword, only same-
coverage models when editing a cuirass) instead of every item of the type.

For each item we scrape the model DIDs:
  1  Setup            2  MotionTable      3  SoundTable
  6  PaletteBase      7  ClothingBase     8  Icon
 22  PhysicsEffectTable
and, when relevant, the int property that identifies the subtype (WeaponSkill
for weapons, ValidLocations for armor, DamageType for casters) plus the int
PaletteTemplate tint (Int 3). Entries are deduped by *visual identity* (Setup +
ClothingBase + PaletteBase + PaletteTemplate) so same-Setup color/armor variants
are all kept, not collapsed onto the first one seen.

Output format:
{ "<wtype_int>": [ {"s":"0x02000723","i":"0x060026B7","n":"Isparian Mace",
                    "st":"0x20000014","pb":"0x04000BEF","cb":"0x100003C7",
                    "pe":"0x3400002B","sub":5,"k":"0x02000723"}, ... ], ... }

Run from the repo root: python build_item_setups.py
"""
import json
import re
from pathlib import Path

REFS = Path("aceforge/references")
OUT = Path("aceforge/web/item_setups.json")

VAL = r"(0x[0-9A-Fa-f]+|\d+)"
DID_ROW = re.compile(r"\((\d+),\s*(\d+),\s*" + VAL + r"\)")
INT_ROW = re.compile(r"\((\d+),\s*(\d+),\s*(-?\d+)\)")

# Every WeenieType is eligible for an item-model catalog EXCEPT the creature-like
# ones (Creature 10, Vendor 12, Pet 76, CombatPet 77) — those carry a
# CreatureType and are covered by build_creature_setups.py's catalog instead.
# We scrape "the entire list": any non-creature type that has ≥1 Setup model
# gets a catalog, so the editor can offer a model dropdown for it.
CREATURE_LIKE = {10, 12, 76, 77}

# Which int property (weenie_properties_int key) subdivides each type into the
# "relevant models" the editor filters on. Absent → the type is one flat list.
#   48 WeaponSkill · 9 ValidLocations (armor coverage) · 45 DamageType (element)
SUBTYPE_INT = {6: 48, 3: 48, 4: 48, 2: 9, 35: 45}

# Shields are inconsistently typed in the base data (Generic, Armor, type 40 …),
# so they'd otherwise scatter across those catalogs and a Generic-typed shield
# would offer all 800+ generic models. Detect them by CombatUse=Shield (Int 51
# == 4) or the Shield ValidLocations bit, and collect them under one synthetic
# "shield" catalog key instead of their weenie type.
COMBATUSE_INT = 51
COMBATUSE_SHIELD = 4
VALIDLOC_SHIELD_BIT = 0x200000  # SHIELD_LOC


def _i(v: str) -> int:
    return int(v, 16) if v.lower().startswith("0x") else int(v)


def _prettify(name: str) -> str:
    """Items usually already carry a clean display name ("Isparian Mace").
    Strip trailing variant suffixes ("-nofall-xp") and tidy casing when the
    name is a bare internal token."""
    n = re.sub(r"-.*$", "", name or "").strip()
    if not n:
        n = name or ""
    if " " in n:
        return n
    return n[:1].upper() + n[1:]


def _name_score(n: str) -> int:
    # Prefer clean display names over internal variant tokens.
    s = len(n)
    if "-" in n or "_" in n: s += 50
    if any(c.isdigit() for c in n): s += 30
    if " " not in n: s += 20
    if not n[:1].isupper(): s += 20
    return s


def main():
    idx = json.loads((REFS / "weenie_index.json").read_text(encoding="utf-8"))
    wd = REFS / "weenies"

    out: dict = {}
    n_ok = n_skip = 0
    # Pass 1: collect one record per weenie and tally, per Setup, how many
    # weenies of each type use it. A Setup shared by (say) 40 weapons and 1 stray
    # generic weenie should be categorized as a weapon, not leak into Generic.
    records = []                 # (setup, t, is_shield, sub, pal_tmpl, dids, name)
    usage: dict[int, dict[int, int]] = {}   # setup -> {weenie_type: count}
    for e in idx:
        t = e.get("t")
        if t is None or t in CREATURE_LIKE:
            continue
        f = wd / e["f"]
        if not f.exists():
            n_skip += 1
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
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

        int_props = {}
        int_sec = re.search(r"weenie_properties_int\b[^;]+;", text)
        if int_sec:
            for mi in INT_ROW.finditer(int_sec.group(0)):
                int_props[int(mi.group(2))] = int(mi.group(3))
        pal_tmpl = int_props.get(3)

        # Shields → the synthetic "shield" catalog, regardless of weenie type.
        is_shield = (int_props.get(COMBATUSE_INT) == COMBATUSE_SHIELD
                     or (int_props.get(9, 0) & VALIDLOC_SHIELD_BIT))
        sub = None
        if not is_shield:
            sub_key = SUBTYPE_INT.get(t)
            if sub_key is not None:
                sub = int_props.get(sub_key)
            usage.setdefault(setup, {})
            usage[setup][t] = usage[setup].get(t, 0) + 1

        records.append((setup, t, is_shield, sub, pal_tmpl, dids, e["n"]))
        n_ok += 1

    # Each Setup's dominant weenie type = the category it belongs to. Ties break
    # toward the lower type number for determinism.
    primary = {s: max(c.items(), key=lambda kv: (kv[1], -kv[0]))[0]
               for s, c in usage.items()}

    # Pass 2: build the buckets. Shields go to 'shield'; every other record only
    # populates a bucket when its weenie type is that Setup's dominant type — so
    # cross-type leakage (a weapon model appearing in the Generic/decoration
    # list, etc.) is eliminated.
    for setup, t, is_shield, sub, pal_tmpl, dids, name in records:
        if is_shield:
            bucket_key, sub2 = "shield", None
        else:
            if primary.get(setup) != t:
                continue
            bucket_key, sub2 = t, sub

        vkey = (setup, dids.get(7), dids.get(6), dids.get(22), pal_tmpl, sub2)
        by_key = out.setdefault(bucket_key, {})
        pretty = _prettify(name)
        if vkey not in by_key:
            ent = {"s": f"0x{setup:08X}", "n": pretty}
            for key, did_type in (("i", 8), ("mt", 2), ("st", 3),
                                  ("pb", 6), ("cb", 7), ("pe", 22)):
                v = dids.get(did_type)
                if v:
                    ent[key] = f"0x{v:08X}"
            if pal_tmpl is not None:
                ent["pi"] = pal_tmpl
            if sub2 is not None:
                ent["sub"] = sub2
            by_key[vkey] = ent
        else:
            cur = by_key[vkey]
            if _name_score(pretty) < _name_score(cur["n"]):
                cur["n"] = pretty

    # dict-of-dict → dict-of-sorted-list. Assign each entry a unique select key
    # "k": the Setup hex when unique in its type, else Setup hex + ".N". Same-name
    # variants get a " (N)" label so the dropdown stays legible.
    final = {}
    for t, by_key in sorted(out.items(), key=lambda kv: str(kv[0])):
        ents = sorted(by_key.values(),
                      key=lambda x: (x.get("sub") if x.get("sub") is not None else 0,
                                     x["n"].lower()))
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
        final[str(t)] = ents
    OUT.write_text(json.dumps(final, separators=(",", ":")), encoding="utf-8")

    total = sum(len(v) for v in final.values())
    print(f"scraped {n_ok} items ({n_skip} skipped) -> "
          f"{len(final)} weenie types, {total} unique models")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    names = {1: "Generic", 2: "Armor", 3: "MissileLauncher", 4: "Missile",
             6: "Melee", 7: "Portal", 8: "Book", 35: "Caster", 38: "Gem",
             18: "Food", 34: "Scroll", 20: "Chest"}
    for t in sorted(final, key=lambda x: -len(final[x]))[:12]:
        label = "Shield" if t == "shield" else names.get(int(t), "?")
        print(f"  type {t} ({label}): {len(final[t])} models, "
              f"e.g. {final[t][0]['n']}")
    if "shield" in final:
        print(f"  shield catalog: {len(final['shield'])} models")


if __name__ == "__main__":
    main()
