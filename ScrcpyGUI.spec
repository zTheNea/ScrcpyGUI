# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (ctk_path, 'customtkinter'),
        ('ui/assets', 'ui/assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'ui',
        'ui.app_window',
        'ui.home',
        'ui.devices',
        'ui.profiles',
        'ui.recordings',
        'ui.settings',
        'ui.services',
        'ui.widgets',
        'ui.theme',
        'ui.state',
        'ui.schema',
        'ui.dialogs',
        'ui.nav',
        'engine',
        'engine.adb',
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
        'scrcpy_gui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy',
        'psutil',
        'win32pdh',
        'win32api',
        'win32con',
        'pywintypes',
        'pythoncom',
        'charset_normalizer',
        '_wmi',
        'PySide6.QtNetwork',
        'PySide6.QtOpenGL',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtXml',
        'unittest',
        'pydoc',
        'pdb',
        'doctest',
        'sqlite3',
    ],
    noarchive=False,
    optimize=0,
)

# Strip unwanted system/JDK forwarder DLLs, WMI/process-inspection extensions, and unused Qt network/SW-GL binaries
_BLOCKED_PREFIXES = (
    'api-ms-win-',
    'ucrtbase.dll',
    '_wmi',
    'psutil',
    'win32pdh',
    'pywintypes',
    'numpy',
    'charset_normalizer',
    'pyee',
)
_BLOCKED_SUBSTRINGS = (
    'opengl32sw.dll',
    'qt6network.dll',
    'qopensslbackend.dll',
    'qschannelbackend.dll',
    'qcertonlybackend.dll',
    'qnetworklistmanager.dll',
    '__mypyc',
    'jdk-',
)

def _keep_binary(entry):
    dest_name = entry[0].replace('\\', '/').lower()
    src_path = (entry[1] or '').replace('\\', '/').lower()
    base = dest_name.split('/')[-1]
    if any(base.startswith(p) or dest_name.startswith(p) for p in _BLOCKED_PREFIXES):
        return False
    if any(s in dest_name or s in src_path for s in _BLOCKED_SUBSTRINGS):
        return False
    return True

a.binaries = [b for b in a.binaries if _keep_binary(b)]

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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui/assets/icon.ico',
)
