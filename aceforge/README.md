# ACEForge — ACEmulator Content Generator

A Windows desktop application for generating complete, import-ready ACEmulator SQL content.
Two modes — Manual (no API key required) and AI (streaming Claude generation).

---

## Modes

### ✏ Manual Mode — No API key required

A full tabbed weenie editor. Pick a content type from the toolbar, it pre-fills
sane defaults, and every field is editable. Multiple weenies can be built together
in one session (creature + generator + drop item). SQL is previewed live as you edit.

**14 property tabs per weenie:**
- Identity (WCID, class_name, weenie type)
- Int / Bool / Float / String / DID Properties (all with add/delete rows, enum dropdowns)
- Attributes & Vitals (Strength, Endurance, MaxHealth, etc.)
- Skills (with SAC dropdown — Untrained/Trained/Specialized)
- Body Parts (all 27 columns per row, full hit-location support)
- Spell Book (spell ID + probability with the probability formula shown inline)
- Emotes (full emote + action chain editor — category, quest filter, WCID filter, all action fields)
- Create List (destination type, WCID, shade, try-to-bond)
- Generator (spawn WCID, delay, when/where, angles)
- Event Filter (with warning: never add event 414 to creatures)

**Session features:**
- Add/remove weenies, reorder with drag
- Save session as JSON to reopen later
- Save All SQL → writes each weenie as its own `.sql` file in a timestamped subfolder

### ✨ AI Mode — Requires Anthropic API key

Prompt-based generation. Describe what you want in natural language, and Claude
generates complete, import-ready SQL streamed live into the output panel.
Save Files splits the output into individual `.sql` files automatically.

---

## Requirements

- **Windows 10/11**
- **Python 3.10+** (for running from source)
- **Anthropic API key** — only needed for AI Mode (`https://console.anthropic.com`)

---

## Quick Start (Running from Source)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy skill reference files into aceforge/references/
#    (from ace-content-generator.skill package)

# 3. Run
python aceforge/main.py
```

---

## Reference Files

Place these in `aceforge/references/` (from the `ace-content-generator.skill` package):

```
aceforge/references/
  enums.md             ← Property enumerations (used by all dropdowns)
  spells.md            ← Spell quick-reference
  all_spells.txt       ← Complete 6,266-entry spell library
  quests.md            ← Quest creation patterns
  lore.md              ← AC lore reference
  schema.md            ← Weenie properties schema
  did_values.md        ← 2,254 Setup/Motion/Sound/Combat DID entries
  icons.md             ← 1,811 icon DID entries
  armor.md             ← Complete armor library (889 pieces)
  clothing.md          ← Complete clothing library
  melee_weapons.md     ← Complete melee weapon library
  missile_weapons.md   ← Complete missile weapon library
  casters.md           ← Complete caster library

aceforge/SKILL.md      ← Main skill instructions (one level up from references/)
```

Manual Mode works without these files (all dropdowns are hardcoded from enums_data.py).
AI Mode requires them — they form the system prompt sent to Claude.

---

## Building a Standalone .exe

```bash
pip install pyinstaller
pyinstaller ACEForge.spec
# Output: dist/ACEForge/ACEForge.exe
# Distribute the entire dist/ACEForge/ folder
```

---

## Configuration

Settings saved to `%APPDATA%\ACEForge\config.json`.

Open **Settings** (top-right) to configure:
- **Anthropic API Key** — only for AI Mode
- **Model** — Sonnet 4 (default), Opus 4, Haiku 4.5
- **Server Name** — appears in generated SQL comments
- **Author** — optional, injected into prompts
- **Output Directory** — where SQL files are saved
- **WCID Ranges** — your server's ranges per content category
  (defaults are Shattered Dawn values — change for your own server)

---

## WCID Configuration for Other Servers

The default WCID ranges are set to Shattered Dawn values. For your own server:
1. Open Settings → scroll to WCID Ranges
2. Set Range Start and Next Available for each category
3. ACEForge injects these into every AI generation and uses them as defaults
   when adding new weenies in Manual Mode

---

## Output Structure

```
[Output Directory]/
  session_20250525_143022/       ← Manual mode (session export)
    800064 Dericost Tomb Sentinel.sql
    800065 Dericost Tomb SentinelGen.sql
    810059 Dericost Ossuary Fragment.sql
  monster_20250525_150000/       ← AI mode (per generation)
    800066 New Creature.sql
    800067 NewCreatureGen.sql
```

---

## License

MIT License. Free to use, modify, and distribute.
Reference files sourced from ACEmulator/ACE-World-16PY (GPL-3.0) and ACViewer (GPL-3.0).
