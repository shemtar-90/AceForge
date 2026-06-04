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

## Script Format

Each block starts with a **Trigger** (no leading dash, ends with colon).
Actions inside a trigger start with `- ActionName: value`.
Branching actions (InqQuest, InqEvent, InqOwnsItems) are followed by
indented branch labels (QuestSuccess/QuestFailure, EventSuccess/EventFailure,
TestSuccess/TestFailure) containing more actions.

**Indentation: 4 spaces per level. No tabs.**

```
TriggerName: optional_key
    - Action: value
    - BranchingAction: param
        BranchLabel:
            - Action: value
        OtherBranchLabel:
            - Action: value

GotoSet: label_name
    - Action: value
```

---

## Trigger Types (top-level blocks)

| Trigger | Purpose |
|---------|---------|
| `Use:` | Player clicks/uses the NPC — main entry point |
| `GotoSet: label` | Named sub-routine, jumped to by `- Goto: label` |
| `ReceiveTalkDirect: keyword` | Fires when player sends keyword to NPC via Tell |
| `HeartBeat:` | Fires on NPC heartbeat timer |
| `Death:` | Fires when NPC/creature dies |
| `Give:` | Fires when player gives item to NPC |
| `Wield:` | Fires when item is wielded |
| `PickUp:` | Fires when item is picked up |

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
| `InqQuest: QuestName` | Quest flag name | Check quest — branches QuestSuccess / QuestFailure |
| `StampQuest: QuestName` | Quest flag name | Set quest flag on player |
| `EraseQuest: QuestName` | Quest flag name | Remove quest flag |
| `InqQuestSolves: QuestName` | Quest flag name | Check completion count — branches QuestSuccess / QuestFailure |
| `UpdateQuest: QuestName` | Quest flag name | Increment quest counter |
| `DecrementQuest: QuestName` | Quest flag name | Decrement quest counter |

### Item Checks
| Action | Value | Effect |
|--------|-------|--------|
| `InqOwnsItems: wcid, count` | Item WCID, quantity | Check if player has N items — branches TestSuccess / TestFailure |
| `TakeItems: wcid, count` | Item WCID, quantity | Remove items from player |
| `Give: wcid` | Item WCID | Give item to player |

### Events
| Action | Value | Effect |
|--------|-------|--------|
| `InqEvent: EventName` | Event name | Check if event active — branches EventSuccess / EventFailure |
| `StartEvent: EventName` | Event name | Start a server event |
| `StopEvent: EventName` | Event name | Stop a server event |

### Rewards
| Action | Value | Effect |
|--------|-------|--------|
| `AwardLevelProportionalXP: N%` | Percentage (e.g. `15%`) | Award XP scaled to player level |
| `AwardNoShareXP: amount` | XP amount | Award flat XP (no fellowship share) |
| `AwardLuminance: amount` | Luminance amount | Award luminance |
| `AwardTrainingCredits: N` | Credit count | Award skill training credits |
| `CastSpell: spell_id` | Spell ID | Cast spell on player |

### Navigation
| Action | Value | Effect |
|--------|-------|--------|
| `Goto: label` | GotoSet name | Jump to a named GotoSet block |

### Other
| Action | Value | Effect |
|--------|-------|--------|
| `StampMyQuest: QuestName` | Quest flag | Set quest flag on the NPC itself |
| `InqMyQuest: QuestName` | Quest flag | Check NPC's own quest flag |
| `MoveHome:` | *(none)* | NPC returns to home position |
| `OpenMe:` | *(none)* | Open this object |
| `CloseMe:` | *(none)* | Close this object |
| `DeleteSelf:` | *(none)* | Remove this weenie from world |

---

## Branching Rules

**InqQuest / InqQuestSolves / InqMyQuest** → branches: `QuestSuccess:` / `QuestFailure:`
Both branches keyed by quest name (ACE matches automatically).

**InqOwnsItems** → branches: `TestSuccess:` / `TestFailure:`
Success is keyed by auto-generated key. Failure fires for any unmatched test in the block.

**InqEvent** → branches: `EventSuccess:` / `EventFailure:`
Success keyed by event name. Failure uses null key (fires for any unmatched test).

---

## Complete Examples

### Simple greeter NPC
```
-- EMOTE SCRIPT (WCID: 850001)
Use:
    - Tell: Greetings, traveler! Welcome to Asheron's Call.
-- END EMOTE SCRIPT
```

### Quest turn-in NPC
```
-- EMOTE SCRIPT (WCID: 850002)
Use:
    - InqQuest: SlayerTask
        QuestSuccess:
            - Tell: You have proven yourself a great warrior!
            - TakeItems: 810051, 10
            - AwardLevelProportionalXP: 20%
            - StampQuest: SlayerTaskDone
        QuestFailure:
            - Tell: Bring me 10 Watcher Fangs, and I shall reward you.
            - StampQuest: SlayerTask
-- END EMOTE SCRIPT
```

### Multi-stage quest NPC (two quest checks in sequence)
```
-- EMOTE SCRIPT (WCID: 850003)
Use:
    - InqQuest: QuestStageOne
        QuestSuccess:
            - Goto: CheckStageTwo
        QuestFailure:
            - Tell: You must complete Stage One first.

GotoSet: CheckStageTwo
    - InqQuest: QuestStageTwo
        QuestSuccess:
            - Tell: You have completed all stages! Here is your reward.
            - AwardLevelProportionalXP: 25%
        QuestFailure:
            - Tell: You must complete Stage Two before claiming your reward.
-- END EMOTE SCRIPT
```

### NPC that checks for items before accepting quest
```
-- EMOTE SCRIPT (WCID: 850004)
Use:
    - InqOwnsItems: 810051, 5
        TestSuccess:
            - TakeItems: 810051, 5
            - Tell: Thank you for the components!
            - AwardLevelProportionalXP: 10%
            - StampQuest: ComponentsDelivered
        TestFailure:
            - Tell: I need 5 Mana Shards before I can help you.
-- END EMOTE SCRIPT
```

### NPC with keyword-triggered interactions
```
-- EMOTE SCRIPT (WCID: 850005)
Use:
    - Tell: Speak the ancient words: 'begin' to start, 'status' to check your progress.

ReceiveTalkDirect: begin
    - InqQuest: AncientTrial
        QuestSuccess:
            - Tell: You have already begun the trial!
        QuestFailure:
            - Tell: The trial has begun. Seek the three stones.
            - StampQuest: AncientTrial

ReceiveTalkDirect: status
    - InqQuest: AncientTrial
        QuestSuccess:
            - Tell: You are on the path. The trial awaits your completion.
        QuestFailure:
            - Tell: You have not yet begun the Ancient Trial.
-- END EMOTE SCRIPT
```

### Event-gated NPC
```
-- EMOTE SCRIPT (WCID: 850006)
Use:
    - InqEvent: HarvestFestival
        EventSuccess:
            - Tell: Welcome to the Harvest Festival! Take this pumpkin as our gift.
            - Give: 810100
        EventFailure:
            - Tell: The festival has not yet begun. Return when the harvest moon rises.
-- END EMOTE SCRIPT
```

---

## What NOT to Do

❌ NEVER write this:
```sql
INSERT INTO `weenie_properties_emote` ...
INSERT INTO `weenie_properties_emote_action` ...
SET @parent_id = LAST_INSERT_ID();
```

✅ ALWAYS write this instead:
```
-- EMOTE SCRIPT (WCID: 850000)
Use:
    - Tell: Hello!
-- END EMOTE SCRIPT
```

The `-- EMOTE SCRIPT` block must appear in the SQL file, outside any other SQL statement.
Place it after the main weenie INSERT block and before any `weenie_properties_create_list` entries.
