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
    'packaging',
    'packaging.version',
]

hiddenimports += collect_submodules('can.interfaces')
hiddenimports += collect_submodules('cryptography')

# Include ONLY non-encrypted files
datas = [
    # Config files (NO .enc extensions)
    ('config/configurations.json', 'config'),
    ('config/release_notes.json', 'config'),
    
    # PDF documentation (NO .enc files)
    ('config/docs/*.pdf', 'config/docs'),
    
    # Assets
    ('assets/logo1.png', 'assets'),
    ('assets/icon.png', 'assets'),
    ('assets/icon.ico', 'assets'),
]

# Collect python-can data files
datas += collect_data_files('can')

# Include PCANBasic.dll from project root
binaries = []
if os.path.exists('PCANBasic.dll'):
    binaries.append(('PCANBasic.dll', '.'))
    print("✓ Including PCANBasic.dll from project root")
else:
    print("⚠ WARNING: PCANBasic.dll not found in project root!")

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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='CANBusMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
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