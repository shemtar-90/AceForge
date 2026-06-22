#!/usr/bin/env python3
"""
build_weenie_names.py — Regenerate aceforge/web/weenie_names.json

Usage:
    python3 build_weenie_names.py 9_WeenieDefaults.zip   # use local zip
    python3 build_weenie_names.py                         # download from GitHub

Output: aceforge/web/weenie_names.json
"""

import io, json, os, re, sys, time, zipfile
from collections import Counter

try:
    import urllib.request
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

GITHUB_ZIP_URL = (
    "https://codeload.github.com/ACEmulator/ACE-World-16PY/zip/"
    "8bcf8f5f3f71dde51c9ebdbacdaf553dd8308aa5"
)

ITEM_CATS = {
    ('MeleeWeapon',    '*'):            'Melee Weapon',
    ('MissileLauncher','*'):            'Missile Weapon',
    ('Ammunition',     '*'):            'Ammunition',
    ('Caster',         '*'):            'Caster',
    ('Missile',        '*'):            'Missile',
    ('Clothing',       '*'):            'Clothing',
    ('Gem',            'Gem'):          'Gem',
    ('Gem',            'Misc'):         'Gem',
    ('Gem',            'Food'):         'Food',
    ('Generic',        'None'):         'Item',
    ('Generic',        'Misc'):         'Item',
    ('Generic',        'Jewelry'):      'Jewelry',
    ('Generic',        'Armor'):        'Armor',
    ('Generic',        'Gem'):          'Gem',
    ('Generic',        'MissileWeapon'):'Missile Weapon',
    ('Generic',        'Food'):         'Food',
    ('Generic',        'Useless'):      'Item',
    ('CraftTool',      '*'):            'Craft Tool',
    ('Stackable',      'Misc'):         'Stackable',
    ('Stackable',      'PromissoryNote'):'Trade Note',
    ('Stackable',      'Money'):        'Currency',
    ('Stackable',      'CraftAlchemyIntermediate'):    'Craft Material',
    ('Stackable',      'CraftFletchingIntermediate'):  'Craft Material',
    ('Stackable',      'CraftCookingBase'):            'Craft Material',
    ('Stackable',      'Gem'):          'Gem',
    ('Chest',          '*'):            'Container',
    ('Container',      '*'):            'Container',
    ('Key',            '*'):            'Key',
    ('Lockpick',       '*'):            'Lockpick',
    ('Food',           '*'):            'Food',
    ('Healer',         '*'):            'Heal Kit',
    ('ManaStone',      '*'):            'Mana Stone',
    ('SpellComponent', '*'):            'Spell Component',
    ('Book',           '*'):            'Book',
    ('Scroll',         '*'):            'Scroll',
    ('AugmentationDevice','*'):         'Augmentation Gem',
    ('SkillAlterationDevice','*'):      'Skill Gem',
    ('AttributeTransferDevice','*'):    'Attribute Transfer',
    ('PetDevice',      '*'):            'Pet Device',
    ('Coin',           '*'):            'Currency',
}

# Three patterns handle the two SQL formats found in ACE-World:
# A) Single-row: VALUES (wcid, 1, 'Name')
# B) Multi-row with comment: (wcid,   1, 'Name') /* Name */
# C) Multi-row fallback: any (wcid, 1, 'value') inside string properties block
NAME_RE_A = re.compile(r"VALUES\s*\(\s*\d+\s*,\s*1\s*,\s*'((?:[^']|'')*)'", re.IGNORECASE)
NAME_RE_B = re.compile(r"\(\s*\d+\s*,\s*1\s*,\s*'((?:[^']|'')*)'\s*\)\s*/\*\s*Name\s*\*/", re.IGNORECASE)
NAME_RE_C = re.compile(r"\(\s*\d+\s*,\s*1\s*,\s*'((?:[^']|'')*)'", re.IGNORECASE)

HERE    = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "aceforge", "web")
OUT     = os.path.join(WEB_DIR, "weenie_names.json")


def get_cat(top_dir, subtype):
    return ITEM_CATS.get((top_dir, subtype)) or ITEM_CATS.get((top_dir, '*'))


def extract_name(sql):
    m = NAME_RE_A.search(sql)
    if m:
        return m.group(1).replace("''", "'")
    m = NAME_RE_B.search(sql)
    if m:
        return m.group(1).replace("''", "'")
    # Fallback: find string properties block, then look for type=1
    sb = re.search(r'weenie_properties_string.*?VALUES(.*?)(?:INSERT|$)',
                   sql, re.IGNORECASE | re.DOTALL)
    if sb:
        m = NAME_RE_C.search(sb.group(1))
        if m:
            return m.group(1).replace("''", "'")
    return ""


def extract_wcid(path):
    fname = path.split('/')[-1]
    m = re.match(r'^0*(\d+)', fname)
    return int(m.group(1)) if m else None


def parse_zip(zf):
    result = {}
    sql_files = [n for n in zf.namelist() if n.endswith('.sql')]
    print(f"  {len(sql_files):,} SQL files")
    for path in sql_files:
        parts = path.split('/')
        if len(parts) < 4:
            continue
        # Support "9 WeenieDefaults/TopDir/SubDir/file.sql"
        # and "ACE-World-xxx/.../SQL/TopDir/subdir/file.sql"
        if 'SQL' in parts:
            si = parts.index('SQL')
            top_dir = parts[si + 1] if si + 1 < len(parts) else ''
            subtype  = parts[si + 2] if si + 2 < len(parts) else '*'
        else:
            top_dir  = parts[1]
            subtype  = parts[2]
        cat = get_cat(top_dir, subtype)
        if not cat:
            continue
        wcid = extract_wcid(path)
        if not wcid:
            continue
        sql  = zf.read(path).decode('utf-8', errors='replace')
        name = extract_name(sql)
        if name and wcid not in result:
            result[wcid] = [wcid, name, cat]
    return result


def build():
    if len(sys.argv) > 1:
        src = sys.argv[1]
        if not os.path.exists(src):
            print(f"Error: {src} not found"); sys.exit(1)
        print(f"Opening {src} …")
        zf = zipfile.ZipFile(src)
    else:
        if not HAS_URLLIB:
            print("No urllib and no zip path given."); sys.exit(1)
        print("Downloading ACE-World zip (~84 MB) …")
        t0 = time.time()
        req = urllib.request.Request(GITHUB_ZIP_URL,
                                     headers={"User-Agent": "ACEForge/build"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        print(f"  {len(data)/1024/1024:.1f} MB in {time.time()-t0:.1f}s")
        zf = zipfile.ZipFile(io.BytesIO(data))

    print("Parsing …")
    t1 = time.time()
    result = parse_zip(zf)
    print(f"  Parsed in {time.time()-t1:.1f}s → {len(result):,} items")

    # Merge curated items (hand-picked names/categories always win)
    items_path = os.path.join(WEB_DIR, "items.json")
    if os.path.exists(items_path):
        for entry in json.load(open(items_path)):
            wcid, name, cat = entry[0], entry[1], entry[2]
            result[wcid] = [wcid, name, cat]

    final = sorted(result.values(), key=lambda x: x[0])
    with open(OUT, "w") as f:
        json.dump(final, f, separators=(",", ":"))

    size_kb = os.path.getsize(OUT) / 1024
    print(f"\n✓ {len(final):,} entries → {OUT} ({size_kb:.0f} KB)")
    cats = Counter(e[2] for e in final)
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:26s}  {count:5d}")


if __name__ == "__main__":
    build()
