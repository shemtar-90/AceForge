# ACE SQL Compact Examples — Local Model Reference

These are real ACEmulator SQL examples. Copy their exact table names, column names, and formatting.
NEVER use CREATE TABLE. NEVER invent column names. Use ONLY these table names.

---

## EXAMPLE 1: Simple Item (use for items, gems, scrolls, food)

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810001;

INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810001, 'shard_of_valor', 6, '2025-01-01 00:00:00');

INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810001,   1,      8192) /* ItemType */
     , (810001,   5,        10) /* EncumbranceVal */
     , (810001,   8,         5) /* Mass */
     , (810001,  16,         8) /* ItemUseable */
     , (810001,  19,       500) /* Value */
     , (810001,  93,      1044) /* PhysicsState */;

INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810001,  22, False) /* Inscribable */;

INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810001,   1, 'Shard of Valor') /* Name */
     , (810001,  15, 'A glowing shard humming with ancient power.') /* ShortDesc */;

INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810001,   1, 0x02000155) /* Setup */
     , (810001,   3, 0x20000014) /* SoundTable */
     , (810001,   8, 0x06001310) /* Icon */
     , (810001,  22, 0x3400002B) /* PhysicsEffectTable */;
```

---

## EXAMPLE 2: Creature/NPC (use for monsters, bosses, vendors, quest givers)

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800100;

INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800100, 'iron_sentinel', 10, '2025-01-01 00:00:00');

INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800100,   1,        16) /* ItemType */
     , (800100,   2,         3) /* CreatureType - Undead */
     , (800100,  25,       150) /* Level */
     , (800100,  93,      3080) /* PhysicsState */
     , (800100, 133,         4) /* ShowableOnRadar */
     , (800100, 146,   3000000) /* XpOverride */;

INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800100,   1, True ) /* Stuck */
     , (800100,  19, True ) /* Attackable */
     , (800100, 120, True ); /* TreasureCorpse */

INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800100,   1,        5) /* HeartbeatInterval */
     , (800100,   3,      0.5) /* HealthRate */
     , (800100,  31,       20) /* VisualAwarenessRange */
     , (800100,  39,      1.2) /* DefaultScale */;

INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800100,   1, 'Iron Sentinel') /* Name */;

INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800100,   1, 0x020002A5) /* Setup */
     , (800100,   2, 0x09000010) /* MotionTable */
     , (800100,   3, 0x20000009) /* SoundTable */
     , (800100,   8, 0x0600108A) /* Icon */
     , (800100,  22, 0x34000026) /* PhysicsEffectTable */
     , (800100,  35,       3101); /* DeathTreasureType */

INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (800100,   1, 200, 0, 0) /* Strength */
     , (800100,   2, 180, 0, 0) /* Endurance */
     , (800100,   3, 160, 0, 0) /* Quickness */
     , (800100,   4, 160, 0, 0) /* Coordination */
     , (800100,   5, 100, 0, 0) /* Focus */
     , (800100,   6, 100, 0, 0); /* Self */

INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (800100,   1, 800, 0, 0, 800) /* MaxHealth */
     , (800100,   3, 600, 0, 0, 600) /* MaxStamina */
     , (800100,   5, 400, 0, 0, 400); /* MaxMana */

INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (800100,   6, 0, 2, 0, 180, 0, 0) /* MeleeDefense */
     , (800100,  44, 0, 2, 0, 200, 0, 0); /* HeavyWeapons */

INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (800100, 0, 4, 0, 0, 80, 80, 80, 80, 80, 80, 80, 80, 0, 1, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0) /* Head */
     , (800100, 1, 4, 0, 0, 80, 80, 80, 80, 80, 80, 80, 80, 0, 1, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0, 0.33, 0, 0); /* Chest */
```

---

## EXAMPLE 3: Quest Flag (use for quest entries)

```sql
DELETE FROM `quest` WHERE `name` = 'MyQuestFlag';

INSERT INTO `quest` (`name`, `min_Delta`, `max_Solves`, `message`, `last_Modified`)
VALUES ('MyQuestFlag', 86400, 1, 'You have completed this quest.', '2025-01-01 00:00:00');
```

---

## EXAMPLE 4: NPC with emote dialogue

```sql
DELETE FROM `weenie` WHERE `class_Id` = 850010;

INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (850010, 'quest_giver_elder', 10, '2025-01-01 00:00:00');

INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (850010,   1,        16) /* ItemType */
     , (850010,  93,      3076) /* PhysicsState */
     , (850010, 133,         4) /* ShowableOnRadar */;

INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (850010,   1, True ) /* Stuck */
     , (850010,  19, False) /* Attackable */;

INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (850010,   1, 'Elder Quinevas') /* Name */;

INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (850010,   1, 0x0200010D) /* Setup */
     , (850010,   2, 0x09000001) /* MotionTable */
     , (850010,   3, 0x20000001) /* SoundTable */
     , (850010,   8, 0x06001F2E) /* Icon */
     , (850010,  22, 0x34000004); /* PhysicsEffectTable */

INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (850010, 9 /* Refuse */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

SET @parent_id = LAST_INSERT_ID();

INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'Seek your own path, traveler. Return when you are ready.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

---

## KEY RULES (repeat for emphasis)
- Table names use backtick quoting: `weenie`, `weenie_properties_int`, `weenie_properties_bool`, etc.
- Column `object_Id` (NOT `weenie_class_id`, NOT `id`, NOT `class_id`)
- Column `type` (NOT `property_name`, NOT `property_type`)  
- Column `value` (NOT `val`, NOT `property_value`)
- NEVER use `CREATE TABLE` — tables already exist in ACE database
- NEVER use custom column names
- Always start with `DELETE FROM \`weenie\` WHERE \`class_Id\` = WCID;`
- Always include `last_Modified` in the weenie INSERT
