# ACEForge
### Asheron's Call Content Development Tool for ACEmulator

**Version 0.3.23 Beta** | Windows Desktop Application

---

## What Is ACEForge?

ACEForge is a desktop application for Asheron's Call private server administrators running [ACEmulator](https://github.com/ACEmulator/ACE). It generates production-ready SQL for the ACE-World database (ACE-World-16PY schema, MySQL) — the exact format the server imports directly, with no hand-cleanup required.

The app is organized into four workspaces ("Forges"), selectable from the tab bar at the top:

| Forge | Purpose |
|-------|---------|
| **🔨 WeenieForge** | Build or edit any weenie — creatures, NPCs, items, weapons, armor, recipes, quest flags, events — through a structured property editor with a live SQL preview. |
| **✨ QuestForge** | Generate complete, correctly-linked quest SQL (kill tasks, collection turn-ins, NPC chains, quest flags) from guided templates, then hand off to WeenieForge for fine-tuning. |
| **📖 LoreForge** | An AI worldbuilding assistant for developing your server's lore, factions, NPCs, and story — kept in per-conversation history. |
| **⚔️ GearForge** | Batch-create custom armor/clothing/weapon sets by cloning base-game gear, or import existing gear SQL to edit and bulk-edit many items at once. |

Content can be created either by hand (structured forms with real-time SQL) or with AI assistance (local via Ollama, or a cloud provider).

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Operating System | Windows 10 / 11 (64-bit) |
| Runtime | Microsoft Edge WebView2 Runtime (preinstalled on current Windows; auto-updates) |
| RAM | 4 GB minimum (8 GB recommended if using local AI) |
| Disk Space | ~50 MB for the app; 2–5 GB additional for AI models (optional) |
| Internet | Required only for cloud AI, Ollama model downloads, and app updates |
| GPU | Not required, but dramatically speeds up local AI generation |

---

## Installation

1. Download `ACEForge_v0.x.x.zip` from the releases page.
2. Extract the zip to any folder on your PC (e.g. `C:\ACEForge\`).
3. Run `ACEForge.exe` to launch.

No installer required — ACEForge is fully portable.

> **First launch** creates a config file at `%APPDATA%\ACEForge\config.json` holding your settings, API keys, and WCID counters. It is never included in any zip or git repository.

---

## WeenieForge

WeenieForge is the core editor. It has two entry points:

- **⬆ Import Weenie SQL** — load any existing weenie `.sql` file to view and edit every property.
- **⬜ Import From Template** — start from a built-in template (Creature/Mob, NPC, Generator, Door, Chest, Event Controller, Stopgap) with stats auto-scaled to a level you choose.

Along the top of the editor are four content sub-tabs — **Weenie**, **Recipe**, **Quest**, **Event** — each producing SQL against the matching ACE table.

### Property Editor

Once content is loaded, properties are grouped into sub-tabs that map directly to the ACE `weenie_properties_*` tables:

| Sub-Tab | Contents |
|---------|----------|
| **Integer 32 / Integer 64** | All int properties. Enum-style ints (ItemType, TargetingTactic, PhysicsState, ShowableOnRadar, RadarBlipColor, ClothingPriority, Locations, UIEffects, and more) render as labeled dropdowns instead of raw numbers. |
| **Boolean** | True/False dropdowns. |
| **Float** | Float properties. `ArmorModVs*` and `Resist*` for every damage type (including Nether) render as intuitive sliders — weaker/stronger for armor mods, and the inverse for resists. |
| **String / Data ID** | String and DID properties. Icon/Setup DIDs get a picker and a live composite icon preview. |
| **Attribs / Skills** | Strength/Endurance/Quickness/Coordination/Focus/Self, Health/Stamina/Mana (base + current), and skills — all with sliders whose ranges you can set per section. |
| **Body Parts** | Per-hit-location armor levels and damage types. |
| **Create Items** | Contained/wielded/sold items (CreateList), with an armor-set helper. |
| **Generator** | `weenie_properties_generator` spawn rows. |
| **Position** | Placement coordinates (cell, origin, angles). |

The **PaletteTemplate** integer has a **Picker** that opens a searchable color palette — with a Grid view (color swatches) and a List view.

### Palette, Icons & 3D Preview

- **Palette Picker** — pick any `PALETTE_ENTRY_INT` value by color swatch or name.
- **Icon Picker** — browse the full game icon set (requires the Icon Library asset package).
- **3D Model Preview** — point Settings at your `client_portal.dat` to preview Setup DIDs in 3D.

---

## QuestForge

QuestForge generates guaranteed-valid quest SQL from templates rather than free-form AI, so quest flags, timers, and kill-task counters are always wired up correctly. Pick a quest type, fill in the guided form, and generate the full file set. Any generated file can be opened directly in WeenieForge for further editing via **✏ Edit in WeenieForge** — quest files open in the Quest sub-tab, weenies in the appropriate editor.

---

## LoreForge

LoreForge is a chat-based AI assistant for server worldbuilding — factions, regions, NPC backstories, quest hooks, and overall narrative. Conversations are saved individually and can be revisited, renamed, or deleted. A **Server Identity** panel lets you set your server's name, intent, and lore so every conversation stays on-theme.

---

## GearForge

GearForge specializes in armor, clothing, and weapons.

- **Set generation** — browse Armor Sets or Weapon Sets, pick the pieces you want (checkboxes), assign a starting WCID and optional name prefix, and generate a batch of editable items.
- **Import** — click **⬆ Import** to load one or more existing `.sql` files. GearForge only accepts armor/clothing/weapon weenies; creatures, jewelry, food, and other non-gear files are rejected automatically. When importing several files at once, the allowable gear is imported and the rest are skipped with a summary.
- **Per-item editor** — edit any Int/Bool/Float/String/DID property or spellbook entry on each item.
- **Bulk Edit** — apply a property change across every generated/imported item at once.
- **Save** — writes each item as its own weenie `.sql` file.

---

## AI Setup (Optional)

WeenieForge and QuestForge work fully offline. AI is only needed for LoreForge and AI-assisted generation.

### Option A — Local AI via Ollama (Recommended)

Runs entirely on your machine: no API key, no token limits, no per-generation cost.

1. Open the Local AI setup from the AI panel.
2. **Download & Install Ollama** — ACEForge fetches the installer (~60 MB) and launches it, then detects it on **↺ Check Again**.
3. **Pull a model** — download runs in the background with a live progress bar and auto-configures on completion.

| Model | Size | Best For |
|-------|------|----------|
| **Qwen 2.5 Coder 7B** ⭐ | ~4.5 GB | SQL/structured output — most accurate for ACE content. |
| CodeLlama 7B | ~3.8 GB | Reliable SQL formatting. |
| Llama 3.2 3B | ~2.0 GB | Fastest, lowest RAM; less reliable on complex chains. |

Ollama starts automatically in the background whenever ACEForge opens.

### Option B — Cloud API Key

Enter a key in **Settings → AI Provider**. OpenAI-compatible endpoints (LM Studio, Groq, Mistral, etc.) are supported via a custom Base URL.

> ⚠ Cloud plans impose token limits that can truncate long, multi-file output. For big quest chains, local Ollama is strongly recommended.

---

## Optional Asset Packages

Distributed separately; not required to run ACEForge but they improve AI accuracy and unlock the icon picker.

| Package | Size | Enables |
|---------|------|---------|
| **Icon Library** (`ACEForge_Icons.zip`) | ~21 MB | The full game icon set for the icon picker and correct icon DIDs. |
| **Weenie Database** (`ACEForge_WeenieDB.zip`) | ~38 MB | Indexed base-game weenies so AI Mode injects exact property values, resists, DIDs, and body-part tables from real game data. |

Install via **Settings → Content Libraries → 📦 Install Library Package…** and select the zip. A progress bar tracks extraction; libraries can be unloaded individually.

---

## Settings

| Setting | Description |
|---------|-------------|
| **Server Name** | Injected into AI prompts as context. |
| **Author / Admin** | Credited in generated file headers. |
| **Default Output Directory** | Where `.sql` files are saved (default: `Documents\ACEForge\output`). |
| **Per-Type Output Directories** | Optional separate folders for **Weenie**, **Recipe**, **Quest**, and **Event** files. Leave any blank to fall back to the default. QuestForge and WeenieForge route each file to the folder matching its detected type. |
| **AI Provider** | Ollama or an OpenAI-compatible cloud endpoint; API key stored only in your local config. |
| **client_portal.dat** | Optional — enables 3D Setup DID previews. |
| **Content Libraries** | Install/unload the Icon and Weenie asset packages. |
| **WCID Ranges** | Per-category next-available WCID counters (see below). |

### WCID Ranges

ACEForge tracks the next free WCID per content category so generated files never collide:

| Category | Default Start |
|----------|--------------|
| Campaign Creatures | 800,000 |
| Custom Items | 810,000 |
| Custom Portals | 820,000 |
| Structures | 830,000 |
| Bosses | 840,000 |
| Custom NPCs | 850,000 |
| Kill Contracts | 860,000 |
| Custom Gear | 870,000 |
| Kill Tasks (KT Flags) | 1,000,000 |

Set each **Next Available** counter to match your live server before generating, to avoid import collisions.

---

## Output & Importing

Every generated file follows the ACE-World MySQL import format, enforced by ACEForge regardless of source:

- Blank line between statements; `/* block comments */` only (no `--` line comments — the importer rejects them).
- `weenie_properties_body_part` and `weenie_properties_emote_action` column lists kept on a single line.
- Generators written as their own file (`WCID + 1,000,000`).
- Each file starts with `DELETE FROM weenie WHERE class_Id = WCID`, so re-importing replaces the existing WCID.

**Recommended import order** for new content: the weenie file first (it must exist before any generator references it), then the generator, then item/quest files. Generators with NULL coordinates won't spawn until `obj_Cell_Id` and origin values are populated.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Dropdowns don't open in the desktop app | Fixed — ACEForge now serves its UI over a local HTTP origin so WebView2 renders native `<select>` popups. Update to the latest build. |
| Blank window on launch | Ensure the Edge WebView2 Runtime is installed; reopen the app. |
| "Output may be incomplete" (AI) | Cloud token limit — switch to Ollama or split the request. |
| Ollama not detected after install | Restart ACEForge, then **↺ Check Again** in Local AI Setup. |
| Import rejected in GearForge | GearForge only accepts armor/clothing/weapon weenies; use WeenieForge for other types. |
| Import fails on the server | Confirm no `--` comments remain and column lists are single-line (ACEForge enforces this on save). |

---

## FAQ

**Can I use ACEForge without any AI?**
Yes. WeenieForge, QuestForge, and GearForge all work fully offline.

**Will it overwrite existing server content?**
Each file leads with `DELETE FROM weenie WHERE class_Id = WCID`; importing replaces that WCID. Verify WCIDs against your live database first.

**Where is my config?**
`%APPDATA%\ACEForge\config.json` — settings, API key, and WCID counters. Never bundled in any zip or commit.

**Can I add my own AI reference files?**
Yes. Drop `.md` files into `aceforge/references/`; they load automatically per content type.

---

## Community

Join the ACEForge Discord for help, updates, and to share content: **https://discord.gg/tfb6XUHVKz**
(There's a **Join Discord** button in the bottom-right of the app.)

---

## Credits

**ACEForge** was built for the Shattered Dawn ACEmulator community.

Built on:
- [ACEmulator](https://github.com/ACEmulator/ACE) — the open-source Asheron's Call server emulator
- [pywebview](https://pywebview.flowrl.com/) — Python desktop shell over Edge WebView2
- [Ollama](https://ollama.com/) — local LLM runtime

Weenie database sourced from the ACE-World core dataset.

---

*ACEForge is a fan-made tool for private server administration. Asheron's Call is a trademark of Warner Bros. Entertainment.*
