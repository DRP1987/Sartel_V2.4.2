"""PyInstaller hook for PCANBasic."""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
import os

# Collect PCANBasic DLL from system
binaries = []
datas = []

# Look for PCANBasic. dll in common locations
pcan_dll_paths = [
    r'C:\Windows\System32\PCANBasic.dll',
    r'C:\Windows\SysWOW64\PCANBasic.dll',
]

for dll_path in pcan_dll_paths:
    if os.path.exists(dll_path):
        binaries.append((dll_path, '. '))
        print(f"Hook: Found PCANBasic.dll at {dll_path}")
        break

hiddenimports = ['ctypes', 'ctypes.wintypes']