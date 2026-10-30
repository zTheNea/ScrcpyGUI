"""Manages scrcpy download, detection and updates from GitHub."""
from __future__ import annotations

import json
import logging
import os

import re
import shutil
import ssl
import subprocess
import threading
import time
import urllib.request
import zipfile
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

from paths import APP_DIR, SCRCPY_DIR, VERSION_FILE, IS_WINDOWS, ensure_app_dir
from engine.adb import get_adb_gateway

GITHUB_API = "https://api.github.com/repos/Genymobile/scrcpy/releases/latest"


_last_unauthorized_count: int = 0
"""Number of unauthorized devices detected in the last :func:`list_devices` call."""

def _subprocess_kwargs() -> dict[str, Any]:
    """Return common subprocess kwargs (hides console window on Windows)."""
    kw: dict[str, Any] = {}
    if IS_WINDOWS:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kw

def get_scrcpy_path() -> Optional[str]:
    """Find scrcpy: app dir > PATH > None."""
    # Check local folder first (mainly Windows)
    local_name = "scrcpy.exe" if IS_WINDOWS else "scrcpy"
    local = os.path.join(SCRCPY_DIR, local_name)
    if os.path.isfile(local):
        return local
    
    # Check PATH
    found = shutil.which("scrcpy")
    if found:
        return found
    return None

def get_installed_version():
    if os.path.isfile(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r") as f:
                return json.load(f).get("version", "")
        except Exception:
            pass
    return ""

def _save_version(ver, url):
    ensure_app_dir()
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": ver, "url": url}, f)

def get_ssl_context():
    """Create a verified SSL context.

    Returns ``None`` on failure — urllib will then use Python's own default
    context which still validates certificates.  We intentionally do NOT
    fall back to ``ssl._create_unverified_context`` to avoid silent MITM
    exposure when downloading binaries.
    """
    try:
        return ssl.create_default_context()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            "Could not create verified SSL context: %s", e,
        )
        return None

def check_latest(callback: Callable[[str, str, Optional[str]], None]) -> None:
    """Check GitHub for the latest scrcpy release asynchronously.

    Calls ``callback(tag, download_url, error)`` upon completion.
    """
    def run():
        try:
            req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "ScrcpyGUI"})
            with urllib.request.urlopen(req, timeout=10, context=get_ssl_context()) as r:
                data = json.loads(r.read().decode())
            tag = data.get("tag_name", "")
            url = ""
            
            # Scrcpy only provides official binaries for Windows
            if IS_WINDOWS:
                for a in data.get("assets", []):
                    name = a.get("name", "")
                    if "win64" in name and name.endswith(".zip"):
                        url = a["browser_download_url"]
                        break
            
            callback(tag, url, None)
        except Exception as e:
            callback("", "", str(e))
    threading.Thread(target=run, daemon=True).start()

def download_and_install(
    url: str,
    progress_cb: Optional[Callable[[float], None]] = None,
    done_cb: Optional[Callable[[Optional[str]], None]] = None,
) -> None:
    """Download scrcpy zip from url and extract to SCRCPY_DIR. (Windows only)

    Parameters
    ----------
    url : str
        The direct asset download URL from GitHub Releases.
    progress_cb : Callable[[float], None], optional
        Called with a progress ratio (0.0 to 1.0) or -1 for indeterminate extraction.
    done_cb : Callable[[Optional[str]], None], optional
        Called with None on success, or an error string on failure.
    """
    if not IS_WINDOWS:
        if done_cb: done_cb("Auto-download is only supported on Windows. Please install scrcpy via your package manager.")
        return

    def run():
        try:
            ensure_app_dir()
            zip_path = os.path.join(APP_DIR, "scrcpy_download.zip")
            # Download
            req = urllib.request.Request(url, headers={"User-Agent": "ScrcpyGUI"})
            with urllib.request.urlopen(req, timeout=120, context=get_ssl_context()) as r:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total > 0:
                            progress_cb(downloaded / total)
            # Extract
            if progress_cb:
                progress_cb(-1)  # indeterminate = extracting

            # Stop adb first to release file locks on Windows binaries/DLLs
            try:
                adb_bin = _get_adb_path()
                if adb_bin and os.path.isfile(adb_bin):
                    subprocess.run([adb_bin, "kill-server"], **_subprocess_kwargs(), timeout=5)
            except Exception:
                pass

            temp_extract = os.path.join(APP_DIR, "_scrcpy_extract_temp")
            if os.path.isdir(temp_extract):
                shutil.rmtree(temp_extract, ignore_errors=True)
            os.makedirs(temp_extract, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(temp_extract)
                members = z.namelist()
                root = members[0].split("/")[0] if "/" in members[0] else ""
                extracted_dir = os.path.join(temp_extract, root) if root and os.path.isdir(os.path.join(temp_extract, root)) else temp_extract

                os.makedirs(SCRCPY_DIR, exist_ok=True)
                for item in os.listdir(extracted_dir):
                    s = os.path.join(extracted_dir, item)
                    d = os.path.join(SCRCPY_DIR, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

            shutil.rmtree(temp_extract, ignore_errors=True)
            if os.path.isfile(zip_path):
                os.remove(zip_path)
            if done_cb:
                done_cb(None)
        except Exception as e:
            if done_cb:
                done_cb(str(e))
    threading.Thread(target=run, daemon=True).start()

def _get_adb_path():
    p = get_scrcpy_path()
    if not p: return shutil.which("adb")
    adb = os.path.join(os.path.dirname(p), "adb.exe" if IS_WINDOWS else "adb")
    if os.path.isfile(adb): return adb
    return shutil.which("adb")


def is_adb_available() -> bool:
    """Return True if ADB is reachable on this system."""
    return _get_adb_path() is not None


def get_unauthorized_count() -> int:
    """Return the number of unauthorized devices from the last :func:`list_devices` call."""
    return _last_unauthorized_count

def get_device_model(serial):
    """Get the real device model name via ADB getprop with caching."""
    return get_adb_gateway().get_device_model(serial)



def list_devices() -> list[tuple[str, str]]:
    """Returns a list of (serial, model) for all connected ADB devices.

    Also updates the module-level ``_last_unauthorized_count`` counter, which
    can be queried via :func:`get_unauthorized_count`.
    """
    global _last_unauthorized_count
    _last_unauthorized_count = 0
    try:
        adb = _get_adb_path() or "adb"
        output = subprocess.check_output(
            [adb, "devices", "-l"], text=True, stderr=subprocess.STDOUT,
            **_subprocess_kwargs()
        )
        lines = output.strip().split("\n")[1:]
        devices = []
        for line in lines:
            if not line.strip():
                continue
            if "unauthorized" in line:
                _last_unauthorized_count += 1
                continue
            if "offline" in line:
                continue
            parts = line.split()
            serial = parts[0]
            # Try to get real model name via getprop
            real_model = get_device_model(serial)
            if real_model:
                model = real_model
            else:
                # Fallback to the model: tag from adb devices -l
                model = "Unknown"
                for p in parts:
                    if p.startswith("model:"):
                        model = p.split(":")[1].replace("_", " ")
                        break
            devices.append((serial, model))
        return devices
    except Exception:
        return []

def connect_wifi(ip: str) -> str:
    """Connect to a device over TCP/IP (runs ``adb connect ip``)."""
    try:
        adb = _get_adb_path()
        if not adb: return "ADB no encontrado"
        r = subprocess.run(
            [adb, "connect", ip], capture_output=True, text=True, timeout=10,
            **_subprocess_kwargs()
        )
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return str(e)

def pair_wifi(ip_port: str, code: str) -> str:
    """Pair with an Android 11+ wireless debugging host (runs ``adb pair ip:port code``)."""
    try:
        adb = _get_adb_path()
        if not adb: return "ADB no encontrado"
        r = subprocess.run(
            [adb, "pair", ip_port, code], capture_output=True, text=True, timeout=15,
            **_subprocess_kwargs()
        )
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return str(e)

def _extract_ip(text):
    """Extracts the first non-loopback IPv4 from text using multiple patterns."""
    if not text: return None
    # 1. Prioritize 'src' (from ip route get)
    m = re.search(r'src\s+(\d{1,3}(?:\.\d{1,3}){3})', text)
    if m: return m.group(1)
    
    # 2. Try 'inet ' (from ip addr show)
    # Filter out common internal/virtual IPs
    for m in re.finditer(r'inet\s+(\d{1,3}(?:\.\d{1,3}){3})', text):
        ip = m.group(1)
        if ip not in ["127.0.0.1", "0.0.0.0"] and not ip.startswith("169.254"):
            return ip
        
    # 3. Try 'inet addr:' (from ifconfig)
    for m in re.finditer(r'inet addr:(\d{1,3}(?:\.\d{1,3}){3})', text):
        ip = m.group(1)
        if ip not in ["127.0.0.1", "0.0.0.0"]:
            return ip
            
    # 4. Try any raw IP match as last resort
    for m in re.finditer(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', text):
        ip = m.group(1)
        if ip not in ["127.0.0.1", "0.0.0.0"] and not ip.startswith("169.254"):
            return ip
    return None
def enable_tcpip(serial: str) -> str:
    """Enables TCP/IP on the device via USB, discovers its Wi-Fi IP and connects."""
    try:
        adb = _get_adb_path()
        if not adb: return "ADB no encontrado"
        if ":" in serial:
            return f"El dispositivo ya está conectado vía Wi-Fi ({serial})"
        kw = _subprocess_kwargs()
        
        # 1. Enable TCP/IP
        subprocess.run([adb, "-s", serial, "tcpip", "5555"], capture_output=True, text=True, timeout=10, **kw)
        
        # Wait for adbd to restart on the device
        time.sleep(1.5)
        
        # 2. Try multiple ways to get IP address
        ip = None
        
        # Method A: ip route get (finds the IP used for active network)
        r = subprocess.run([adb, "-s", serial, "shell", "ip", "route", "get", "1.1.1.1"], capture_output=True, text=True, timeout=5, **kw)
        ip = _extract_ip(r.stdout)
        
        if not ip:
            # Method B: getprop dhcp.wlan0.ipaddress
            r = subprocess.run([adb, "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress"], capture_output=True, text=True, timeout=5, **kw)
            val = r.stdout.strip()
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', val) and val != "0.0.0.0":
                ip = val
                
        if not ip:
            # Method C: ip addr show wlan0 (or variations)
            for iface in ["wlan0", "wlan1", "eth0", "p2p-wlan0-0", "ra0", "swlan0"]:
                r = subprocess.run([adb, "-s", serial, "shell", "ip", "addr", "show", iface], capture_output=True, text=True, timeout=5, **kw)
                ip = _extract_ip(r.stdout)
                if ip: break
            
        if not ip:
            # Method D: generic ip addr show
            r = subprocess.run([adb, "-s", serial, "shell", "ip", "addr", "show"], capture_output=True, text=True, timeout=5, **kw)
            ip = _extract_ip(r.stdout)

        if not ip:
            # Method E: dumpsys wifi or connectivity
            r = subprocess.run([adb, "-s", serial, "shell", "dumpsys", "connectivity"], capture_output=True, text=True, timeout=5, **kw)
            ip = _extract_ip(r.stdout)

        if ip:
            # 3. Connect to the discovered IP
            conn_res = subprocess.run([adb, "connect", f"{ip}:5555"], capture_output=True, text=True, timeout=10, **kw)
            out = (conn_res.stdout.strip() + " " + conn_res.stderr.strip()).lower()
            if "connected to" in out or "already connected" in out:
                return f"Conectado a {ip} vía Wi-Fi"
            return f"IP detectada ({ip}), pero falló la conexión: {conn_res.stdout.strip() or conn_res.stderr.strip()}"
        return "Modo TCP/IP activo, pero no pude obtener la IP automáticamente. Conéctate manualmente."
    except Exception as e:
        return f"Error: {str(e)}"

POPULAR_APP_NAMES: dict[str, str] = {
    # Browsers
    "com.brave.browser": "Brave Browser",
    "com.android.chrome": "Google Chrome",
    "org.mozilla.firefox": "Firefox",
    "com.microsoft.emmx": "Microsoft Edge",
    "com.opera.browser": "Opera",
    "com.opera.mini.native": "Opera Mini",
    "com.duckduckgo.mobile.android": "DuckDuckGo",
    "org.lineageos.jelly": "Navegador Jelly",
    # Messaging & Social
    "com.whatsapp": "WhatsApp",
    "com.whatsapp.w4b": "WhatsApp Business",
    "org.telegram.messenger": "Telegram",
    "org.thunderdog.challegram": "Telegram X",
    "com.discord": "Discord",
    "com.instagram.android": "Instagram",
    "com.facebook.katana": "Facebook",
    "com.facebook.orca": "Messenger",
    "com.facebook.lite": "Facebook Lite",
    "com.zhiliaoapp.musically": "TikTok",
    "com.twitter.android": "X (Twitter)",
    "com.snapchat.android": "Snapchat",
    "com.reddit.frontpage": "Reddit",
    "com.pinterest": "Pinterest",
    "com.linkedin.android": "LinkedIn",
    "com.slack": "Slack",
    "com.skype.raider": "Skype",
    "com.viber.voip": "Viber",
    # Multimedia & Streaming
    "com.google.android.youtube": "YouTube",
    "com.google.android.apps.youtube.music": "YouTube Music",
    "com.spotify.music": "Spotify",
    "com.netflix.mediaclient": "Netflix",
    "com.amazon.avod.thirdpartyclient": "Prime Video",
    "com.disney.disneyplus": "Disney+",
    "com.max.main": "Max",
    "tv.twitch.android.app": "Twitch",
    "org.videolan.vlc": "VLC",
    "com.crunchyroll.crunchyrollapp": "Crunchyroll",
    # Google Ecosystem
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.gm": "Gmail",
    "com.google.android.apps.photos": "Google Fotos",
    "com.google.android.apps.docs": "Google Drive",
    "com.google.android.keep": "Google Keep",
    "com.google.android.calendar": "Google Calendar",
    "com.google.android.deskclock": "Reloj (Google)",
    "com.google.android.calculator": "Calculadora (Google)",
    "com.google.android.googlequicksearchbox": "Google",
    "com.google.android.apps.translate": "Traductor de Google",
    # Productivity & Office
    "com.microsoft.office.word": "Microsoft Word",
    "com.microsoft.office.excel": "Microsoft Excel",
    "com.microsoft.office.powerpoint": "PowerPoint",
    "com.microsoft.office.officehubrow": "Microsoft 365 (Office)",
    "com.adobe.reader": "Adobe Acrobat Reader",
    "notion.id": "Notion",
    # System & Hardware Tools
    "com.android.vending": "Google Play Store",
    "com.android.settings": "Ajustes del Sistema",
    "com.android.camera": "Cámara",
    "com.android.camera2": "Cámara",
    "org.lineageos.aperture": "Cámara (Aperture)",
    "com.android.gallery3d": "Galería",
    "com.android.documentsui": "Archivos / Descargas",
    "com.android.calculator2": "Calculadora",
    "com.android.deskclock": "Reloj y Alarma",
    "com.android.dialer": "Teléfono",
    "com.android.contacts": "Contactos",
    "com.android.messaging": "Mensajes SMS",
    "com.android.fmradio": "Radio FM",
    "flar2.devcheck": "DevCheck Hardware",
    "io.chaldeaprjkt.gamespace": "Game Space",
    "org.lineageos.eleven": "Reproductor de Música",
    "org.lineageos.etar": "Calendario (Etar)",
    "org.lineageos.recorder": "Grabadora de Voz",
    "org.lineageos.audiofx": "AudioFX",
    "org.omnirom.logcat": "MatLog / Logcat",
    "com.google.ar.core": "Google Play Services for AR",
}


def _clean_app_name(pkg: str) -> str:
    if pkg in POPULAR_APP_NAMES:
        return POPULAR_APP_NAMES[pkg]
    parts = pkg.split(".")
    meaningful = [p for p in parts if p.lower() not in ("com", "org", "net", "io", "android", "app", "google", "apps", "mobile")]
    if meaningful:
        return " ".join(m.capitalize() for m in meaningful[-2:])
    return parts[-1].capitalize()


def get_installed_apps(device_id: str) -> list[tuple[str, str]]:
    """Scan and return installed launchable and user apps as (friendly_name, package_name) pairs."""
    clean_serial = device_id.split(" (")[0].strip() if device_id else ""
    if not clean_serial or "Sin dispositivos" in clean_serial or "Buscando" in clean_serial:
        return []
    apps = get_adb_gateway().list_installed_apps(clean_serial)
    return [(a.friendly_name, a.package) for a in apps]



def run_scrcpy_query(flag: str, device: Optional[str] = None) -> tuple[bool, str]:
    """Execute a query flag (e.g. --list-encoders, --list-cameras, --list-displays) and return output."""
    path = get_scrcpy_path()
    if not path:
        return False, "❌ scrcpy no encontrado."
    
    cmd = [path, flag]
    if device and "Buscando" not in device and "Sin dispositivos" not in device:
        serial = device.split(" (")[0].strip()
        if serial:
            cmd.extend(["-s", serial])
            
    try:
        kw = _subprocess_kwargs()
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=12,
            cwd=os.path.dirname(path),
            **kw
        )
        out = r.stdout.strip() or r.stderr.strip()
        return True, out or "Comando ejecutado sin salida."
    except Exception as e:
        return False, f"❌ Error al consultar {flag}: {e}"


def parse_encoders(raw_output: str) -> dict:
    """Parse output from scrcpy --list-encoders into structured video and audio codecs."""
    video_codecs = []
    audio_codecs = []
    video_encoders = []
    audio_encoders = []
    
    # Known scrcpy codecs
    known_v_codecs = ["h264", "h265", "av1", "vp9", "vp8"]
    known_a_codecs = ["opus", "aac", "flac", "raw"]
    
    for line in raw_output.splitlines():
        line_clean = line.strip()
        # Look for --video-codec=<codec>
        m_vc = re.search(r'--video-codec=([a-zA-Z0-9_]+)', line_clean)
        if m_vc:
            c = m_vc.group(1).lower()
            if c in known_v_codecs and c not in video_codecs:
                video_codecs.append(c)
                
        # Look for --audio-codec=<codec>
        m_ac = re.search(r'--audio-codec=([a-zA-Z0-9_]+)', line_clean)
        if m_ac:
            c = m_ac.group(1).lower()
            if c in known_a_codecs and c not in audio_codecs:
                audio_codecs.append(c)
                
        # Look for encoder names
        m_ve = re.search(r"--video-encoder=['\"]?([^'\"]+)['\"]?", line_clean)
        if m_ve:
            enc = m_ve.group(1)
            if enc not in video_encoders:
                video_encoders.append(enc)
                
        m_ae = re.search(r"--audio-encoder=['\"]?([^'\"]+)['\"]?", line_clean)
        if m_ae:
            enc = m_ae.group(1)
            if enc not in audio_encoders:
                audio_encoders.append(enc)

    # Fallbacks if parsing didn't find any specific codecs
    if not video_codecs:
        video_codecs = ["h264", "h265", "av1", "vp9", "vp8"]
    if not audio_codecs:
        audio_codecs = ["opus", "aac", "flac", "raw"]

    return {
        "video_codecs": video_codecs,
        "audio_codecs": audio_codecs,
        "video_encoders": video_encoders,
        "audio_encoders": audio_encoders,
    }


def parse_cameras(raw_output: str) -> list[tuple[str, str, str]]:
    """Parse output from scrcpy --list-cameras.
    
    Returns list of (camera_id, facing, display_label).
    """
    cameras = []
    # Lines like: --camera-id=0    (facing: back) or --camera-id=1 (facing: front)
    pattern = re.compile(r'--camera-id=([0-9]+)(?:.*?facing[:\s]+([a-zA-Z]+))?', re.IGNORECASE)
    
    for line in raw_output.splitlines():
        line_clean = line.strip()
        m = pattern.search(line_clean)
        if m:
            cid = m.group(1)
            facing = (m.group(2) or "").lower()
            if facing == "back":
                label = f"ID {cid} (Trasera principal)"
            elif facing == "front":
                label = f"ID {cid} (Frontal)"
            elif facing == "external":
                label = f"ID {cid} (Externa)"
            else:
                label = f"ID {cid}"
            
            if not any(c[0] == cid for c in cameras):
                cameras.append((cid, facing, label))
                
    if not cameras:
        cameras = [("0", "back", "ID 0 (Trasera)"), ("1", "front", "ID 1 (Frontal)")]
        
    return cameras


def parse_displays(raw_output: str) -> list[tuple[str, str]]:
    """Parse output from scrcpy --list-displays.
    
    Returns list of (display_id, display_label).
    """
    displays = []
    pattern = re.compile(r'--display-id=([0-9]+)(?:.*?([0-9]+x[0-9]+))?', re.IGNORECASE)
    
    for line in raw_output.splitlines():
        line_clean = line.strip()
        m = pattern.search(line_clean)
        if m:
            did = m.group(1)
            res = m.group(2) or ""
            label = f"ID {did} ({res})" if res else f"ID {did}"
            if did == "0":
                label += " - Pantalla Principal"
            if not any(d[0] == did for d in displays):
                displays.append((did, label))
                
    if not displays:
        displays = [("0", "ID 0 - Pantalla Principal")]
        
    return displays


def get_device_full_info(device_serial: str) -> dict:
    """Retrieve full hardware and OS properties for a device via ADB getprop."""
    adb = _get_adb_path()
    if not adb:
        return {"brand": "Android", "model": "Dispositivo", "android_version": "14", "sdk": 34}
        
    try:
        kw = _subprocess_kwargs()
        r = subprocess.run(
            [adb, "-s", device_serial, "shell", "getprop"],
            capture_output=True, text=True, timeout=5, **kw
        )
        out = r.stdout
        
        def _get_val(prop_name: str) -> str:
            m = re.search(rf'\[{re.escape(prop_name)}\]:\s*\[(.*?)\]', out)
            return m.group(1).strip() if m else ""
            
        model = _get_val("ro.product.model") or _get_val("ro.product.marketname") or "Android"
        brand = _get_val("ro.product.brand") or _get_val("ro.product.manufacturer") or ""
        android_ver = _get_val("ro.build.version.release") or "14"
        sdk_str = _get_val("ro.build.version.sdk")
        soc = _get_val("ro.soc.model") or _get_val("ro.board.platform") or ""
        
        try:
            sdk_int = int(sdk_str)
        except Exception:
            sdk_int = 34
            
        return {
            "model": model,
            "brand": brand.capitalize(),
            "android_version": android_ver,
            "sdk": sdk_int,
            "soc": soc,
        }
    except Exception:
        return {"brand": "Android", "model": "Dispositivo", "android_version": "14", "sdk": 34, "soc": ""}


def scan_device_capabilities(device_serial: str) -> dict:
    """Execute full hardware scan of encoders, cameras, displays, and OS support for a device."""
    clean_serial = device_serial.split(" (")[0].strip()
    
    # 1. Device Info via ADB
    hw_info = get_device_full_info(clean_serial)
    
    # 2. Encoders via scrcpy query
    _, enc_raw = run_scrcpy_query("--list-encoders", clean_serial)
    encoders_info = parse_encoders(enc_raw)
    
    # 3. Cameras via scrcpy query
    _, cam_raw = run_scrcpy_query("--list-cameras", clean_serial)
    cameras_list = parse_cameras(cam_raw)
    
    # 4. Displays via scrcpy query
    _, dsp_raw = run_scrcpy_query("--list-displays", clean_serial)
    displays_list = parse_displays(dsp_raw)
    
    sdk = hw_info.get("sdk", 34)
    
    return {
        "serial": clean_serial,
        "model": hw_info.get("model", "Dispositivo"),
        "brand": hw_info.get("brand", "Android"),
        "android_version": hw_info.get("android_version", "14"),
        "sdk": sdk,
        "soc": hw_info.get("soc", ""),
        "video_codecs": encoders_info["video_codecs"],
        "audio_codecs": encoders_info["audio_codecs"],
        "video_encoders": encoders_info["video_encoders"],
        "audio_encoders": encoders_info["audio_encoders"],
        "cameras": cameras_list,
        "displays": displays_list,
        "supports_audio": sdk >= 30, # Android 11+
        "supports_virtual_display": sdk >= 29, # Android 10+
        "supports_flex_display": sdk >= 34, # Android 14+
        "supports_uhid": sdk >= 24, # Android 7.0+
    }


def enable_desktop_freeform(device: Optional[str] = None) -> tuple[bool, str]:
    """Enable Android freeform windows and force desktop mode on external displays via ADB."""
    path = get_scrcpy_path()
    adb = "adb"
    if path:
        local_adb = os.path.join(os.path.dirname(path), "adb.exe" if IS_WINDOWS else "adb")
        if os.path.isfile(local_adb):
            adb = local_adb
        else:
            adb = shutil.which("adb") or "adb"
            
    serial = device.split(" (")[0].strip() if device and "Buscando" not in device and "Sin dispositivos" not in device else None
    base_cmd = [adb]
    if serial:
        base_cmd.extend(["-s", serial])
        
    try:
        kw = _subprocess_kwargs()
        subprocess.run(base_cmd + ["shell", "settings", "put", "global", "enable_freeform_support", "1"], timeout=6, **kw)
        subprocess.run(base_cmd + ["shell", "settings", "put", "global", "force_desktop_mode_on_external_displays", "1"], timeout=6, **kw)
        return True, "✅ Modo Escritorio y Ventanas Libres activados vía ADB en tu dispositivo."
    except Exception as e:
        return False, f"❌ Error al activar Modo Escritorio en Android: {e}"


