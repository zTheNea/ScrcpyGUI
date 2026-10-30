# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['scrcpy_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[(ctk_path, 'customtkinter')],
    hiddenimports=[
        'customtkinter',
        'gui',
        'gui.widgets',
        'paths',
        'strings',
        'presets',
        'command_builder',
        'config_manager',
        'scrcpy_manager',
        'history_manager',
        'diagnostics',
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
    a.binaries,
    a.datas,
    [],
    name='ScrcpyGUI',
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
)
