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

# ── App icon ──────────────────────────────────────────────────────────────────
icon_datas = []
icon_file = Path('AF_Icon.ico')
if icon_file.exists():
    icon_datas.append((str(icon_file), '.'))

print(f"[spec] Bundling {len(web_datas)} web file(s): {[d[0] for d in web_datas]}")
print(f"[spec] Bundling {len(ref_datas)} reference file(s)")

# Collect all submodules and data for packages that use dynamic imports
from PyInstaller.utils.hooks import collect_all, collect_submodules
openai_datas, openai_binaries, openai_hiddenimports = collect_all('openai')
anthropic_datas, anthropic_binaries, anthropic_hiddenimports = collect_all('anthropic')
httpx_datas, httpx_binaries, httpx_hiddenimports = collect_all('httpx')
httpcore_datas, httpcore_binaries, httpcore_hiddenimports = collect_all('httpcore')

a = Analysis(
    ['aceforge/main.py'],
    pathex=['.'],
    binaries=openai_binaries + anthropic_binaries + httpx_binaries + httpcore_binaries,
    datas=ref_datas + web_datas + icon_datas + openai_datas + anthropic_datas + httpx_datas + httpcore_datas,
    hiddenimports=[
        'anthropic',
        'openai',
        'openai.resources',
        'openai.resources.chat',
        'openai.resources.chat.completions',
        'openai._streaming',
        'openai._client',
        'google.generativeai',
        'google.ai.generativelanguage_v1beta',
        'httpx',
        'httpcore',
        'anyio',
        'anyio.streams',
        'anyio.streams.memory',
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        'pythonnet',
    ] + openai_hiddenimports + anthropic_hiddenimports + httpx_hiddenimports + httpcore_hiddenimports,
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
    icon='AF_Icon.ico' if Path('AF_Icon.ico').exists() else None,
)
