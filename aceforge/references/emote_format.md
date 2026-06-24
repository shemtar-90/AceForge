# ACEForge Emote Format — WeenieFab Compact Script

## MANDATORY: Write Emotes in WeenieFab Format — NOT Raw SQL

You MUST NOT write raw `INSERT INTO weenie_properties_emote` or
`INSERT INTO weenie_properties_emote_action` SQL statements.
ACEForge will reject them and the emotes will not load correctly.

Instead, write emotes as a WeenieFab compact script block, using these markers:

```
-- EMOTE SCRIPT (WCID: <wcid>)
<script here>
-- END EMOTE SCRIPT
```

ACEForge automatically converts this to correct ACE SQL at save time.
The WCID in the marker MUST match the NPC/creature's WCID exactly.

---

## CRITICAL — VALID TRIGGER NAMES

The following is the **complete and exhaustive** list of valid top-level trigger names.
**DO NOT invent trigger names.** Any trigger name not on this list will cause a parse error.

| Trigger | Purpose |
|---------|---------|
| `Use:` | Player clicks/uses the NPC — main entry point |
| `GotoSet: label` | Named sub-routine jumped to by `- Goto: label` |
| `ReceiveTalkDirect: keyword` | Fires when player sends keyword via Tell |
| `HeartBeat:` | Fires on NPC heartbeat timer |
| `Death:` | Fires when NPC/creature dies |
| `Give:` | Fires when player gives ANY item to NPC |
| `Wield:` | Fires when item is wielded |
| `UnWield:` | Fires when item is unwielded |
| `PickUp:` | Fires when item is picked up |
| `Drop:` | Fires when item is dropped |
| `Vendor:` | Vendor-specific trigger |
| `Activation:` | Fires on object activation |
| `Taunt:` | Fires when creature taunts |
| `WoundedTaunt:` | Fires when creature is wounded |
| `KillTaunt:` | Fires when creature kills |
| `NewEnemy:` | Fires when creature acquires new target |
| `Scream:` | Fires on creature scream |
| `Homesick:` | Fires when creature returns home |
| `ReceiveCritical:` | Fires when creature receives a critical hit |
| `ResistSpell:` | Fires when creature resists a spell |
| `HearChat:` | Fires when NPC hears local chat |
| `ReceiveLocalSignal:` | Fires on a local signal |

**INVALID triggers that do NOT exist — never use these:**
- ReceiveGive ← DOES NOT EXIST (use `Give:` instead)
- ReceiveItem ← DOES NOT EXIST
- OnKill ← DOES NOT EXIST
- OnDeath ← DOES NOT EXIST (use `Death:`)
- OnGive ← DOES NOT EXIST (use `Give:`)
- QuestComplete ← DOES NOT EXIST
- PlayerNear ← DOES NOT EXIST

---

## Branch Labels (NOT standalone triggers)

These appear only indented inside branching actions (InqQuest, InqOwnsItems, etc.):

| Label | Used after |
|-------|-----------|
| `QuestSuccess:` | InqQuest, InqQuestSolves, InqMyQuest |
| `QuestFailure:` | InqQuest, InqQuestSolves, InqMyQuest |
| `TestSuccess:` | InqOwnsItems, InqYesNo, InqIntStat, InqBoolStat, InqSkillTrained |
| `TestFailure:` | InqOwnsItems, InqYesNo, InqIntStat, InqBoolStat, InqSkillTrained |
| `EventSuccess:` | InqEvent |
| `EventFailure:` | InqEvent |

---

## Script Format

Each block starts with a **Trigger** (no leading dash, ends with colon).
Actions inside a trigger start with `- ActionName: value`.
Branching actions are followed by indented branch labels.

**Indentation: 4 spaces per level. No tabs.**

```
Use:
    - Tell: Hello traveler!
    - InqQuest: MyQuestTimer
        QuestSuccess:
            - Tell: You've already done this quest.
        QuestFailure:
            - Goto: StartQuest

GotoSet: StartQuest
    - Tell: Please help me!
    - StampQuest: MyQuestTimer

Give:
    - InqOwnsItems: 810001, 1
        TestSuccess:
            - TakeItems: 810001, 1
            - Tell: Thank you!
            - Give: 810002
            - StampQuest: MyQuestTimer
        TestFailure:
            - Tell: I have no use for that.

Death:
    - LocalBroadcast: The creature falls!
```

---

## Action Types

### Dialog
| Action | Value | Effect |
|--------|-------|--------|
| `Tell: text` | Message text | Private message to player |
| `Say: text` | Message text | NPC speaks in local chat |
| `LocalBroadcast: text` | Message text | Area-wide broadcast |

### Quest Flags
| Action | Value | Effect |
|--------|-------|--------|
| `InqQuest: QuestName` | Quest flag | Check quest — branches QuestSuccess/QuestFailure |
| `StampQuest: QuestName` | Quest flag | Set quest flag |
| `EraseQuest: QuestName` | Quest flag | Remove quest flag |
| `InqQuestSolves: QuestName, min, max` | Quest flag | Check completion count |
| `UpdateQuest: QuestName` | Quest flag | Increment quest counter |
| `DecrementQuest: QuestName` | Quest flag | Decrement quest counter |
| `SetQuestCompletions: QuestName, count` | Quest flag | Set exact completions |

### Items
| Action | Value | Effect |
|--------|-------|--------|
| `Give: wcid` | Item WCID | Give item to player |
| `TakeItems: wcid, qty` | WCID, quantity | Take items from player |
| `InqOwnsItems: wcid, qty` | WCID, quantity | Check if player owns items — branches TestSuccess/TestFailure |

### XP & Currency
| Action | Value | Effect |
|--------|-------|--------|
| `AwardXP: amount` | Flat XP | Award XP |
| `AwardLevelProportionalXP: N%` | e.g. `5%` | Award % of level XP |
| `AwardLuminance: amount` | Luminance | Award luminance |

### Flow Control
| Action | Value | Effect |
|--------|-------|--------|
| `Goto: label` | GotoSet name | Jump to named GotoSet block |
| `InqYesNo: question` | Question text | Ask yes/no — TestSuccess/TestFailure |
| `InqEvent: EventName` | Event name | Check server event — EventSuccess/EventFailure |

### Stats
| Action | Value | Effect |
|--------|-------|--------|
| `InqIntStat: StatName, min - max` | Stat range | Check int stat value |
| `SetIntStat: StatName, value` | Stat, value | Set int stat |
| `InqSkillTrained: SkillName` | Skill name | Check if skill trained — TestSuccess/TestFailure |

### Motion & Effects
| Action | Value | Effect |
|--------|-------|--------|
| `Motion: MotionName` | e.g. `Bow` | Play NPC animation |

---

## Example: Item Turn-In Quest

```
Use:
    - InqQuest: UlgrimRationsQuestTimer
        QuestSuccess:
            - Tell: I cannot accept more rations so soon, traveler.
        QuestFailure:
            - Goto: AcceptRations

GotoSet: AcceptRations
    - Tell: Bring me 1 Ration Pack if you want to trade.

Give:
    - InqOwnsItems: 29221, 1
        TestSuccess:
            - TakeItems: 29221, 1
            - Tell: Ah, excellent rations! My thanks. Here, take this for your trouble.
            - Give: 29553
            - AwardLevelProportionalXP: 5%
            - AwardLuminance: 2500
            - StampQuest: UlgrimRationsQuestTimer, 1
        TestFailure:
            - Tell: I have no use for that, traveler.
```

Note: `Give:` fires for ANY item the player hands the NPC. Use `InqOwnsItems` inside
the Give block to check which specific item was given. There is no `ReceiveGive` trigger.

---

## No-Argument Actions

These actions take no value — write them **without a colon**:

```
- OpenMe
- CloseMe
- MoveHome
- TurnToTarget
- DeleteSelf
- KillSelf
- RemoveVitaePenalty
- TeleportSelf
```

### Doors and Remote-Controlled Objects

Doors listen for signals via `ReceiveLocalSignal`. The signal name goes in the
trigger line (not the action). Two separate blocks handle open and close:

```
ReceiveLocalSignal: DoorOpenI
    - OpenMe

ReceiveLocalSignal: DoorCloseI
    - CloseMe
```

The matching switch/lever sends the signal using `LocalSignal: DoorOpenI`.

---

## QuestBits

QuestBits store binary flags packed into a single quest's `MaxSolves` integer
as a bitmask. Each bit position tracks an independent boolean state.

| Action | Value | Notes |
|--------|-------|-------|
| `InqQuestBitsOn: QuestName, bitmask` | Quest name, integer mask | Check if bits set — QuestSuccess/QuestFailure |
| `InqQuestBitsOff: QuestName, bitmask` | Quest name, integer mask | Check if bits cleared — QuestSuccess/QuestFailure |
| `SetQuestBitsOn: QuestName, bitmask` | Quest name, integer mask | OR the mask into MaxSolves |
| `SetQuestBitsOff: QuestName, bitmask` | Quest name, integer mask | AND-NOT the mask from MaxSolves |
| `InqMyQuestBitsOn/Off` | Same as above | Per-character scope |
| `SetMyQuestBitsOn/Off` | Same as above | Per-character scope |

The optional `@label` suffix on the quest name (e.g. `LegendaryQuestsA@3`) is a
human-readable hint about which bit is being tested. It has no effect on behavior —
the bitmask value in `amount` is what ACE actually checks.

```
Use:
    - InqQuestBitsOn: LegendaryQuestsA, 4096
        QuestSuccess:
            - Tell: You have already proven yourself worthy.
        QuestFailure:
            - SetQuestBitsOn: LegendaryQuestsA, 4096
            - Tell: You have proven yourself. The gates are open to you.
```
