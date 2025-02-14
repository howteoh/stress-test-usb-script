# -*- mode: python ; coding: utf-8 -*-
import os

# 獲取當前目錄
current_dir = os.path.dirname(os.path.abspath('__file__'))
icon_path = os.path.join(current_dir, 'logo.ico')

a = Analysis(
    ['usb_detector.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['win32api', 'win32file', 'wmi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'PIL', 'pandas', 'scipy', 
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'email', 'html', 'http', 'xml',
        'unittest', 'pydoc', 'doctest', 'argparse',
        'calendar', 'ftplib', 'hashlib', 'json'
    ],
    noarchive=False
)

pyz = PYZ(a.pure, optimize=2)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='USB_Detector',
    debug=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    optimize=2,
    uac_admin=False
)
