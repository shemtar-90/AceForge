# Raid Boss Creature Examples — Live Server Reference

Key patterns for raid-tier bosses:
- Very high Level (5000+), very high XpOverride and LuminanceAward
- `AiOptions (140)=1` CanOpenDoors, `FriendType (72)` for faction
- `AiAllowedCombatStyle (101)` bitmask for attack types
- High resist values across all damage types
- Generator at WCID+1,000,000, separate from creature file

## 803321 Drakin Raid Boss One.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 803321;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (803321, 'DrakinRaidOne', 10, '2024-04-23 08:02:07') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (803321,   1,         16) /* ItemType - Creature */
     , (803321,   2,         71) /* CreatureType - Margul */
     , (803321,   3,         11) /* PaletteTemplate - Maroon */
     , (803321,   6,         -1) /* ItemsCapacity */
     , (803321,   7,         -1) /* ContainersCapacity */
     , (803321,  16,          1) /* ItemUseable - No */
     , (803321,  25,       5000) /* Level */
     , (803321,  27,          0) /* ArmorType - None */
     , (803321,  40,          2) /* CombatMode - Melee */
     , (803321,  72,         22) /* FriendType - Shadow */
     , (803321,  93,       1032) /* PhysicsState - ReportCollisions, Gravity */
     , (803321, 101,        131) /* AiAllowedCombatStyle - Unarmed, OneHanded, ThrownWeapon */
     , (803321, 133,          2) /* ShowableOnRadar - ShowMovement */
     , (803321, 140,          1) /* AiOptions - CanOpenDoors */
     , (803321, 146,   99999999) /* XpOverride */
     , (803321, 332,   30000000) /* LuminanceAward */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (803321,   1, True ) /* Stuck */
     , (803321,   6, True ) /* AiUsesMana */
     , (803321,  11, False) /* IgnoreCollisions */
     , (803321,  12, True ) /* ReportCollisions */
     , (803321,  13, False) /* Ethereal */
     , (803321,  14, True ) /* GravityStatus */
     , (803321,  19, True ) /* Attackable */
     , (803321,  65, True ) /* IgnoreMagicResist */
     , (803321,  66, True ) /* IgnoreMagicArmor */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (803321,   1,       5) /* HeartbeatInterval */
     , (803321,   2,       0) /* HeartbeatTimestamp */
     , (803321,   3,     0.4) /* HealthRate */
     , (803321,   4,       5) /* StaminaRate */
     , (803321,   5,       1) /* ManaRate */
     , (803321,  13,      10) /* ArmorModVsSlash */
     , (803321,  14,      10) /* ArmorModVsPierce */
     , (803321,  15,      10) /* ArmorModVsBludgeon */
     , (803321,  16,      10) /* ArmorModVsCold */
     , (803321,  17,      10) /* ArmorModVsFire */
     , (803321,  18,      10) /* ArmorModVsAcid */
     , (803321,  19,      10) /* ArmorModVsElectric */
     , (803321,  31,      30) /* VisualAwarenessRange */
     , (803321,  34,       1) /* PowerupTime */
     , (803321,  36,       1) /* ChargeSpeed */
     , (803321,  39,       4) /* DefaultScale */
     , (803321,  64,   0.001) /* ResistSlash */
     , (803321,  65,   0.001) /* ResistPierce */
     , (803321,  66,   0.001) /* ResistBludgeon */
     , (803321,  67,   0.001) /* ResistFire */
     , (803321,  68,   0.001) /* ResistCold */
     , (803321,  69,   0.001) /* ResistAcid */
     , (803321,  70,   0.001) /* ResistElectric */
     , (803321,  71,       1) /* ResistHealthBoost */
     , (803321,  72,       1) /* ResistStaminaDrain */
     , (803321,  73,       1) /* ResistStaminaBoost */
     , (803321,  74,       1) /* ResistManaDrain */
     , (803321,  75,       1) /* ResistManaBoost */
     , (803321,  80,       3) /* AiUseMagicDelay */
     , (803321, 104,      10) /* ObviousRadarRange */
     , (803321, 117,     0.5) /* FocusedProbability */
     , (803321, 122,       2) /* AiAcquireHealth */
     , (803321, 125,   0.001) /* ResistHealthDrain */
     , (803321, 166,   0.001) /* ResistNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (803321,   1, 'Dragon of the Deep') /* Name */
     , (803321,  45, 'raid1KT') /* KillQuest */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (803321,   1,   33561507) /* Setup */
     , (803321,   2,  150995485) /* MotionTable */
     , (803321,   3,  536870921) /* SoundTable */
     , (803321,   4,  805306386) /* CombatTable */
     , (803321,   6,   67109307) /* PaletteBase */
     , (803321,   7,  268435631) /* ClothingBase */
     , (803321,   8,  100667938) /* Icon */
     , (803321,  19,         87) /* ActivationAnimation */
     , (803321,  22,  872415260) /* PhysicsEffectTable */
     , (803321,  30,         87) /* PhysicsScript - BreatheLightning */
     , (803321,  35,       5000) /* DeathTreasureType */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (803321,  0, 64, 150000, 0.75,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 1, 0.44,  0.3,    0, 0.44,    0,    0,    0,    0,    0,    0,    0,    0) /* Head */
     , (803321,  1, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 2, 0.33, 0.17,    0, 0.33, 0.17,    0, 0.33, 0.17,    0, 0.33, 0.17,    0) /* Chest */
     , (803321,  2, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 3,    0, 0.17,    0,    0, 0.17,    0,    0,    0,    0,    0, 0.17,    0) /* Abdomen */
     , (803321,  3, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 1, 0.13, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.17,    0, 0.23, 0.03,    0) /* UpperArm */
     , (803321,  4, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 2,    0,  0.2,    0,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0) /* LowerArm */
     , (803321,  5, 64, 150000, 0.75,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 20,    0,  0.1,    0,    0,  0.2,    0,    0,    0,    0,    0,  0.2,    0) /* Hand */
     , (803321,  6, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 3,    0, 0.03, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18, 0.44, 0.13, 0.18) /* UpperLeg */
     , (803321,  7, 64,      0,    0,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 3,    0,    0,  0.6,    0,    0,  0.6, 0.44,  0.2,  0.6,    0,    0,  0.6) /* LowerLeg */
     , (803321,  8, 64, 150000, 0.75,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 3,    0,    0, 0.22,    0,    0, 0.22,    0, 0.03, 0.22,    0,    0, 0.22) /* Foot */
     , (803321,  9, 64, 150000,  0.5,  55000,  423,  376,  423,  376,  470,  376,  470,    0, 1,  0.1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0) /* Horn */
     , (803321, 22, 64, 150000,  0.5,    0,    0,    0,    0,    0,    0,    0,    0,    0, 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0) /* Breath */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (803321,   1,150000, 0, 0) /* Strength */
     , (803321,   2,150000, 0, 0) /* Endurance */
     , (803321,   3, 320, 0, 0) /* Quickness */
     , (803321,   4, 750, 0, 0) /* Coordination */
     , (803321,   5,1400, 0, 0) /* Focus */
     , (803321,   6,1400, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (803321,   1,25000000, 0, 0,25000000) /* MaxHealth */
     , (803321,   3,25000000, 0, 0,25000000) /* MaxStamina */
     , (803321,   5,25000000, 0, 0,25000000) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (803321,  6, 0, 3, 0, 350, 0, 0) /* MeleeDefense        Specialized */
     , (803321,  7, 0, 3, 0, 350, 0, 0) /* MissileDefense      Specialized */
     , (803321, 15, 0, 3, 0, 350, 0, 0) /* MagicDefense        Specialized */
     , (803321, 31, 0, 3, 0,2405, 0, 0) /* CreatureEnchantment Specialized */
     , (803321, 32, 0, 3, 0,2405, 0, 0) /* ItemEnchantment     Specialized */
     , (803321, 33, 0, 3, 0,2405, 0, 0) /* LifeMagic           Specialized */
     , (803321, 34, 0, 3, 0,3400, 0, 0) /* WarMagic            Specialized */
     , (803321, 45, 0, 3, 0,4450, 0, 0) /* LightWeapons        Specialized */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 20 /* ReceiveCritical */, 0.1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 23 /* StartEvent */, 0, 1, NULL, 'TownBossAyan', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 20 /* ReceiveCritical */, 0.2, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 20 /* ReceiveCritical */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'raid1KT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'raid1KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Well done! You have destroyed the monsters who have taken over my dungeon. Here is your reward.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 801690, 25000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 300000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 33 /* IncrementQuest */, 0, 1, NULL, 'Reputation', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 250000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have gained +250,000 Reputation!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 22 /* StampQuest */, 0, 1, NULL, 'raid1KTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'raid1KT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 19 /* CastSpellInstant */, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2046 /* Portal to Teth */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'raid1KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803321, 3 /* Death */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 24 /* StopEvent */, 0, 1, NULL, 'TownBossAyan', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_create_list` (`object_Id`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)
VALUES (803321, 9,803287,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803288,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803289,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803290,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803291,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803292,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803293,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803294,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803295,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803325,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803321, 9,803331,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */;
```

## 803378 Drakin Raid Boss Two.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 803378;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (803378, 'DrakinRaidTwo', 10, '2024-04-23 08:53:06') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (803378,   0,          0) /*  */
     , (803378,   1,         16) /* ItemType - Creature */
     , (803378,   2,         71) /* CreatureType - Margul */
     , (803378,   3,         11) /* PaletteTemplate - Maroon */
     , (803378,   6,         -1) /* ItemsCapacity */
     , (803378,   7,         -1) /* ContainersCapacity */
     , (803378,  16,          1) /* ItemUseable - No */
     , (803378,  25,       5000) /* Level */
     , (803378,  27,          0) /* ArmorType - None */
     , (803378,  40,          2) /* CombatMode - Melee */
     , (803378,  72,         22) /* FriendType - Shadow */
     , (803378,  93,       1032) /* PhysicsState - ReportCollisions, Gravity */
     , (803378, 101,        131) /* AiAllowedCombatStyle - Unarmed, OneHanded, ThrownWeapon */
     , (803378, 133,          2) /* ShowableOnRadar - ShowMovement */
     , (803378, 140,          1) /* AiOptions - CanOpenDoors */
     , (803378, 146,   99999999) /* XpOverride */
     , (803378, 332,   30000000) /* LuminanceAward */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (803378,   1, True ) /* Stuck */
     , (803378,   6, True ) /* AiUsesMana */
     , (803378,  11, False) /* IgnoreCollisions */
     , (803378,  12, True ) /* ReportCollisions */
     , (803378,  13, False) /* Ethereal */
     , (803378,  14, True ) /* GravityStatus */
     , (803378,  19, True ) /* Attackable */
     , (803378,  65, True ) /* IgnoreMagicResist */
     , (803378,  66, True ) /* IgnoreMagicArmor */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (803378,   1,       5) /* HeartbeatInterval */
     , (803378,   2,       0) /* HeartbeatTimestamp */
     , (803378,   3,     0.4) /* HealthRate */
     , (803378,   4,       5) /* StaminaRate */
     , (803378,   5,       1) /* ManaRate */
     , (803378,  13,      10) /* ArmorModVsSlash */
     , (803378,  14,      10) /* ArmorModVsPierce */
     , (803378,  15,      10) /* ArmorModVsBludgeon */
     , (803378,  16,      10) /* ArmorModVsCold */
     , (803378,  17,      10) /* ArmorModVsFire */
     , (803378,  18,      10) /* ArmorModVsAcid */
     , (803378,  19,      10) /* ArmorModVsElectric */
     , (803378,  31,      30) /* VisualAwarenessRange */
     , (803378,  34,       1) /* PowerupTime */
     , (803378,  36,       1) /* ChargeSpeed */
     , (803378,  39,       4) /* DefaultScale */
     , (803378,  64,   0.001) /* ResistSlash */
     , (803378,  65,   0.001) /* ResistPierce */
     , (803378,  66,   0.001) /* ResistBludgeon */
     , (803378,  67,   0.001) /* ResistFire */
     , (803378,  68,   0.001) /* ResistCold */
     , (803378,  69,   0.001) /* ResistAcid */
     , (803378,  70,   0.001) /* ResistElectric */
     , (803378,  71,       1) /* ResistHealthBoost */
     , (803378,  72,       1) /* ResistStaminaDrain */
     , (803378,  73,       1) /* ResistStaminaBoost */
     , (803378,  74,       1) /* ResistManaDrain */
     , (803378,  75,       1) /* ResistManaBoost */
     , (803378,  80,       3) /* AiUseMagicDelay */
     , (803378, 104,      10) /* ObviousRadarRange */
     , (803378, 117,     0.5) /* FocusedProbability */
     , (803378, 122,       2) /* AiAcquireHealth */
     , (803378, 125,   0.001) /* ResistHealthDrain */
     , (803378, 166,   0.001) /* ResistNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (803378,   1, 'Aun Drakin of the Dark') /* Name */
     , (803378,  45, 'raid2KT') /* KillQuest */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (803378,   1,   33559858) /* Setup */
     , (803378,   2,  150995348) /* MotionTable */
     , (803378,   3,  536871107) /* SoundTable */
     , (803378,   4,  805306368) /* CombatTable */
     , (803378,   6,   67116771) /* PaletteBase */
     , (803378,   7,  268437061) /* ClothingBase */
     , (803378,   8,  100688542) /* Icon */
     , (803378,  22,  872415417) /* PhysicsEffectTable */
     , (803378,  30,         85) /* PhysicsScript - BreatheFrost */
     , (803378,  35,       5000) /* DeathTreasureType */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (803378,  0,  4, 150000, 0.75,  55000,  231,  251,  254,  330,  330,  363,  330,    0, 1,  0.1,    0,    0,  0.1,    0,    0,  0.1,    0,    0,  0.1,    0,    0) /* Head */
     , (803378,  5,  1, 150000, 0.75,  55000,  231,  251,  254,  330,  330,  363,  330,    0, 2, 0.45,  0.2,    0, 0.45,  0.2,    0, 0.45,  0.2,    0, 0.45,  0.2,    0) /* Hand */
     , (803378, 16,  4, 150000,  0.5,  55000,  231,  251,  254,  330,  330,  363,  330,    0, 2, 0.45,  0.4, 0.45, 0.45,  0.4, 0.45, 0.45,  0.4, 0.45, 0.45,  0.4, 0.45) /* Torso */
     , (803378, 18,  2, 150000,  0.5,  55000,  231,  251,  254,  330,  330,  363,  330,    0, 2,    0,  0.2,  0.1,    0,  0.2,  0.1,    0,  0.2,  0.1,    0,  0.2,  0.1) /* Arm */
     , (803378, 19,  2, 150000, 0.75,  55000,  231,  251,  254,  330,  330,  363,  330,    0, 3,    0,  0.2, 0.45,    0,  0.2, 0.45,    0,  0.2, 0.45,    0,  0.2, 0.45) /* Leg */
     , (803378, 22, 32, 150000,  0.5,    0,    0,    0,    0,    0,    0,    0,    0,    0, 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0) /* Breath */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (803378,   1,150000, 0, 0) /* Strength */
     , (803378,   2,150000, 0, 0) /* Endurance */
     , (803378,   3, 320, 0, 0) /* Quickness */
     , (803378,   4, 750, 0, 0) /* Coordination */
     , (803378,   5,1400, 0, 0) /* Focus */
     , (803378,   6,1400, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (803378,   1,25000000, 0, 0,25000000) /* MaxHealth */
     , (803378,   3,25000000, 0, 0,25000000) /* MaxStamina */
     , (803378,   5,25000000, 0, 0,25000000) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (803378,  6, 0, 3, 0, 350, 0, 0) /* MeleeDefense        Specialized */
     , (803378,  7, 0, 3, 0, 350, 0, 0) /* MissileDefense      Specialized */
     , (803378, 15, 0, 3, 0, 350, 0, 0) /* MagicDefense        Specialized */
     , (803378, 31, 0, 3, 0,2405, 0, 0) /* CreatureEnchantment Specialized */
     , (803378, 32, 0, 3, 0,2405, 0, 0) /* ItemEnchantment     Specialized */
     , (803378, 33, 0, 3, 0,2405, 0, 0) /* LifeMagic           Specialized */
     , (803378, 34, 0, 3, 0,3400, 0, 0) /* WarMagic            Specialized */
     , (803378, 45, 0, 3, 0,4450, 0, 0) /* LightWeapons        Specialized */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 20 /* ReceiveCritical */, 0.1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 23 /* StartEvent */, 0, 1, NULL, 'TownBossBaishi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 20 /* ReceiveCritical */, 0.2, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 20 /* ReceiveCritical */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'raid2KT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'raid2KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Well done! You have destroyed the monsters who have taken over my dungeon. Here is your reward.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 801690, 25000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 300000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 33 /* IncrementQuest */, 0, 1, NULL, 'Reputation', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 250000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have gained +250,000 Reputation!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 22 /* StampQuest */, 0, 1, NULL, 'raid2KTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'raid2KT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 19 /* CastSpellInstant */, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2046 /* Portal to Teth */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'raid2KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803378, 3 /* Death */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 24 /* StopEvent */, 0, 1, NULL, 'TownBossBaishi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_create_list` (`object_Id`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)
VALUES (803378, 9,803287,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803288,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803289,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803290,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803291,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803292,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803293,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803294,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803295,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803325,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803378, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */;
```

## 803516 Elemental Raid Boss Three.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 803516;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (803516, 'ElementalRaidThree', 10, '2024-04-23 09:02:16') /* Creature */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (803516,   0,          0) /*  */
     , (803516,   1,         16) /* ItemType - Creature */
     , (803516,   2,         62) /* CreatureType - Margul */
     , (803516,   3,         21) /* PaletteTemplate - Maroon */
     , (803516,   6,         -1) /* ItemsCapacity */
     , (803516,   7,         -1) /* ContainersCapacity */
     , (803516,  16,          1) /* ItemUseable - No */
     , (803516,  25,       5000) /* Level */
     , (803516,  27,          0) /* ArmorType - None */
     , (803516,  40,          2) /* CombatMode - Melee */
     , (803516,  72,         22) /* FriendType - Shadow */
     , (803516,  93,       1032) /* PhysicsState - ReportCollisions, Gravity */
     , (803516, 101,        131) /* AiAllowedCombatStyle - Unarmed, OneHanded, ThrownWeapon */
     , (803516, 133,          2) /* ShowableOnRadar - ShowMovement */
     , (803516, 140,          1) /* AiOptions - CanOpenDoors */
     , (803516, 146,   99999999) /* XpOverride */
     , (803516, 332,   30000000) /* LuminanceAward */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (803516,   1, True ) /* Stuck */
     , (803516,   6, True ) /* AiUsesMana */
     , (803516,  11, False) /* IgnoreCollisions */
     , (803516,  12, True ) /* ReportCollisions */
     , (803516,  13, False) /* Ethereal */
     , (803516,  14, True ) /* GravityStatus */
     , (803516,  19, True ) /* Attackable */
     , (803516,  65, True ) /* IgnoreMagicResist */
     , (803516,  66, True ) /* IgnoreMagicArmor */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (803516,   1,       5) /* HeartbeatInterval */
     , (803516,   2,       0) /* HeartbeatTimestamp */
     , (803516,   3,     0.4) /* HealthRate */
     , (803516,   4,       5) /* StaminaRate */
     , (803516,   5,       1) /* ManaRate */
     , (803516,  13,      10) /* ArmorModVsSlash */
     , (803516,  14,      10) /* ArmorModVsPierce */
     , (803516,  15,      10) /* ArmorModVsBludgeon */
     , (803516,  16,      10) /* ArmorModVsCold */
     , (803516,  17,      10) /* ArmorModVsFire */
     , (803516,  18,      10) /* ArmorModVsAcid */
     , (803516,  19,      10) /* ArmorModVsElectric */
     , (803516,  31,      30) /* VisualAwarenessRange */
     , (803516,  34,       1) /* PowerupTime */
     , (803516,  36,       1) /* ChargeSpeed */
     , (803516,  39,     2.7) /* DefaultScale */
     , (803516,  64,   0.001) /* ResistSlash */
     , (803516,  65,   0.001) /* ResistPierce */
     , (803516,  66,   0.001) /* ResistBludgeon */
     , (803516,  67,   0.001) /* ResistFire */
     , (803516,  68,   0.001) /* ResistCold */
     , (803516,  69,   0.001) /* ResistAcid */
     , (803516,  70,   0.001) /* ResistElectric */
     , (803516,  71,       1) /* ResistHealthBoost */
     , (803516,  72,       1) /* ResistStaminaDrain */
     , (803516,  73,       1) /* ResistStaminaBoost */
     , (803516,  74,       1) /* ResistManaDrain */
     , (803516,  75,       1) /* ResistManaBoost */
     , (803516,  80,       3) /* AiUseMagicDelay */
     , (803516, 104,      10) /* ObviousRadarRange */
     , (803516, 117,     0.5) /* FocusedProbability */
     , (803516, 122,       2) /* AiAcquireHealth */
     , (803516, 125,   0.001) /* ResistHealthDrain */
     , (803516, 166,   0.001) /* ResistNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (803516,   1, 'Prismatic Exalt') /* Name */
     , (803516,  45, 'raid3KT') /* KillQuest */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (803516,   1, 0x02001919) /* Setup */
     , (803516,   2, 0x090001A8) /* MotionTable */
     , (803516,   3, 0x200000D3) /* SoundTable */
     , (803516,   4, 0x30000000) /* CombatTable */
     , (803516,   8, 0x06002B2E) /* Icon */
     , (803516,  22, 0x34000025) /* PhysicsEffectTable */
     , (803516,  30,         85) /* PhysicsScript - BreatheFrost */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (803516,  0,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 1, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0) /* Head */
     , (803516,  1,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 2, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0) /* Chest */
     , (803516,  2,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 3,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0) /* Abdomen */
     , (803516,  3,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 1, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0) /* UpperArm */
     , (803516,  4,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 2,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0) /* LowerArm */
     , (803516,  5,1024,150000, 0.75,55000,27500,27500,27500,27500,27500,27500,27500,    0, 2,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0) /* Hand */
     , (803516,  6,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 3,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18) /* UpperLeg */
     , (803516,  7,1024,  0,    0,55000,27500,27500,27500,27500,27500,27500,27500,    0, 3,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6) /* LowerLeg */
     , (803516,  8,1024,150000, 0.75,55000,27500,27500,27500,27500,27500,27500,27500,    0, 3,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22) /* Foot */
     , (803516, 22,  8,150000,  0.5,    0,    0,    0,    0,    0,    0,    0,    0,    0, 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0) /* Breath */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (803516,   1,150000, 0, 0) /* Strength */
     , (803516,   2,150000, 0, 0) /* Endurance */
     , (803516,   3, 320, 0, 0) /* Quickness */
     , (803516,   4, 750, 0, 0) /* Coordination */
     , (803516,   5,1400, 0, 0) /* Focus */
     , (803516,   6,1400, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (803516,   1,25000000, 0, 0,25000000) /* MaxHealth */
     , (803516,   3,25000000, 0, 0,25000000) /* MaxStamina */
     , (803516,   5,25000000, 0, 0,25000000) /* MaxMana */;
INSERT INTO `weenie_properties_skill` (`object_Id`, `type`, `level_From_P_P`, `s_a_c`, `p_p`, `init_Level`, `resistance_At_Last_Check`, `last_Used_Time`)
VALUES (803516,  6, 0, 3, 0, 350, 0, 0) /* MeleeDefense        Specialized */
     , (803516,  7, 0, 3, 0, 350, 0, 0) /* MissileDefense      Specialized */
     , (803516, 15, 0, 3, 0, 350, 0, 0) /* MagicDefense        Specialized */
     , (803516, 31, 0, 3, 0,2405, 0, 0) /* CreatureEnchantment Specialized */
     , (803516, 32, 0, 3, 0,2405, 0, 0) /* ItemEnchantment     Specialized */
     , (803516, 33, 0, 3, 0,2405, 0, 0) /* LifeMagic           Specialized */
     , (803516, 34, 0, 3, 0,3400, 0, 0) /* WarMagic            Specialized */
     , (803516, 45, 0, 3, 0,4450, 0, 0) /* LightWeapons        Specialized */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 14 /* Taunt */, 0.1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 88 /* LocalSignal */, 0, 1, NULL, 'UnleashFury', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 14 /* Taunt */, 0.2, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 20 /* ReceiveCritical */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'raid3KT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'raid3KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Well done! You have destroyed the monsters who have taken over my dungeon. Here is your reward.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 801690, 25000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 300000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 33 /* IncrementQuest */, 0, 1, NULL, 'Reputation', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 250000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have gained +250,000 Reputation!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 22 /* StampQuest */, 0, 1, NULL, 'raid3KTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'raid3KT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 19 /* CastSpellInstant */, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2046 /* Portal to Teth */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'raid3KT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 19 /* CastSpellInstant */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4643 /* Incantation of Drain Health Other */, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (803516, 20 /* ReceiveCritical */, 0.1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 88 /* LocalSignal */, 0, 1, NULL, 'UnleashFury', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 8 /* Say */, 0, 0, NULL, 'Another mortal soul collected!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 8 /* Say */, 0, 0, NULL, 'Die you Derethian scum!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 8 /* Say */, 0, 0, NULL, 'The taste of blood, how I''ve missed it!', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_create_list` (`object_Id`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)
VALUES (803516, 9,803287,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803288,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803289,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803290,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803291,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803292,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803293,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803294,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803295,  0, 0,0.001, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,     0,  0, 0,0.999, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803325,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803379,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */
     , (803516, 9,803559,  0, 0,    1, False) /* Create Ring of Mangled Fervor (800030) for ContainTreasure */;
```

