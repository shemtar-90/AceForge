# ACEForge — Building the Installer

This document covers how to go from source code to a distributable
`ACEForge_1.0.0_Setup.exe` that anyone can double-click and install.

---

## What the installer does

When users run `ACEForge_1.0.0_Setup.exe` they get:
- A standard Windows installation wizard (Next / Next / Install / Finish)
- ACEForge installed to `C:\Program Files\ACEForge\`
- A Start Menu shortcut under `ACEForge\`
- A Desktop shortcut
- An entry in Add/Remove Programs (with uninstaller)
- Optional: shortcut to the output folder in Documents

No Python required. No command line. Just double-click.

---

## Prerequisites (developer machine only)

Users installing the finished product need nothing. You as the developer need:

| Tool | Where to get it | Why |
|------|----------------|-----|
| Python 3.10+ | https://python.org | Runs the build |
| NSIS 3.x | https://nsis.sourceforge.io/Download | Creates the installer |

When installing Python, check **"Add Python to PATH"**.
When installing NSIS, use the default options.

---

## Step 1 — Add reference files

Copy these from `ace-content-generator.skill` into `aceforge/references/`:

```
aceforge/references/
  enums.md
  spells.md
  all_spells.txt
  quests.md
  lore.md
  schema.md
  did_values.md
  icons.md
  armor.md
  clothing.md
  melee_weapons.md
  missile_weapons.md
  casters.md

aceforge/SKILL.md   ← place here (one level up from references/)
```

Manual Mode works without these.
AI Mode requires them — they form the knowledge base sent to Claude.

---

## Step 2 — Build the executable

Double-click `build.bat`.

It will:
1. Install `customtkinter`, `anthropic`, and `pyinstaller` via pip
2. Check that reference files are present
3. Run PyInstaller using `ACEForge.spec`
4. Output `dist\ACEForge\ACEForge.exe` and supporting files

This takes 2–5 minutes on the first run.

---

## Step 3 — (Optional) Add a custom icon

Create a 256×256 `.ico` file and place it at:
```
installer_assets\aceforge.ico
```

If this file doesn't exist, the installer build script automatically
patches the NSIS script to skip icon references.

---

## Step 4 — Build the installer

Double-click `installer_build.bat`.

It will:
1. Confirm `dist\ACEForge\ACEForge.exe` exists
2. Find your NSIS installation automatically
3. Compile `installer.nsi` into `ACEForge_1.0.0_Setup.exe`

The output is a single self-contained file ready to distribute.

---

## Alternative: Compile NSIS manually

If `installer_build.bat` doesn't find NSIS, you can compile manually:
1. Right-click `installer.nsi` in Windows Explorer
2. Select **"Compile NSIS Script"**

---

## Folder structure after a successful build

```
ACEForge/
  dist/
    ACEForge/               ← PyInstaller output (the raw .exe + support files)
      ACEForge.exe
      _internal/
        customtkinter/
        aceforge/
          references/       ← Reference files bundled inside the exe
          ...
  ACEForge_1.0.0_Setup.exe  ← Final installer — this is what you distribute
  build.bat
  installer.nsi
  installer_build.bat
  ...
```

---

## What gets preserved on uninstall

The uninstaller removes everything in `C:\Program Files\ACEForge\`.

It intentionally **does not** remove:
- `%APPDATA%\ACEForge\config.json` — user settings, API key, WCID ranges

This means settings survive a reinstall or upgrade.

---

## Updating the version number

When you release a new version, update these in one place:

1. `aceforge/__init__.py` — `__version__ = "1.0.0"`
2. `aceforge/app.py` — `APP_VERSION = "1.0.0"`
3. `installer.nsi` — `!define APPVERSION "1.0.0"`
4. `installer_build.bat` — the `ACEForge_1.0.0_Setup.exe` filename check

---

## Testing the installer

After building, test on a clean Windows machine (or VM) to confirm:

- [ ] Installer runs without errors
- [ ] ACEForge appears in Start Menu
- [ ] Desktop shortcut launches the app
- [ ] Manual mode works immediately (no API key)
- [ ] Settings persist after close and reopen
- [ ] AI mode prompts for API key gracefully
- [ ] Uninstaller removes the app cleanly from Add/Remove Programs
