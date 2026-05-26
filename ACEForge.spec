# ACEForge PyInstaller build spec
# One-file mode: everything packed into a single ACEForge.exe
# This avoids the python311.dll path issue on end-user machines.

import os
from pathlib import Path

block_cipher = None

# ── Reference files ───────────────────────────────────────────────────────────
refs_dir = Path('aceforge/references')
ref_datas = []
if refs_dir.exists():
    for f in refs_dir.iterdir():
        if f.is_file():
            ref_datas.append((str(f), 'aceforge/references'))

skill_md = Path('aceforge/SKILL.md')
if skill_md.exists():
    ref_datas.append((str(skill_md), 'aceforge'))

# ── CustomTkinter assets ──────────────────────────────────────────────────────
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)
ctk_assets = os.path.join(ctk_path, 'assets')

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
        '_tkinter',
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

# ── One-file EXE ──────────────────────────────────────────────────────────────
# exclude_binaries=False and no COLLECT = single self-contained .exe
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ACEForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
