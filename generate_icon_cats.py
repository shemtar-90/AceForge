#!/usr/bin/env python3
"""
ACEForge Icon Category Generator (DAT-authoritative rewrite)

Builds the hierarchical ICON_CATEGORY_MAP used by the icon picker in
aceforge/web/index.html. Categories are derived from AUTHORITATIVE sources
instead of DID-range guesswork:

  * Spell icons  -> parsed directly from the client_portal.dat SpellTable
                    (0x0E00000E), sub-tiered by magic school.
  * Everything else -> the weenie library (references/weenies), keyed on each
                    weenie's real ItemType property, then sub-tiered by name
                    patterns / weenie-type directory.

This fixes the old bug where ~480 assorted item icons were bulk-dumped into a
bogus "Spells/Spell" bucket.

Usage:
    python generate_icon_cats.py            # rewrite the map in index.html
    python generate_icon_cats.py --dry-run  # print the category tree only
"""

import os, re, sys, json, struct, collections

HERE        = os.path.dirname(os.path.abspath(__file__))
WEENIE_ROOT = os.path.join(HERE, 'aceforge', 'references', 'weenies')
INDEX_HTML  = os.path.join(HERE, 'aceforge', 'web', 'index.html')

ITYPE_RE = re.compile(rb'/\* ItemType - (\w+) \*/')
ICON_RE  = re.compile(rb'\(\s*\d+,\s*8,\s*0x([0-9A-Fa-f]{8})\)\s*/\* Icon')
NAME_RE  = re.compile(rb"\(\s*\d+,\s*1,\s*'([^']*)'\)\s*/\* Name")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Spell icons from the DAT SpellTable
# ─────────────────────────────────────────────────────────────────────────────
SCHOOL = {1: 'War Magic', 2: 'Life Magic', 3: 'Creature Enchantment',
          4: 'Item Enchantment', 5: 'Void Magic', 6: 'Void Magic', 7: 'Void Magic'}


def _find_portal_dat():
    cfg = os.path.join(os.environ.get('APPDATA', ''), 'ACEForge', 'config.json')
    if os.path.isfile(cfg):
        try:
            p = json.load(open(cfg)).get('portal_dat')
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass
    for c in (r"C:\Turbine\Asheron's Call\client_portal.dat",):
        if os.path.isfile(c):
            return c
    return None


def load_spell_icons():
    """Return {icon_hex_upper: 'Spells/<School>'} parsed from the DAT.

    Anchored on each known spell name (from spells.json) so we never have to
    parse the fragile variable-length spell tail. Returns {} if the DAT or
    spells.json is unavailable (the weenie pass still produces a full map)."""
    dat = _find_portal_dat()
    spells_json = os.path.join(HERE, 'aceforge', 'web', 'spells.json')
    if not dat or not os.path.isfile(spells_json):
        print("  (SpellTable skipped - portal.dat or spells.json not found)")
        return {}
    sys.path.insert(0, os.path.join(HERE, 'aceforge'))
    try:
        from dat_loader import DatDatabase
    except Exception as e:
        print(f"  (SpellTable skipped - dat_loader import failed: {e})")
        return {}

    blob = DatDatabase(dat).read_file(0x0E00000E)
    if not blob:
        print("  (SpellTable skipped - 0x0E00000E not in DAT)")
        return {}

    def nibswap(b): return bytes(((c >> 4) | (c << 4)) & 0xFF for c in b)
    def align4(o):  return (o + 3) & ~3

    def rstr(o):
        ln, = struct.unpack_from('<H', blob, o); o += 2
        return align4(o + ln)  # we only need the offset past the string

    spells = json.load(open(spells_json, encoding='utf-8'))
    out, seen = {}, set()
    for sid, name in spells:
        anchor = (struct.pack('<I', sid) + struct.pack('<H', len(name))
                  + nibswap(name.encode('latin-1', 'replace')))
        i = blob.find(anchor)
        if i < 0:
            continue
        o = rstr(i + 4)          # skip key + Name
        o = rstr(o)              # skip Desc
        school, icon = struct.unpack_from('<II', blob, o)
        if (icon >> 24) != 0x06:
            continue
        did = f"{icon:08X}"
        seen.add(did)
        out.setdefault(did, 'Spells/' + SCHOOL.get(school, 'Other'))
    print(f"  SpellTable: {len(seen)} unique spell icons")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 2. Weenie-library categorisation
# ─────────────────────────────────────────────────────────────────────────────

# Armor set names (checked longest-first). Everything unmatched -> Armor/Other.
ARMOR_SETS = [
    'Alduressa', 'Amuli', 'Celdon', 'Chainmail', 'Chiran', 'Covenant',
    'Diforsa', 'Koujia', 'Leather', 'Lorica', 'Nariyad', "O-Yoroi",
    'Platemail', 'Scalemail', 'Yoroi', 'Olthoi', 'Academy', 'Empyrean',
    'Haebrean', 'Knorr', 'Noble', 'Pathwarden', 'Prismatic', 'Relic',
    'Shadow', "Shou-Jen", 'Soldier', 'Explorer', 'Faction', 'Tenassa',
    'Gelidite', 'Dusk', 'Studded',
]

# Ammunition (checked before the weapon-class tables).
AMMO_WORDS = ['Arrow', 'Quarrel', 'Bolt', 'Dart', 'Spike', 'Spines',
              'Djarid', 'Pebble', 'Shot', 'Ball', 'Minnow']

# Melee/missile weapon classes by keyword.
WEAPON_CLASS = [
    ('Bow', ['Bow', 'Longbow', 'Shortbow', 'Yumi', 'Yag']),
    ('Crossbow', ['Crossbow', 'Arbalest', 'Slingbow']),
    ('Atlatl', ['Atlatl']),
    ('Thrown', ['Javelin', 'Shuriken', 'Shouken', 'Throwing', 'Star', 'Stars',
                'Discus', 'Chakram']),
    ('Sword', ['Sword', 'Rapier', 'Scimitar', 'Sabre', 'Katana', 'Ken',
               'Espadon', 'Nabut', 'Takuba', 'Schlager', 'Baselard', 'Tachi',
               'Shamshir', 'Shashqa', 'Kaskara', 'Simi', 'Yaoji', 'Falchion',
               'Broadsword', 'Longsword', 'Dagabi']),
    ('Axe', ['Axe', 'Hatchet', 'Cleaver', 'Ono', 'Masammiu', 'Basher',
             'Budiaq', 'Dabus']),
    ('Mace', ['Mace', 'Club', 'Hammer', 'Morning Star', 'Flail', 'Mattekar',
              'Cudgel', 'Tetsubo', 'Nekode', 'Ta Ming', 'Jitte', 'Nabot',
              'War Hammer', 'Spiked Club']),
    ('Dagger', ['Dagger', 'Knife', 'Poniard', 'Stiletto', 'Jambiya', 'Tanto',
                'Dirk', 'Khanjar', 'Kris', 'Kukri', 'Bunny']),
    ('Spear', ['Spear', 'Lance', 'Trident', 'Naginata', 'Yari', 'Corsesca',
               'Partizan', 'Halberd', 'Nariyyah', 'Glaive', 'Megalixir']),
    ('Staff', ['Staff', 'Quarterstaff', 'Nunchaku', 'Tofun', 'Kasrullah']),
    ('Unarmed', ['Cestus', 'Katar', 'Claw', 'Knuckle', 'Push Dagger']),
]

# Armor slot fallback (used when no set name matches).
ARMOR_SLOT = [
    ('Head', ['Helm', 'Helmet', 'Basinet', 'Coif', 'Mask', 'Cowl', 'Headdress',
              'Crown', 'Circlet', 'Kabuton', 'Oculus', 'Heaume', 'Fez']),
    ('Shield', ['Shield', 'Aegis', 'Buckler', 'Kite', 'Tower', 'Targe']),
    ('Chest', ['Coat', 'Breastplate', 'Cuirass', 'Hauberk', 'Shirt', 'Robe',
               'Vest', 'Chestplate', 'Corselet', 'Kabozu']),
    ('Legs', ['Leggings', 'Girth', 'Tasset', 'Greaves', 'Legs', 'Pants',
              'Cuisses', 'Chausses', 'Kilt', 'Skirt']),
    ('Hands', ['Gauntlets', 'Gloves', 'Mitten', 'Cesti']),
    ('Feet', ['Boots', 'Sollerets', 'Sabatons', 'Shoes', 'Sandals', 'Greaves']),
    ('Arms', ['Pauldron', 'Spaulder', 'Bracer', 'Vambrace', 'Rerebrace']),
]

CASTER_CLASS = [
    ('Wand', ['Wand', 'Baton', 'Rod']),
    ('Staff', ['Staff']),
    ('Sceptre', ['Sceptre', 'Scepter']),
    ('Orb', ['Orb']),
]

JEWELRY_CLASS = [
    ('Ring', ['Ring']),
    ('Necklace', ['Necklace', 'Amulet', 'Pendant', 'Medallion', 'Gorget', 'Collar']),
    ('Bracelet', ['Bracelet', 'Bracer', 'Armband']),
    ('Trinket', []),  # fallback
]

CLOTHING_CLASS = [
    ('Headwear', ['Hat', 'Cap', 'Cowl', 'Hood', 'Crown', 'Helm', 'Turban',
                  'Coif', 'Beret', 'Circlet', 'Fez', 'Bandana']),
    ('Cloak', ['Cloak', 'Cape', 'Mantle', 'Shroud']),
    ('Shirt', ['Shirt', 'Tunic', 'Doublet', 'Blouse', 'Vest', 'Jerkin',
               'Smock', 'Shift', 'Chemise', 'Toga', 'Robe', 'Gown', 'Qafiya']),
    ('Pants', ['Pants', 'Breeches', 'Trousers', 'Leggings', 'Kilt', 'Skirt',
               'Loincloth', 'Hakama']),
    ('Footwear', ['Shoes', 'Boots', 'Sandals', 'Slippers', 'Sabatons']),
    ('Gloves', ['Gloves', 'Gauntlets', 'Mittens']),
]

FOOD_CLASS = [
    ('Drink', ['Ale', 'Wine', 'Beer', 'Water', 'Juice', 'Milk', 'Grog',
               'Cider', 'Mead', 'Tea', 'Draught', 'Brew', 'Elixir', 'Flask']),
    ('Potion', ['Potion', 'Philtre', 'Tonic', 'Serum']),
    ('Food', []),  # fallback
]

# Misc/Generic weenies routed by their weenie-type directory.
DIR_TO_CAT = {
    'House': 'Housing/Decoration', 'HousePortal': 'Housing/Portal',
    'Hook': 'Housing/Hook', 'Hooker': 'Housing/Hook', 'Storage': 'Housing/Storage',
    'SlumLord': 'Housing/Decoration',
    'Door': 'Structures/Door', 'Switch': 'Structures/Switch',
    'HotSpot': 'Structures/Hotspot', 'PressurePlate': 'Structures/Hotspot',
    'LifeStone': 'Structures/Lifestone', 'Portal': 'Portals',
    'LightSource': 'Structures/Light', 'Machine': 'Structures/Machine',
    'Healer': 'Consumables/Healing', 'Lockpick': 'Tools/Lockpick',
    'CraftTool': 'Tools/Craft', 'SkillAlterationDevice': 'Consumables/Utility',
    'AttributeTransferDevice': 'Consumables/Utility',
    'Book': 'Books & Scrolls/Book', 'Scroll': 'Books & Scrolls/Scroll',
    'Deed': 'Quest/Deed', 'Corpse': 'Creatures/Corpse',
    'ProjectileSpell': 'Spells/Projectile', 'Channel': 'Misc/Channel',
    'PKModifier': 'Consumables/Utility', 'GamePiece': 'Misc/Game',
}

CREATURE_NPC_DIRS = {'Vendor', 'Healer'}


def has(name, words):
    low = name.lower()
    return any(w.lower() in low for w in words)


def sub_by_table(name, table, default):
    for label, words in table:
        if words and has(name, words):
            return label
    return default


def categorize(itype, name, top):
    """Return a 'Primary/Sub' category string for one weenie.

    `itype` is the authoritative ItemType *name* string parsed from the SQL
    comment (e.g. 'Armor', 'MeleeWeapon', 'CraftFletchingIntermediate'), not a
    numeric flag - the high-bit flag values are ambiguous so we route by name.
    """
    # Ammunition (arrows/quarrels/etc) - route before the weapon tables ---
    if top == 'Ammunition' or has(name, AMMO_WORDS):
        if itype in ('MeleeWeapon', 'MissileWeapon') or top in ('Ammunition', 'Missile'):
            return 'Weapons/Missile/Ammunition'

    # Weapons ------------------------------------------------------------
    if itype == 'MeleeWeapon':
        return 'Weapons/Melee/' + sub_by_table(name, WEAPON_CLASS, 'Other')
    if itype == 'MissileWeapon':
        return 'Weapons/Missile/' + sub_by_table(name, WEAPON_CLASS, 'Missile')
    if itype == 'Caster':
        return 'Weapons/Caster/' + sub_by_table(name, CASTER_CLASS, 'Wand')

    # Armor / Clothing / Jewelry ----------------------------------------
    if itype == 'Armor':
        for s in ARMOR_SETS:
            if s.lower() in name.lower():
                return 'Armor/Sets/' + s
        return 'Armor/Pieces/' + sub_by_table(name, ARMOR_SLOT, 'Other')
    if itype == 'Clothing':
        return 'Clothing/' + sub_by_table(name, CLOTHING_CLASS, 'Other')
    if itype == 'Jewelry':
        return 'Jewelry/' + sub_by_table(name, JEWELRY_CLASS, 'Trinket')

    # Consumables / crafting --------------------------------------------
    if itype == 'Food':
        return 'Food/' + sub_by_table(name, FOOD_CLASS, 'Food')
    if itype == 'Gem':
        return 'Gems/Gem'
    if itype == 'ManaStone':
        return 'Gems/Mana Stone'
    if itype == 'SpellComponents':
        return 'Spell Components/Component'
    if itype == 'CraftCookingBase':
        return 'Crafting/Cooking'
    if itype in ('CraftAlchemyBase', 'CraftAlchemyIntermediate'):
        return 'Crafting/Alchemy'
    if itype in ('CraftFletchingBase', 'CraftFletchingIntermediate'):
        return 'Crafting/Fletching'
    if itype == 'TinkeringMaterial':
        return 'Crafting/Salvage'
    if itype == 'TinkeringTool':
        return 'Tools/Craft'

    # Currency / keys / services ----------------------------------------
    if itype == 'Money':
        return 'Currency/Coin'
    if itype == 'PromissoryNote':
        return 'Currency/Promissory'
    if itype == 'Key':
        return 'Keys/Key'
    if itype == 'Service':
        return 'Services/Service'
    if itype == 'Portal':
        return 'Portals'
    if itype == 'LifeStone':
        return 'Structures/Lifestone'
    if itype == 'Container':
        return 'Containers/Chest' if top == 'Chest' else 'Containers/Container'
    if itype == 'Writable':
        return 'Books & Scrolls/Scroll' if top == 'Scroll' else 'Books & Scrolls/Book'

    # Creatures / NPCs ---------------------------------------------------
    if itype == 'Creature':
        return 'NPCs/Vendor' if top in CREATURE_NPC_DIRS else 'Creatures/Creature'

    # Fallback: route by weenie-type directory --------------------------
    if top in DIR_TO_CAT:
        return DIR_TO_CAT[top]
    if top == 'Creature':
        return 'Creatures/Creature'
    if top == 'Vendor':
        return 'NPCs/Vendor'

    # Name-based rescue for the Generic grab-bag ------------------------
    if has(name, ['Cottage', 'Villa', 'Mansion', 'Apartment', 'Settlement',
                  'Housing', 'Dwelling']):
        return 'Housing/Deed'
    if has(name, ['Ingot', 'Nugget', 'Bar of', 'Ore']):
        return 'Crafting/Trade Goods'
    if has(name, ['Generator', ' Gen', 'Spawner']):
        return 'Misc/Generator'
    if has(name, ['Token', 'Coupon', 'Voucher']):
        return 'Misc/Token'
    return 'Misc/Other'


def load_weenie_cats():
    """Return {icon_hex: Counter(category -> weenie count)}."""
    icon_cats = collections.defaultdict(collections.Counter)
    scanned = 0
    for dp, _, fs in os.walk(WEENIE_ROOT):
        for fn in fs:
            if not fn.endswith('.sql'):
                continue
            top = os.path.relpath(os.path.join(dp, fn), WEENIE_ROOT
                                  ).replace(os.sep, '/').split('/')[0]
            with open(os.path.join(dp, fn), 'rb') as f:
                d = f.read(6000)
            ic = ICON_RE.search(d)
            if not ic:
                continue
            it = ITYPE_RE.search(d)
            nm = NAME_RE.search(d)
            itype = it.group(1).decode('ascii') if it else ''
            name = nm.group(1).decode('latin-1') if nm else ''
            did = ic.group(1).decode().upper()
            icon_cats[did][categorize(itype, name, top)] += 1
            scanned += 1
    print(f"  Weenie library: {scanned} icon references, "
          f"{len(icon_cats)} unique icons")
    return icon_cats


# ─────────────────────────────────────────────────────────────────────────────
# 3. Merge + emit
# ─────────────────────────────────────────────────────────────────────────────
def build_map():
    print("Building icon category map...")
    spell_icons = load_spell_icons()
    icon_cats = load_weenie_cats()

    resolved = {}
    for did, counter in icon_cats.items():
        resolved[did] = counter.most_common(1)[0][0]
    # Spell icons are authoritative for their DIDs (override weenie guesses).
    for did, cat in spell_icons.items():
        resolved[did] = cat

    cat_map = collections.defaultdict(list)
    for did, cat in resolved.items():
        cat_map[cat].append(did)
    return {k: sorted(v) for k, v in sorted(cat_map.items())}


def print_tree(cat_map):
    tree = collections.defaultdict(list)
    for cat, dids in cat_map.items():
        top = cat.split('/')[0]
        tree[top].append((cat, len(dids)))
    total = sum(len(v) for v in cat_map.values())
    print(f"\n{total} icons across {len(cat_map)} categories:\n")
    for top in sorted(tree):
        n = sum(c for _, c in tree[top])
        print(f"  {top}  ({n})")
        for cat, c in sorted(tree[top]):
            sub = cat.split('/', 1)[1] if '/' in cat else '(root)'
            print(f"      {sub:<28} {c:>4}")


def inject(cat_map):
    src = open(INDEX_HTML, encoding='utf-8').read()
    payload = json.dumps(cat_map, separators=(',', ':'))
    new_line = f"const ICON_CATEGORY_MAP = {payload};"
    pat = re.compile(r'const ICON_CATEGORY_MAP = \{.*?\};', re.DOTALL)
    if not pat.search(src):
        print("ERROR: could not find ICON_CATEGORY_MAP in index.html")
        sys.exit(1)
    src = pat.sub(lambda m: new_line, src, count=1)
    open(INDEX_HTML, 'w', encoding='utf-8').write(src)
    print(f"\nInjected new map into {INDEX_HTML} ({len(payload)/1024:.1f} KB)")


def main():
    cat_map = build_map()
    print_tree(cat_map)
    if '--dry-run' in sys.argv:
        print("\n(dry run - index.html not modified)")
    else:
        inject(cat_map)


if __name__ == '__main__':
    main()
