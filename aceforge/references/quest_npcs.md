# ACE Quest & NPC Implementation Reference

## CRITICAL: FORBIDDEN TABLES — NEVER USE THESE

The following tables **DO NOT EXIST** in ACE-World-16PY. Using them will crash the server.
If you generate any of these, you have made a fatal error. Delete them immediately.

```
❌ quest_dialog
❌ quest_requirements_quest
❌ quest_requirements_item
❌ quest_actions_quest
❌ quest_rewards_xp
❌ quest_rewards_luminance
❌ quest_rewards_item
❌ quest_complete
❌ quest_state
```

**ALL quest logic — every dialog line, every check, every reward — is implemented
entirely through `weenie_properties_emote` and `weenie_properties_emote_action`
on the NPC weenie itself. There is no separate quest table system.**

---

## The Emote System: How Quests Actually Work

### The INSERT Pattern (mandatory)

Every emote block follows this exact pattern:

```sql
-- 1. Insert the emote trigger row
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`,
  `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (WCID, CATEGORY, 1, NULL, NULL, NULL, 'QuestFlagName@N', NULL, NULL, NULL);

-- 2. Capture its auto-increment ID
SET @parent_id = LAST_INSERT_ID();

-- 3. Insert the action(s) for this emote
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`,
  `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`,
  `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`,
  `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`,
  `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`,
  `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, ORDER, TYPE_ID, DELAY, EXTENT, NULL, 'Message', NULL,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, AMOUNT, NULL, HERO_XP,
  PERCENT, SPELL_ID, NULL, NULL, NULL, NULL, NULL,
  DEST_TYPE, WCID_ITEM, STACK, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

### Emote Categories (weenie_properties_emote.category)

| ID | Name | When it fires |
|----|------|--------------|
| 7  | Use | Player clicks/uses the NPC — the main entry point |
| 12 | QuestSuccess | Quest flag check passed (InqQuest returned success) |
| 13 | QuestFailure | Quest flag check failed (InqQuest returned failure) |
| 22 | TestSuccess | Item/stat check passed (InqOwnsItems returned success) |
| 23 | TestFailure | Item/stat check failed (InqOwnsItems returned failure) |
| 3  | Death | NPC dies |
| 6  | Give | Player gives item to NPC |
| 2  | Vendor | Vendor interaction |
| 5  | HeartBeat | Fires on heartbeat interval |

### Key Emote Action Types (weenie_properties_emote_action.type)

| ID | Name | Purpose | Key fields |
|----|------|---------|------------|
| 10 | Tell | Send private message to player | `message` |
| 8  | Say | NPC says out loud (local chat) | `message` |
| 21 | InqQuest | Check quest flag value — branches to QuestSuccess/QuestFailure | `message` = 'QuestName@Value' |
| 22 | StampQuest | Set a quest flag on the player | `message` = 'QuestName, Value' |
| 31 | EraseQuest | Remove a quest flag | `message` = 'QuestName' |
| 76 | InqOwnsItems | Check if player has N of item — branches to TestSuccess/TestFailure | `weenie_Class_Id`, `stack_Size` |
| 74 | TakeItems | Remove items from player inventory | `weenie_Class_Id`, `stack_Size` |
| 62 | AwardNoShareXP | Give XP (solo, not shared) | `amount_64` = XP amount |
| 49 | AwardLevelProportionalXP | Give % of level XP | `percent` = fraction (0.15 = 15%) |
| 113| AwardLuminance | Give luminance | `hero_X_P_64` = luminance amount |
| 56 | CreateTreasure | Give item to player | `weenie_Class_Id`, `stack_Size`, `destination_Type` |
| 70 | SetQuestCompletions | Set quest to specific value | `message` = 'QuestName', `amount` = value |
| 30 | InqQuestSolves | Check number of times completed | `message` = 'QuestName@MaxSolves' |

---

## Quest Logic Pattern: Simple Collection Quest

This is the standard pattern for "collect N items, bring to NPC":

```
Player uses NPC
  → Use (cat=7): InqQuest('QuestName@3')   [check if quest solves >= 3 = completed]
    → QuestFailure (cat=13) [quest not at 3 solves = not completed, proceed]
      → InqQuest('QuestName@1')   [check if quest started = value >= 1]
        → QuestSuccess (cat=12) [quest started, player is in progress]
          → InqOwnsItems(ItemWCID, qty)   [check if player has the items]
            → TestSuccess (cat=22) [has items — complete quest]
                → Tell "Great, you have them!"
                → TakeItems(ItemWCID, qty)
                → AwardNoShareXP / AwardLevelProportionalXP
                → AwardLuminance
                → StampQuest('QuestName, 3')   [mark as done]
            → TestFailure (cat=23) [doesn't have items yet]
                → Tell "Keep looking, bring me X of Item Y"
        → QuestFailure (cat=13) [quest not started yet]
            → Tell "Introduction dialog"
            → StampQuest('QuestName, 1')   [mark quest as started]
    → QuestSuccess (cat=12) [quest already at 3 = completed]
        → Tell "Thank you again, but I don't need more help."
```

### Naming Convention for Quest Flags
- Quest flag names must be a single string with NO spaces: `FreddieFlowerQuest`
- The `@N` suffix in InqQuest means "check if value >= N": `FreddieFlowerQuest@3` = "has this been done 3+ times?"
- StampQuest increments by 1 each time it is called, OR you can use SetQuestCompletions to set a specific value

### InqOwnsItems String Naming
When using InqOwnsItems, the `message` field becomes the label for the branching QuestSuccess/QuestFailure emotes that follow it. Use a unique descriptive name:
- `'OwnsItem-WCID_UniqueN'` — e.g. `'OwnsItem-810063_2'`

---

## Complete Example: Simple Collection Quest NPC

NPC Freddie asks player to collect 5 Wilting Flowers (WCID 810063).

```sql
DELETE FROM `weenie` WHERE `class_Id` = 850011;

INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (850011, 'freddie', 31, '2025-01-01 00:00:00');

INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (850011, 1, 16) /* ItemType - Creature */
     , (850011, 2, 31) /* CreatureType - Human */
     , (850011, 6, -1) /* ItemsCapacity */
     , (850011, 7, -1) /* ContainersCapacity */
     , (850011, 16, 32) /* ItemUseable - Remote */
     , (850011, 25, 275) /* Level */
     , (850011, 93, 6292504) /* PhysicsState */
     , (850011, 95, 8) /* RadarBlipColor - Yellow */
     , (850011, 133, 4) /* ShowableOnRadar */
     , (850011, 134, 16); /* PlayerKillerStatus - RubberGlue */

INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (850011, 1, True) /* Stuck */
     , (850011, 13, False) /* Ethereal */
     , (850011, 14, True) /* GravityStatus */
     , (850011, 15, True) /* LightsStatus */
     , (850011, 19, False) /* Attackable */;

INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (850011, 39, 1.0); /* DefaultScale */

INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (850011, 1, 'Freddie'); /* Name */

INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (850011, 1, 0x02000003) /* Setup - Generic Human Male */
     , (850011, 8, 0x06000002); /* Icon */

-- ENTRY POINT: Player uses NPC → check if quest already completed
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FreddieFlowerQuestStart@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Quest completed already
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FreddieFlowerQuestStart@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'Thank you again for your help. My flowers are safe!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Not yet completed → check if started
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FreddieFlowerQuestStart@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FreddieFlowerQuestStart@1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Started → check if player has flowers
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FreddieFlowerQuestStart@1', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 76 /* InqOwnsItems */, 0, 1, NULL, 'OwnsItem-810063_check', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810063, 5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Has 5 flowers → complete quest
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 22 /* TestSuccess */, 1, NULL, NULL, NULL, 'OwnsItem-810063_check', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'Fantastic! You have found all of my flowers! You are my hero! Here is your reward!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 74 /* TakeItems */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810063, 5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.15, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 22 /* StampQuest */, 0, 1, NULL, 'FreddieFlowerQuestStart, 3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Doesn't have flowers yet
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 23 /* TestFailure */, 1, NULL, NULL, NULL, 'OwnsItem-810063_check', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'You are almost there! I need a total of 5 Wilting Flowers. Keep looking!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- Quest not started yet → introduce quest
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850011, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FreddieFlowerQuestStart@1', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'Greetings, traveler! I''m Freddie. My prize-winning Wilting Flowers just West of Eastham have wilted! Could you bring me 5 of them?', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 22 /* StampQuest */, 0, 1, NULL, 'FreddieFlowerQuestStart, 1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

---

## Rules Summary

1. **NEVER** use quest_dialog, quest_requirements_*, quest_actions_*, quest_rewards_* tables
2. **ALWAYS** use `SET @parent_id = LAST_INSERT_ID();` after every emote INSERT
3. Quest branching works via category matching on the `quest` field: `'QuestName@N'`
4. StampQuest message format: `'QuestName, Value'` (with comma and space)
5. InqQuest message format: `'QuestName@MinValue'`
6. InqOwnsItems message field becomes the label for the following TestSuccess/TestFailure branches
7. All 40 NULL columns in emote_action must be present — use NULL for unused fields
8. AwardLevelProportionalXP uses `percent` field (0.15 = 15% of level XP)
9. AwardLuminance uses `hero_X_P_64` field for the luminance amount
10. NPC wtype=31 (Creature), ItemType(1)=16, set Attackable(19)=False, PlayerKillerStatus(134)=16

---

## CRITICAL: Item Give vs Refuse Category

When a player hands an item to an NPC for a quest, use **Refuse (category=1)** with `weenie_Class_Id` set to the item WCID — NOT Give (category=6).

- `Give (6)` with no `weenie_Class_Id` fires for ANY item given to the NPC
- `Refuse (1)` with `weenie_Class_Id=ITEM_WCID` fires specifically when THAT item is handed to the NPC

```sql
-- CORRECT: Player hands Wilting Flowers (810063) to Freddie
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, ...)
VALUES (850011, 1 /* Refuse */, 1, 810063 /* Wilting Flowers */, NULL, NULL, 'FreddieFlowerQuest@1', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
-- Then InqOwnsItems to check if player has 5...
```

The `quest` field on the Refuse emote row acts as a filter — the emote only fires if the quest flag condition is met.

---

## Quest Naming Conventions (MANDATORY)

Every quest MUST create these named flag entries. Do not skip any of them.

### Standard Collection/Turn-In Quest (non-kill):
```
QuestName           — Main completion counter (StampQuest increments this)
QuestNameStart      — Set to 1 when player accepts, checked for in-progress state  
QuestNameTimer      — Optional daily/weekly cooldown timer (StampQuest after reward)
```

### Kill Task Quest:
```
KillTaskName             — Main kill counter (incremented by kill task system)
KillTaskNameProgress     — In-progress flag, set to 1 when player accepts
KillTaskNameComplete     — Set to 1 when kill count is met
KillTaskNameTimer        — Cooldown timer stamped after reward
```

### Example for Freddie's Flower Quest:
- `FreddieFlowerQuest` — completion counter (values: 0=not started, 1=in progress, 2+=complete)
- `FreddieFlowerQuestStart` — progress tracker
- `FreddieFlowerQuestTimer` — cooldown after reward

### InqQuest logic:
- `FreddieFlowerQuest@2` = "has this quest been completed 2+ times?" → QuestSuccess if yes
- `FreddieFlowerQuestStart@1` = "has start flag been set 1+ times?" → QuestSuccess if yes (in progress)
- StampQuest `'FreddieFlowerQuest, 1'` = set/increment FreddieFlowerQuest by 1

---

## Generator — Always Required for Creature/NPC

Every creature and NPC weenie MUST have a companion generator weenie.
WCID = creature_WCID + 1,000,000.

The generator file must be output as a SEPARATE SQL file with its own FILE: header, NOT appended to the creature file.

```
/* ===== FILE: 1850011 freddie_gen.sql ===== */

DELETE FROM `weenie` WHERE `class_Id` = 1850011;

INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (1850011, 'freddie_gen', 7, '2025-01-01 00:00:00');

INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (1850011, 93, 262144) /* PhysicsState - Hidden */
     , (1850011, 133, 4); /* ShowableOnRadar */

INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (1850011, 1, 850011, 300, 1, 1, 2, 4, -1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

`when_Create=2` = Always (respawn after death), `where_Create=4` = Specific landcell position.
Coordinates are NULL here — the admin fills them in when placing via a spawn tool.

---

## Correct NPC/Creature Property Values

### NPC Standard Properties (type=31, wType=31 Creature)
```sql
INSERT INTO `weenie_properties_int` (...)
VALUES (WCID, 1, 16)    /* ItemType - Creature */
     , (WCID, 2, 31)    /* CreatureType - Human */
     , (WCID, 6, -1)    /* ItemsCapacity */
     , (WCID, 7, -1)    /* ContainersCapacity */
     , (WCID, 16, 32)   /* ItemUseable - Remote */
     , (WCID, 25, 275)  /* Level */
     , (WCID, 93, 6292504) /* PhysicsState */
     , (WCID, 95, 8)    /* RadarBlipColor - Yellow */
     , (WCID, 133, 4)   /* ShowableOnRadar - Always */
     , (WCID, 134, 16)  /* PlayerKillerStatus - RubberGlue */
     , (WCID, 146, 0);  /* XpOverride */

INSERT INTO `weenie_properties_bool` (...)
VALUES (WCID, 1, True)   /* Stuck */
     , (WCID, 19, False); /* Attackable */

INSERT INTO `weenie_properties_float` (...)
VALUES (WCID, 1, 60)    /* HeartbeatInterval */
     , (WCID, 3, 2)     /* HealthRate */
     , (WCID, 4, 5)     /* StaminaRate */
     , (WCID, 5, 1)     /* ManaRate */
     , (WCID, 39, 1.0)  /* DefaultScale */
     , (WCID, 54, 3.0); /* UseRadius */

INSERT INTO `weenie_properties_d_i_d` (...)
VALUES (WCID, 1, 0x02000003) /* Setup - Generic Human Male */
     , (WCID, 8, 0x06001036); /* Icon */
```

