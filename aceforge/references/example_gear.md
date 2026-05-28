# Gear Examples (Weapons/Armor/Jewelry) — Live Server Reference Examples
These are real SQL files from the Shattered Dawn ACEmulator server.
Use these as the authoritative format for all generated SQL.

## 870016 Necklace of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870016;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870016, 'Necklace of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870016,   1,          8) /* ItemType - Jewelry */
     , (870016,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870016,   5,        100) /* EncumbranceVal */
     , (870016,   8,         90) /* Mass */
     , (870016,   9,      32768) /* ValidLocations - NeckWear */
     , (870016,  16,          1) /* ItemUseable - No */
     , (870016,  19,      50000) /* Value */
     , (870016,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870016,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870016, 106,        350) /* ItemSpellcraft */
     , (870016, 107,       3000) /* ItemCurMana */
     , (870016, 108,       3000) /* ItemMaxMana */
     , (870016, 109,          0) /* ItemDifficulty */
     , (870016, 110,          0) /* ItemAllegianceRankLimit */
     , (870016, 151,          2) /* HookType - Wall */
     , (870016, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870016,  11, True ) /* IgnoreCollisions */
     , (870016,  13, True ) /* Ethereal */
     , (870016,  14, True ) /* GravityStatus */
     , (870016,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870016,   5,  -0.033) /* ManaRate */
     , (870016,  12,    0.66) /* Shade */
     , (870016,  39,     0.9) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870016,   1, 'Necklace of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870016,   1, 0x020000F8) /* Setup */
     , (870016,   3, 0x20000014) /* SoundTable */
     , (870016,   6, 0x04000BEF) /* PaletteBase */
     , (870016,   8, 0x06005BE3) /* Icon */
     , (870016,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870016,  36, 0x0E000012) /* MutateFilter */
     , (870016,  46, 0x38000032) /* TsysMutationFilter */
     , (870016,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870016,  2666,      2)  /* Incantation of Arcane Enlightenment Self */
     , (870016,  4686,      2)  /* Incantation of Item Enchantment Mastery Self */
     , (870016,  6041,      2)  /* Legendary Arcane Prowess */;
```

## 870017 Bracelet of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870017;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870017, 'Bracelet of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870017,   1,          8) /* ItemType - Jewelry */
     , (870017,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870017,   5,         60) /* EncumbranceVal */
     , (870017,   8,         90) /* Mass */
     , (870017,   9,     196608) /* ValidLocations - WristWear */
     , (870017,  16,          1) /* ItemUseable - No */
     , (870017,  19,      50000) /* Value */
     , (870017,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870017,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870017, 106,        350) /* ItemSpellcraft */
     , (870017, 107,       3000) /* ItemCurMana */
     , (870017, 108,       3000) /* ItemMaxMana */
     , (870017, 109,          0) /* ItemDifficulty */
     , (870017, 110,          0) /* ItemAllegianceRankLimit */
     , (870017, 151,          2) /* HookType - Wall */
     , (870017, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_int64` (`object_Id`, `type`, `value`)
VALUES (870017,   4,          0) /* ItemTotalXp */
     , (870017,   5, 2000000000) /* ItemBaseXp */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870017,  11, True ) /* IgnoreCollisions */
     , (870017,  13, True ) /* Ethereal */
     , (870017,  14, True ) /* GravityStatus */
     , (870017,  19, True ) /* Attackable */
     , (870017,  22, True ) /* Inscribable */
     , (870017, 100, False) /* Dyable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870017,   5,  -0.033) /* ManaRate */
     , (870017,  12,    0.66) /* Shade */
     , (870017,  39,     0.5) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870017,   1, 'Bracelet of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870017,   1, 0x020000FB) /* Setup */
     , (870017,   3, 0x20000014) /* SoundTable */
     , (870017,   6, 0x04000BEF) /* PaletteBase */
     , (870017,   8, 0x06005BDE) /* Icon */
     , (870017,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870017,  36, 0x0E000012) /* MutateFilter */
     , (870017,  46, 0x38000032) /* TsysMutationFilter */
     , (870017,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870017,  4694,      2)  /* Epic Focus */
     , (870017,  6124,      2)  /* Incantation of Armor Tinkering Expertise Self */
     , (870017,  2014,      2)  /* Incantation of Item Tinkering Expertise Self */;
```

## 870018 Wristband of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870018;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870018, 'Wristband of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870018,   1,          8) /* ItemType - Jewelry */
     , (870018,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870018,   5,         60) /* EncumbranceVal */
     , (870018,   8,         90) /* Mass */
     , (870018,   9,     196608) /* ValidLocations - WristWear */
     , (870018,  16,          1) /* ItemUseable - No */
     , (870018,  19,      50000) /* Value */
     , (870018,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870018,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870018, 106,        350) /* ItemSpellcraft */
     , (870018, 107,       3000) /* ItemCurMana */
     , (870018, 108,       3000) /* ItemMaxMana */
     , (870018, 109,          0) /* ItemDifficulty */
     , (870018, 110,          0) /* ItemAllegianceRankLimit */
     , (870018, 151,          2) /* HookType - Wall */
     , (870018, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870018,  11, True ) /* IgnoreCollisions */
     , (870018,  13, True ) /* Ethereal */
     , (870018,  14, True ) /* GravityStatus */
     , (870018,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870018,   5,  -0.033) /* ManaRate */
     , (870018,  12,    0.66) /* Shade */
     , (870018,  39,     0.5) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870018,   1, 'Wristband of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870018,   1, 0x020000FB) /* Setup */
     , (870018,   3, 0x20000014) /* SoundTable */
     , (870018,   6, 0x04000BEF) /* PaletteBase */
     , (870018,   8, 0x06005BE2) /* Icon */
     , (870018,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870018,  36, 0x0E000012) /* MutateFilter */
     , (870018,  46, 0x38000032) /* TsysMutationFilter */
     , (870018,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870018,  3955,      2)  /* Epic Acid Ward */
     , (870018,  4693,      2)  /* Epic Flame Ward */
     , (870018,  4708,      2)  /* Epic Frost Ward */;
```

## 870019 Band of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870019;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870019, 'Band of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870019,   1,          8) /* ItemType - Jewelry */
     , (870019,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870019,   5,         15) /* EncumbranceVal */
     , (870019,   8,         90) /* Mass */
     , (870019,   9,     786432) /* ValidLocations - FingerWear */
     , (870019,  16,          1) /* ItemUseable - No */
     , (870019,  19,      50000) /* Value */
     , (870019,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870019,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870019, 106,        350) /* ItemSpellcraft */
     , (870019, 107,       3000) /* ItemCurMana */
     , (870019, 108,       3000) /* ItemMaxMana */
     , (870019, 109,          0) /* ItemDifficulty */
     , (870019, 110,          0) /* ItemAllegianceRankLimit */
     , (870019, 151,          2) /* HookType - Wall */
     , (870019, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870019,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870019,   5,  -0.033) /* ManaRate */
     , (870019,  12,    0.66) /* Shade */
     , (870019,  39,     0.5) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870019,   1, 'Band of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870019,   1, 0x02000103) /* Setup */
     , (870019,   3, 0x20000014) /* SoundTable */
     , (870019,   6, 0x04000BEF) /* PaletteBase */
     , (870019,   8, 0x06005BE6) /* Icon */
     , (870019,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870019,  36, 0x0E000012) /* MutateFilter */
     , (870019,  46, 0x38000032) /* TsysMutationFilter */
     , (870019,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870019,  5896,      2)  /* Epic Willpower */
     , (870019,  5897,      2)  /* Incantation of Willpower Self */
     , (870019,  4020,      2)  /* Incantation of Mana Renewal Self */;
```

## 870020 Ring of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870020;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870020, 'Ring of the Dawn', 1, '2021-11-01 00:00:00') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870020,   1,          8) /* ItemType - Jewelry */
     , (870020,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870020,   5,         15) /* EncumbranceVal */
     , (870020,   8,         90) /* Mass */
     , (870020,   9,     786432) /* ValidLocations - FingerWear */
     , (870020,  16,          1) /* ItemUseable - No */
     , (870020,  19,      50000) /* Value */
     , (870020,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870020,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870020, 106,        350) /* ItemSpellcraft */
     , (870020, 107,       3000) /* ItemCurMana */
     , (870020, 108,       3000) /* ItemMaxMana */
     , (870020, 151,          2) /* HookType - Wall */
     , (870020, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870020,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870020,   5,  -0.033) /* ManaRate */
     , (870020,  12,    0.66) /* Shade */
     , (870020,  39,     0.5) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870020,   1, 'Ring of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870020,   1, 0x02000103) /* Setup */
     , (870020,   3, 0x20000014) /* SoundTable */
     , (870020,   6, 0x04000BEF) /* PaletteBase */
     , (870020,   8, 0x06005BE8) /* Icon */
     , (870020,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870020,  36, 0x0E000012) /* MutateFilter */
     , (870020,  46, 0x38000032) /* TsysMutationFilter */
     , (870020,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870020,  5894,      2)  /* Incantation of Quickness Self */
     , (870020,  5893,      2)  /* Incantation of Invulnerability Self */
     , (870020,  2005,      2)  /* Incantation of Sprint Self */;
```

## 870021 Trinket of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870021;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870021, 'Trinket of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870021,   1,          8) /* ItemType - Jewelry */
     , (870021,   5,         60) /* EncumbranceVal */
     , (870021,   9,   67108864) /* ValidLocations - TrinketOne */
     , (870021,  16,          1) /* ItemUseable - No */
     , (870021,  19,         50) /* Value */
     , (870021,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870021, 106,         50) /* ItemSpellcraft */
     , (870021, 107,       6000) /* ItemCurMana */
     , (870021, 108,       6000) /* ItemMaxMana */
     , (870021, 109,         15) /* ItemDifficulty */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870021,  11, True ) /* IgnoreCollisions */
     , (870021,  13, True ) /* Ethereal */
     , (870021,  14, True ) /* GravityStatus */
     , (870021,  19, True ) /* Attackable */
     , (870021,  22, True ) /* Inscribable */
     , (870021,  91, False) /* Retained */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870021,   5,  -0.049) /* ManaRate */
     , (870021,  39,    0.67) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870021,   1, 'Trinket of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870021,   1, 0x02000179) /* Setup */
     , (870021,   3, 0x20000014) /* SoundTable */
     , (870021,   8, 0x06006AA4) /* Icon */
     , (870021,  22, 0x3400002B) /* PhysicsEffectTable */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870021,  4697,      2)  /* Augmented Understanding II */
     , (870021,  5895,      2)  /* Augmented Understanding II */
     , (870021,  4679,      2)  /* Augmented Understanding II */
     , (870021,  6105,      2)  /* Legendary Focus */;
```

## 870006 Boots of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870006;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870006, 'Boots of the Dawn', 2, '2021-11-01 00:00:00') /* Clothing */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870006,   1,          2) /* ItemType - Armor */
     , (870006,   3,         39) /* PaletteTemplate - Black */
     , (870006,   4,      65536) /* ClothingPriority - Feet */
     , (870006,   5,        225) /* EncumbranceVal */
     , (870006,   9,        256) /* ValidLocations - FootWear */
     , (870006,  16,          1) /* ItemUseable - No */
     , (870006,  18,          1) /* UiEffects - Magical */
     , (870006,  19,          1) /* Value */
     , (870006,  28,        270) /* ArmorLevel */
     , (870006,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870006, 106,        400) /* ItemSpellcraft */
     , (870006, 107,        800) /* ItemCurMana */
     , (870006, 108,        800) /* ItemMaxMana */
     , (870006, 109,        220) /* ItemDifficulty */
     , (870006, 151,          9) /* HookType - Floor, Yard */
     , (870006, 158,          7) /* WieldRequirements - Level */
     , (870006, 159,          1) /* WieldSkillType - Axe */
     , (870006, 160,        275) /* WieldDifficulty */
     , (870006, 265,         47) /* EquipmentSetId - AncientRelicUpgrade */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870006,  22, True ) /* Inscribable */
     , (870006,  69, False) /* IsSellable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870006,   5,  -0.033) /* ManaRate */
     , (870006,  13,     1.3) /* ArmorModVsSlash */
     , (870006,  14,     0.8) /* ArmorModVsPierce */
     , (870006,  15,     1.3) /* ArmorModVsBludgeon */
     , (870006,  16,       1) /* ArmorModVsCold */
     , (870006,  17,       1) /* ArmorModVsFire */
     , (870006,  18,     1.1) /* ArmorModVsAcid */
     , (870006,  19,     0.5) /* ArmorModVsElectric */
     , (870006, 165,       1) /* ArmorModVsNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870006,   1, 'Boots of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870006,   1, 0x020000DE) /* Setup */
     , (870006,   3, 0x20000014) /* SoundTable */
     , (870006,   7, 0x1000068D) /* ClothingBase */
     , (870006,   8, 0x060027AD) /* Icon */
     , (870006,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870006,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870006,  4019,      2)  /* Epic Quickness */
     , (870006,  3956,      2)  /* Incantation of Impenetrability */
     , (870006,  4710,      2)  /* Epic Sprint */;
```

## 870007 Helm of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870007;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870007, 'Helm of the Dawn', 2, '2021-11-01 00:00:00') /* Clothing */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870007,   1,          2) /* ItemType - Armor */
     , (870007,   3,         39) /* PaletteTemplate - Black */
     , (870007,   4,      16384) /* ClothingPriority - Head */
     , (870007,   5,        350) /* EncumbranceVal */
     , (870007,   9,          1) /* ValidLocations - HeadWear */
     , (870007,  16,          1) /* ItemUseable - No */
     , (870007,  18,          1) /* UiEffects - Magical */
     , (870007,  19,          1) /* Value */
     , (870007,  28,        270) /* ArmorLevel */
     , (870007,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870007, 106,        400) /* ItemSpellcraft */
     , (870007, 107,        800) /* ItemCurMana */
     , (870007, 108,        800) /* ItemMaxMana */
     , (870007, 109,        220) /* ItemDifficulty */
     , (870007, 158,          7) /* WieldRequirements - Level */
     , (870007, 159,          1) /* WieldSkillType - Axe */
     , (870007, 160,        275) /* WieldDifficulty */
     , (870007, 265,         47) /* EquipmentSetId - AncientRelicUpgrade */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870007,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870007,   5,  -0.033) /* ManaRate */
     , (870007,  13,     1.3) /* ArmorModVsSlash */
     , (870007,  14,     0.8) /* ArmorModVsPierce */
     , (870007,  15,     1.3) /* ArmorModVsBludgeon */
     , (870007,  16,       1) /* ArmorModVsCold */
     , (870007,  17,       1) /* ArmorModVsFire */
     , (870007,  18,     1.1) /* ArmorModVsAcid */
     , (870007,  19,     0.5) /* ArmorModVsElectric */
     , (870007, 165,       1) /* ArmorModVsNether */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870007,   1, 'Helm of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870007,   1, 0x0200122A) /* Setup */
     , (870007,   3, 0x20000014) /* SoundTable */
     , (870007,   7, 0x1000068B) /* ClothingBase */
     , (870007,   8, 0x060061D7) /* Icon */
     , (870007,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870007,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870007,  3964,      2)  /* Epic Focus */
     , (870007,  4227,      2)  /* Incantation of Impenetrability */
     , (870007,  4911,      2)  /* Epic Mana Conversion Prowess */;
```

## 870016 Necklace of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870016;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870016, 'Necklace of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870016,   1,          8) /* ItemType - Jewelry */
     , (870016,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870016,   5,        100) /* EncumbranceVal */
     , (870016,   8,         90) /* Mass */
     , (870016,   9,      32768) /* ValidLocations - NeckWear */
     , (870016,  16,          1) /* ItemUseable - No */
     , (870016,  19,      50000) /* Value */
     , (870016,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870016,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870016, 106,        350) /* ItemSpellcraft */
     , (870016, 107,       3000) /* ItemCurMana */
     , (870016, 108,       3000) /* ItemMaxMana */
     , (870016, 109,          0) /* ItemDifficulty */
     , (870016, 110,          0) /* ItemAllegianceRankLimit */
     , (870016, 151,          2) /* HookType - Wall */
     , (870016, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870016,  11, True ) /* IgnoreCollisions */
     , (870016,  13, True ) /* Ethereal */
     , (870016,  14, True ) /* GravityStatus */
     , (870016,  22, True ) /* Inscribable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870016,   5,  -0.033) /* ManaRate */
     , (870016,  12,    0.66) /* Shade */
     , (870016,  39,     0.9) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870016,   1, 'Necklace of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870016,   1, 0x020000F8) /* Setup */
     , (870016,   3, 0x20000014) /* SoundTable */
     , (870016,   6, 0x04000BEF) /* PaletteBase */
     , (870016,   8, 0x06005BE3) /* Icon */
     , (870016,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870016,  36, 0x0E000012) /* MutateFilter */
     , (870016,  46, 0x38000032) /* TsysMutationFilter */
     , (870016,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870016,  2666,      2)  /* Incantation of Arcane Enlightenment Self */
     , (870016,  4686,      2)  /* Incantation of Item Enchantment Mastery Self */
     , (870016,  6041,      2)  /* Legendary Arcane Prowess */;
```

## 870017 Bracelet of the Dawn.sql

```sql
DELETE FROM `weenie` WHERE `class_Id` = 870017;
INSERT INTO `weenie` (`class_Id`, `class_Name`, `type`, `last_Modified`)
VALUES (870017, 'Bracelet of the Dawn', 1, '2021-11-17 16:56:08') /* Generic */;
INSERT INTO `weenie_properties_int` (`object_Id`, `type`, `value`)
VALUES (870017,   1,          8) /* ItemType - Jewelry */
     , (870017,   3,          1) /* PaletteTemplate - AquaBlue */
     , (870017,   5,         60) /* EncumbranceVal */
     , (870017,   8,         90) /* Mass */
     , (870017,   9,     196608) /* ValidLocations - WristWear */
     , (870017,  16,          1) /* ItemUseable - No */
     , (870017,  19,      50000) /* Value */
     , (870017,  26,          1) /* AccountRequirements - AsheronsCall_Subscription */
     , (870017,  93,       1044) /* PhysicsState - Ethereal, IgnoreCollisions, Gravity */
     , (870017, 106,        350) /* ItemSpellcraft */
     , (870017, 107,       3000) /* ItemCurMana */
     , (870017, 108,       3000) /* ItemMaxMana */
     , (870017, 109,          0) /* ItemDifficulty */
     , (870017, 110,          0) /* ItemAllegianceRankLimit */
     , (870017, 151,          2) /* HookType - Wall */
     , (870017, 169,  118162702) /* TsysMutationData */;
INSERT INTO `weenie_properties_int64` (`object_Id`, `type`, `value`)
VALUES (870017,   4,          0) /* ItemTotalXp */
     , (870017,   5, 2000000000) /* ItemBaseXp */;
INSERT INTO `weenie_properties_bool` (`object_Id`, `type`, `value`)
VALUES (870017,  11, True ) /* IgnoreCollisions */
     , (870017,  13, True ) /* Ethereal */
     , (870017,  14, True ) /* GravityStatus */
     , (870017,  19, True ) /* Attackable */
     , (870017,  22, True ) /* Inscribable */
     , (870017, 100, False) /* Dyable */;
INSERT INTO `weenie_properties_float` (`object_Id`, `type`, `value`)
VALUES (870017,   5,  -0.033) /* ManaRate */
     , (870017,  12,    0.66) /* Shade */
     , (870017,  39,     0.5) /* DefaultScale */;
INSERT INTO `weenie_properties_string` (`object_Id`, `type`, `value`)
VALUES (870017,   1, 'Bracelet of the Dawn') /* Name */;
INSERT INTO `weenie_properties_d_i_d` (`object_Id`, `type`, `value`)
VALUES (870017,   1, 0x020000FB) /* Setup */
     , (870017,   3, 0x20000014) /* SoundTable */
     , (870017,   6, 0x04000BEF) /* PaletteBase */
     , (870017,   8, 0x06005BDE) /* Icon */
     , (870017,  22, 0x3400002B) /* PhysicsEffectTable */
     , (870017,  36, 0x0E000012) /* MutateFilter */
     , (870017,  46, 0x38000032) /* TsysMutationFilter */
     , (870017,  52, 0x06005B0C) /* IconUnderlay */;
INSERT INTO `weenie_properties_spell_book` (`object_Id`, `spell`, `probability`)
VALUES (870017,  4694,      2)  /* Epic Focus */
     , (870017,  6124,      2)  /* Incantation of Armor Tinkering Expertise Self */
     , (870017,  2014,      2)  /* Incantation of Item Tinkering Expertise Self */;
```

