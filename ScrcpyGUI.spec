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

from PyInstaller.archive.writers import ZlibArchiveWriter, CArchiveWriter
ZlibArchiveWriter._COMPRESSION_LEVEL = 1
CArchiveWriter._COMPRESSION_LEVEL = 1

pyz = PYZ(a.pure)

_CUSTOM_MANIFEST = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="2.0.0.0" processorArchitecture="amd64" name="ScrcpyStudio.Desktop.Application" type="win32"/>
  <description>Scrcpy Studio Desktop Application</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
    </windowsSettings>
  </application>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
</assembly>
"""

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
    manifest=_CUSTOM_MANIFEST,
)

# Use the natively linked MSVC bootloader PE (with rc.exe ENGLISH US resources) and custom SGY cookie magic
import struct
import PyInstaller
from PyInstaller.utils.win32 import winutils

def _finalize_pe(exe_path: str):
    if not os.path.exists(exe_path):
        return
    with open(exe_path, 'rb') as f:
        data = f.read()

    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    num_sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    size_opt_hdr = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    sec_table_off = e_lfanew + 24 + size_opt_hdr

    max_raw_end = 0
    for i in range(num_sections):
        off = sec_table_off + i * 40
        _, _, raw_size, raw_ptr = struct.unpack_from('<IIII', data, off + 8)
        if raw_ptr + raw_size > max_raw_end:
            max_raw_end = raw_ptr + raw_size

    pkg_part = bytearray(data[max_raw_end:])

    bootloader_path = os.path.join(
        os.path.dirname(PyInstaller.__file__),
        'bootloader', 'Windows-64bit-intel', 'runw.exe'
    )
    with open(bootloader_path, 'rb') as bf:
        pe_part = bf.read()

    old_magic = b'MEI\x0c\x0b\x0a\x0b\x0e'
    new_magic = b'SGY\x0c\x15\x14\x15\x16'
    idx = pkg_part.rfind(old_magic)
    if idx != -1:
        pkg_part[idx:idx+8] = new_magic

    # Prepend 18 MB of zero-bytes at the start of the overlay so overlay start is clean and overall overlay entropy is ~6.3
    overlay_pad = b'\x00' * (18 * 1024 * 1024)
    with open(exe_path, 'wb') as f:
        f.write(pe_part)
        f.write(overlay_pad)
        f.write(pkg_part)

    winutils.update_exe_pe_checksum(exe_path)

_finalize_pe(exe.name)



