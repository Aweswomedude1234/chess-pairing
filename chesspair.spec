# chesspair.spec
# PyInstaller build spec for ChessPair
# Usage: pyinstaller chesspair.spec

import sys
import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, BUNDLE, COLLECT

block_cipher = None

# Detect if icon files exist, use them if available
icon_ico = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None
icon_icns = 'assets/icon.icns' if os.path.exists('assets/icon.icns') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox',
                   'tkinter.filedialog', 'tkinter.simpledialog'],
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

# ── Windows EXE ──────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ChessPair',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_ico,
)

# ── macOS .app Bundle ────────────────────────────────────────────────────────
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ChessPair.app',
        icon=icon_icns,
        bundle_identifier='com.chesspair.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
        },
    )
