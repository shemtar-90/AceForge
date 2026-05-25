"""
ACEForge Enum Data
All enum lookups used by the manual editor dropdowns.
Sourced from enums.md (ACE Emulator authoritative source).
"""

WEENIE_TYPES = {
    1: "Generic", 2: "Clothing", 3: "MissileLauncher", 4: "Missile",
    6: "MeleeWeapon", 7: "Portal", 8: "Book", 9: "Coin", 10: "Creature",
    12: "Vendor", 18: "Food", 19: "Door", 20: "Chest", 21: "Container",
    22: "Key", 24: "PressurePlate", 25: "LifeStone", 26: "Switch",
    28: "Healer", 29: "LightSource", 32: "SpellComponent", 34: "Scroll",
    35: "Caster", 37: "ManaStone", 38: "Gem", 51: "Stackable",
}

CREATURE_TYPES = {
    1:"Olthoi", 2:"Banderling", 3:"Drudge", 4:"Mosswart", 5:"Lugian",
    6:"Tumerok", 7:"Mite", 8:"Tusker", 9:"PhyntosWasp", 10:"Rat",
    11:"Auroch", 13:"Golem", 14:"Undead", 15:"Gromnie", 16:"Reedshark",
    17:"Armoredillo", 18:"Fae", 19:"Virindi", 20:"Wisp", 21:"Knathtead",
    22:"Shadow", 23:"Mattekar", 24:"Mumiyah", 25:"Rabbit", 26:"Sclavus",
    27:"ShallowsShark", 28:"Monouga", 29:"Zefir", 30:"Skeleton", 31:"Human",
    32:"Shreth", 33:"Chittick", 34:"Moarsman", 35:"OlthoiLarvae", 36:"Slithis",
    37:"Deru", 38:"FireElemental", 39:"Snowman", 41:"Bunny",
    42:"LightningElemental", 43:"Rockslide", 44:"Grievver", 45:"Niffis",
    46:"Ursuin", 47:"Crystal", 48:"HollowMinion", 49:"Scarecrow", 50:"Idol",
    51:"Empyrean", 52:"Hopeslayer", 53:"Doll", 54:"Marionette", 55:"Carenzi",
    56:"Siraluun", 57:"AunTumerok", 58:"HeaTumerok", 59:"Simulacrum",
    60:"AcidElemental", 61:"FrostElemental", 62:"Elemental", 63:"Statue",
    65:"AlteredHuman", 67:"Harbinger", 68:"DarkSarcophagus", 70:"GotrokLugian",
    71:"Margul", 75:"Burun", 77:"Ghost", 78:"Fiun", 79:"Eater", 80:"Penguin",
    81:"Ruschk", 82:"Thrungus", 83:"ViamontianKnight", 84:"Remoran",
    85:"Swarm", 86:"Moar", 87:"EnchantedArms", 88:"Sleech", 89:"Mukkir",
    90:"Merwart", 92:"ParadoxOlthoi", 99:"GearKnight", 100:"Gurog", 101:"Anekshay",
}

PALETTE_TEMPLATES = {
    1:"AquaBlue", 2:"Blue", 3:"BluePurple", 4:"Brown", 5:"DarkBlue",
    6:"DeepBrown", 7:"DeepGreen", 8:"Green", 9:"Grey", 10:"LightBlue",
    11:"Maroon", 12:"Navy", 13:"Purple", 14:"Red", 15:"RedPurple",
    16:"Rose", 17:"Yellow", 18:"YellowBrown", 19:"Copper", 20:"Silver",
    21:"Gold", 22:"Aqua", 39:"Black", 40:"Bronze", 41:"SandyYellow",
    42:"DarkBrown", 43:"LightBrown", 44:"TanRed", 45:"PaleGreen",
    46:"Tan", 47:"PastyYellow", 48:"SnowyWhite",
}

DAMAGE_TYPES = {
    0:"None", 1:"Slash", 2:"Pierce", 4:"Bludgeon", 8:"Cold",
    16:"Fire", 32:"Acid", 64:"Electric", 128:"Health", 256:"Stamina",
    512:"Mana", 1024:"Nether",
}

COMBAT_STYLES = {
    1:"Unarmed", 2:"OneHanded", 4:"OneHandedAndShield", 6:"OneHanded+Shield",
    8:"TwoHanded", 16:"Bow", 32:"Crossbow", 64:"Sling",
    128:"ThrownWeapon", 256:"DualWield", 512:"Magic", 1024:"Atlatl",
    2048:"ThrownShield",
}

ATTACK_TYPES = {
    1:"Punch", 2:"Thrust", 4:"Slash", 6:"Thrust+Slash", 8:"Kick",
    16:"OffhandPunch", 32:"DoubleSlash", 64:"TripleSlash",
    128:"DoubleThrust", 256:"TripleThrust",
}

SKILL_TYPES = {
    6:"MeleeDefense", 7:"MissileDefense", 14:"ArcaneLore", 15:"MagicDefense",
    16:"ManaConversion", 18:"ItemAppraisal", 19:"PersonalAppraisal",
    20:"Deception", 21:"Healing", 22:"Jump", 23:"Lockpick", 24:"Run",
    27:"CreatureAppraisal", 28:"WeaponAppraisal", 29:"ArmorAppraisal",
    30:"MagicItemAppraisal", 31:"CreatureEnchantment", 32:"ItemEnchantment",
    33:"LifeMagic", 34:"WarMagic", 35:"Leadership", 36:"Loyalty",
    37:"Fletching", 38:"Alchemy", 39:"Cooking", 40:"Salvaging",
    41:"TwoHandedCombat", 43:"VoidMagic", 44:"HeavyWeapons",
    45:"LightWeapons", 46:"FinesseWeapons", 47:"MissileWeapons",
    48:"Shield", 49:"DualWield", 50:"Recklessness", 51:"SneakAttack",
    52:"DirtyFighting", 54:"Summoning",
}

SKILL_SAC = {1: "Untrained", 2: "Trained", 3: "Specialized"}

PHYSICS_STATES = {
    1044:  "1044 — Item/Generator (Ethereal+IgnoreCollisions+Gravity)",
    3080:  "3080 — Standard Creature (ReportCollisions+Gravity+LightingOn)",
    6292504: "6292504 — NPC (ReportCollisions+IgnoreCollisions+Gravity+EdgeSlide)",
}

PHYSICS_STATE_VALUES = {
    "Item/Generator": 1044,
    "Standard Creature": 3080,
    "NPC": 6292504,
}

RADAR_BLIP_COLORS = {
    1:"Blue", 2:"Gold", 3:"White", 4:"Purple", 5:"Red",
    6:"Pink", 7:"Green", 8:"Yellow (NPC)", 9:"Cyan",
}

PLAYER_KILLER_STATUS = {
    0:"NonPK", 2:"PK", 4:"PKLite", 8:"Free", 16:"RubberGlue",
}

ITEM_USEABLE = {
    1:"No", 2:"Self", 4:"Wielded", 8:"Contained", 16:"Viewed", 32:"Remote",
}

BONDED_STATUS = {
    -2:"Destroy", -1:"Slippery", 0:"Normal", 1:"Bonded", 2:"Sticky",
}

ATTUNED_STATUS = {0:"Normal", 1:"Attuned", 2:"Sticky"}

COMBAT_MODE = {1:"Unarmed", 2:"Melee", 3:"Missile", 4:"Magic"}

COMBAT_USE = {0:"None", 1:"Melee", 2:"Missile", 3:"Ammo", 4:"Shield", 5:"TwoHanded"}

TARGETING_TACTICS = {
    1:"Random", 2:"Focused", 4:"LastDamager", 5:"Random+LastDamager",
    8:"TopDamager", 16:"Weakest", 32:"Strongest", 64:"Nearest",
}

TOLERANCE = {
    0:"None", 1:"NoAttack", 2:"Appraise", 8:"Provoke",
    32:"Target", 64:"Retaliate", 128:"Monster",
}

SHOWABLE_ON_RADAR = {0:"Never", 2:"Movement", 4:"Always"}

REGEN_LOCATION_TYPE = {
    1:"OnTop", 2:"Scatter", 4:"Specific", 8:"Contain", 16:"Wield",
    32:"Shop", 64:"Treasure", 66:"ScatterTreasure", 68:"SpecificTreasure",
    72:"ContainTreasure", 80:"WieldTreasure", 96:"ShopTreasure",
}

REGEN_TYPE_WHEN = {1:"Destruction", 2:"PickUp", 4:"Death"}

DESTINATION_TYPE = {
    1:"Contain", 2:"Wield", 4:"Shop", 8:"Treasure",
    9:"ContainTreasure", 10:"WieldTreasure", 12:"ShopTreasure",
}

EMOTE_CATEGORY = {
    1:"Refuse", 2:"Vendor", 3:"Death", 4:"Portal", 5:"HeartBeat",
    6:"Give", 7:"Use", 8:"Activation", 9:"Generation", 10:"PickUp",
    11:"Drop", 12:"QuestSuccess", 13:"QuestFailure", 14:"Taunt",
    15:"WoundedTaunt", 16:"KillTaunt", 17:"NewEnemy", 18:"Scream",
    19:"Homesick", 20:"ReceiveCritical", 21:"ResistSpell",
    22:"TestSuccess", 23:"TestFailure", 24:"HearChat", 25:"Wield",
    26:"UnWield", 27:"EventSuccess", 28:"EventFailure",
    29:"TestNoQuality", 30:"QuestNoFellow", 31:"TestNoFellow",
    32:"GotoSet", 33:"NumFellowsSuccess", 34:"NumFellowsFailure",
    35:"NumCharacterTitlesSuccess", 36:"NumCharacterTitlesFailure",
    37:"ReceiveLocalSignal", 38:"ReceiveTalkDirect",
}

EMOTE_TYPE = {
    2:"AwardXP", 3:"Give", 4:"MoveHome", 5:"Motion", 6:"Move",
    7:"PhysScript", 8:"Say", 9:"Sound", 10:"Tell", 11:"Turn",
    12:"TurnToTarget", 13:"TextDirect", 14:"CastSpell",
    15:"Activate", 16:"WorldBroadcast", 17:"LocalBroadcast",
    18:"DirectBroadcast", 19:"CastSpellInstant", 20:"UpdateQuest",
    21:"InqQuest", 22:"StampQuest", 23:"StartEvent", 24:"StopEvent",
    30:"InqQuestSolves", 31:"EraseQuest", 32:"DecrementQuest",
    33:"IncrementQuest", 34:"AddCharacterTitle", 35:"InqBoolStat",
    36:"InqIntStat", 47:"AwardTrainingCredits", 48:"InflictVitaePenalty",
    49:"AwardLevelProportionalXP", 50:"AwardLevelProportionalSkillXP",
    51:"InqEvent", 52:"ForceMotion", 53:"SetIntStat",
    67:"Goto", 68:"PopUp", 69:"SetBoolStat", 70:"SetQuestCompletions",
    72:"Generate", 74:"TakeItems", 75:"InqYesNo", 76:"InqOwnsItems",
    77:"DeleteSelf", 78:"KillSelf", 79:"UpdateMyQuest",
    80:"InqMyQuest", 81:"StampMyQuest", 82:"InqMyQuestSolves",
    83:"EraseMyQuest", 87:"MoveToPos", 88:"LocalSignal",
    89:"InqPackSpace", 90:"RemoveVitaePenalty",
    99:"TeleportTarget", 100:"TeleportSelf",
    112:"SpendLuminance", 113:"AwardLuminance", 115:"SetInt64Stat",
    116:"OpenMe", 117:"CloseMe", 119:"AddContract", 120:"RemoveContract",
}

BODY_PART_KEYS = {
    0:"Head", 1:"Chest", 2:"Abdomen", 3:"UpperArm", 4:"LowerArm",
    5:"Hand", 6:"UpperLeg", 7:"LowerLeg", 8:"Foot",
    9:"Horn", 10:"FrontLeg", 12:"FrontFoot", 13:"RearLeg",
    15:"RearFoot", 16:"Torso", 17:"Tail", 18:"Arm", 19:"Leg",
    20:"Claw", 21:"Wings", 22:"Breath", 23:"Tentacle", 26:"Cloak",
}

PROPERTY_INT_NAMES = {
    1:"ItemType", 2:"CreatureType", 3:"PaletteTemplate", 4:"ClothingPriority",
    5:"EncumbranceVal", 6:"ItemsCapacity", 7:"ContainersCapacity", 8:"Mass",
    9:"ValidLocations", 10:"CurrentWieldedLocation", 11:"MaxStackSize",
    12:"StackSize", 13:"StackUnitEncumbrance", 14:"StackUnitMass",
    15:"StackUnitValue", 16:"ItemUseable", 17:"RareId", 18:"UiEffects",
    19:"Value", 25:"Level", 27:"ArmorType", 28:"ArmorLevel", 33:"Bonded",
    36:"ResistMagic", 37:"ResistItemAppraisal", 38:"ResistLockpick",
    40:"CombatMode", 44:"Damage", 45:"DamageType", 46:"DefaultCombatStyle",
    47:"AttackType", 48:"WeaponSkill", 49:"WeaponTime", 50:"AmmoType",
    51:"CombatUse", 52:"ParentLocation", 67:"Tolerance", 68:"TargetingTactic",
    69:"CombatTactic", 74:"MerchandiseItemTypes", 75:"MerchandiseMinValue",
    76:"MerchandiseMaxValue", 81:"MaxGeneratedObjects", 82:"InitGeneratedObjects",
    86:"MinLevel", 87:"MaxLevel", 89:"BoosterEnum", 90:"BoostValue",
    91:"MaxStructure", 92:"Structure", 93:"PhysicsState", 94:"TargetType",
    95:"RadarBlipColor", 100:"GeneratorType", 101:"AiAllowedCombatStyle",
    106:"ItemSpellcraft", 107:"ItemCurMana", 108:"ItemMaxMana", 114:"Attuned",
    126:"VendorHappyMean", 127:"VendorHappyVariance", 133:"ShowableOnRadar",
    134:"PlayerKillerStatus", 140:"AiOptions", 142:"GeneratorTimeType",
    146:"XpOverride", 150:"HookPlacement", 151:"HookType", 158:"WieldRequirements",
    159:"WieldSkilltype", 160:"WieldDifficulty", 169:"TsysMutationData",
    204:"ElementalDamageBonus", 270:"WieldRequirements2", 271:"WieldSkilltype2",
    272:"WieldDifficulty2", 292:"Cleaving", 307:"DamageRating",
    308:"DamageResistRating", 313:"CritRating", 314:"CritDamageRating",
    315:"CritResistRating", 317:"HealingResistRating", 323:"HealingBoostRating",
    332:"LuminanceAward", 353:"WeaponType", 390:"Enlightenment",
}

PROPERTY_BOOL_NAMES = {
    1:"Stuck", 6:"AiUsesMana", 7:"AiUseHumanMagicAnimations", 8:"AllowGive",
    11:"IgnoreCollisions", 12:"ReportCollisions", 13:"Ethereal",
    14:"GravityStatus", 15:"LightsStatus", 18:"Visibility", 19:"Attackable",
    22:"Inscribable", 23:"DestroyOnSell", 29:"NoCorpse",
    39:"DealMagicalItems", 41:"ReportCollisionsAsEnvironment",
    42:"AllowEdgeSlide", 50:"NeverFailCasting", 52:"AiImmobile",
    63:"UnlimitedUse", 65:"IgnoreMagicResist", 66:"IgnoreMagicArmor",
    79:"AiAcceptEverything", 91:"Retained", 98:"Invincible", 120:"TreasureCorpse",
}

PROPERTY_FLOAT_NAMES = {
    1:"HeartbeatInterval", 2:"HeartbeatTimestamp", 3:"HealthRate",
    4:"StaminaRate", 5:"ManaRate", 11:"ResetInterval", 12:"Shade",
    13:"ArmorModVsSlash", 14:"ArmorModVsPierce", 15:"ArmorModVsBludgeon",
    16:"ArmorModVsCold", 17:"ArmorModVsFire", 18:"ArmorModVsAcid",
    19:"ArmorModVsElectric", 21:"WeaponLength", 22:"DamageVariance",
    29:"WeaponDefense", 31:"VisualAwarenessRange", 34:"PowerupTime",
    36:"ChargeSpeed", 37:"BuyPrice", 38:"SellPrice", 39:"DefaultScale",
    41:"RegenerationInterval", 43:"GeneratorRadius", 54:"UseRadius",
    62:"WeaponOffense", 64:"ResistSlash", 65:"ResistPierce",
    66:"ResistBludgeon", 67:"ResistFire", 68:"ResistCold",
    69:"ResistAcid", 70:"ResistElectric", 71:"ResistHealthBoost",
    72:"ResistStaminaDrain", 73:"ResistStaminaBoost", 74:"ResistManaDrain",
    75:"ResistManaBoost", 80:"AiUseMagicDelay", 104:"ObviousRadarRange",
    122:"AiAcquireHealth", 125:"ResistHealthDrain", 136:"CriticalMultiplier",
    144:"ManaConversionMod", 149:"WeaponMissileDefense",
    150:"WeaponMagicDefense", 152:"ElementalDamageMod",
    165:"ArmorModVsNether", 166:"ResistNether",
}

PROPERTY_STRING_NAMES = {
    1:"Name", 7:"Inscription", 14:"Use", 15:"ShortDesc", 16:"LongDesc",
    17:"ActivationTalk", 18:"UseMessage", 20:"PluralName",
    22:"ActivationFailure", 33:"Quest", 34:"GeneratorEvent",
    38:"AppraisalPortalDestination", 45:"KillQuest",
    49:"KillQuest2", 50:"KillQuest3", 51:"UseSendsSignal",
}

PROPERTY_DID_NAMES = {
    1:"Setup", 2:"MotionTable", 3:"SoundTable", 4:"CombatTable",
    6:"PaletteBase", 7:"Clothingbase", 8:"Icon", 22:"PhysicsEffectTable",
    28:"Spell", 32:"WieldedTreasureType", 35:"DeathTreasureType",
    36:"MutateFilter", 38:"UseCreateItem", 46:"TsysMutationFilter",
    50:"IconOverlay", 52:"IconUnderlay", 55:"ProcSpell",
}

PROPERTY_ATTRIBUTE_NAMES = {
    1:"Strength", 2:"Endurance", 3:"Quickness", 4:"Coordination",
    5:"Focus", 6:"Self",
}

PROPERTY_ATTRIBUTE2ND_NAMES = {1:"MaxHealth", 3:"MaxStamina", 5:"MaxMana"}

# Common DID values for quick lookup
COMMON_PHYSICS_EFFECT_TABLES = {
    "Standard Creature": "0x34000026",
    "Standard Item/Generator": "0x3400002B",
    "Generator (invisible)": "0x34000072",
}

COMMON_SOUND_TABLES = {
    "Human/NPC": "0x20000008",
    "Generic/Item": "0x20000014",
    "Skeleton": "0x20000006",
    "Tumerok": "0x20000013",
}

# Motion commands (hex -> name) for emote motion dropdown
MOTION_COMMANDS = {
    "318767239": "Wave",
    "318767230": "ClapHands",
    "318767231": "Cry",
    "318767232": "Laugh",
    "318767236": "Point",
    "318767241": "HeartyLaugh",
    "318767242": "Salute",
    "318767246": "WaveHigh",
    "318767247": "WaveLow",
    "318767250": "Kneel",
    "318767252": "Shiver",
    "318767229": "BowDeep",
    "268435537": "Twitch1",
    "268435538": "Twitch2",
    "268435539": "Twitch3",
    "268435540": "Twitch4",
}


def make_dropdown_list(d: dict, show_id: bool = True) -> list[str]:
    """Convert an enum dict to display strings for CTkOptionMenu."""
    if show_id:
        return [f"{k} — {v}" for k, v in sorted(d.items())]
    return [v for v in sorted(d.values())]


def parse_dropdown_id(selection: str) -> int | None:
    """Extract the ID from a 'ID — Name' dropdown string."""
    try:
        return int(selection.split(" — ")[0])
    except (ValueError, IndexError):
        return None
