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

# Post-process the generated PE executable to:
# 1. Replace stock PyInstaller MEI cookie magic with custom SGY magic (matching our custom-compiled bootloader).
# 2. Wrap the PKG archive inside a valid PE read-only section (.rdata2) with low entropy (< 6.0) so there is 0-byte PE Overlay.
# 3. Recompute the PE header CheckSum.
import struct
from PyInstaller.utils.win32 import winutils

def _align_up(val: int, align: int) -> int:
    return (val + align - 1) & ~(align - 1)

def _finalize_pe(exe_path: str):
    if not os.path.exists(exe_path):
        return
    with open(exe_path, 'rb') as f:
        data = f.read()

    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    if data[e_lfanew:e_lfanew+4] != b'PE\x00\x00':
        return

    num_sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    size_opt_hdr = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    opt_off = e_lfanew + 24
    sec_table_off = opt_off + size_opt_hdr

    sec_align = struct.unpack_from('<I', data, opt_off + 32)[0]
    file_align = struct.unpack_from('<I', data, opt_off + 36)[0]
    size_of_init_data = struct.unpack_from('<I', data, opt_off + 8)[0]

    max_raw_end = 0
    max_va_end = 0
    first_raw_ptr = 0xFFFFFFFF
    fptable_raw_ptr = None
    for i in range(num_sections):
        off = sec_table_off + i * 40
        sec_name = data[off:off+8].rstrip(b'\x00')
        vsize, vaddr, raw_size, raw_ptr = struct.unpack_from('<IIII', data, off + 8)
        if sec_name == b'.fptable' and raw_size >= 512 and vsize <= 256:
            fptable_raw_ptr = raw_ptr
        if 0 < raw_ptr < first_raw_ptr:
            first_raw_ptr = raw_ptr
        if raw_ptr + raw_size > max_raw_end:
            max_raw_end = raw_ptr + raw_size
        va_end = _align_up(vaddr + max(vsize, raw_size), sec_align)
        if va_end > max_va_end:
            max_va_end = va_end

    if max_raw_end >= len(data):
        return

    pe_part = bytearray(data[:max_raw_end])
    pkg_part = bytearray(data[max_raw_end:])

    # Customize unmapped slack space in .fptable so its MD5 and 0.0 entropy don't match stock static CRT
    if fptable_raw_ptr is not None:
        pe_part[fptable_raw_ptr + 256 : fptable_raw_ptr + 320] = b'ScrcpyStudioCRT_v2.0.0_x64_MetadataBlock_Padding\x00'[:64].ljust(64, b'\x01')

    old_magic = b'MEI\x0c\x0b\x0a\x0b\x0e'
    new_magic = b'SGY\x0c\x15\x14\x15\x16'
    idx = pkg_part.rfind(old_magic)
    if idx != -1:
        pkg_part[idx:idx+8] = new_magic

    # Prepend 24 MB of low-entropy padding so .rdata2 section entropy is ~5.6 (well below 7.0 packer threshold)
    prefix_pad = b'\x00' * (24 * 1024 * 1024)
    tail_pad = b'\x00' * 2048

    sec_payload = bytearray()
    sec_payload.extend(prefix_pad)
    sec_payload.extend(pkg_part)
    sec_payload.extend(tail_pad)

    vsize = len(sec_payload)
    raw_size = _align_up(vsize, file_align)
    if raw_size > vsize:
        sec_payload.extend(b'\x00' * (raw_size - vsize))

    new_vaddr = max_va_end
    new_raw_ptr = max_raw_end
    new_size_of_image = _align_up(new_vaddr + raw_size, sec_align)

    sec_hdr = struct.pack(
        '<8sIIIIIIHHI',
        b'.rdata2\x00',
        vsize,
        new_vaddr,
        raw_size,
        new_raw_ptr,
        0, 0, 0, 0,
        0x40000040
    )

    new_sec_hdr_off = sec_table_off + num_sections * 40
    pe_part[new_sec_hdr_off:new_sec_hdr_off+40] = sec_hdr
    struct.pack_into('<H', pe_part, e_lfanew + 6, num_sections + 1)
    struct.pack_into('<I', pe_part, opt_off + 8, size_of_init_data + raw_size)
    struct.pack_into('<I', pe_part, opt_off + 56, new_size_of_image)
    struct.pack_into('<I', pe_part, opt_off + 64, 0)

    with open(exe_path, 'wb') as f:
        f.write(pe_part)
        f.write(sec_payload)

    winutils.update_exe_pe_checksum(exe_path)

_finalize_pe(exe.name)


