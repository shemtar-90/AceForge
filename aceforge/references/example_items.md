# Item & Kill Contract Examples — Live Server Reference Examples
These are real SQL files from the Shattered Dawn ACEmulator server.
Use these as the authoritative format for all generated SQL.

## 810024 RiftStalkerNoPerch.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810024;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810024, 'RiftStalkerNoPerch', 24, '2024-11-30 11:23:54') /* PressurePlate */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810024,   1,        128) /* ItemType - Misc */
     , (810024,   5,        500) /* EncumbranceVal */
     , (810024,   8,        250) /* Mass */
     , (810024,   9,          0) /* ValidLocations - None */
     , (810024,  16,          1) /* ItemUseable - No */
     , (810024,  19,       1000) /* Value */
     , (810024,  83,       2048) /* ActivationResponse - Emote */
     , (810024,  93,       1036) /* PhysicsState - Ethereal, ReportCollisions, Gravity */
     , (810024, 119,          1) /* Active */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810024,   1, True ) /* Stuck */
     , (810024,  11, False) /* IgnoreCollisions */
     , (810024,  12, True ) /* ReportCollisions */
     , (810024,  13, True ) /* Ethereal */
     , (810024,  14, False) /* GravityStatus */
     , (810024,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (810024,  11,      30) /* ResetInterval */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810024,   1, 'RiftStalkerNoPerch') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810024,   1, 0x02000450) /* Setup */
     , (810024,   2, 0x09000021) /* MotionTable */
     , (810024,   8, 0x060012D2) /* Icon */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (810024, 8 /* Activation */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 99 /* TeleportTarget */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0xF4BA0008 /* 0xF4BA0008 [11.716688 190.97905 181.91992] -0.024297 0 0 0.999705 */, 11.716688, 190.97905, 181.91992, -0.024297, 0, 0, 0.999705);
```

## 810025 GeneralAretheiNoPerch.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810025;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810025, 'GeneralAretheiNoPerch', 24, '2024-11-30 08:38:39') /* PressurePlate */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810025,   1,        128) /* ItemType - Misc */
     , (810025,   5,        500) /* EncumbranceVal */
     , (810025,   8,        250) /* Mass */
     , (810025,   9,          0) /* ValidLocations - None */
     , (810025,  16,          1) /* ItemUseable - No */
     , (810025,  19,       1000) /* Value */
     , (810025,  83,       2048) /* ActivationResponse - Emote */
     , (810025,  93,       1036) /* PhysicsState - Ethereal, ReportCollisions, Gravity */
     , (810025, 119,          1) /* Active */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810025,   1, True ) /* Stuck */
     , (810025,  11, False) /* IgnoreCollisions */
     , (810025,  12, True ) /* ReportCollisions */
     , (810025,  13, True ) /* Ethereal */
     , (810025,  14, False) /* GravityStatus */
     , (810025,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (810025,  11,      30) /* ResetInterval */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810025,   1, 'GeneralAretheiNoPerch') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810025,   1, 0x02000450) /* Setup */
     , (810025,   2, 0x09000021) /* MotionTable */
     , (810025,   8, 0x060012D2) /* Icon */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (810025, 8 /* Activation */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 99 /* TeleportTarget */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0x2BF50110 /* 0x2BF50110 [20.021273 -368.2966 0.005] 0.999898 0 0 0.014284 */, 20.021273, -368.2966, 0.005, 0.999898, 0, 0, 0.014284);
```

## 810028 ThorunfrunTuuNoPerch.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810028;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810028, 'ThorunfrunTuuNoPerch', 24, '2024-12-01 07:08:06') /* PressurePlate */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810028,   1,        128) /* ItemType - Misc */
     , (810028,   5,        500) /* EncumbranceVal */
     , (810028,   8,        250) /* Mass */
     , (810028,   9,          0) /* ValidLocations - None */
     , (810028,  16,          1) /* ItemUseable - No */
     , (810028,  19,       1000) /* Value */
     , (810028,  83,       2048) /* ActivationResponse - Emote */
     , (810028,  93,       1036) /* PhysicsState - Ethereal, ReportCollisions, Gravity */
     , (810028, 119,          1) /* Active */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810028,   1, True ) /* Stuck */
     , (810028,  11, False) /* IgnoreCollisions */
     , (810028,  12, True ) /* ReportCollisions */
     , (810028,  13, True ) /* Ethereal */
     , (810028,  14, False) /* GravityStatus */
     , (810028,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (810028,  11,      30) /* ResetInterval */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810028,   1, 'ThorunfrunTuuNoPerch') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810028,   1, 0x02000450) /* Setup */
     , (810028,   2, 0x09000021) /* MotionTable */
     , (810028,   8, 0x060012D2) /* Icon */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (810028, 8 /* Activation */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 99 /* TeleportTarget */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0x2BF50115 /* 0x2BF50115 [30.047455 -41.697563 0.005] 0.999947 0 0 -0.01028 */, 30.047455, -41.697563, 0.005, 0.999947, 0, 0, -0.01028);
```

## 810031 IlristrasNoPerch.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810031;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810031, 'IlristrasNoPerch', 24, '2024-12-01 12:49:33') /* PressurePlate */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810031,   1,        128) /* ItemType - Misc */
     , (810031,   5,        500) /* EncumbranceVal */
     , (810031,   8,        250) /* Mass */
     , (810031,   9,          0) /* ValidLocations - None */
     , (810031,  16,          1) /* ItemUseable - No */
     , (810031,  19,       1000) /* Value */
     , (810031,  83,       2048) /* ActivationResponse - Emote */
     , (810031,  93,       1036) /* PhysicsState - Ethereal, ReportCollisions, Gravity */
     , (810031, 119,          1) /* Active */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810031,   1, True ) /* Stuck */
     , (810031,  11, False) /* IgnoreCollisions */
     , (810031,  12, True ) /* ReportCollisions */
     , (810031,  13, True ) /* Ethereal */
     , (810031,  14, False) /* GravityStatus */
     , (810031,  18, True ) /* Visibility */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (810031,  11,      30) /* ResetInterval */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810031,   1, 'IlristrasNoPerch') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810031,   1, 0x02000450) /* Setup */
     , (810031,   2, 0x09000021) /* MotionTable */
     , (810031,   8, 0x060012D2) /* Icon */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (810031, 8 /* Activation */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 99 /* TeleportTarget */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0x2BF50137 /* 0x2BF50137 [240 -38 0.005] 1 0 0 0 */, 240, -38, 0.005, 1, 0, 0, 0);
```

## 810003 Blood of the Singularity (UNUSED).sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 810003;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (810003, 'Blood of the Singularity', 38, '2021-11-01 00:00:00') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (810003,   1,       2048) /* ItemType - Gem */
     , (810003,   5,         50) /* EncumbranceVal */
     , (810003,  11,        100) /* MaxStackSize */
     , (810003,  12,          1) /* StackSize */
     , (810003,  13,         50) /* StackUnitEncumbrance */
     , (810003,  15,        150) /* StackUnitValue */
     , (810003,  16,          1) /* ItemUseable - No */
     , (810003,  19,        150) /* Value */
     , (810003,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (810003,  23, True ) /* DestroyOnSell */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (810003,   1, 'Blood of the Singularity') /* Name */
     , (810003,  14, 'Encapsulated blood from a minion of the Singularity, infused with the Quiddity. These can be turned in to gain access to raids.') /* Use */
     , (810003,  20, 'Blood of the Singularity') /* PluralName */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (810003,   1, 0x02000179) /* Setup */
     , (810003,   3, 0x20000014) /* SoundTable */
     , (810003,   8,  100686640) /* Icon */
     , (810003,  22, 0x3400002B) /* PhysicsEffectTable */
     , (810003,  50,  100670496) /* IconOverlay */;
```

## 860000 Echo Rift Kill Contract.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 860000;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (860000, 'Echo Rift Kill Contract', 38, '2024-12-02 11:30:07') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (860000,   1,       2048) /* ItemType - Gem */
     , (860000,   3,         39) /* PaletteTemplate - Black */
     , (860000,   5,          5) /* EncumbranceVal */
     , (860000,   8,          5) /* Mass */
     , (860000,  11,         50) /* MaxStackSize */
     , (860000,  12,          1) /* StackSize */
     , (860000,  13,          5) /* StackUnitEncumbrance */
     , (860000,  14,          5) /* StackUnitMass */
     , (860000,  15,         50) /* StackUnitValue */
     , (860000,  16,          8) /* ItemUseable - Contained */
     , (860000,  18,          0) /* UiEffects - Magical */
     , (860000,  19,          1) /* Value */
     , (860000,  33,          1) /* Bonded - Bonded */
     , (860000,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (860000,  94,         16) /* TargetType - Creature */
     , (860000, 106,        325) /* ItemSpellcraft */
     , (860000, 107,      10000) /* ItemCurMana */
     , (860000, 108,      10000) /* ItemMaxMana */
     , (860000, 114,          1) /* Attuned - Attuned */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (860000,  22, True ) /* Inscribable */
     , (860000,  63, True ) /* UnlimitedUse */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (860000,   1, 'Echo Rift Kill Contract') /* Name */
     , (860000,  14, 'Use this to activate a contract. Once the contract is completed, use it again to receive your rewards. Mobs are located on Fractured Caul.') /* Use */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (860000,   1, 0x02000155) /* Setup */
     , (860000,   3, 0x20000014) /* SoundTable */
     , (860000,   8, 0x060030A8) /* Icon */
     , (860000,  22, 0x3400002B) /* PhysicsEffectTable */
     , (860000,  52, 0x0600335A) /* IconUnderlay */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'RiftEchoKTTimer@6', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftEchoKTTimer@6', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this daily task too recently.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftEchoKTTimer@6', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'RiftEchoKT@KillTaskInProgress', NULL, 1, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftEchoKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'RiftEchoKT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftEchoKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this Kill Contract.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 22 /* StampQuest */, 0, 1, NULL, 'RiftEchoKTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 31 /* EraseQuest */, 0, 1, NULL, 'RiftEchoKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'RiftEchoCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 22 /* StampQuest */, 0, 1, NULL, 'RiftEchoCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftEchoKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You are not quite finished with this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860000, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftEchoKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Kill 100 Rift Echoes to complete this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 70 /* SetQuestCompletions */, 0, 1, NULL, 'RiftEchoKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 860001 Virindi Experimenter Kill Contract.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 860001;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (860001, 'Virindi Experimenter Kill Contract', 38, '2025-01-08 06:34:41') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (860001,   1,       2048) /* ItemType - Gem */
     , (860001,   3,         39) /* PaletteTemplate - Black */
     , (860001,   5,          5) /* EncumbranceVal */
     , (860001,   8,          5) /* Mass */
     , (860001,  11,         50) /* MaxStackSize */
     , (860001,  12,          1) /* StackSize */
     , (860001,  13,          5) /* StackUnitEncumbrance */
     , (860001,  14,          5) /* StackUnitMass */
     , (860001,  15,         50) /* StackUnitValue */
     , (860001,  16,          8) /* ItemUseable - Contained */
     , (860001,  18,          0) /* UiEffects - Magical */
     , (860001,  19,          1) /* Value */
     , (860001,  33,          1) /* Bonded - Bonded */
     , (860001,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (860001,  94,         16) /* TargetType - Creature */
     , (860001, 106,        325) /* ItemSpellcraft */
     , (860001, 107,      10000) /* ItemCurMana */
     , (860001, 108,      10000) /* ItemMaxMana */
     , (860001, 114,          1) /* Attuned - Attuned */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (860001,  22, True ) /* Inscribable */
     , (860001,  63, True ) /* UnlimitedUse */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (860001,   1, 'Virindi Experimenter Kill Contract') /* Name */
     , (860001,  14, 'Use this to activate a contract. Once the contract is completed, use it again to receive your rewards. Mobs are located on Fractured Caul.') /* Use */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (860001,   1, 0x02000155) /* Setup */
     , (860001,   3, 0x20000014) /* SoundTable */
     , (860001,   8, 0x060030A8) /* Icon */
     , (860001,  22, 0x3400002B) /* PhysicsEffectTable */
     , (860001,  52, 0x0600335A) /* IconUnderlay */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'ExperimenterKTTimer@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'ExperimenterKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this daily task too recently.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'ExperimenterKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'ExperimenterKT@KillTaskInProgress', NULL, 1, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'ExperimenterKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'ExperimenterKT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'ExperimenterKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this Kill Contract.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 22 /* StampQuest */, 0, 1, NULL, 'ExperimenterKTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 31 /* EraseQuest */, 0, 1, NULL, 'ExperimenterKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'ExperimenterCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 22 /* StampQuest */, 0, 1, NULL, 'ExperimenterCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'ExperimenterKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You are not quite finished with this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860001, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'ExperimenterKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Kill 100 Virindi Experimenters to complete this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 70 /* SetQuestCompletions */, 0, 1, NULL, 'ExperimenterKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 860002 Rift Mercenary Kill Contract.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 860002;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (860002, 'Riftborne Mercenary Kill Contract', 38, '2024-12-02 11:33:25') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (860002,   1,       2048) /* ItemType - Gem */
     , (860002,   3,         39) /* PaletteTemplate - Black */
     , (860002,   5,          5) /* EncumbranceVal */
     , (860002,   8,          5) /* Mass */
     , (860002,  11,         50) /* MaxStackSize */
     , (860002,  12,          1) /* StackSize */
     , (860002,  13,          5) /* StackUnitEncumbrance */
     , (860002,  14,          5) /* StackUnitMass */
     , (860002,  15,         50) /* StackUnitValue */
     , (860002,  16,          8) /* ItemUseable - Contained */
     , (860002,  18,          0) /* UiEffects - Magical */
     , (860002,  19,          1) /* Value */
     , (860002,  33,          1) /* Bonded - Bonded */
     , (860002,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (860002,  94,         16) /* TargetType - Creature */
     , (860002, 106,        325) /* ItemSpellcraft */
     , (860002, 107,      10000) /* ItemCurMana */
     , (860002, 108,      10000) /* ItemMaxMana */
     , (860002, 114,          1) /* Attuned - Attuned */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (860002,  22, True ) /* Inscribable */
     , (860002,  63, True ) /* UnlimitedUse */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (860002,   1, 'Riftborne Mercenary Kill Contract') /* Name */
     , (860002,  14, 'Use this to activate a contract. Once the contract is completed, use it again to receive your rewards. Mobs are located on Frozen Wasteland.') /* Use */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (860002,   1, 0x02000155) /* Setup */
     , (860002,   3, 0x20000014) /* SoundTable */
     , (860002,   8, 0x060030A8) /* Icon */
     , (860002,  22, 0x3400002B) /* PhysicsEffectTable */
     , (860002,  52, 0x0600335C) /* IconUnderlay */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'RiftborneMercenaryKTTimer@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this daily task too recently.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'RiftborneMercenaryKT@KillTaskInProgress', NULL, 1, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'RiftborneMercenaryKT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this Kill Contract.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 22 /* StampQuest */, 0, 1, NULL, 'RiftborneMercenaryKTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 31 /* EraseQuest */, 0, 1, NULL, 'RiftborneMercenaryKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'RiftborneMercenaryCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 22 /* StampQuest */, 0, 1, NULL, 'RiftborneMercenaryCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You are not quite finished with this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860002, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'RiftborneMercenaryKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Kill 100 Riftborne Mercenaries to complete this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 70 /* SetQuestCompletions */, 0, 1, NULL, 'RiftborneMercenaryKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 860003 Frostbitten Soldier Kill Contract.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 860003;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (860003, 'Frostbitten Soldier Kill Contract', 38, '2024-12-02 11:33:47') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (860003,   1,       2048) /* ItemType - Gem */
     , (860003,   3,         39) /* PaletteTemplate - Black */
     , (860003,   5,          5) /* EncumbranceVal */
     , (860003,   8,          5) /* Mass */
     , (860003,  11,         50) /* MaxStackSize */
     , (860003,  12,          1) /* StackSize */
     , (860003,  13,          5) /* StackUnitEncumbrance */
     , (860003,  14,          5) /* StackUnitMass */
     , (860003,  15,         50) /* StackUnitValue */
     , (860003,  16,          8) /* ItemUseable - Contained */
     , (860003,  18,          0) /* UiEffects - Magical */
     , (860003,  19,          1) /* Value */
     , (860003,  33,          1) /* Bonded - Bonded */
     , (860003,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (860003,  94,         16) /* TargetType - Creature */
     , (860003, 106,        325) /* ItemSpellcraft */
     , (860003, 107,      10000) /* ItemCurMana */
     , (860003, 108,      10000) /* ItemMaxMana */
     , (860003, 114,          1) /* Attuned - Attuned */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (860003,  22, True ) /* Inscribable */
     , (860003,  63, True ) /* UnlimitedUse */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (860003,   1, 'Frostbitten Soldier Kill Contract') /* Name */
     , (860003,  14, 'Use this to activate a contract. Once the contract is completed, use it again to receive your rewards. Mobs are located on Frozen Wasteland.') /* Use */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (860003,   1, 0x02000155) /* Setup */
     , (860003,   3, 0x20000014) /* SoundTable */
     , (860003,   8, 0x060030A8) /* Icon */
     , (860003,  22, 0x3400002B) /* PhysicsEffectTable */
     , (860003,  52, 0x0600335C) /* IconUnderlay */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FrostbittenSoldierKTTimer@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this daily task too recently.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'FrostbittenSoldierKT@KillTaskInProgress', NULL, 1, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FrostbittenSoldierKT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this Kill Contract.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 22 /* StampQuest */, 0, 1, NULL, 'FrostbittenSoldierKTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 31 /* EraseQuest */, 0, 1, NULL, 'FrostbittenSoldierKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'FrostbittenSoldierCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 22 /* StampQuest */, 0, 1, NULL, 'FrostbittenSoldierCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You are not quite finished with this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860003, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FrostbittenSoldierKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Kill 100 Frostbitten Soldier to complete this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 70 /* SetQuestCompletions */, 0, 1, NULL, 'FrostbittenSoldierKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

## 860004 Failed Experiment Kill Contract.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 860004;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (860004, 'Failed Experiment Kill Contract', 38, '2024-12-02 11:34:21') /* Gem */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (860004,   1,       2048) /* ItemType - Gem1 */
     , (860004,   3,         39) /* PaletteTemplate - Black */
     , (860004,   5,          5) /* EncumbranceVal */
     , (860004,   8,          5) /* Mass */
     , (860004,  11,         50) /* MaxStackSize */
     , (860004,  12,          1) /* StackSize */
     , (860004,  13,          5) /* StackUnitEncumbrance */
     , (860004,  14,          5) /* StackUnitMass */
     , (860004,  15,         50) /* StackUnitValue */
     , (860004,  16,          8) /* ItemUseable - Contained */
     , (860004,  18,          0) /* UiEffects - Magical */
     , (860004,  19,          1) /* Value */
     , (860004,  33,          1) /* Bonded - Bonded */
     , (860004,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (860004,  94,         16) /* TargetType - Creature */
     , (860004, 106,        325) /* ItemSpellcraft */
     , (860004, 107,      10000) /* ItemCurMana */
     , (860004, 108,      10000) /* ItemMaxMana */
     , (860004, 114,          1) /* Attuned - Attuned */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (860004,  22, True ) /* Inscribable */
     , (860004,  63, True ) /* UnlimitedUse */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (860004,   1, 'Failed Experiment Kill Contract') /* Name */
     , (860004,  14, 'Use this to activate a contract. Once the contract is completed, use it again to receive your rewards. Mobs are located on Norehsa''s Island.') /* Use */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (860004,   1, 0x02000155) /* Setup */
     , (860004,   3, 0x20000014) /* SoundTable */
     , (860004,   8, 0x060030A8) /* Icon */
     , (860004,  22, 0x3400002B) /* PhysicsEffectTable */
     , (860004,  52, 0x0600335B) /* IconUnderlay */;
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 7 /* Use */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FailedExperimentKTTimer@3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FailedExperimentKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this daily task too recently.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FailedExperimentKTTimer@3', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 30 /* InqQuestSolves */, 0, 1, NULL, 'FailedExperimentKT@KillTaskInProgress', NULL, 1, 2147483647, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FailedExperimentKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 21 /* InqQuest */, 0, 1, NULL, 'FailedExperimentKT@KillTaskCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 12 /* QuestSuccess */, 1, NULL, NULL, NULL, 'FailedExperimentKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You have completed this Kill Contract.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 49 /* AwardLevelProportionalXP */, 0, 1, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 2, 113 /* AwardLuminance */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5000000, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 3, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 810005, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 4, 3 /* Give */, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20630 /* Trade Note (250,000) */, 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 5, 22 /* StampQuest */, 0, 1, NULL, 'FailedExperimentKTTimer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 6, 31 /* EraseQuest */, 0, 1, NULL, 'FailedExperimentKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 7, 31 /* EraseQuest */, 0, 1, NULL, 'FailedExperimentCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 8, 22 /* StampQuest */, 0, 1, NULL, 'FailedExperimentCompleted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FailedExperimentKT@KillTaskCompleted', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'You are not quite finished with this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `weenie_properties_emote` (`object_Id`, `category`, `probability`, `weenie_Class_Id`, `style`, `substyle`, `quest`, `vendor_Type`, `min_Health`, `max_Health`)
VALUES (860004, 13 /* QuestFailure */, 1, NULL, NULL, NULL, 'FailedExperimentKT@KillTaskInProgress', NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 18 /* DirectBroadcast */, 0, 1, NULL, 'Kill 100 Failed Experiments to complete this task.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
     , (@parent_id, 1, 70 /* SetQuestCompletions */, 0, 1, NULL, 'FailedExperimentKT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

