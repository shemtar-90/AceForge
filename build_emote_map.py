"""
build_emote_map.py — Auto-builds confirmed emote type/category maps
from your ACE world database by cross-referencing known weenie behaviors.

Usage:
    python build_emote_map.py --host localhost --port 3306 \
        --user root --password yourpass --db ace_world

Outputs: confirmed_emote_maps.txt  (paste into emote_parser.py)
"""

import argparse, sys

try:
    import mysql.connector
except ImportError:
    print("Install: pip install mysql-connector-python")
    sys.exit(1)

# ─── Known type names from our confirmed tests so far ────────────────────────
KNOWN_ACTION_TYPES = {
    10: 'Tell',
    21: 'InqQuest',
    22: 'StampQuest',
    23: 'StartEvent',
    24: 'StopEvent',
    49: 'AwardLevelProportionalXP',
    51: 'InqEvent',
    67: 'Goto',
    74: 'TakeItems',
    76: 'InqOwnsItems',
}

KNOWN_CATEGORIES = {
    7:  'Use',
    12: 'QuestSuccess',
    13: 'QuestFailure',
    22: 'TestSuccess',
    23: 'TestFailure',
    27: 'EventSuccess',
    28: 'EventFailure',
    32: 'GotoSet',
    38: 'ReceiveTalkDirect',
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host',     default='localhost')
    ap.add_argument('--port',     type=int, default=3306)
    ap.add_argument('--user',     default='root')
    ap.add_argument('--password', default='')
    ap.add_argument('--db',       default='ace_world')
    args = ap.parse_args()

    print(f"Connecting to {args.host}:{args.port}/{args.db}...")
    conn = mysql.connector.connect(
        host=args.host, port=args.port,
        user=args.user, password=args.password,
        database=args.db)
    cur = conn.cursor()

    # ── Action types ──────────────────────────────────────────────────────────
    cur.execute("""
        SELECT a.type, COUNT(*) AS uses,
               GROUP_CONCAT(DISTINCT w.class_Name
                   ORDER BY uses DESC SEPARATOR ' | ')
        FROM weenie_properties_emote_action a
        JOIN weenie_properties_emote e ON a.emote_Id = e.id
        JOIN weenie w ON e.object_Id = w.class_Id
        GROUP BY a.type
        ORDER BY a.type
    """)
    action_rows = cur.fetchall()

    # ── Categories ────────────────────────────────────────────────────────────
    cur.execute("""
        SELECT e.category, COUNT(*) AS uses,
               GROUP_CONCAT(DISTINCT w.class_Name
                   ORDER BY uses DESC SEPARATOR ' | ')
        FROM weenie_properties_emote e
        JOIN weenie w ON e.object_Id = w.class_Id
        GROUP BY e.category
        ORDER BY e.category
    """)
    cat_rows = cur.fetchall()
    conn.close()

    lines = []
    lines.append("=" * 70)
    lines.append("ACTION TYPE MAP  (paste into ACTION_TYPE_MAP in emote_parser.py)")
    lines.append("=" * 70)
    lines.append("ACTION_TYPE_MAP: Dict[str, int] = {")

    for type_id, uses, examples in action_rows:
        known = KNOWN_ACTION_TYPES.get(type_id)
        ex_short = (examples or '')[:60]
        if known:
            lines.append(f"    '{known}': {type_id},  # {uses:,} uses — CONFIRMED")
        else:
            lines.append(f"    # UNKNOWN_{type_id}: {type_id},  # {uses:,} uses — examples: {ex_short}")

    lines.append("}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("CATEGORY MAP  (paste into CATEGORY_MAP in emote_parser.py)")
    lines.append("=" * 70)
    lines.append("CATEGORY_MAP: Dict[str, int] = {")

    for cat_id, uses, examples in cat_rows:
        known = KNOWN_CATEGORIES.get(cat_id)
        ex_short = (examples or '')[:60]
        if known:
            lines.append(f"    '{known}': {cat_id},  # {uses:,} uses — CONFIRMED")
        else:
            lines.append(f"    # UNKNOWN_{cat_id}: {cat_id},  # {uses:,} uses — examples: {ex_short}")

    lines.append("}")

    out = '\n'.join(lines)
    print(out)

    with open('confirmed_emote_maps.txt', 'w') as f:
        f.write(out)
    print(f"\nSaved to confirmed_emote_maps.txt")
    print(f"Identified {len(KNOWN_ACTION_TYPES)} / {len(action_rows)} action types")
    print(f"Identified {len(KNOWN_CATEGORIES)} / {len(cat_rows)} categories")

if __name__ == '__main__':
    main()
