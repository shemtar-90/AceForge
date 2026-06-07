#!/usr/bin/env python3
"""
ACEForge Icon Category Generator
Run this script once from your ACEForge directory to build icon_cats.js.
It scans your weenie library and reverse-maps each icon DID to a content
category based on which weenie types use it.

Usage: python generate_icon_cats.py
"""

import os, sys, json, glob
from collections import defaultdict, Counter

WEENIE_ROOT = os.path.join(os.path.dirname(__file__), 'aceforge', 'references', 'weenies')
OUT_JS      = os.path.join(os.path.dirname(__file__), 'aceforge', 'web', 'icon_cats.js')
ICON_RE     = b',   8, 0x'

# Map subdir names to UI category labels
SUBDIR_TO_CAT = {
    'MeleeWeapon':'Weapons',  'MissileWeapon':'Weapons', 'Caster':'Weapons',
    'Ammunition': 'Weapons',
    'Armor':      'Armor',
    'Clothing':   'Clothing', 'Jewelry':'Clothing',
    'Gem':        'Gems',     'ManaStone':'Gems',        'Crystal':'Gems',
    'Food':       'Food',
    'Key':        'Keys',
    'SpellComponent':'Stackables', 'TinkeringMaterial':'Stackables',
    'Money':      'Stackables', 'Coin':'Stackables',
    'Container':  'Containers', 'Chest':'Containers',
    'TinkeringTool':'Tools', 'CraftTool':'Tools',
    'Book':       'Scrolls',   'Writable':'Scrolls',
    'Doll':       'Items',     'AttributeTransferDevice':'Items',
    'Deed':       'Items',
    'Foci':       'Foci',
    'LifeStone':  'Structures','Portal':'Structures',
    'Idol':       'Structures','Statue':'Structures',
    'Door':       'Structures','Switch':'Structures',
    'Cottage':    'Structures','Mansion':'Structures',
    'Villa':      'Structures','Apartment':'Structures',
    'HousePortal':'Structures',
}

CREATURE_SUBDIRS = {
    'Creature','AcidElemental','AlteredHuman','AunTumerok','Banderling',
    'BleachedRabbit','Bunny','Burun','Carenzi','Chicken','Chittick',
    'DarkSarcophagus','Deru','Drudge','Elemental','Empyrean',
    'FireElemental','FrostElemental','Ghost','Golem','GotrokLugian',
    'Grievver','GrimacingRabbit','Gromnie','HeaTumerok','HollowMinion',
    'Hopeslayer','Human','Knathtead','LightningElemental','Lugian',
    'Margul','Marionette','Mattekar','Mite','Moarsman','Monouga',
    'Mosswart','NastyRabbit','Niffis','Olthoi','OlthoiLarvae',
    'PhyntosWasp','Rabbit','Rat','Reedshark','Rockslide','Scarecrow',
    'Sclavus','Shadow','ShallowsShark','Shreth','Simulacrum','Siraluun',
    'Skeleton','Slithis','Snowman','Tumerok','Tusker','Undead',
    'Ursuin','Virindi','Wisp','Zefir', 'Cow',
}

NPC_TOPS = {'AdvocateFane','AllegianceBindstone','Vendor'}

CATEGORY_ORDER = [
    'Weapons','Armor','Clothing','Scrolls','Gems','Food',
    'Keys','Tools','Stackables','Containers','Foci',
    'Items','Creatures','NPCs','Structures','Misc',
]

def main():
    if not os.path.isdir(WEENIE_ROOT):
        print(f"ERROR: Weenie library not found at:\n  {WEENIE_ROOT}")
        print("Install the weenie library first via Settings → Content Libraries.")
        sys.exit(1)

    # Collect all SQL file paths
    all_paths = []
    for root, dirs, files in os.walk(WEENIE_ROOT):
        for fn in files:
            if fn.endswith('.sql'):
                all_paths.append(root)
                break  # just need to know dirs exist

    # Walk and categorize
    icon_cats = defaultdict(Counter)
    total = processed = 0

    tops = [d for d in os.listdir(WEENIE_ROOT)
            if os.path.isdir(os.path.join(WEENIE_ROOT, d))]

    for top in tops:
        tp = os.path.join(WEENIE_ROOT, top)
        for sub in os.listdir(tp):
            sp = os.path.join(tp, sub)
            if not os.path.isdir(sp):
                continue
            if sub in SUBDIR_TO_CAT:
                cat = SUBDIR_TO_CAT[sub]
            elif sub in CREATURE_SUBDIRS:
                cat = 'Creatures'
            elif top in NPC_TOPS or 'Npc' in sub:
                cat = 'NPCs'
            else:
                cat = 'Misc'

            for fn in os.listdir(sp):
                if not fn.endswith('.sql'):
                    continue
                fpath = os.path.join(sp, fn)
                total += 1
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()
                except Exception:
                    continue
                idx = data.find(ICON_RE)
                if idx < 0:
                    continue
                s = idx + 9
                e = s
                while e < s + 8 and e < len(data) and chr(data[e]) in '0123456789abcdefABCDEF':
                    e += 1
                try:
                    val = int(data[s:e], 16)
                    icon_cats[hex(val)][cat] += 1
                    processed += 1
                except Exception:
                    continue

        print(f"  [{tops.index(top)+1}/{len(tops)}] {top}... {processed} icons so far")

    print(f"\nScanned {total} weenies, found {processed} with icon DIDs")
    print(f"Unique icon DIDs: {len(icon_cats)}")

    # Build dominant-category result
    result = {}
    cat_counts = Counter()
    for icon_hex, counter in icon_cats.items():
        dominant = counter.most_common(1)[0][0]
        result[icon_hex] = dominant
        cat_counts[dominant] += 1

    print("\nCategory breakdown:")
    for cat in CATEGORY_ORDER:
        if cat in cat_counts:
            print(f"  {cat:<14} {cat_counts[cat]:>5}")

    # Write icon_cats.js
    entries = ','.join(f'"{k}":"{v}"' for k, v in sorted(result.items()))
    js  = f"// Generated by generate_icon_cats.py — {len(result)} icon DIDs categorized\n"
    js += f"const ICON_CATS={{{entries}}};\n"
    js += f"const ICON_CAT_LIST={json.dumps(CATEGORY_ORDER)};\n"

    with open(OUT_JS, 'w') as f:
        f.write(js)

    kb = os.path.getsize(OUT_JS) / 1024
    print(f"\n✓ Written: {OUT_JS} ({kb:.1f} KB)")
    print("Restart ACEForge to load the new category tabs in the icon picker.")

if __name__ == '__main__':
    main()
