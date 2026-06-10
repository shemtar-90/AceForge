## ⚠ CRITICAL SCHEMA — MEMORIZE BEFORE GENERATING

### `weenie` table — EXACTLY 4 COLUMNS, NO MORE:
```sql
DELETE FROM `weenie` WHERE `class_Id` = WCID;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (WCID, 'slug_name', 10, '2025-01-01 00:00:00');
```
NEVER write: INSERT INTO `weenie` (`class_Id`, `type`, `value`) — THIS IS WRONG.
NEVER add extra rows to the weenie INSERT. ONE row per weenie.

### Property tables use `object_Id`, `type`, `value` — integer type enums only:
```sql
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (WCID,   1,        16) /* ItemType */
     , (WCID,  25,       200) /* Level */;
```
STOP when you have covered all needed properties. DO NOT increment type indefinitely.
ONLY insert property rows for properties this weenie actually needs.

### Emote actions — NO `object_Id` column, uses @parent_id:
```sql
INSERT INTO `weenie_properties_emote` (...)
VALUES (WCID, 9 /* Refuse */, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET @parent_id = LAST_INSERT_ID();
INSERT INTO `weenie_properties_emote_action` (`emote_Id`, `order`, `type`, `delay`, `extent`, `motion`, `message`, `test_String`, `min`, `max`, `min_64`, `max_64`, `min_Dbl`, `max_Dbl`, `stat`, `display`, `amount`, `amount_64`, `hero_X_P_64`, `percent`, `spell_Id`, `wealth_Rating`, `treasure_Class`, `treasure_Type`, `p_Script`, `sound`, `destination_Type`, `weenie_Class_Id`, `stack_Size`, `palette`, `shade`, `try_To_Bond`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (@parent_id, 0, 10 /* Tell */, 0, 1, NULL, 'Your message here.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
```

### STOP CONDITIONS — finish the file when:
- All required property tables are populated
- Emotes are written
- File ends with semicolon on last statement
- DO NOT pad with extra rows, DO NOT loop type IDs from 1 to 300
