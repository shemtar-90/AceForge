# Chest / Container Examples — Live Server Reference

## ValHeel Empowered Legendary Chest (300140)

Key patterns:
- `type=20` (Chest weenie type)
- `ItemType=512` (Container), `ItemsCapacity`, `ContainersCapacity` for storage
- `Locked=True`, `DefaultLocked=True`, `LockCode` string for keyed chests
- `ChestRegenOnClose=True` for chests that reset when closed
- `MaxGeneratedObjects (81)`, `InitGeneratedObjects (82)` for loot count
- `weenie_properties_generator` with `where_Create=72` (ContainTreasure) for loot inside chest
- `probability=-1` means always generate (not random)

```sql
DELETE FROM `weenie` WHERE `class_Id` = 300140;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (300140, 'ValHeellegendarychest', 20, '0121-11-01 00:00:00') /* Chest */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (300140,   1,        512) /* ItemType - Container */
     , (300140,   5,       9000) /* EncumbranceVal */
     , (300140,   6,        120) /* ItemsCapacity */
     , (300140,   7,         20) /* ContainersCapacity */
     , (300140,   8,       3000) /* Mass */
     , (300140,  16,         48) /* ItemUseable - ViewedRemote */
     , (300140,  19,       2500) /* Value */
     , (300140,  37,        240) /* ResistItemAppraisal */
     , (300140,  38,       9999) /* ResistLockpick */
     , (300140,  81,         40) /* MaxGeneratedObjects */
     , (300140,  82,         20) /* InitGeneratedObjects */
     , (300140,  83,          2) /* ActivationResponse - Use */
     , (300140,  93,       1048) /* PhysicsState - ReportCollisions, IgnoreCollisions, Gravity */
     , (300140,  96,        500) /* EncumbranceCapacity */
     , (300140, 100,          1) /* GeneratorType - Relative */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (300140,   1, True ) /* Stuck */
     , (300140,   2, False) /* Open */
     , (300140,   3, True ) /* Locked */
     , (300140,  12, True ) /* ReportCollisions */
     , (300140,  13, False) /* Ethereal */
     , (300140,  33, False) /* ResetMessagePending */
     , (300140,  34, False) /* DefaultOpen */
     , (300140,  35, True ) /* DefaultLocked */
     , (300140,  86, True ) /* ChestRegenOnClose */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (300140,  39,     1.1) /* DefaultScale */
     , (300140,  54,       1) /* UseRadius */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (300140,   1, 'ValHeel Empowered Legendary Chest') /* Name */
     , (300140,  12, 'valheelkey') /* LockCode */
     , (300140,  14, 'Use this item to open it and see its contents.') /* Use */
     , (300140,  16, 'A chest containing the highest quality mixed gear. ') /* LongDesc */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (300140,   1,   33557027) /* Setup */
     , (300140,   2,  150994948) /* MotionTable */
     , (300140,   3,  536870945) /* SoundTable */
     , (300140,   7,  268436160) /* ClothingBase */
     , (300140,   8,  100671480) /* Icon */
     , (300140,  22,  872415275) /* PhysicsEffectTable */;
INSERT INTO `weenie_properties_generator` (`object_Id`, `probability`, `weenie_Class_Id`, `delay`, `init_Create`, `max_Create`, `when_Create`, `where_Create`, `stack_Size`, `palette_Id`, `shade`, `obj_Cell_Id`, `origin_X`, `origin_Y`, `origin_Z`, `angles_W`, `angles_X`, `angles_Y`, `angles_Z`)
VALUES (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */
     , (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */
     , (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */
     , (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */
     , (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */
     , (300140, -1, 3111, 0, 1, 1, 2, 72, -1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0) /* Generate UNKNOWN RANDOMLY GENERATED TREASURE (x1 up to max of 1) - Regenerate upon PickUp - Location to (re)Generate: ContainTreasure */;
```
