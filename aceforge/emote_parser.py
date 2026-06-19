"""
emote_parser.py — Phase 1 (revised)
WeenieFab compact emote format → ACEmulator SQL (ACE-World-16PY schema).

Branching model (confirmed from WeenieFab SQL output):
  InqQuest / InqQuestSolves with QuestSuccess / QuestFailure branches produce
  SEPARATE emote rows with category=QuestSuccess (12) or QuestFailure (13),
  with quest=<questName> matching the InqQuest's message field.
  ACE resolves these automatically — no Goto needed for branching.

SQL format: uses LAST_INSERT_ID() / @parent_id pattern, no explicit id column.
"""

from __future__ import annotations
import re

# ── Motion name → integer ID map (for YAML import) ───────────────────────────
# Covers all motion values from the ACEForge motion lists
MOTION_NAME_TO_ID: dict[str, int] = {
    # Idle / NPC
    "Ready":             1090519043,
    "HandCombat":        2147483708,
    "NonCombat":         2147483709,
    "ChestBeat":         268435533,
    "Twitch1":           268435537,
    "Twitch2":           268435538,
    "Twitch3":           268435539,
    "Twitch4":           268435540,
    # Player emotes
    "ShakeFist":         318767225,
    "Beckon":            318767226,
    "BeSeeingYou":       318767227,
    "BlowKiss":          318767228,
    "BowDeep":           318767229,
    "ClapHands":         318767230,
    "Cry":               318767231,
    "Laugh":             318767232,
    "MimeEat":           318767233,
    "MimeDrink":         318767234,
    "Nod":               318767235,
    "Point":             318767236,
    "ShakeHead":         318767237,
    "Shrug":             318767238,
    "Akimbo":            318767240,
    "HeartyLaugh":       318767241,
    "Salute":            318767242,
    "ScratchHead":       318767243,
    "SmackHead":         318767244,
    "TapFoot":           318767245,
    "WaveHigh":          318767246,
    "WaveLow":           318767247,
    "YawnStretch":       318767248,
    "Cringe":            318767249,
    "Kneel":             318767250,
    "Plead":             318767251,
    "Shiver":            318767252,
    "Shoo":              318767253,
    "Slouch":            318767254,
    "Spit":              318767255,
    "Surrender":         318767256,
    "Woah":              318767257,
    "Winded":            318767258,
    "YMCA":              301990043,
    # Monster
    "SpecialAttack1":    268435661,
    "SpecialAttack2":    268435662,
    "SpecialAttack3":    268435663,
    "MissileAttack1":    268435664,
    "MissileAttack2":    268435665,
    "MissileAttack3":    268435666,
    "CastSpell":         1073742035,
}

def _motion_name_to_id(name: str) -> int | None:
    """Convert a motion name string to its integer ID, or None if not found."""
    # Try direct lookup
    v = MOTION_NAME_TO_ID.get(name)
    if v is not None:
        return v
    # Try stripping parenthetical suffix e.g. "Ready (0x41000003)"
    base = name.split('(')[0].strip()
    v = MOTION_NAME_TO_ID.get(base)
    if v is not None:
        return v
    # Try parsing as integer (hex or decimal)
    try:
        return int(name, 0)
    except (ValueError, TypeError):
        return None

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY MAP  — confirmed from WeenieFab SQL (ACE-World-16PY)
# ─────────────────────────────────────────────────────────────────────────────
# NOTE: These differ from the standard ACE C# enum. Values confirmed from
# actual WeenieFab SQL output. Add/correct as you verify more categories.

CATEGORY_MAP: Dict[str, int] = {
    # ── Complete authoritative list from EmoteScriptLib/Entity/Enum/EmoteCategory.cs ──
    'Invalid':                  0,
    'Refuse':                   1,
    'Vendor':                   2,
    'Death':                    3,
    'Portal':                   4,
    'HeartBeat':                5,
    'Give':                     6,
    'Use':                      7,
    'Activation':               8,
    'Generation':               9,
    'PickUp':                   10,
    'Drop':                     11,
    'QuestSuccess':             12,
    'QuestFailure':             13,
    'Taunt':                    14,
    'WoundedTaunt':             15,
    'KillTaunt':                16,
    'NewEnemy':                 17,
    'Scream':                   18,
    'Homesick':                 19,
    'ReceiveCritical':          20,
    'ResistSpell':              21,
    'TestSuccess':              22,
    'TestFailure':              23,
    'HearChat':                 24,
    'Wield':                    25,
    'UnWield':                  26,
    'EventSuccess':             27,
    'EventFailure':             28,
    'TestNoQuality':            29,
    'QuestNoFellow':            30,
    'TestNoFellow':             31,
    'GotoSet':                  32,
    'NumFellowsSuccess':        33,
    'NumFellowsFailure':        34,
    'NumCharacterTitlesSuccess':35,
    'NumCharacterTitlesFailure':36,
    'ReceiveLocalSignal':       37,
    'ReceiveTalkDirect':        38,
}
# ─────────────────────────────────────────────────────────────────────────────
# ACTION TYPE MAP  — confirmed from WeenieFab SQL
# ─────────────────────────────────────────────────────────────────────────────

ACTION_TYPE_MAP: Dict[str, int] = {
    # ── Complete authoritative list from EmoteScriptLib/Entity/Enum/EmoteType.cs ──
    'Invalid':                      0,
    'Act':                          1,
    'AwardXP':                      2,
    'Give':                         3,
    'MoveHome':                     4,
    'Motion':                       5,
    'Move':                         6,
    'PhysScript':                   7,
    'Say':                          8,
    'Sound':                        9,
    'Tell':                         10,
    'Turn':                         11,
    'TurnToTarget':                 12,
    'TextDirect':                   13,
    'CastSpell':                    14,
    'Activate':                     15,
    'WorldBroadcast':               16,
    'LocalBroadcast':               17,
    'DirectBroadcast':              18,
    'CastSpellInstant':             19,
    'UpdateQuest':                  20,
    'InqQuest':                     21,
    'StampQuest':                   22,
    'StartEvent':                   23,
    'StopEvent':                    24,
    'BLog':                         25,
    'AdminSpam':                    26,
    'TeachSpell':                   27,
    'AwardSkillXP':                 28,
    'AwardSkillPoints':             29,
    'InqQuestSolves':               30,
    'EraseQuest':                   31,
    'DecrementQuest':               32,
    'IncrementQuest':               33,
    'AddCharacterTitle':            34,
    'InqBoolStat':                  35,
    'InqIntStat':                   36,
    'InqFloatStat':                 37,
    'InqStringStat':                38,
    'InqAttributeStat':             39,
    'InqRawAttributeStat':          40,
    'InqSecondaryAttributeStat':    41,
    'InqRawSecondaryAttributeStat': 42,
    'InqSkillStat':                 43,
    'InqRawSkillStat':              44,
    'InqSkillTrained':              45,
    'InqSkillSpecialized':          46,
    'AwardTrainingCredits':         47,
    'InflictVitaePenalty':          48,
    'AwardLevelProportionalXP':     49,
    'AwardLevelProportionalSkillXP':50,
    'InqEvent':                     51,
    'ForceMotion':                  52,
    'SetIntStat':                   53,
    'IncrementIntStat':             54,
    'DecrementIntStat':             55,
    'CreateTreasure':               56,
    'ResetHomePosition':            57,
    'InqFellowQuest':               58,
    'InqFellowNum':                 59,
    'UpdateFellowQuest':            60,
    'StampFellowQuest':             61,
    'AwardNoShareXP':               62,
    'SetSanctuaryPosition':         63,
    'TellFellow':                   64,
    'FellowBroadcast':              65,
    'LockFellow':                   66,
    'Goto':                         67,
    'PopUp':                        68,
    'SetBoolStat':                  69,
    'SetQuestCompletions':          70,
    'InqNumCharacterTitles':        71,
    'Generate':                     72,
    'PetCastSpellOnOwner':          73,
    'TakeItems':                    74,
    'InqYesNo':                     75,
    'InqOwnsItems':                 76,
    'DeleteSelf':                   77,
    'KillSelf':                     78,
    'UpdateMyQuest':                79,
    'InqMyQuest':                   80,
    'StampMyQuest':                 81,
    'InqMyQuestSolves':             82,
    'EraseMyQuest':                 83,
    'DecrementMyQuest':             84,
    'IncrementMyQuest':             85,
    'SetMyQuestCompletions':        86,
    'MoveToPos':                    87,
    'LocalSignal':                  88,
    'InqPackSpace':                 89,
    'RemoveVitaePenalty':           90,
    'SetEyeTexture':                91,
    'SetEyePalette':                92,
    'SetNoseTexture':               93,
    'SetNosePalette':               94,
    'SetMouthTexture':              95,
    'SetMouthPalette':              96,
    'SetHeadObject':                97,
    'SetHeadPalette':               98,
    'TeleportTarget':               99,
    'TeleportSelf':                 100,
    'StartBarber':                  101,
    'InqQuestBitsOn':               102,
    'InqQuestBitsOff':              103,
    'InqMyQuestBitsOn':             104,
    'InqMyQuestBitsOff':            105,
    'SetQuestBitsOn':               106,
    'SetQuestBitsOff':              107,
    'SetMyQuestBitsOn':             108,
    'SetMyQuestBitsOff':            109,
    'UntrainSkill':                 110,
    'SetAltRacialSkills':           111,
    'SpendLuminance':               112,
    'AwardLuminance':               113,
    'InqInt64Stat':                 114,
    'SetInt64Stat':                 115,
    'OpenMe':                       116,
    'CloseMe':                      117,
    'SetFloatStat':                 118,
    'AddContract':                  119,
    'RemoveContract':               120,
    'InqContractsFull':             121,
}
# Quest-based branching: both success/failure use QuestSuccess/QuestFailure
# keyed by quest name (the value after InqQuest:)
QUEST_BRANCHING_ACTIONS = {
    'InqQuest', 'InqQuestSolves', 'InqMyQuest', 'InqMyQuestSolves',
    'InqFellowQuest', 'InqFellowNum',
}
# Stat-based branching: TestSuccess keyed by auto-key, TestFailure quest=NULL
STAT_BRANCHING_ACTIONS = {
    'InqOwnsItems', 'InqEvent', 'InqBoolStat', 'InqIntStat', 'InqSkillStat',
    'InqSkillSpecialized', 'InqSkillTraining', 'InqContractsFull',
    'InqNumCharacterTitles', 'InqPackSpace', 'InqYesNo',
}
BRANCHING_ACTIONS = QUEST_BRANCHING_ACTIONS | STAT_BRANCHING_ACTIONS

# Branch label → category ID
BRANCH_CATEGORY: Dict[str, int] = {
    'QuestSuccess': CATEGORY_MAP['QuestSuccess'],
    'QuestFailure': CATEGORY_MAP['QuestFailure'],
    'TestSuccess':  22,  # confirmed
    'TestFailure':  23,  # confirmed
    'EventSuccess': 27,  # confirmed
    'EventFailure': 28,  # confirmed
    'NumFellowsSuccess': 33,  # InqFellowNum: fellowship within range
    'NumFellowsFailure': 34,  # InqFellowNum: fellowship above max
    'TestNoFellow':      31,  # InqFellowNum: fellowship below min (third branch)
}

BRANCH_LABELS = set(BRANCH_CATEGORY.keys())


# Confirmed ID → name for SQL comments (takes precedence over reverse-map collisions)
CONFIRMED_CATEGORY_NAMES: Dict[int, str] = {
    # Complete — sourced from EmoteCategory.cs
    1: 'Refuse',
    2: 'Vendor',
    3: 'Death',
    4: 'Portal',
    5: 'HeartBeat',
    6: 'Give',
    7: 'Use',
    8: 'Activation',
    9: 'Generation',
    10: 'PickUp',
    11: 'Drop',
    12: 'QuestSuccess',
    13: 'QuestFailure',
    14: 'Taunt',
    15: 'WoundedTaunt',
    16: 'KillTaunt',
    17: 'NewEnemy',
    18: 'Scream',
    19: 'Homesick',
    20: 'ReceiveCritical',
    21: 'ResistSpell',
    22: 'TestSuccess',
    23: 'TestFailure',
    24: 'HearChat',
    25: 'Wield',
    26: 'UnWield',
    27: 'EventSuccess',
    28: 'EventFailure',
    29: 'TestNoQuality',
    30: 'QuestNoFellow',
    31: 'TestNoFellow',
    32: 'GotoSet',
    33: 'NumFellowsSuccess',
    34: 'NumFellowsFailure',
    35: 'NumCharacterTitlesSuccess',
    36: 'NumCharacterTitlesFailure',
    37: 'ReceiveLocalSignal',
    38: 'ReceiveTalkDirect',
}

CONFIRMED_ACTION_NAMES: Dict[int, str] = {
    # Complete — sourced from EmoteType.cs
    1: 'Act',
    2: 'AwardXP',
    3: 'Give',
    4: 'MoveHome',
    5: 'Motion',
    6: 'Move',
    7: 'PhysScript',
    8: 'Say',
    9: 'Sound',
    10: 'Tell',
    11: 'Turn',
    12: 'TurnToTarget',
    13: 'TextDirect',
    14: 'CastSpell',
    15: 'Activate',
    16: 'WorldBroadcast',
    17: 'LocalBroadcast',
    18: 'DirectBroadcast',
    19: 'CastSpellInstant',
    20: 'UpdateQuest',
    21: 'InqQuest',
    22: 'StampQuest',
    23: 'StartEvent',
    24: 'StopEvent',
    25: 'BLog',
    26: 'AdminSpam',
    27: 'TeachSpell',
    28: 'AwardSkillXP',
    29: 'AwardSkillPoints',
    30: 'InqQuestSolves',
    31: 'EraseQuest',
    32: 'DecrementQuest',
    33: 'IncrementQuest',
    34: 'AddCharacterTitle',
    35: 'InqBoolStat',
    36: 'InqIntStat',
    37: 'InqFloatStat',
    38: 'InqStringStat',
    39: 'InqAttributeStat',
    40: 'InqRawAttributeStat',
    41: 'InqSecondaryAttributeStat',
    42: 'InqRawSecondaryAttributeStat',
    43: 'InqSkillStat',
    44: 'InqRawSkillStat',
    45: 'InqSkillTrained',
    46: 'InqSkillSpecialized',
    47: 'AwardTrainingCredits',
    48: 'InflictVitaePenalty',
    49: 'AwardLevelProportionalXP',
    50: 'AwardLevelProportionalSkillXP',
    51: 'InqEvent',
    52: 'ForceMotion',
    53: 'SetIntStat',
    54: 'IncrementIntStat',
    55: 'DecrementIntStat',
    56: 'CreateTreasure',
    57: 'ResetHomePosition',
    58: 'InqFellowQuest',
    59: 'InqFellowNum',
    60: 'UpdateFellowQuest',
    61: 'StampFellowQuest',
    62: 'AwardNoShareXP',
    63: 'SetSanctuaryPosition',
    64: 'TellFellow',
    65: 'FellowBroadcast',
    66: 'LockFellow',
    67: 'Goto',
    68: 'PopUp',
    69: 'SetBoolStat',
    70: 'SetQuestCompletions',
    71: 'InqNumCharacterTitles',
    72: 'Generate',
    73: 'PetCastSpellOnOwner',
    74: 'TakeItems',
    75: 'InqYesNo',
    76: 'InqOwnsItems',
    77: 'DeleteSelf',
    78: 'KillSelf',
    79: 'UpdateMyQuest',
    80: 'InqMyQuest',
    81: 'StampMyQuest',
    82: 'InqMyQuestSolves',
    83: 'EraseMyQuest',
    84: 'DecrementMyQuest',
    85: 'IncrementMyQuest',
    86: 'SetMyQuestCompletions',
    87: 'MoveToPos',
    88: 'LocalSignal',
    89: 'InqPackSpace',
    90: 'RemoveVitaePenalty',
    91: 'SetEyeTexture',
    92: 'SetEyePalette',
    93: 'SetNoseTexture',
    94: 'SetNosePalette',
    95: 'SetMouthTexture',
    96: 'SetMouthPalette',
    97: 'SetHeadObject',
    98: 'SetHeadPalette',
    99: 'TeleportTarget',
    100: 'TeleportSelf',
    101: 'StartBarber',
    102: 'InqQuestBitsOn',
    103: 'InqQuestBitsOff',
    104: 'InqMyQuestBitsOn',
    105: 'InqMyQuestBitsOff',
    106: 'SetQuestBitsOn',
    107: 'SetQuestBitsOff',
    108: 'SetMyQuestBitsOn',
    109: 'SetMyQuestBitsOff',
    110: 'UntrainSkill',
    111: 'SetAltRacialSkills',
    112: 'SpendLuminance',
    113: 'AwardLuminance',
    114: 'InqInt64Stat',
    115: 'SetInt64Stat',
    116: 'OpenMe',
    117: 'CloseMe',
    118: 'SetFloatStat',
    119: 'AddContract',
    120: 'RemoveContract',
    121: 'InqContractsFull',
}
# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EmoteBlock:
    """One emote row (trigger, GotoSet, or branch result)."""
    category:    int
    quest:       Optional[str]   = None  # GotoSet name OR branch quest key
    probability: float           = 1.0
    actions:     List['EmoteAction'] = field(default_factory=list)


@dataclass
class EmoteAction:
    """One action row within an EmoteBlock."""
    action_type: int
    delay:       float = 0.0
    extent:      float = 1.0
    motion:      Optional[int]   = None
    message:     Optional[str]   = None
    test_string: Optional[str]   = None
    min_int:     Optional[int]   = None   # pos 8  — int min (InqQuestSolves etc.)
    max_int:     Optional[int]   = None   # pos 9  — int max
    min_64:      Optional[int]   = None   # pos 10 — bigint min (AwardLevelProportionalXP range)
    max_64:      Optional[int]   = None   # pos 11 — bigint max
    stat:        Optional[int]   = None
    display:     Optional[int]   = None
    amount:      Optional[int]   = None
    amount_64:   Optional[int]   = None
    hero_xp_64:  Optional[int]   = None   # pos 18 — hero_X_P_64
    percent:     Optional[float] = None
    spell_id:    Optional[int]   = None
    weenie_class_id: Optional[int] = None
    stack_size:  Optional[int]   = None
    # Branch blocks generated by this action
    branch_blocks: List[EmoteBlock] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# TOKENIZER
# ─────────────────────────────────────────────────────────────────────────────

def _detect_indent_unit(lines: List[str]) -> int:
    for ln in lines:
        s = ln.lstrip()
        if not s or s.startswith('#'):
            continue
        spaces = len(ln) - len(s)
        if spaces > 0:
            return spaces
    return 4


def tokenize(text: str) -> List[Tuple[int, str]]:
    raw  = text.replace('\t', '    ').splitlines()
    unit = _detect_indent_unit(raw)
    out  = []
    for ln in raw:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        level = (len(ln) - len(ln.lstrip())) // unit
        out.append((level, s))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# VALUE PARSERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_wcid_stack(v: str) -> Tuple[int, Optional[int]]:
    """Parse 'wcid' / 'wcid, N' / 'Name (display) (wcid), N'"""
    # Pattern: ends with (wcid) or (wcid), stack
    m = re.search(r'\((\d+)\)\s*(?:,\s*(\d+))?$', v)
    if m:
        return int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
    # Simple: "wcid" or "wcid, stack"
    parts = re.split(r',\s*', v.strip(), maxsplit=1)
    try:
        wcid  = int(parts[0].strip().replace(',', ''))
        stack = int(parts[1].strip().replace(',', '')) if len(parts) > 1 else None
        return wcid, stack
    except ValueError:
        return 0, None


def parse_action_value(name: str, v: str, warnings: List[str]) -> dict:
    attrs = {}
    v = v.strip()

    if name in ('Tell', 'Say', 'DirectBroadcast', 'FellowBroadcast',
                'LocalBroadcast', 'WorldBroadcast', 'AdminSpam', 'BLog',
                'PopUp', 'TextDirect', 'TellFellow'):
        attrs['message'] = v

    elif name == 'Give':
        wcid, stack = _parse_wcid_stack(v)
        attrs['weenie_class_id'] = wcid
        if stack: attrs['stack_size'] = stack

    elif name in ('TakeItems',):
        wcid, stack = _parse_wcid_stack(v)
        attrs['weenie_class_id'] = wcid
        if stack: attrs['stack_size'] = stack

    elif name in ('StampQuest', 'StampMyQuest', 'StampFellowQuest',
                  'UpdateQuest', 'UpdateMyQuest', 'UpdateFellowQuest',
                  ):
        # EmoteScriptLib: Message = quest
        attrs['message'] = v.strip()

    elif name in ('EraseQuest', 'EraseMyQuest',
                  'InqQuestBitsOn', 'InqQuestBitsOff',
                  'InqMyQuestBitsOn', 'InqMyQuestBitsOff',
                  'SetQuestBitsOn', 'SetQuestBitsOff',
                  'SetMyQuestBitsOn', 'SetMyQuestBitsOff',
                  ):
        # EmoteScriptLib: Message = quest
        attrs['message'] = v.strip()

    elif name in ('IncrementQuest', 'DecrementQuest',
                  'IncrementMyQuest', 'DecrementMyQuest',
                  ):
        # EmoteScriptLib: Message = quest, Amount = amount (optional, default 1)
        parts = [p.strip() for p in v.split(',', 1)]
        attrs['message'] = parts[0]
        if len(parts) > 1:
            try: attrs['amount'] = int(parts[1].strip())
            except: pass
        # default amount stays None (ACE defaults to 1)

    elif name in ('StartEvent', 'StopEvent'):
        attrs['message'] = v.strip()

    elif name == 'InqQuest':
        # Full quest name — keep @suffix (e.g. ExperimenterKT@KillTaskCompleted)
        attrs['message'] = v.strip()

    elif name in ('InqQuestSolves', 'InqMyQuestSolves'):
        # Format: "QuestName@suffix, N"  or  "QuestName@suffix, N - M"
        # EmoteScriptLib: Message = quest (full name including @suffix), Min = N, Max = M (default int.MaxValue)
        comma = v.rfind(',')
        if comma != -1:
            attrs['message'] = v[:comma].strip()
            range_str = v[comma+1:].strip()
            if ' - ' in range_str:
                parts = range_str.split(' - ', 1)
                try:
                    attrs['min_int'] = int(parts[0].strip().replace(',', ''))
                    attrs['max_int'] = int(parts[1].strip().replace(',', ''))
                except: pass
            else:
                try:
                    attrs['min_int'] = int(range_str.replace(',', ''))
                    attrs['max_int'] = 2147483647  # int.MaxValue
                except: pass
        else:
            attrs['message'] = v.strip()

    elif name == 'InqFellowQuest':
        # message = quest name (same as InqQuest)
        attrs['message'] = re.split(r'[@,]', v)[0].strip()

    elif name == 'InqFellowNum':
        # Value is the literal range key, e.g. "HasFellowNum_1-9_7" — kept
        # verbatim in message (matches SQL `quest`/`message` column and the
        # YAML convention). The embedded "<min>-<max>" is also extracted into
        # the real min/max integer columns, since the source SQL populates
        # both independently of the key string.
        attrs['message'] = v.strip()
        m = re.search(r'_(\d+)-(\d+)_', v)
        if m:
            try:
                attrs['min_int'] = int(m.group(1))
                attrs['max_int'] = int(m.group(2))
            except: pass

    elif name == 'InqOwnsItems':
        # Parse "wcid, count" or "wcid, min-max"
        # auto-key is generated in _parse_branch_labels, not here
        # Stack size: use first numeric value if not a range; None for ranges
        parts = [p.strip() for p in v.split(',', 1)]
        try: wcid = int(parts[0])
        except: wcid = 0
        attrs['weenie_class_id'] = wcid
        if len(parts) > 1:
            count_str = parts[1].strip()
            if '-' not in count_str:
                try: attrs['stack_size'] = int(count_str)
                except: pass
            # range like "1-3" → stack_size stays None

    elif name == 'AwardLevelProportionalXP':
        # Format: "N%"  or  "N%, min - max"  (min/max are bigint)
        m = re.match(r'(\d+(?:\.\d+)?)%', v)
        if m:
            attrs['percent'] = float(m.group(1)) / 100.0
            # Parse optional range after the percent
            rest = v[m.end():].strip().lstrip(',').strip()
            if rest:
                if ' - ' in rest:
                    parts = rest.split(' - ', 1)
                    try:
                        attrs['min_64'] = int(parts[0].strip().replace(',', ''))
                        attrs['max_64'] = int(parts[1].strip().replace(',', ''))
                    except: pass
                else:
                    try: attrs['max_64'] = int(rest.replace(',', ''))
                    except: pass
        else:
            warnings.append(f'Could not parse AwardLevelProportionalXP: {v!r}')

    elif name in ('AwardLuminance', 'SpendLuminance'):
        # EmoteScriptLib: Amount64 = amount → amount_64 column
        try:    attrs['amount_64'] = int(re.sub(r'[,\s]', '', v.split()[0]))
        except: warnings.append(f'Could not parse luminance: {v!r}')

    elif name == 'AwardNoShareXP':
        # EmoteScriptLib: Amount64 = amount → amount_64 column
        try:    attrs['amount_64'] = int(re.sub(r'[,\s]', '', v.split()[0]))
        except: warnings.append(f'Could not parse AwardNoShareXP: {v!r}')

    elif name == 'AwardSkillXP':
        try:    attrs['amount_64'] = int(re.sub(r'[,\s]', '', v.split()[0]))
        except: warnings.append(f'Could not parse AwardSkillXP: {v!r}')

    elif name == 'CastSpell':
        try:    attrs['spell_id'] = int(re.sub(r'[,\s]', '', v))
        except: warnings.append(f'Could not parse CastSpell: {v!r}')

    elif name in ('Motion', 'ForceMotion'):
        v_clean = v.strip()
        mid = _motion_name_to_id(v_clean)
        if mid is not None:
            attrs['motion'] = mid
        else:
            try:    attrs['motion'] = int(re.sub(r'[,\s]', '', v_clean))
            except: warnings.append(f'Could not parse Motion: {v!r}')

    elif name == 'Goto':
        attrs['message'] = v

    elif name == 'InqEvent':
        attrs['message'] = v.strip()  # event name in message field

    elif name in ('LocalSignal', 'SendSignal'):
        attrs['message'] = v

    elif name == 'TeachSpell':
        try:    attrs['spell_id'] = int(re.sub(r'[,\s]', '', v))
        except: warnings.append(f'Could not parse TeachSpell: {v!r}')

    elif name == 'SetIntStat':
        m = re.match(r'(\d+)\s*[,=]\s*(\d+)', v)
        if m:
            attrs['stat']   = int(m.group(1))
            attrs['amount'] = int(m.group(2))

    elif name == 'SetBoolStat':
        m = re.match(r'(\d+)\s*[,=]\s*(\w+)', v)
        if m:
            attrs['stat']    = int(m.group(1))
            attrs['display'] = 1 if m.group(2).lower() == 'true' else 0

    elif name == 'InqBoolStat':
        m = re.match(r'(\d+)\s*[,=]\s*(\w+)', v)
        if m:
            attrs['stat']    = int(m.group(1))
            attrs['display'] = 1 if m.group(2).lower() == 'true' else 0

    elif name == 'InqIntStat':
        m = re.match(r'(\d+)\s*[,=]\s*(\d+)', v)
        if m:
            attrs['stat']   = int(m.group(1))
            attrs['amount'] = int(m.group(2))

    elif name in ('SetQuestCompletions', 'SetMyQuestCompletions'):
        # EmoteScriptLib: Message = quest, Amount = amount
        parts = [p.strip() for p in v.split(',', 1)]
        attrs['message'] = parts[0]
        if len(parts) > 1:
            try: attrs['amount'] = int(parts[1].strip())
            except: pass

    elif name in ('AwardXP',):
        # AwardXP → amount_64
        try: attrs['amount_64'] = int(re.sub(r'[,\s]', '', v.split()[0]))
        except: warnings.append(f'Could not parse AwardXP: {v!r}')

    elif name in ('AwardTrainingCredits', 'AwardSkillPoints'):
        # amount field
        try: attrs['amount'] = int(re.sub(r'[,\s]', '', v.split()[0]))
        except: warnings.append(f'Could not parse {name}: {v!r}')

    else:
        if v:
            attrs['message'] = v
            warnings.append(
                f"Action '{name}' has no specific parser — value stored in message. "
                f"Please verify the generated SQL.")
    return attrs


# ─────────────────────────────────────────────────────────────────────────────
# RECURSIVE PARSER
# ─────────────────────────────────────────────────────────────────────────────

class _Parser:
    def __init__(self, tokens, warnings):
        self.tokens          = tokens
        self.pos             = 0
        self.warnings        = warnings
        self._auto_key_counts: dict = {}  # tracks InqOwnsItems / stat-based auto-keys

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        tok = self.tokens[self.pos]; self.pos += 1; return tok

    def parse_all(self) -> List[EmoteBlock]:
        blocks = []
        while self.peek():
            lv, content = self.peek()
            if lv != 0:
                self.warnings.append(f'Unexpected indent at top level: {content!r}')
                self.consume(); continue
            blk = self._parse_block_header()
            if blk: blocks.append(blk)
        return blocks

    def _parse_block_header(self) -> Optional[EmoteBlock]:
        lv, content = self.consume()
        if ':' not in content:
            self.warnings.append(f'Top-level line missing colon: {content!r}')
            return None
        cat_str, _, param = content.partition(':')
        cat_str = cat_str.strip(); param = param.strip()
        cat_id  = CATEGORY_MAP.get(cat_str)
        if cat_id is None:
            self.warnings.append(f"Unknown category '{cat_str}' — skipping block.")
            while self.peek() and self.peek()[0] > lv: self.consume()
            return None

        quest = param if cat_str == 'GotoSet' else (param if param else None)
        block = EmoteBlock(category=cat_id, quest=quest)
        block.actions = self._parse_actions(lv + 1)
        return block

    def _parse_actions(self, expected_lv: int) -> List[EmoteAction]:
        actions = []
        while self.peek() and self.peek()[0] >= expected_lv:
            lv, content = self.peek()
            if lv > expected_lv:
                self.warnings.append(f'Extra indent, skipping: {content!r}')
                self.consume(); continue
            if lv < expected_lv: break
            if not content.startswith('-'): break
            self.consume()
            act = self._parse_action_line(content[1:].strip(), expected_lv)
            if act: actions.append(act)
        return actions

    def _parse_action_line(self, content: str, action_lv: int) -> Optional[EmoteAction]:
        delay = 0.0
        m = re.match(r'^Delay\s*:\s*(\d+(?:\.\d+)?)\s*,\s*(.+)$', content, re.IGNORECASE)
        if m:
            delay   = float(m.group(1))
            content = m.group(2).strip()

        colon  = content.find(':')
        a_name = content[:colon].strip() if colon != -1 else content.strip()
        a_val  = content[colon+1:].strip() if colon != -1 else ''

        type_id = ACTION_TYPE_MAP.get(a_name)
        if type_id is None:
            self.warnings.append(
                f"Unknown action '{a_name}' — add to ACTION_TYPE_MAP and verify ID.")
            type_id = ACTION_TYPE_MAP['Tell']
            a_val   = f'[{a_name}: {a_val}]'
            a_name  = 'Tell'

        attrs  = parse_action_value(a_name, a_val, self.warnings)
        action = EmoteAction(action_type=type_id, delay=delay, **attrs)

        # Parse branch labels if this is a branching action
        if a_name in BRANCHING_ACTIONS:
            quest_key = attrs.get('message', a_val.split('@')[0].strip())
            self._parse_branch_labels(action, action_lv + 1, quest_key, a_name)

        # ── Inline GotoSet: GoTo actions can carry an inline GotoSet sub-block ──
        # Syntax:  - GoTo: QuestOneCheck
        #              GotoSet:
        #                  - Tell: Checked!
        # → produces a separate GotoSet emote block in the SQL output
        if a_name in ('Goto', 'GoTo', 'goto'):
            if self.peek() and self.peek()[0] == action_lv + 1:
                _, next_label = self.peek()
                if next_label.rstrip(':').strip() in ('GotoSet', 'Gotoset', 'gotoset'):
                    self.consume()  # consume 'GotoSet:'
                    gs_label  = action.message or a_val.strip()
                    gs_actions = self._parse_actions(action_lv + 2)
                    gs_block   = EmoteBlock(
                        category=CATEGORY_MAP.get('GotoSet', 32),
                        quest=gs_label,
                        actions=gs_actions,
                    )
                    action.branch_blocks.append(gs_block)

        return action

    def _parse_branch_labels(self, action: EmoteAction, branch_lv: int,
                               quest_key: str, action_name: str = ''):
        """
        Parse branch sub-blocks (QuestSuccess/QuestFailure, TestSuccess/TestFailure).

        Quest-based (InqQuest etc.):  both branches keyed by quest_key.
        Stat-based (InqOwnsItems etc.): TestSuccess keyed, TestFailure quest=NULL.
        InqOwnsItems also overrides action.message with the auto-key.
        """
        is_stat_based = action_name in STAT_BRANCHING_ACTIONS

        # Generate auto-key for stat-based actions (e.g. InqOwnsItems)
        if is_stat_based and action_name == 'InqOwnsItems':
            # Generate 'OwnsItem-{wcid}' as key, store in action.message
            wcid = action.weenie_class_id or 0
            base = f'OwnsItem-{wcid}'
            count = self._auto_key_counts.get(base, 0) + 1
            self._auto_key_counts[base] = count
            auto_key = base if count == 1 else f'{base}_{count}'
            action.message = auto_key
            quest_key      = auto_key
        elif is_stat_based and action_name == 'InqEvent':
            # Key = event name (already in action.message from parse_action_value)
            quest_key = action.message or 'event-unknown'
            # action.message already correct — no override needed
        elif is_stat_based:
            # Generic stat-based fallback: generate key from action name
            base = f'{action_name}-auto'
            count = self._auto_key_counts.get(base, 0) + 1
            self._auto_key_counts[base] = count
            auto_key = base if count == 1 else f'{base}_{count}'
            action.message = auto_key
            quest_key      = auto_key

        while self.peek() and self.peek()[0] == branch_lv:
            _, label = self.peek()
            label_key = label.rstrip(':')
            if label_key not in BRANCH_LABELS: break
            self.consume()
            cat_id  = BRANCH_CATEGORY.get(label_key, 12)
            actions = self._parse_actions(branch_lv + 1)

            # Determine quest value for this branch emote
            if is_stat_based:
                # TestSuccess keyed, TestFailure unkeyed (quest=NULL)
                is_failure = label_key in ('TestFailure', 'QuestFailure', 'EventFailure')
                branch_quest = None if is_failure else quest_key
            else:
                # Quest-based: both branches keyed by quest_key
                branch_quest = quest_key

            action.branch_blocks.append(
                EmoteBlock(category=cat_id, quest=branch_quest, actions=actions))


# ─────────────────────────────────────────────────────────────────────────────
# FLATTEN — collect ALL blocks in emission order (DFS, branches after parent)
# ─────────────────────────────────────────────────────────────────────────────

def _collect_blocks(top_blocks: List[EmoteBlock]) -> List[EmoteBlock]:
    """Flatten all EmoteBlocks into emission order via true DFS recursion."""
    result: List[EmoteBlock] = []
    seen:   set              = set()

    def _walk(blk: EmoteBlock):
        key = id(blk)
        if key in seen:
            return
        seen.add(key)
        result.append(blk)
        # Recursively walk ALL branch blocks at any depth
        for act in blk.actions:
            for sub_blk in act.branch_blocks:
                _walk(sub_blk)   # _walk handles its own actions recursively

    for blk in top_blocks:
        _walk(blk)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SQL EMITTER
# ─────────────────────────────────────────────────────────────────────────────

_NULL = 'NULL'

def _sq(s: Optional[str]) -> str:
    if s is None: return _NULL
    return "'" + s.replace("'", "''").replace('\\', '\\\\') + "'"

def _n(v, default=_NULL) -> str:
    return str(v) if v is not None else default

def _f(v: Optional[float], default=_NULL) -> str:
    if v is None: return default
    # Match WeenieFab float precision
    return f'{v:.8f}'.rstrip('0').rstrip('.')  if '.' in f'{v:.8f}' else str(v)


# Full emote_action column list (matches WeenieFab schema exactly)
_EMOTE_ACTION_COLS = (
    '`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, '
    '`message`, `test_String`, `min`, `max`, `min_64`, `max_64`, '
    '`min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, '
    '`hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, '
    '`treasure_Class`, `treasure_Type`, `p_Script`, `sound`, '
    '`destination_Type`, `weenie_Class_Id`, `stack_Size`, '
    '`palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, '
    '`origin_X`, `origin_Y`, `origin_Z`, '
    '`angles_W`, `angles_X`, `angles_Y`, `angles_Z`'
)

_EMOTE_COLS = (
    '`object_Id`, `category`, `probability`, `weenie_Class_Id`, '
    '`style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`'
)


def _action_values(act: EmoteAction, prefix: str = '@parent_id', order: int = 0) -> str:
    t_name  = CONFIRMED_ACTION_NAMES.get(act.action_type) or next((k for k, v in ACTION_TYPE_MAP.items() if v == act.action_type), str(act.action_type))
    percent = _f(act.percent) if act.percent is not None else _NULL
    return (
        f"({prefix}, {order}, {act.action_type} /* {t_name} */, "
        f"{_f(act.delay, '0')}, {_f(act.extent, '1')}, "
        f"{_n(act.motion)}, "                    # motion
        f"{_sq(act.message)}, "                  # message
        f"{_sq(act.test_string)}, "              # test_String
        f"{_n(act.min_int)}, {_n(act.max_int)}, "  # min, max  (int)
        f"{_n(act.min_64)}, {_n(act.max_64)}, "    # min_64, max_64  (bigint)
        f"NULL, NULL, "                           # min_Dbl, max_Dbl
        f"{_n(act.stat)}, "                      # stat
        f"{_n(act.display)}, "                   # display
        f"{_n(act.amount)}, "                    # amount
        f"{_n(act.amount_64)}, "                 # amount_64
        f"{_n(act.hero_xp_64)}, "               # hero_X_P_64
        f"{percent}, "                           # percent
        f"{_n(act.spell_id)}, "                  # spell_Id
        f"NULL, NULL, NULL, "                    # wealth_Rating, treasure_Class, treasure_Type
        f"NULL, NULL, NULL, "                    # p_Script, sound, destination_Type
        f"{_n(act.weenie_class_id)}, "           # weenie_Class_Id
        f"{_n(act.stack_size)}, "                # stack_Size
        f"NULL, NULL, NULL, "                    # palette, shade, try_To_Bond
        f"NULL, "                                # obj_Cell_Id
        f"NULL, NULL, NULL, "                    # origin_X/Y/Z
        f"NULL, NULL, NULL, NULL)"               # angles_W/X/Y/Z
    )


def _generate_sql(wcid: int, all_blocks: List[EmoteBlock]) -> str:
    parts: List[str] = []
    cat_name_map = {v: k for k, v in CATEGORY_MAP.items()}

    for blk in all_blocks:
        cat_label = CONFIRMED_CATEGORY_NAMES.get(blk.category) or cat_name_map.get(blk.category, str(blk.category))
        quest_val = _sq(blk.quest)

        # ── INSERT emote row ────────────────────────────────────────────────
        parts.append(
            f"INSERT INTO `weenie_properties_emote` ({_EMOTE_COLS})\n"
            f"VALUES ({wcid}, {blk.category} /* {cat_label} */, "
            f"1, NULL, NULL, NULL, "       # probability = 1 (not 1.0)
            f"{quest_val}, NULL, NULL, NULL);"
        )
        parts.append("")                   # blank line before SET
        parts.append("SET @parent_id = LAST_INSERT_ID();")
        parts.append("")                   # blank line after SET

        # ── INSERT action rows (multi-value if > 1) ─────────────────────────
        if blk.actions:
            parts.append(
                f"INSERT INTO `weenie_properties_emote_action` ({_EMOTE_ACTION_COLS})"
            )
            # First row on same line as VALUES; subsequent rows use '     , '
            rows = [_action_values(act, '@parent_id', i)
                    for i, act in enumerate(blk.actions)]
            first = f"VALUES {rows[0]}"
            rest  = ["     , " + r for r in rows[1:]]
            parts.append("\n".join([first] + rest) + ";")
            parts.append("")               # blank line after action block

    return '\n'.join(parts).rstrip() + '\n'


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def parse_emote_text(text: str, wcid: int, start_emote_id: int = 1) -> dict:
    """
    Convert WeenieFab compact emote text to ACEmulator SQL.

    Returns dict:
        sql          - Generated SQL string
        warnings     - Non-fatal issues (especially VERIFY items)
        emote_count  - Number of emote rows
        action_count - Number of emote action rows
        error        - None or error string
    """
    warnings: List[str] = []
    try:
        tokens     = tokenize(text)
        parser     = _Parser(tokens, warnings)
        top_blocks = parser.parse_all()

        if not top_blocks:
            return {'sql': '', 'warnings': warnings,
                    'emote_count': 0, 'action_count': 0,
                    'error': 'No valid emote blocks found.'}

        all_blocks   = _collect_blocks(top_blocks)
        emote_count  = len(all_blocks)
        action_count = sum(len(b.actions) for b in all_blocks)
        sql          = _generate_sql(wcid, all_blocks)

        # Serialize blocks for JS Builder consumption
        blocks_data = []
        for blk in all_blocks:
            bd = {'category': blk.category, 'quest': blk.quest, 'actions': []}
            for act in blk.actions:
                bd['actions'].append({
                    'type':           act.action_type,
                    'delay':          act.delay,
                    'message':        act.message,
                    'test_string':    act.test_string,
                    'weenie_class_id':act.weenie_class_id,
                    'stack_size':     act.stack_size,
                    'percent':        act.percent,
                    'hero_xp_64':     act.hero_xp_64,
                    'amount_64':      act.amount_64,
                    'amount':         act.amount,
                    'spell_id':       act.spell_id,
                    'min_int':        act.min_int,
                    'max_int':        act.max_int,
                    'min_64':         act.min_64,
                    'max_64':         act.max_64,
                    'stat':           act.stat,
                    'motion':         act.motion,
                    'display':        act.display,
                })
            blocks_data.append(bd)

        return {'sql': sql, 'warnings': warnings,
                'emote_count': emote_count, 'action_count': action_count,
                'blocks': blocks_data, 'error': None}

    except Exception as exc:
        import traceback
        warnings.append(traceback.format_exc())
        return {'sql': '', 'warnings': warnings,
                'emote_count': 0, 'action_count': 0, 'error': str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys, pathlib
    if len(sys.argv) < 3:
        print('Usage: python -B -m aceforge.emote_parser <file.txt> <wcid>')
        sys.exit(1)
    text   = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    wcid   = int(sys.argv[2])
    result = parse_emote_text(text, wcid)
    if result['error']:
        print(f'ERROR: {result["error"]}', file=sys.stderr)
    for w in result['warnings']:
        print(f'WARN: {w}', file=sys.stderr)
    print(f'-- Emote rows: {result["emote_count"]}  Action rows: {result["action_count"]}')
    print()
    print(result['sql'])
