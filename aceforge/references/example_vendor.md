# Vendor NPC Examples — Live Server Reference

## The Shop (802323) — Full Vendor with Alternate Currency and Shop Inventory

Key patterns:
- `type=12` (Vendor weenie type)
- `MerchandiseItemTypes (74)`, `MerchandiseMinValue (75)`, `MerchandiseMaxValue (76)` in INT
- `BuyPrice (37)` and `SellPrice (38)` in FLOAT
- `DealMagicalItems (39)` in BOOL to allow magic items
- `AlternateCurrency (57)` in DID — custom currency WCID
- `weenie_properties_create_list` for shop inventory (destination_Type=4=Shop)
- Vendor emotes use `category=2` (Vendor) with `vendor_Type` 1=Open, 2=Close, 3=Sell, 4=Buy

```sql
DELETE FROM `weenie` WHERE `class_Id` = 802323;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (802323, 'The Shop', 12, '2023-02-17 08:30:53') /* Vendor */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (802323,   1,         16) /* ItemType - Creature */
     , (802323,   2,         31) /* CreatureType - Human */
     , (802323,   6,         -1) /* ItemsCapacity */
     , (802323,   7,         -1) /* ContainersCapacity */
     , (802323,   8,        120) /* Mass */
     , (802323,  16,         32) /* ItemUseable - Remote */
     , (802323,  25,          3) /* Level */
     , (802323,  27,          0) /* ArmorType - None */
     , (802323,  74,    4481568) /* MerchandiseItemTypes - VendorGrocer */
     , (802323,  75,          0) /* MerchandiseMinValue */
     , (802323,  76,    1000000) /* MerchandiseMaxValue */
     , (802323,  93,    2098200) /* PhysicsState - ReportCollisions, IgnoreCollisions, Gravity, ReportCollisionsAsEnvironment */
     , (802323, 133,          4) /* ShowableOnRadar - ShowAlways */
     , (802323, 134,         16) /* PlayerKillerStatus - RubberGlue */
     , (802323, 146,         20) /* XpOverride */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (802323,   1, True ) /* Stuck */
     , (802323,  12, True ) /* ReportCollisions */
     , (802323,  13, False) /* Ethereal */
     , (802323,  19, False) /* Attackable */
     , (802323,  39, True ) /* DealMagicalItems */
     , (802323,  41, True ) /* ReportCollisionsAsEnvironment */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (802323,   1,       5) /* HeartbeatInterval */
     , (802323,   2,       0) /* HeartbeatTimestamp */
     , (802323,   3,    0.16) /* HealthRate */
     , (802323,   4,       5) /* StaminaRate */
     , (802323,   5,       1) /* ManaRate */
     , (802323,  11,     300) /* ResetInterval */
     , (802323,  13,     0.9) /* ArmorModVsSlash */
     , (802323,  14,       1) /* ArmorModVsPierce */
     , (802323,  15,     1.1) /* ArmorModVsBludgeon */
     , (802323,  16,     0.4) /* ArmorModVsCold */
     , (802323,  17,     0.4) /* ArmorModVsFire */
     , (802323,  18,       1) /* ArmorModVsAcid */
     , (802323,  19,     0.6) /* ArmorModVsElectric */
     , (802323,  37,     0.9) /* BuyPrice */
     , (802323,  38,       1) /* SellPrice */
     , (802323,  54,       3) /* UseRadius */
     , (802323,  64,       1) /* ResistSlash */
     , (802323,  65,       1) /* ResistPierce */
     , (802323,  66,       1) /* ResistBludgeon */
     , (802323,  67,       1) /* ResistFire */
     , (802323,  68,       1) /* ResistCold */
     , (802323,  69,       1) /* ResistAcid */
     , (802323,  70,       1) /* ResistElectric */
     , (802323,  71,       1) /* ResistHealthBoost */
     , (802323,  72,       1) /* ResistStaminaDrain */
     , (802323,  73,       1) /* ResistStaminaBoost */
     , (802323,  74,       1) /* ResistManaDrain */
     , (802323,  75,       1) /* ResistManaBoost */
     , (802323, 104,      10) /* ObviousRadarRange */
     , (802323, 125,       1) /* ResistHealthDrain */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (802323,   1, 'The Shop') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (802323,   1,   33554433) /* Setup */
     , (802323,   2,  150994945) /* MotionTable */
     , (802323,   3,  536870913) /* SoundTable */
     , (802323,   4,  805306368) /* CombatTable */
     , (802323,   8,  100667446) /* Icon */
     , (802323,  57,     801690) /* AlternateCurrency - AshCoin */;
INSERT INTO `weenie_properties_attribute` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`)
VALUES (802323,   1,  20, 0, 0) /* Strength */
     , (802323,   2,  25, 0, 0) /* Endurance */
     , (802323,   3,  45, 0, 0) /* Quickness */
     , (802323,   4,  35, 0, 0) /* Coordination */
     , (802323,   5,  35, 0, 0) /* Focus */
     , (802323,   6,  25, 0, 0) /* Self */;
INSERT INTO `weenie_properties_attribute_2nd` (`object_Id`, `type`, `init_Level`, `level_From_C_P`, `c_P_Spent`, `current_Level`)
VALUES (802323,   1,    25, 0, 0, 38) /* MaxHealth */
     , (802323,   3,    50, 0, 0, 75) /* MaxStamina */
     , (802323,   5,    20, 0, 0, 45) /* MaxMana */;
INSERT INTO `weenie_properties_body_part` (`object_Id`, `key`, `d_Type`, `d_Val`, `d_Var`, `base_Armor`, `armor_Vs_Slash`, `armor_Vs_Pierce`, `armor_Vs_Bludgeon`, `armor_Vs_Cold`, `armor_Vs_Fire`, `armor_Vs_Acid`, `armor_Vs_Electric`, `armor_Vs_Nether`, `b_h`, `h_l_f`, `m_l_f`, `l_l_f`, `h_r_f`, `m_r_f`, `l_r_f`, `h_l_b`, `m_l_b`, `l_l_b`, `h_r_b`, `m_r_b`, `l_r_b`)
VALUES (802323,  0,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 1, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0, 0.33,    0,    0) /* Head */
     , (802323,  1,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0, 0.44, 0.17,    0) /* Chest */
     , (802323,  2,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0,    0, 0.17,    0) /* Abdomen */
     , (802323,  3,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 1, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0, 0.23, 0.03,    0) /* UpperArm */
     , (802323,  4,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0,    0,  0.3,    0) /* LowerArm */
     , (802323,  5,  4,  2, 0.75,    0,    0,    0,    0,    0,    0,    0,    0,    0, 2,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0,    0,  0.2,    0) /* Hand */
     , (802323,  6,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18,    0, 0.13, 0.18) /* UpperLeg */
     , (802323,  7,  4,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6,    0,    0,  0.6) /* LowerLeg */
     , (802323,  8,  4,  2, 0.75,    0,    0,    0,    0,    0,    0,    0,    0,    0, 3,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22,    0,    0, 0.22) /* Foot */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (802323,  2 /* Vendor */,    0.8, NULL, NULL, NULL, NULL, 1 /* Open */, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id,  0,  10 /* Tell */, 0, 1, NULL, 'Welcome! What''s your pleasure today?', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (802323,  2 /* Vendor */,    0.8, NULL, NULL, NULL, NULL, 2 /* Close */, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id,  0,  10 /* Tell */, 0, 1, NULL, 'Thank you for your business. Please return soon.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (802323,  2 /* Vendor */,    0.8, NULL, NULL, NULL, NULL, 3 /* Sell */, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id,  0,  10 /* Tell */, 0, 1, NULL, 'You drive a hard bargain, my friend.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (802323,  2 /* Vendor */,    0.8, NULL, NULL, NULL, NULL, 4 /* Buy */, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id,  0,  10 /* Tell */, 0, 1, NULL, 'An excellent purchase.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_create_list` (`object_Id`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`)
VALUES (802323, 2, 26007,  0, 82, 0.67, False) /* Create Gelidite Robe (26007) for Wield */
     , (802323, 2,   127,  0, 7, 0.33, False) /* Create Pants (127) for Wield */
     , (802323, 2,   132,  0, 18, 1, False) /* Create Shoes (132) for Wield */
     , (802323, 2,   118,  0, 8, 0, False) /* Create Cap (118) for Wield */
     , (802323, 2, 10696,  0, 9, 0.5, False) /* Create Apron (10696) for Wield */
     , (802323, 4, 30253, -1, 8, 1, False) /* Create Limitless Lockpick (30253) for Shop */
     , (802323, 4, 30109, -1, 8, 1, False) /* Create Invigorating Elixir (30109) for Shop */
     , (802323, 4, 30108, -1, 8, 1, False) /* Create Miraculous Elixir (30108) for Shop */
     , (802323, 4, 30107, -1, 8, 1, False) /* Create Refreshing Elixir (30107) for Shop */
     , (802323, 4, 30133, -1, 8, 1, False) /* Create Rune of Dispel (30133) for Shop */
     , (802323, 4, 52034, -1, 8, 1, False) /* Create Casino Exquisite Keyring (52034) for Shop */
     , (802323, 4, 30258, -1, 8, 1, False) /* Create Shimmering Skeleton Key (30258) for Shop */
     , (802323, 4, 802324, -1, 8, 1, False) /* Create Haven Aetheria of Destruction (802324) for Shop */
     , (802323, 4, 802325, -1, 8, 1, False) /* Create Haven Aetheria of Fury (802325) for Shop */
     , (802323, 4, 802326, -1, 8, 1, False) /* Create Haven Aetheria of Growth (802326) for Shop */
     , (802323, 4, 802327, -1, 8, 1, False) /* Create Haven Aetheria of Vigor (802327) for Shop */
     , (802323, 4, 802328, -1, 8, 1, False) /* Create Haven Aetheria of Defense (802328) for Shop */
     , (802323, 4, 802329, -1, 8, 1, False) /* Create Haven Aetheria of Destruction (802329) for Shop */
     , (802323, 4, 802330, -1, 8, 1, False) /* Create Haven Aetheria of Fury (802330) for Shop */
     , (802323, 4, 802331, -1, 8, 1, False) /* Create Haven Aetheria of Growth (802331) for Shop */
     , (802323, 4, 802332, -1, 8, 1, False) /* Create Haven Aetheria of Vigor (802332) for Shop */
     , (802323, 4, 802333, -1, 8, 1, False) /* Create Haven Aetheria of Defense (802333) for Shop */
     , (802323, 4, 802334, -1, 8, 1, False) /* Create Haven Aetheria of Destruction (802334) for Shop */
     , (802323, 4, 802335, -1, 8, 1, False) /* Create Haven Aetheria of Fury (802335) for Shop */
     , (802323, 4, 802336, -1, 8, 1, False) /* Create Haven Aetheria of Growth (802336) for Shop */
     , (802323, 4, 802337, -1, 8, 1, False) /* Create Haven Aetheria of Vigor (802337) for Shop */
     , (802323, 4, 802338, -1, 8, 1, False) /* Create Haven Aetheria of Defense (802338) for Shop */
     , (802323, 4, 802403, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 30247, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 30248, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 30249, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 803308, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 803309, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 803310, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 803350, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */
     , (802323, 4, 803351, -1, 0, 0, False) /* Create Rock Polishing Kit for Shop */;
```
