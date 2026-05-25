# ACEForge PyInstaller build spec
# Build: pyinstaller ACEForge.spec --noconfirm --clean

import os
from pathlib import Path

block_cipher = None

# ── Collect reference files ───────────────────────────────────────────────────
# Each entry is (source_path, destination_folder_inside_bundle)
# source_path must be the actual file path on disk
# destination is where it lands relative to the bundle root
refs_dir = Path('aceforge/references')
ref_datas = []

if refs_dir.exists():
    for f in refs_dir.iterdir():
        if f.is_file():
            # f is e.g. Path('aceforge/references/enums.md')
            # destination 'aceforge/references' puts it at
            # _internal/aceforge/references/enums.md inside the bundle
            ref_datas.append((str(f), 'aceforge/references'))

# Bundle SKILL.md one level up from references/
skill_md = Path('aceforge/SKILL.md')
if skill_md.exists():
    ref_datas.append((str(skill_md), 'aceforge'))

# ── CustomTkinter assets ──────────────────────────────────────────────────────
import customtkinter
ctk_assets = os.path.join(os.path.dirname(customtkinter.__file__), 'assets')

a = Analysis(
    ['aceforge/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (ctk_assets, 'customtkinter/assets'),
    ] + ref_datas,
    hiddenimports=[
        'customtkinter',
        'anthropic',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ACEForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ACEForge',
)
