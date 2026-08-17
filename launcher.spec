# -*- mode: python ; coding: utf-8 -*-
"""
launcher.spec — PyInstaller spec for the AI TestData Generator Launcher EXE.

Build with:
    pyinstaller launcher.spec --clean

Output: dist\Launcher.exe  (single-file, windowed — no console flash)
"""

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Data files to bundle inside the EXE
datas = [
    # Ship the entire launcher_ui folder so the HTTP server can serve index.html
    ('launcher_ui', 'launcher_ui'),
]

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # windowed=True hides the console window entirely
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Optional: add an icon here
    # icon='launcher_ui\\icon.ico',
)
