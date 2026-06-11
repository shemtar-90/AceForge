# ACEForge AI Content Schema

You generate ACE content as a JSON object. ACEForge converts this JSON to correct SQL automatically.
You NEVER write SQL. You NEVER write INSERT statements. Output JSON only.

## Output Format

```json
{
  "wcid": 800001,
  "content_type": "creature",
  "name": "Tumerok Berserker",
  "class_name": "tumerok_berserker",
  "weenie_type": 10,
  "short_desc": "A fierce Tumerok warrior.",
  "level": 150,
  "xp": 500000,
  "health": 1200,
  "stamina": 900,
  "mana": 400,
  "creature_type": "Tumerok",
  "strength": 250, "endurance": 220, "quickness": 200,
  "coordination": 210, "focus": 120, "self": 120,
  "melee_defense": 180,
  "attack_skill_name": "HeavyWeapons",
  "attack_skill": 200,
  "armor": 80,
  "scale": 1.0,
  "visual_range": 20.0,
  "loot_tier": 3101,
  "kill_quest": "TumerokBerserkerKT",
  "emotes": "Death:\n    - Say: For the tribe!"
}
```

## content_type values
- `creature` — monster/mob
- `npc` — quest giver, non-combat NPC
- `vendor` — shop keeper
- `boss` — named boss creature
- `item` — generic item, token, quest item
- `generator` — spawner weenie (one per creature/NPC)
- `quest` — quest flag entry (goes in quest table, not weenie table)

## Field Reference

### All content types
| Field | Type | Notes |
|-------|------|-------|
| `wcid` | int | Assigned by planner |
| `content_type` | string | See above |
| `name` | string | Display name |
| `class_name` | string | Lowercase underscore slug |
| `weenie_type` | int | 10=Creature/NPC, 6=Item, 35=Generator |
| `short_desc` | string | Short description |
| `long_desc` | string | Long description |

### Creature / NPC / Boss fields
| Field | Type | Notes |
|-------|------|-------|
| `level` | int | Creature level |
| `xp` | int | XP override |
| `health` | int | Max health |
| `stamina` | int | Max stamina |
| `mana` | int | Max mana |
| `creature_type` | string | Human, Tumerok, Drudge, Olthoi, Shadow, Undead, Mosswart, Lugian, Virindi, Golem |
| `strength` | int | Attribute value |
| `endurance` | int | Attribute value |
| `quickness` | int | Attribute value |
| `coordination` | int | Attribute value |
| `focus` | int | Attribute value |
| `self` | int | Attribute value |
| `melee_defense` | int | Melee defense skill |
| `attack_skill_name` | string | HeavyWeapons, LightWeapons, FinesseWeapons, MissileWeapons, WarMagic, LifeMagic |
| `attack_skill` | int | Attack skill level |
| `armor` | int | Base armor value (same for all body parts) |
| `scale` | float | Size scale (1.0 = normal) |
| `visual_range` | float | Aggro range in meters |
| `loot_tier` | int | DeathTreasureType (3101=T4, 3102=T5, 3103=T6, 3104=T7, 3105=T8) |
| `kill_quest` | string | Kill quest flag name for this creature |
| `attackable` | bool | true for monsters, false for friendly NPCs |
| `treasure_corpse` | bool | true = drops loot on death |
| `create_list` | array | Items always on corpse, see below |

### Item fields
| Field | Type | Notes |
|-------|------|-------|
| `item_type` | string | misc, writable, gem, key, food, melee_weapon, armor, clothing |
| `encumbrance` | int | Weight in burdens |
| `mass` | int | Mass value |
| `value` | int | Pyreal value |
| `useable` | int | 1=No, 2=Self, 4=Wielded, 8=Contained, 16=Ground |
| `max_stack` | int | Stack size (stackable items only) |
| `inscribable` | bool | Can be inscribed |

### Generator fields
| Field | Type | Notes |
|-------|------|-------|
| `target_wcid` | int | WCID of creature to spawn |
| `delay` | float | Respawn delay in seconds |
| `init_create` | int | Initial spawn count |
| `max_create` | int | Max simultaneous spawns |
| `when_create` | int | 1=Always |
| `where_create` | int | 1=Scatter, 2=Specific |

### Quest flag fields
| Field | Type | Notes |
|-------|------|-------|
| `quest_name` | string | Quest flag identifier |
| `min_delta` | int | Cooldown in seconds (86400=24h) |
| `max_solves` | int | Max completions (1=once, -1=unlimited) |
| `message` | string | Completion message |

### create_list items
```json
"create_list": [
  {"wcid": 273, "qty": 5000, "destination": "corpse_drop", "comment": "Pyreals"},
  {"wcid": 810050, "qty": 1, "destination": "corpse_drop", "comment": "Reward Item"}
]
```
destination: `corpse_drop`, `contain`, `shop`, `wield`

### emotes field
Write emotes in WeenieFab YAML format inside the `emotes` field string.
Use `\n` for newlines. Use 4-space indentation. ACEForge converts this to SQL.

```json
"emotes": "Use:\n    - InqQuest: MyQuestTimer\n        QuestSuccess:\n            - Tell: You have already completed this quest.\n        QuestFailure:\n            - Goto: GiveQuest\n\nGotoSet: GiveQuest\n    - Tell: Bring me the artifact.\n    - StampQuest: MyQuestTimer"
```

Valid trigger names: Use, GotoSet, Give, Death, HeartBeat, Taunt, WoundedTaunt, KillTaunt, NewEnemy, Refuse, Activation, ReceiveTalkDirect
Valid actions: Tell, Say, LocalBroadcast, InqQuest, StampQuest, EraseQuest, InqQuestSolves, Give, TakeItems, InqOwnsItems, AwardXP, AwardLevelProportionalXP, AwardLuminance, Goto, Motion

## Complete NPC Example

```json
{
  "wcid": 850001,
  "content_type": "npc",
  "name": "Ulgrim the Unpleasant",
  "class_name": "ulgrim_the_unpleasant",
  "weenie_type": 10,
  "short_desc": "A gruff and battle-hardened warrior.",
  "level": 1,
  "xp": 0,
  "health": 500,
  "stamina": 500,
  "mana": 500,
  "creature_type": "Human",
  "strength": 200, "endurance": 200, "quickness": 150,
  "coordination": 150, "focus": 100, "self": 100,
  "melee_defense": 200,
  "attack_skill_name": "HeavyWeapons",
  "attack_skill": 200,
  "armor": 0,
  "attackable": false,
  "treasure_corpse": false,
  "emotes": "Use:\n    - InqQuest: UlgrimQuestTimer\n        QuestSuccess:\n            - Tell: You have already proven yourself, warrior.\n        QuestFailure:\n            - Goto: StartQuest\n\nGotoSet: StartQuest\n    - Tell: So you think you can handle my trials, whelp?\n    - Tell: Kill 50 Tumerok Berserkers. Then we will talk.\n    - StampQuest: UlgrimQuestTimer"
}
```

## RULES
- Output ONLY the JSON object. No SQL. No explanations. No markdown outside the JSON.
- Every file gets its own JSON object.
- The planner assigns WCIDs — use them exactly.
- Generators must reference the creature WCID in `target_wcid`.
- NPCs with quests need emotes. Creatures with kill quests need `kill_quest` field.
