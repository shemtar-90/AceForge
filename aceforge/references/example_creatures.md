# Creature Examples — Live Server Reference Examples
These are real SQL files from the Shattered Dawn ACEmulator server.
Use these as the authoritative format for all generated SQL.

## 800000 Rift Echo.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800000;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800000, 'Rift Echo', 10, '2025-04-06 09:53:32') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800000,   1,         16) /* ItemType - Creature */
     , (800000,   2,         19) /* CreatureType - Virindi */
     , (800000,   6,         -1) /* ItemsCapacity */
     , (800000,   7,         -1) /* ContainersCapacity */
     , (800000,  16,          1) /* ItemUseable - No */
     , (800000,  25,        275) /* Level */
     , (800000,  27,          0) /* ArmorType - None */
     , (800000,  40,          2) /* CombatMode - Melee */
     , (800000,  68,          5) /* TargetingTactic - Random, LastDamager */
     , (800000,  69,          4) /* CombatTactic - LastDamager */
     , (800000,  93,       3080) /* PhysicsState - ReportCollisions, Gravity, LightingOn */
     , (800000, 133,          4) /* ShowableOnRadar - ShowAlways */
     , (800000, 146,   34000000) /* XpOverride */
     , (800000, 308,          5) /* DamageResistenceRating */
     , (800000, 316,          5) /* CritDamageResistenceRating */
     , (800000, 332,      25000) /* LuminanceAward */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800000,   1, True ) /* Stuck */
     , (800000,   6, True ) /* AiUsesMana */
     , (800000,  11, False) /* IgnoreCollisions */
     , (800000,  12, True ) /* ReportCollisions */
     , (800000,  13, False) /* Ethereal */
     , (800000,  14, True ) /* GravityStatus */
     , (800000,  15, True ) /* LightsStatus */
     , (800000,  19, True ) /* Attackable */
     , (800000,  50, True ) /* NeverFailCasting */
     , (800000, 120, True ) /* TreasureCorpse */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800000,   1,       5) /* HeartbeatInterval */
     , (800000,   2,       0) /* HeartbeatTimestamp */
     , (800000,   3,     0.6) /* HealthRate */
     , (800000,   4,     0.5) /* StaminaRate */
     , (800000,   5,       2) /* ManaRate */
     , (800000,  12,   0.667) /* Shade */
     , (800000,  13,     0.9) /* ArmorModVsSlash */
     , (800000,  14,       1) /* ArmorModVsPierce */
     , (800000,  15,       1) /* ArmorModVsBludgeon */
     , (800000,  16,       1) /* ArmorModVsCold */
     , (800000,  17,     0.8) /* ArmorModVsFire */
     , (800000,  18,       1) /* ArmorModVsAcid */
     , (800000,  19,       1) /* ArmorModVsElectric */
     , (800000,  31,      18) /* VisualAwarenessRange */
     , (800000,  34,       1) /* PowerupTime */
     , (800000,  36,       1) /* ChargeSpeed */
     , (800000,  64,       1) /* ResistSlash */
     , (800000,  65,       1) /* ResistPierce */
     , (800000,  66,       1) /* ResistBludgeon */
     , (800000,  67,       1) /* ResistFire */
     , (800000,  68,       1) /* ResistCold */
     , (800000,  69,       1) /* ResistAcid */
     , (800000,  70,       1) /* ResistElectric */
     , (800000,  80,       3) /* AiUseMagicDelay */
     , (800000, 104,      10) /* ObviousRadarRange */
     , (800000, 122,       2) /* AiAcquireHealth */
     , (800000, 125,       1) /* ResistHealthDrain */
     , (800000, 165,       1) /* ArmorModVsNether */
     , (800000, 166,     0.5) /* ResistNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800000,   1, 'Rift Echo') /* Name */
     , (800000,  45, 'RiftEchoKT') /* KillQuest */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800000,   1, 0x02000A6E) /* Setup */
     , (800000,   2, 0x0900008F) /* MotionTable */
     , (800000,   3, 0x20000059) /* SoundTable */
     , (800000,   4, 0x30000027) /* CombatTable */
     , (800000,   8, 0x060020D6) /* Icon */
     , (800000,  22, 0x3400008F) /* PhysicsEffectTable */
     , (800000,  35,       3111) /* DeathTreasureType - Loot Tier: 7 */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (800000,  0,  4, 100, 0.75,  100,  250,  250,  250,  250,  250,  250,  250,    0, 1,  0.5,  0.2,    0,  0.5,  0.2,    0,    0,    0,    0,    0,    0,    0) /* Head */
     , (800000, 10,  4, 100,    0,  100,  250,  250,  250,  250,  250,  250,  250,    0, 2,  0.2,  0.4,  0.5,  0.2,  0.4,  0.5,    0,    0,    0,    0,    0,    0) /* FrontLeg */
     , (800000, 12,  4, 100, 0.75,  100,  250,  250,  250,  250,  250,  250,  250,    0, 3,    0,    0, 0.25,    0,    0, 0.25,    0,    0,    0,    0,    0,    0) /* FrontFoot */
     , (800000, 13,  4, 100,    0,  100,  250,  250,  250,  250,  250,  250,  250,    0, 2,    0,    0,    0,    0,    0,    0,  0.3,  0.4,  0.5,  0.3,  0.4,  0.5) /* RearLeg */
     , (800000, 15,  4, 100, 0.75,  100,  250,  250,  250,  250,  250,  250,  250,    0, 3,    0,    0,    0,    0,    0,    0,    0,    0, 0.25,    0,    0, 0.25) /* RearFoot */
     , (800000, 16,  4, 100,    0,  100,  250,  250,  250,  250,  250,  250,  250,    0, 2,  0.3,  0.4, 0.25,  0.3,  0.4, 0.25,  0.6,  0.5, 0.25,  0.6,  0.5, 0.25) /* Torso */
     , (800000, 22, 64, 100, 0.75,  100,  250,  250,  250,  250,  250,  250,  250,    0, 2,    0,    0,    0,    0,    0,    0,  0.1,  0.1,    0,  0.1,  0.1,    0) /* Breath */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (800000,   1, 275, 0, 0) /* Strength */
     , (800000,   2, 275, 0, 0) /* Endurance */
     , (800000,   3, 250, 0, 0) /* Quickness */
     , (800000,   4, 250, 0, 0) /* Coordination */
     , (800000,   5, 225, 0, 0) /* Focus */
     , (800000,   6, 225, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (800000,   1, 1800, 0, 0,2500) /* MaxHealth */
     , (800000,   3, 1200, 0, 0,2500) /* MaxStamina */
     , (800000,   5, 1000, 0, 0,2500) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (800000,  6, 0, 2, 0, 300, 0, 0) /* MeleeDefense        Trained */
     , (800000,  7, 0, 2, 0, 300, 0, 0) /* MissileDefense      Trained */
     , (800000, 15, 0, 2, 0, 300, 0, 0) /* MagicDefense        Trained */
     , (800000, 16, 0, 2, 0, 300, 0, 0) /* ManaConversion      Trained */
     , (800000, 31, 0, 2, 0, 300, 0, 0) /* CreatureEnchantment Trained */
     , (800000, 33, 0, 2, 0, 300, 0, 0) /* LifeMagic           Trained */
     , (800000, 34, 0, 2, 0, 300, 0, 0) /* WarMagic            Trained */
     , (800000, 41, 0, 2, 0, 420, 0, 0) /* TwoHandedCombat     Trained */
     , (800000, 43, 0, 2, 0, 300, 0, 0) /* VoidMagic           Trained */
     , (800000, 44, 0, 2, 0, 420, 0, 0) /* HeavyWeapons        Trained */
     , (800000, 45, 0, 2, 0, 420, 0, 0) /* LightWeapons        Trained */
     , (800000, 46, 0, 2, 0, 420, 0, 0) /* FinesseWeapons      Trained */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (800000,  1788,   1.04) /* Eye of the Storm */
     , (800000,  4312,  1.042) /* Incantation of Imperil Other */
     , (800000,  4450,  1.045) /* Incantation of Lightning Blast */
     , (800000,  4451,  1.048) /* Incantation of Lightning Bolt */
     , (800000,  4483,  1.043) /* Incantation of Lightning Vulnerability Other */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 3 /* Death */, 0.08, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'RiftShardsTimer@4', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftShardsTimer@4', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 76 /* InqOwnsItems */, 0, 1, NULL, 'OwnsItem-810008_5', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810008, 50, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 23 /* TestFailure */, 1, NULL, NULL, NULL, 'OwnsItem-810008_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810008, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 20 /* ReceiveCritical */, 0.01, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'AuraBuff@5', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'AuraBuff@5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 33 /* IncrementQuest */, 0, 1, NULL, 'Aura', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 67 /* Goto */, 0, 1, NULL, 'AuraCheck', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'AuraBuff@5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Your Aura has reset!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 31 /* EraseQuest */, 0, 1, NULL, 'AuraBuff', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 31 /* EraseQuest */, 0, 1, NULL, 'Aura', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 22 /* StampQuest */, 0, 1, NULL, 'AuraBuff', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 32 /* GotoSet */, 1, NULL, NULL, NULL, 'AuraCheck', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'Aura@100-100_5', NULL, 100, 100, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'Aura@100-100_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.049999997, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'Aura@100-100_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'Aura@80-99_5', NULL, 80, 99, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'Aura@80-99_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.04, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'Aura@80-99_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'Aura@60-79_5', NULL, 60, 79, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'Aura@60-79_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.03, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'Aura@60-79_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'Aura@40-59_5', NULL, 40, 59, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'Aura@40-59_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.02, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'Aura@40-59_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'Aura@20-39_5', NULL, 20, 39, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'Aura@20-39_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.01, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'Aura@20-39_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have %tqc/100 Aura! You will earn an XP bonus after earning 20 Aura.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 800001 RiftEchoGen.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800001;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800001, 'RiftEchoGen', 1, '2021-11-01 00:00:00') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800001,  81,          5) /* MaxGeneratedObjects */
     , (800001,  82,          5) /* InitGeneratedObjects */
     , (800001,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800001,   1, True ) /* Stuck */
     , (800001,  11, True ) /* IgnoreCollisions */
     , (800001,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800001,  41,     60) /* RegenerationInterval */
     , (800001,  43,     50) /* GeneratorRadius */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800001,   1, 'RiftEchoGen') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800001,   1, 0x0200026B) /* Setup */
     , (800001,   8, 0x06001066) /* Icon */;
INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (800001, -1, 800000, 1, 5, 5, 1, 2, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate Kou-an Wasp (850136) (x1 up to max of 2) - Regenerate upon Destruction - Location to (re)Generate: Scatter */;
```

## 800008 Dimensional Anchor.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800008;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800008, 'Dimensional Anchor', 1, '2026-01-22 05:57:02') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800008,  16,         32) /* ItemUseable - Remote */
     , (800008,  81,          6) /* MaxGeneratedObjects */
     , (800008,  82,          6) /* InitGeneratedObjects */
     , (800008,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (800008, 133,          4) /* ShowableOnRadar - ShowAlways */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800008,   1, True ) /* Stuck */
     , (800008,  11, True ) /* IgnoreCollisions */
     , (800008,  18, False) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800008,  39,       2) /* DefaultScale */
     , (800008,  41,      60) /* RegenerationInterval */
     , (800008,  43,      10) /* GeneratorRadius */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800008,   1, 'Dimensional Anchor') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800008,   1, 0x020014FB) /* Setup */
     , (800008,   2, 0x09000229) /* MotionTable */
     , (800008,   3, 0x2000005F) /* SoundTable */
     , (800008,   8, 0x060022C4) /* Icon */
     , (800008,  22, 0x3400006B) /* PhysicsEffectTable */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'DimensionalAnchorTimer@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'DimensionalAnchorTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have too recently completed this daily task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'DimensionalAnchorTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 67 /* Goto */, 0, 1, NULL, 'DisableAnchor', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 32 /* GotoSet */, 1, NULL, NULL, NULL, 'DisableAnchor', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'DimensionalAnchorDisabled@14', NULL, 14, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'DimensionalAnchorDisabled@14', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 76 /* InqOwnsItems */, 0, 1, NULL, 'OwnsItem-810007_4', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810007, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 22 /* TestSuccess */, 1, NULL, NULL, NULL, 'OwnsItem-810007_4', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 74 /* TakeItems */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810007, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 52 /* ForceMotion */, 0, 1, 0x1300007E /* ClapHands */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 18 /* DirectBroadcast */, 3, 1, NULL, 'You have disabled a Dimensional Anchor.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 18 /* DirectBroadcast */, 2, 1, NULL, 'You have disabled 15 Dimensional Anchors! Here is your reward:', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 67 /* Goto */, 0, 1, NULL, 'Reward', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 32 /* GotoSet */, 1, NULL, NULL, NULL, 'Reward', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 31 /* EraseQuest */, 0, 1, NULL, 'DimensionalAnchorDisabled', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 22 /* StampQuest */, 0, 1, NULL, 'DimensionalAnchorTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 31 /* EraseQuest */, 0, 1, NULL, 'DimensionalAnchorsCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 22 /* StampQuest */, 0, 1, NULL, 'DimensionalAnchorsCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 77 /* DeleteSelf */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 23 /* TestFailure */, 1, NULL, NULL, NULL, 'OwnsItem-810007_4', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'This requires an Anchora Crystal to disable.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'DimensionalAnchorDisabled@14', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 76 /* InqOwnsItems */, 0, 1, NULL, 'OwnsItem-810007_5', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810007, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 22 /* TestSuccess */, 1, NULL, NULL, NULL, 'OwnsItem-810007_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 74 /* TakeItems */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810007, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 52 /* ForceMotion */, 0, 1, 0x1300007E /* ClapHands */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 18 /* DirectBroadcast */, 3, 1, NULL, 'You have disabled a Dimensional Anchor.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 33 /* IncrementQuest */, 0, 1, NULL, 'DimensionalAnchorDisabled', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 77 /* DeleteSelf */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (800008, 23 /* TestFailure */, 1, NULL, NULL, NULL, 'OwnsItem-810007_5', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'This requires a Stabil Crystal to disable.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (800008, -1, 800011, 1, 5, 5, 1, 2, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate Kou-an Wasp (850136) (x1 up to max of 2) - Regenerate upon Destruction - Location to (re)Generate: Scatter */
     , (800008, -1, 800009, 1, 1, 1, 1, 1, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate Kou-an Wasp (850136) (x1 up to max of 2) - Regenerate upon Destruction - Location to (re)Generate: Scatter */;
```

## 800009 Dimensional Anchor Essence.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800009;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800009, 'DimensionalAnchorEssence', 1, '2005-02-09 10:00:00') /* General */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800009,   1,        128) /* ItemType - Misc */
     , (800009,  93,       3084) /* PhysicsState - Ethereal, ReportCollisions, Gravity, LightingOn */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800009,   1, True ) /* Stuck */
     , (800009,  11, False) /* IgnoreCollisions */
     , (800009,  12, True ) /* ReportCollisions */
     , (800009,  13, True ) /* Ethereal */
     , (800009,  15, True ) /* LightsStatus */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800009,  39,       0.15) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800009,   1, 'DAEssence') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800009,   1,   33560582) /* Setup */
     , (800009,   2,  150994947) /* MotionTable */
     , (800009,   8,  100667499) /* Icon */;
```

## 800010 DimensionalAnchorGen.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 800010;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (800010, 'DimensionalAnchorGen', 1, '2021-11-01 00:00:00') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (800010,  81,          1) /* MaxGeneratedObjects */
     , (800010,  82,          1) /* InitGeneratedObjects */
     , (800010,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (800010,   1, True ) /* Stuck */
     , (800010,  11, True ) /* IgnoreCollisions */
     , (800010,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (800010,  41,     120) /* RegenerationInterval */
     , (800010,  43,       1) /* GeneratorRadius */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (800010,   1, 'DimensionalAnchorGen') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (800010,   1, 0x0200026B) /* Setup */
     , (800010,   8, 0x06001066) /* Icon */;
INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (800010, -1, 800008, 1, 1, 1, 1, 1, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate Kou-an Wasp (850136) (x1 up to max of 2) - Regenerate upon Destruction - Location to (re)Generate: Scatter */;
```

## 840029 Ilristras.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 840029;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (840029, 'Ilristras', 10, '2024-12-01 12:24:07') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (840029,   1,         16) /* ItemType - Creature */
     , (840029,   2,         19) /* CreatureType - Virindi */
     , (840029,   3,         39) /* PaletteTemplate - Black */
     , (840029,   6,         -1) /* ItemsCapacity */
     , (840029,   7,         -1) /* ContainersCapacity */
     , (840029,  16,          1) /* ItemUseable - No */
     , (840029,  25,        275) /* Level */
     , (840029,  27,          0) /* ArmorType - None */
     , (840029,  40,          2) /* CombatMode - Melee */
     , (840029,  68,          5) /* TargetingTactic - Random, LastDamager */
     , (840029,  69,          4) /* CombatTactic - LastDamager */
     , (840029,  93,       3080) /* PhysicsState - ReportCollisions, Gravity, LightingOn */
     , (840029, 133,          4) /* ShowableOnRadar - ShowAlways */
     , (840029, 146,    9500000) /* XpOverride */
     , (840029, 290,          1) /* ReceiveLocalSignals */
     , (840029, 291,         40) /* ReceiveLocalSignalRange */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (840029,   1, True ) /* Stuck */
     , (840029,   6, True ) /* AiUsesMana */
     , (840029,  11, False) /* IgnoreCollisions */
     , (840029,  12, True ) /* ReportCollisions */
     , (840029,  13, False) /* Ethereal */
     , (840029,  14, True ) /* GravityStatus */
     , (840029,  15, True ) /* LightsStatus */
     , (840029,  19, True ) /* Attackable */
     , (840029,  50, True ) /* NeverFailCasting */
     , (840029, 120, False) /* TreasureCorpse */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (840029,   1,       5) /* HeartbeatInterval */
     , (840029,   2,       0) /* HeartbeatTimestamp */
     , (840029,   3,     0.6) /* HealthRate */
     , (840029,   4,     0.5) /* StaminaRate */
     , (840029,   5,       2) /* ManaRate */
     , (840029,  12,   0.667) /* Shade */
     , (840029,  13,     0.9) /* ArmorModVsSlash */
     , (840029,  14,       1) /* ArmorModVsPierce */
     , (840029,  15,       1) /* ArmorModVsBludgeon */
     , (840029,  16,       1) /* ArmorModVsCold */
     , (840029,  17,     0.9) /* ArmorModVsFire */
     , (840029,  18,       1) /* ArmorModVsAcid */
     , (840029,  19,       1) /* ArmorModVsElectric */
     , (840029,  31,      18) /* VisualAwarenessRange */
     , (840029,  34,       1) /* PowerupTime */
     , (840029,  36,       1) /* ChargeSpeed */
     , (840029,  39,     2.3) /* DefaultScale */
     , (840029,  64,     0.7) /* ResistSlash */
     , (840029,  65,     0.6) /* ResistPierce */
     , (840029,  66,     0.6) /* ResistBludgeon */
     , (840029,  67,     0.7) /* ResistFire */
     , (840029,  68,     0.7) /* ResistCold */
     , (840029,  69,     0.6) /* ResistAcid */
     , (840029,  70,     0.7) /* ResistElectric */
     , (840029,  76,     0.2) /* Translucency */
     , (840029,  80,       3) /* AiUseMagicDelay */
     , (840029, 104,      10) /* ObviousRadarRange */
     , (840029, 122,       2) /* AiAcquireHealth */
     , (840029, 125,     0.8) /* ResistHealthDrain */
     , (840029, 165,       1) /* ArmorModVsNether */
     , (840029, 166,     0.3) /* ResistNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (840029,   1, 'Ilristras') /* Name */
     , (840029,  45, 'IlristrasKT') /* KillQuest */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (840029,   1, 0x02001BCD) /* Setup */
     , (840029,   2, 0x0900021F) /* MotionTable */
     , (840029,   3, 0x20000012) /* SoundTable */
     , (840029,   4, 0x3000000D) /* CombatTable */
     , (840029,   6, 0x040009B2) /* PaletteBase */
     , (840029,   7, 0x10000854) /* ClothingBase */
     , (840029,   8, 0x06001227) /* Icon */
     , (840029,  22, 0x34000029) /* PhysicsEffectTable */
     , (840029,  35,       2000) /* DeathTreasureType - Loot Tier: 8 */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (840029,  0,  0,625, 0.25, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 1, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0) /* Head */
     , (840029,  1, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 2, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0) /* Chest */
     , (840029,  2, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 3,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0) /* Abdomen */
     , (840029,  3, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 1, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0) /* UpperArm */
     , (840029,  4, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 2,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0) /* LowerArm */
     , (840029,  5, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 2,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0) /* Hand */
     , (840029,  6, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 3,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18) /* UpperLeg */
     , (840029,  7, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 3,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6) /* LowerLeg */
     , (840029,  8, 32,625,    0, 2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,    0, 3,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22) /* Foot */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (840029,   1, 500, 0, 0) /* Strength */
     , (840029,   2, 500, 0, 0) /* Endurance */
     , (840029,   3, 400, 0, 0) /* Quickness */
     , (840029,   4, 400, 0, 0) /* Coordination */
     , (840029,   5, 350, 0, 0) /* Focus */
     , (840029,   6, 350, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (840029,   1,324000, 0, 0,324000) /* MaxHealth */
     , (840029,   3, 50000, 0, 0,50000) /* MaxStamina */
     , (840029,   5, 50000, 0, 0,50000) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (840029,  6, 0, 2, 0, 500, 0, 0) /* MeleeDefense        Trained */
     , (840029,  7, 0, 2, 0, 375, 0, 0) /* MissileDefense      Trained */
     , (840029, 15, 0, 2, 0, 375, 0, 0) /* MagicDefense        Trained */
     , (840029, 16, 0, 2, 0, 400, 0, 0) /* ManaConversion      Trained */
     , (840029, 31, 0, 2, 0, 600, 0, 0) /* CreatureEnchantment Trained */
     , (840029, 33, 0, 2, 0, 600, 0, 0) /* LifeMagic           Trained */
     , (840029, 34, 0, 2, 0, 400, 0, 0) /* WarMagic            Trained */
     , (840029, 41, 0, 2, 0, 460, 0, 0) /* TwoHandedCombat     Trained */
     , (840029, 43, 0, 2, 0, 400, 0, 0) /* VoidMagic           Trained */
     , (840029, 44, 0, 2, 0, 460, 0, 0) /* HeavyWeapons        Trained */
     , (840029, 45, 0, 2, 0, 460, 0, 0) /* LightWeapons        Trained */
     , (840029, 46, 0, 2, 0, 460, 0, 0) /* FinesseWeapons      Trained */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (840029, 20 /* ReceiveCritical */, 0.05, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 88 /* LocalSignal */, 0, 1, NULL, 'BallsOfDeath', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 4 /* MoveHome */, 12, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (840029, 20 /* ReceiveCritical */, 0.07, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 14 /* CastSpell */, 2, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4312 /* Incantation of Imperil Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4292 /* Incantation of Bafflement Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4294 /* Incantation of Clumsiness Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (840029, 20 /* ReceiveCritical */, 0.15, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 2, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4658 /* Incantation of Stamina to Health Self */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 19 /* CastSpellInstant */, 2, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4656 /* Incantation of Mana to Stamina Self */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 840030 IlristrasGen.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 840030;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (840030, 'IlristrasGen', 1, '2021-11-01 00:00:00') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (840030,  81,          1) /* MaxGeneratedObjects */
     , (840030,  82,          1) /* InitGeneratedObjects */
     , (840030,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (840030,   1, True ) /* Stuck */
     , (840030,  11, True ) /* IgnoreCollisions */
     , (840030,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (840030,  41,   10800) /* RegenerationInterval */
     , (840030,  43,       1) /* GeneratorRadius */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (840030,   1, 'IlristrasGen') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (840030,   1, 0x0200026B) /* Setup */
     , (840030,   8, 0x06001066) /* Icon */;
INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (840030, -1, 840029, 1, 1, 1, 1, 1, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate Kou-an Wasp (850136) (x1 up to max of 2) - Regenerate upon Destruction - Location to (re)Generate: Scatter */;
```

## 840031 Ilristras CastBot.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 840031;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (840031, 'Ilristras CastBot', 10, '2024-12-01 12:37:25') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (840031,   1,         16) /* ItemType - Creature */
     , (840031,   2,         31) /* CreatureType - Human */
     , (840031,   6,         -1) /* ItemsCapacity */
     , (840031,   7,         -1) /* ContainersCapacity */
     , (840031,   8,        120) /* Mass */
     , (840031,  16,          1) /* ItemUseable - No */
     , (840031,  25,        999) /* Level */
     , (840031,  27,          0) /* ArmorType - None */
     , (840031,  93,    6292508) /* PhysicsState - Ethereal, ReportCollisions, IgnoreCollisions, Gravity, ReportCollisionsAsEnvironment, EdgeSlide */
     , (840031,  95,          8) /* RadarBlipColor - Yellow */
     , (840031, 133,          0) /* ShowableOnRadar - Undefined */
     , (840031, 134,         16) /* PlayerKillerStatus - RubberGlue */
     , (840031, 146,       1894) /* XpOverride */
     , (840031, 290,          1) /* ReceiveLocalSignals */
     , (840031, 291,         40) /* ReceiveLocalSignalRange */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (840031,   1, True ) /* Stuck */
     , (840031,  12, True ) /* ReportCollisions */
     , (840031,  13, True ) /* Ethereal */
     , (840031,  18, True ) /* Visibility */
     , (840031,  19, False) /* Attackable */
     , (840031,  41, True ) /* ReportCollisionsAsEnvironment */
     , (840031,  42, True ) /* AllowEdgeSlide */
     , (840031,  50, True ) /* NeverFailCasting */
     , (840031,  52, True ) /* AiImmobile */
     , (840031,  65, True ) /* IgnoreMagicResist */
     , (840031,  66, True ) /* IgnoreMagicArmor */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (840031,   1,       2) /* HeartbeatInterval */
     , (840031,   2,       0) /* HeartbeatTimestamp */
     , (840031,   3,    0.16) /* HealthRate */
     , (840031,   4,       5) /* StaminaRate */
     , (840031,   5,       1) /* ManaRate */
     , (840031,  13,     0.9) /* ArmorModVsSlash */
     , (840031,  14,       1) /* ArmorModVsPierce */
     , (840031,  15,     1.1) /* ArmorModVsBludgeon */
     , (840031,  16,     0.4) /* ArmorModVsCold */
     , (840031,  17,     0.4) /* ArmorModVsFire */
     , (840031,  18,       1) /* ArmorModVsAcid */
     , (840031,  19,     0.6) /* ArmorModVsElectric */
     , (840031,  54,       3) /* UseRadius */
     , (840031,  64,       1) /* ResistSlash */
     , (840031,  65,       1) /* ResistPierce */
     , (840031,  66,       1) /* ResistBludgeon */
     , (840031,  67,       1) /* ResistFire */
     , (840031,  68,       1) /* ResistCold */
     , (840031,  69,       1) /* ResistAcid */
     , (840031,  70,       1) /* ResistElectric */
     , (840031,  71,       1) /* ResistHealthBoost */
     , (840031,  72,       1) /* ResistStaminaDrain */
     , (840031,  73,       1) /* ResistStaminaBoost */
     , (840031,  74,       1) /* ResistManaDrain */
     , (840031,  75,       1) /* ResistManaBoost */
     , (840031, 104,      10) /* ObviousRadarRange */
     , (840031, 125,       1) /* ResistHealthDrain */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (840031,   1, 'DeathBalls') /* Name */
     , (840031,   5, 'Invisible Event Controller') /* Template */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (840031,   1, 0x02000001) /* Setup */
     , (840031,   2, 0x09000001) /* MotionTable */
     , (840031,   3, 0x20000001) /* SoundTable */
     , (840031,   4, 0x30000000) /* CombatTable */
     , (840031,   8, 0x06001036) /* Icon */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (840031,  0,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 1, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0) /* Head */
     , (840031,  1,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0) /* Chest */
     , (840031,  2,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0) /* Abdomen */
     , (840031,  3,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 1, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0) /* UpperArm */
     , (840031,  4,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0) /* LowerArm */
     , (840031,  5,  4,25000, 0.75,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0) /* Hand */
     , (840031,  6,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18) /* UpperLeg */
     , (840031,  7,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6) /* LowerLeg */
     , (840031,  8,  4,25000, 0.75,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22) /* Foot */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (840031,   1,500000, 0, 0) /* Strength */
     , (840031,   2,500000, 0, 0) /* Endurance */
     , (840031,   3,500000, 0, 0) /* Quickness */
     , (840031,   4,500000, 0, 0) /* Coordination */
     , (840031,   5,5000000, 0, 0) /* Focus */
     , (840031,   6,5000000, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (840031,   1,3000000, 0, 0,3000000) /* MaxHealth */
     , (840031,   3,3000000, 0, 0,3000000) /* MaxStamina */
     , (840031,   5,3000000, 0, 0,3000000) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (840031,  6, 0, 2, 0, 800, 0,500000) /* MeleeDefense        Trained */
     , (840031,  7, 0, 2, 0, 800, 0,500000) /* MissileDefense      Trained */
     , (840031, 13, 0, 2, 0, 800, 0,500000) /* UnarmedCombat       Trained */
     , (840031, 33, 0, 3, 0, 800, 0,500000) /* LifeMagic            Specialized */
     , (840031, 34, 0, 3, 0, 800, 0,500000) /* WarMagic            Specialized */
     , (840031, 43, 0, 3, 0, 800, 0,500000) /* VoidMagic            Specialized */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (840031, 37 /* ReceiveLocalSignal */, 1, NULL, NULL, NULL, 'Attack', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 6, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2791 /* Rolling Death */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 19 /* CastSpellInstant */, 3, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2791 /* Rolling Death */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 19 /* CastSpellInstant */, 3, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2791 /* Rolling Death */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 19 /* CastSpellInstant */, 3, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2791 /* Rolling Death */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 19 /* CastSpellInstant */, 3, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2791 /* Rolling Death */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

