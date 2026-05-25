# ACEForge PyInstaller build spec
# Build: pyinstaller ACEForge.spec
#
# Requirements before building:
#   pip install pyinstaller customtkinter anthropic
#   Place all references/ files in aceforge/references/ directory

import os
from pathlib import Path

block_cipher = None

# Collect all reference files to bundle
refs_dir = Path('aceforge/references')
ref_datas = [
    (str(refs_dir / f), 'aceforge/references')
    for f in refs_dir.iterdir()
    if f.is_file()
] if refs_dir.exists() else []

# Bundle SKILL.md from skill root too
skill_md = Path('aceforge/SKILL.md')
if skill_md.exists():
    ref_datas.append((str(skill_md), 'aceforge'))

a = Analysis(
    ['aceforge/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # CustomTkinter assets (required for the UI framework)
        (
            os.path.join(
                __import__('customtkinter').__path__[0],
                'assets'
            ),
            'customtkinter/assets'
        ),
    ] + ref_datas,
    hiddenimports=[
        'customtkinter',
        'anthropic',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
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
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add path to .ico file here if you have one
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
