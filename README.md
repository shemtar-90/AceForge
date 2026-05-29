# ACEForge — Weenie Workbench
### Content Creation Tool for ACEmulator (Asheron's Call Private Servers)

**Version 1.8.0** | Windows Desktop Application

---

## What Is ACEForge?

ACEForge is a desktop application for Asheron's Call private server administrators running [ACEmulator](https://github.com/ACEmulator/ACE). It generates production-ready SQL files for the ACE-World database — the format the server imports directly.

Instead of writing SQL by hand or navigating complex database schemas, ACEForge gives you two ways to create content:

- **Manual Mode** — Fill out a structured form, see the SQL update in real time, save when ready.
- **AI Mode** — Describe what you want in plain English. The AI writes the complete SQL file set, including generators, emote chains, quest flags, and all related tables.

Every file ACEForge produces is import-ready. No cleanup needed.

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Operating System | Windows 10 / 11 (64-bit) |
| RAM | 4 GB minimum (8 GB recommended if using local AI) |
| Disk Space | ~50 MB for the app; 2–5 GB additional for AI models (optional) |
| Internet | Required for cloud AI providers and initial Ollama model download |
| GPU | Not required, but dramatically speeds up local AI generation |

---

## Installation

1. Download `ACEForge_v1.x.x.zip` from the releases page.
2. Extract the zip to any folder on your PC (e.g. `C:\ACEForge\`).
3. Run `ACEForge.exe` to launch.

No installer required. ACEForge is fully portable.

> **First launch**: ACEForge will create a config file at `%APPDATA%\ACEForge\config.json`. This stores your API keys, server settings, and WCID counters. It is never included in any zip or git repository.

---

## Optional Asset Packages

Two large asset packages are distributed separately and are not required to run ACEForge, but significantly improve AI Mode accuracy.

### Icon Library (`ACEForge_Icons.zip` — ~21 MB)
Contains all 12,371 game icon PNGs and the icon index file. Enables the icon picker in the form and allows the AI to reference correct icon DIDs.

### Weenie Database (`ACEForge_WeenieDB.zip` — ~38 MB)
Contains all 29,569 base-game weenie SQL files indexed for lookup. When installed, AI Mode automatically finds and injects matching base-game weenies into every generation request — giving the AI exact property values, resist floats, DID setups, and body part tables from the actual game.

#### Installing Asset Packages

1. Open ACEForge and click **Settings** (top-right).
2. Scroll to **Content Libraries**.
3. Click **📦 Install Library Package…**
4. Browse to and select the zip file (`ACEForge_Icons.zip` or `ACEForge_WeenieDB.zip`).
5. A progress bar tracks extraction. Both packages install automatically — no manual file placement needed.

The status panel shows ✅ with entry counts when each library is active. Libraries can be unloaded individually from the same panel.

---

## First-Time Setup

### Step 1 — Configure Your Server

Open **Settings** and fill in:

| Field | Description |
|-------|-------------|
| **Server Name** | Your server's name. Used in AI prompts as context. |
| **Author / Admin** | Your name or handle. Credited in generated file headers. |
| **Output Folder** | Where `.sql` files are saved. Defaults to `Documents\ACEForge\output`. |
| **Auto-Open Folder** | If enabled, opens the output folder after each save. |

### Step 2 — WCID Ranges

ACEForge tracks the next available WCID for each content category so generated files never collide. Default ranges:

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
| Generators | Target WCID + 1,000,000 |

Update the **Next Available** counter for each category to match your server's current state before generating new content.

### Step 3 — Set Up AI

Choose one of two AI approaches:

---

#### Option A — Local AI via Ollama (Recommended)

Local AI runs entirely on your machine. No API key, no token limits, no internet required after setup, and no cost per generation.

**To set up:**

1. In AI Mode, click the **⟳ LOCAL AI** button at the top of the panel.
2. The Local AI Setup window opens with a guided two-step process.

**Step 1 — Install Ollama**

Click **⬇ Download & Install Ollama**. ACEForge downloads the installer (~60 MB) from ollama.com and launches it automatically. After installation finishes, click **↺ Check Again** — ACEForge will detect it.

**Step 2 — Download a Model**

Three models are available. Click **⬇ Pull** next to your preferred model. ACEForge downloads it in the background with a live progress bar (e.g. *"Downloading qwen2.5-coder:7b… 2.1 GB / 4.5 GB"*). When the download completes, ACEForge automatically configures itself to use that model. No settings to touch.

**Recommended Models:**

| Model | Size | Best For |
|-------|------|----------|
| **Qwen 2.5 Coder 7B** ⭐ | 4.5 GB | SQL generation — trained on structured/schema data. Most accurate for ACE content. |
| CodeLlama 7B | 3.8 GB | Good SQL output, reliable formatting. Meta's code model. |
| Llama 3.2 3B | 2.0 GB | Fastest, lowest RAM use. Less reliable for complex quest chains. |

Once set up, Ollama starts automatically in the background every time ACEForge opens.

---

#### Option B — Cloud API Key

If you already have an API key from a supported provider, enter it in Settings under **AI Provider**.

| Provider | Notes |
|----------|-------|
| **Anthropic** (Claude) | High quality. Token limits apply per plan. |
| **Google AI Studio** | Fast. Free tier available. |
| **OpenAI** | Works with GPT-4o and compatible endpoints. |
| **OpenAI-Compatible** | For LM Studio, Groq, Mistral, or any OpenAI-format endpoint. Enter a custom Base URL. |

> ⚠ **Cloud API Notice:** SQL output length may be limited by your plan's token quota. For long quest chains or multi-file generation, local Ollama is strongly recommended.

---

## Manual Mode

Manual Mode gives you a structured form for each content type. The SQL preview on the right updates in real time as you type.

### Content Types

| Tab | Icon | What It Creates |
|-----|------|----------------|
| **Creature** | ✠ | Combat-ready hostile mobs with full stat, resist, and body part tables |
| **NPC** | ◆ | Quest givers, merchants, and interactive characters |
| **Item** | ◈ | Quest tokens, gems, stackables, consumables, containers |
| **Weapon** | ⚔ | Melee weapons, missile launchers, and casters |
| **Armor/Clothing** | ⛨ | Armor and clothing for all body locations |
| **Jewelry** | ◎ | Rings, necklaces, bracelets, wristlets |
| **Recipe** | ⚗ | Crafting recipes combining source and target items |
| **Quest** | ◇ | Quest flags, kill task counters, and timer flags |
| **Generator** | ⟳ | Spawn generators for creatures, NPCs, and objects |

### Presets

Every content type has a **Presets** dropdown populated with common starting points. Selecting a preset fills in sensible defaults that you can adjust before saving.

### Sub-Tabs

Each content type has multiple sub-tabs within the form:

| Sub-Tab | Available On | Contents |
|---------|-------------|----------|
| **⚙ Properties** | All types | Name, WCID, level, scale, resistances, radar color, etc. |
| **◈ Attributes** | Creature, NPC | Strength, Endurance, Quickness, Coordination, Focus, Self, plus Health/Stamina/Mana |
| **+ Skills** | Creature, NPC | Skill training level and init value |
| **+ Spellbook** | Creature, NPC, Jewelry | Spell IDs and cast probabilities |
| **✠ Body Parts** | Creature, NPC | Hit location armor levels and damage types |
| **◇ Emotes** | NPC, Item | Quest dialogue and emote action chains |

### Generator Tab

The Generator tab creates `weenie_properties_generator` entries — the records that tell the server where and when to spawn a creature or NPC.

**Available presets:**

| Preset | Respawn | Spawn Condition |
|--------|---------|----------------|
| Creature Respawn | 300s (5 min) | Always |
| Boss (Rare) | 3600s (1 hour) | Always |
| Event Spawn | 60s | Event only |
| NPC (Stationary) | 0s | Always |
| Chest / Container | 1800s (30 min) | Always |

Enter the **Target WCID** — the creature or NPC this generator spawns. The **Generator WCID** auto-calculates as `Target WCID + 1,000,000`.

The **Placement Coordinates** section (obj_Cell_Id, Origin X/Y/Z, Angles W/X/Y/Z) can be left as NULL and filled in later using a spawn tool or by editing the file directly.

### Saving

Click **+ Save** in the SQL preview panel to write the file to your output folder. The WCID counter for that content category increments automatically. If **Auto-Open Folder** is enabled, the output folder opens immediately.

---

## AI Mode

AI Mode takes a plain-English description and produces complete, multi-file SQL output ready for server import.

### How to Use

1. Select the content type from the tabs (Creature, NPC, Item, etc.).
2. Type a description in the **Prompt** box.
3. Click **Generate** or press **Ctrl+Enter**.
4. The AI streams its response into the output panel in real time.
5. When generation is complete, click **💾 Save Files** to write all files to your output folder.

### Writing Effective Prompts

The more specific you are, the better the output.

**Basic:**
> `A fire elemental creature at level 150`

**Detailed:**
> `A level 150 fire elemental boss named Ignareth the Undying. High fire resistance, weak to cold. Drops a custom fire essence item. Casts Flame Arc VII and Inferno VII. Requires level 200+ to wield any drops.`

**Quest chain:**
> `An NPC named Aldric Stonewatch who gives a collection quest. Players must bring him 5 Ancient Stone Tablets found in Olthoi-infested ruins. Reward: 15% level-proportional XP and 10,000 luminance. Include start, in-progress, and completion dialogue.`

### What AI Mode Produces

For a creature or NPC request, AI Mode typically outputs:

| File | Contents |
|------|----------|
| `WCID Name.sql` | The weenie (all property tables) |
| `WCID Name gen.sql` | The generator (always a separate file, WCID + 1,000,000) |
| `WCID Item Name.sql` | Any custom drop items defined in the prompt |
| `QuestName.sql` | Quest flag entries, if a quest was described |

Each file is saved individually using `/* ===== FILE: filename.sql ===== */` markers that ACEForge's parser uses to split the output.

### Quest Naming Conventions (AI Mode)

ACEForge follows the standard ACE quest flag naming pattern:

**Standard collection/turn-in quest:**
- `QuestName` — Main completion counter
- `QuestNameStart` — Set when player accepts; checked for in-progress state
- `QuestNameTimer` — Cooldown after completion

**Kill task:**
- `KillTaskName` — Kill counter (incremented by kill task system)
- `KillTaskNameProgress` — In-progress flag
- `KillTaskNameComplete` — Set when kill count is met
- `KillTaskNameTimer` — Cooldown after reward

### Incomplete Output Warning

If the AI stops before finishing all files, an amber ⚠ warning banner appears in the output panel. This is a token limit issue, most common with cloud API plans on complex requests.

**Solutions:**
- Switch to local Ollama (no token limits)
- Split the request into smaller pieces (generate the NPC separately from the quest)
- Retry — results vary between runs

---

## Output Files

All files save to your configured output folder (`Documents\ACEForge\output` by default).

### SQL Format

Every generated file follows the ACE-World MySQL import format with these rules always enforced by ACEForge — regardless of what the AI produced:

- Blank line between every SQL statement (after each `;`)
- No `--` line comments (ACE importer rejects them) — only `/* block comments */`
- `weenie_properties_body_part` column list always on a single line
- `weenie_properties_emote_action` column list always on a single line
- File names use spaces, never underscores (`850010 Shadow Fiend.sql`)
- Generator files are always separate from the creature/NPC file

### File Naming

```
850010 Shadow Fiend.sql          creature / NPC / item / weapon / armor / jewelry
1850010 shadow fiend gen.sql     generator (auto-created for creature/NPC)
AncientTabletQuest.sql           quest flag entries
```

---

## Importing Into Your Server

1. Copy generated `.sql` files to your ACE database tools folder.
2. Import using your MySQL client or the ACE world database importer.
3. Recommended import order for a new creature:
   - `WCID Name.sql` first (the weenie must exist before the generator references it)
   - `WCID Name gen.sql` second
   - Any item or quest files

> Generators with NULL coordinates will not spawn anything until `obj_Cell_Id` and origin values are populated. Use a spawn tool or edit the file with coordinates from your world editor.

---

## Settings Reference

### AI Provider

| Setting | Description |
|---------|-------------|
| Provider | anthropic, google, openai, compatible, or ollama |
| API Key | Your key for cloud providers (stored only in `%APPDATA%\ACEForge\config.json`) |
| Model | Model string (e.g. `claude-sonnet-4-20250514`, `qwen2.5-coder:7b`) |
| Base URL | Required for compatible/Ollama providers |

### Server

| Setting | Description |
|---------|-------------|
| Server Name | Injected into every AI prompt as context |
| Author | Your name/handle; included in file headers |
| Output Folder | Where `.sql` files are saved |
| Auto-Open Folder | Opens the output folder after each save |

### WCID Ranges

Each category has a **Start** (fixed) and **Next Available** (increments after each save). Set Next Available to match your live server to avoid WCID collisions on import.

### Content Libraries

| Library | Source File | Size |
|---------|-------------|------|
| Icon Library | `ACEForge_Icons.zip` | ~21 MB |
| Weenie Database | `ACEForge_WeenieDB.zip` | ~38 MB |

Click **📦 Install Library Package…** to install either. A progress bar tracks extraction. Use Unload to remove without reinstalling the app.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Blank form on launch | JavaScript crash on load | Reopen app; verify Edge WebView2 runtime is installed |
| `--` comments in output | Pre-v1.6.6 cached output | Update to latest; parser strips them automatically on every save |
| Underscores in file names | Pre-v1.6.6 bug | Update to latest |
| Generator appended to creature file | Pre-v1.7.0 bug | Update to latest; generator is always its own file |
| "Output may be incomplete" warning | Token limit hit | Switch to Ollama or split the prompt into smaller requests |
| Ollama not detected after install | PATH not updated | Open Local AI Setup → Click ↺ Check Again after restarting ACEForge |
| Import fails on server | Formatting error | Verify no `--` comments remain; check body_part column list is one line |
| Library install shows no progress | Very fast extraction | Normal — small packages finish before progress renders |

---

## Frequently Asked Questions

**Can I use ACEForge without any AI at all?**
Yes. Manual Mode works completely offline with no API key or Ollama required.

**Will ACEForge overwrite existing content on my server?**
Every file starts with `DELETE FROM weenie WHERE class_Id = WCID`. If that WCID exists, the import replaces it. Always verify WCIDs against your live database before importing.

**Can I add my own reference files for the AI?**
Yes. Drop `.md` files into `aceforge/references/`. They are loaded automatically per content type. Creature prompts load `example_creatures.md`, NPC prompts load `example_npcs.md`, and so on.

**Where is my config saved?**
`%APPDATA%\ACEForge\config.json` — your API key, output folder, and WCID counters. Never included in any zip, git commit, or distributed package.

**The AI generated incorrect table names.**
Install the Weenie Database library package. It gives the AI exact property formats from real game data. If errors persist, regenerate — AI output is non-deterministic and results vary between runs.

---

## Credits

**ACEForge** was built for the Shattered Dawn ACEmulator community.

Built on:
- [ACEmulator](https://github.com/ACEmulator/ACE) — the open-source Asheron's Call server emulator
- [pywebview](https://pywebview.flowrl.com/) — Python desktop shell using Edge WebView2
- [Ollama](https://ollama.com/) — local LLM runtime (MIT license)

Weenie database sourced from the ACE-World core dataset.

---

*ACEForge is a fan-made tool for private server administration. Asheron's Call is a trademark of Warner Bros. Entertainment.*
