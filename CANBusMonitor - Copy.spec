# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PCANBasic',
    'can',
    'can.interface',
    'can.interfaces',
    'can.interfaces.pcan',
    'can.interfaces.pcan.basic',
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'requests',
    'psutil',
    'uuid',
]

hiddenimports += collect_submodules('can.interfaces')
hiddenimports += collect_submodules('cryptography')

# ONLY include encrypted files (. enc)
datas = [
    ('config/configurations.json.enc', 'config'),
    ('config/release_notes.json', 'config'),
    ('config/docs/*.enc', 'config/docs'),
    ('assets/logo1.png', 'assets'),
    ('assets/icon.png', 'assets'),
    ('assets/icon.ico', 'assets'),
]

datas += collect_data_files('can')

binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a. pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='CANBusMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False in production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CANBusMonitor',
)