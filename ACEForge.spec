# ACEForge PyInstaller build spec — one-file mode
import os, sys
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

# ── Web UI — index.html must land at aceforge/web/index.html in the bundle ───
web_dir = Path('aceforge/web')
web_datas = []
if web_dir.exists():
    for f in web_dir.iterdir():
        if f.is_file():
            web_datas.append((str(f), 'aceforge/web'))

print(f"[spec] Bundling {len(web_datas)} web file(s): {[d[0] for d in web_datas]}")
print(f"[spec] Bundling {len(ref_datas)} reference file(s)")

a = Analysis(
    ['aceforge/main.py'],
    pathex=['.'],
    binaries=[],
    datas=ref_datas + web_datas,
    hiddenimports=[
        'anthropic',
        'openai',
        'google.generativeai',
        'google.ai.generativelanguage_v1beta',
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        'pythonnet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['customtkinter', 'tkinter', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
