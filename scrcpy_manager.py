"""Manages scrcpy download, detection and updates from GitHub."""
import os, json, shutil, zipfile, urllib.request, threading, platform, ssl, subprocess, re, time

GITHUB_API = "https://api.github.com/repos/Genymobile/scrcpy/releases/latest"

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ScrcpyGUI")
else:
    # Linux/MacOS standard path for user data
    APP_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "ScrcpyGUI")

SCRCPY_DIR = os.path.join(APP_DIR, "scrcpy")
VERSION_FILE = os.path.join(APP_DIR, "version.json")

def _subprocess_kwargs():
    """Return common subprocess kwargs (hides console window on Windows)."""
    kw = {}
    if IS_WINDOWS:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kw

def get_scrcpy_path():
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
    os.makedirs(APP_DIR, exist_ok=True)
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": ver, "url": url}, f)

def get_ssl_context():
    """Create an SSL context. Uses verified certificates by default, with unverified fallback."""
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        try:
            return ssl._create_unverified_context()
        except AttributeError:
            return None

def check_latest(callback):
    """Check GitHub for latest release. Calls callback(tag, download_url, error)."""
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

def download_and_install(url, progress_cb=None, done_cb=None):
    """Download zip from url, extract to SCRCPY_DIR. (Windows only)"""
    if not IS_WINDOWS:
        if done_cb: done_cb("Auto-download is only supported on Windows. Please install scrcpy via your package manager.")
        return

    def run():
        try:
            os.makedirs(APP_DIR, exist_ok=True)
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
            if os.path.isdir(SCRCPY_DIR):
                shutil.rmtree(SCRCPY_DIR, ignore_errors=True)
            with zipfile.ZipFile(zip_path, "r") as z:
                members = z.namelist()
                # Find the root folder inside zip
                root = members[0].split("/")[0] if "/" in members[0] else ""
                z.extractall(APP_DIR)
                extracted = os.path.join(APP_DIR, root) if root else None
                if extracted and os.path.isdir(extracted) and extracted != SCRCPY_DIR:
                    os.rename(extracted, SCRCPY_DIR)
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

def get_device_model(serial):
    """Get the real device model name via ADB getprop (e.g. 'Samsung Galaxy S24')."""
    try:
        adb = _get_adb_path() or "adb"
        kw = _subprocess_kwargs()
        # Try manufacturer + model for a full name
        r_brand = subprocess.run(
            [adb, "-s", serial, "shell", "getprop", "ro.product.brand"],
            capture_output=True, text=True, timeout=3, **kw
        )
        r_model = subprocess.run(
            [adb, "-s", serial, "shell", "getprop", "ro.product.model"],
            capture_output=True, text=True, timeout=3, **kw
        )
        brand = r_brand.stdout.strip().capitalize()
        model = r_model.stdout.strip()
        if brand and model:
            # Avoid duplicating brand in model (e.g. "Samsung Samsung Galaxy...")
            if model.lower().startswith(brand.lower()):
                return model
            return f"{brand} {model}"
        if model:
            return model
    except Exception:
        pass
    return None


def list_devices():
    """Returns a list of (serial, model) for connected devices."""
    try:
        adb = _get_adb_path() or "adb"
        output = subprocess.check_output(
            [adb, "devices", "-l"], text=True, stderr=subprocess.STDOUT,
            **_subprocess_kwargs()
        )
        lines = output.strip().split("\n")[1:]
        devices = []
        for line in lines:
            if not line.strip() or "offline" in line or "unauthorized" in line:
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

def connect_wifi(ip):
    """Runs adb connect ip."""
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

def pair_wifi(ip_port, code):
    """Runs adb pair ip:port code."""
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

def enable_tcpip(serial):
    """Runs adb tcpip 5555, gets IP using multiple methods, and connects."""
    try:
        adb = _get_adb_path()
        if not adb: return "ADB no encontrado"
        kw = _subprocess_kwargs()
        
        # 1. Enable TCP/IP
        subprocess.run([adb, "-s", serial, "tcpip", "5555"], capture_output=True, text=True, timeout=10, **kw)
        
        # IMPORTANT: Wait for adbd to restart on the device. 
        # Without this, the next 'adb shell' command might fail or return empty.
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
            for iface in ["wlan0", "wlan1", "eth0", "p2p-wlan0-0", "ra0"]:
                r = subprocess.run([adb, "-s", serial, "shell", "ip", "addr", "show", iface], capture_output=True, text=True, timeout=5, **kw)
                ip = _extract_ip(r.stdout)
                if ip: break
            
        if not ip:
            # Method D: generic ip addr show (last resort)
            r = subprocess.run([adb, "-s", serial, "shell", "ip", "addr", "show"], capture_output=True, text=True, timeout=5, **kw)
            ip = _extract_ip(r.stdout)

        if ip:
            # 3. Connect
            subprocess.run([adb, "connect", f"{ip}:5555"], capture_output=True, text=True, timeout=10, **kw)
            return f"Conectado a {ip} vía Wi-Fi"
        return "Modo TCP/IP activo, pero no pude obtener la IP automáticamente. Conéctate manualmente."
    except Exception as e:
        return f"Error: {str(e)}"

def get_installed_apps(device_id):
    """Escáner Universal Triple: Máxima compatibilidad Android."""
    try:
        adb = _get_adb_path() or "adb"
        raw_output = ""
        kw = _subprocess_kwargs()
        
        # Intentar 3 métodos diferentes por orden de modernidad
        cmds = [
            [adb, "-s", device_id, "shell", "cmd", "package", "list", "packages", "-3"],
            [adb, "-s", device_id, "shell", "pm", "list", "packages"],
            [adb, "-s", device_id, "shell", "pm", "list", "packages", "-f"]
        ]
        
        for c in cmds:
            res = subprocess.run(c, capture_output=True, text=True, timeout=5, **kw)
            if res.stdout and len(res.stdout.strip()) > 10:
                raw_output = res.stdout
                break
        
        if not raw_output:
            # Último recurso: Dumpsys filtrado en Python (pipes no funcionan sin shell)
            res = subprocess.run(
                [adb, "-s", device_id, "shell", "dumpsys", "package"],
                capture_output=True, text=True, timeout=10, **kw
            )
            # Filtrar líneas que contengan "Package [" y extraer el nombre del paquete
            for line in res.stdout.splitlines():
                if "Package [" in line:
                    try:
                        pkg = line.split("[")[1].split("]")[0].strip()
                        if pkg and "." in pkg:
                            raw_output += f"package:{pkg}\n"
                    except (IndexError, ValueError):
                        pass

        packages = []
        for line in raw_output.splitlines():
            line = line.strip()
            if not line: continue
            
            # Limpiar prefijos comunes de ADB
            pkg = line.replace("package:", "")
            if "=" in pkg: pkg = pkg.split("=")[-1] # Caso con ruta de archivo
            pkg = pkg.strip()
            
            if pkg and "." in pkg:
                # Nombre amigable simple
                name = pkg.split(".")[-1].capitalize()
                if name.lower() in ["android", "app", "google"] and len(pkg.split(".")) > 1:
                    name = pkg.split(".")[-2].capitalize()
                packages.append((name, pkg))
        
        # Eliminar duplicados y ordenar
        unique_apps = list(set(packages))
        return sorted(unique_apps, key=lambda x: x[0])
    except Exception as e:
        print(f"Error en escaneo universal: {e}")
        return []
