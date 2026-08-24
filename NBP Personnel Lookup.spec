# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPECPATH)

# PyInstaller Analysis(datas=...) expects (source, destination_folder) pairs.
# Build those pairs explicitly so the packaged onedir app gets:
#   _internal/ui/...
#   _internal/data/...
def collect_folder(folder_name):
    root = project_root / folder_name
    if not root.exists():
        return []

    items = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        destination = path.parent.relative_to(project_root)
        items.append((str(path), str(destination)))
    return items


datas = collect_folder('ui') + collect_folder('data')

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
