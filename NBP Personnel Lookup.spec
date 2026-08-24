# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.datastruct import Tree

project_root = Path(SPECPATH)

# Collect the UI exactly under _internal/ui in the onedir build.
datas = list(Tree(str(project_root / 'ui'), prefix='ui'))
if (project_root / 'data').exists():
    datas += list(Tree(str(project_root / 'data'), prefix='data'))

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'webview',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        'tkinter',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NBP Personnel Lookup',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NBP Personnel Lookup',
)
