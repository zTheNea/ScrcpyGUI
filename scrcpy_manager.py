"""Manages scrcpy download, detection and updates from GitHub."""
import os, json, shutil, zipfile, urllib.request, threading, platform, ssl

GITHUB_API = "https://api.github.com/repos/Genymobile/scrcpy/releases/latest"

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ScrcpyGUI")
else:
    # Linux/MacOS standard path for user data
    APP_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "ScrcpyGUI")

SCRCPY_DIR = os.path.join(APP_DIR, "scrcpy")
VERSION_FILE = os.path.join(APP_DIR, "version.json")

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
    """Create a context that ignores certificate verification errors if needed."""
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

def list_devices():
    """Returns a list of (serial, model) for connected devices."""
    import subprocess
    try:
        # Run adb devices -l to get model names
        output = subprocess.check_output(["adb", "devices", "-l"], text=True, stderr=subprocess.STDOUT)
        lines = output.strip().split("\n")[1:]
        devices = []
        for line in lines:
            if not line.strip() or "offline" in line or "unauthorized" in line:
                continue
            parts = line.split()
            serial = parts[0]
            model = "Unknown"
            for p in parts:
                if p.startswith("model:"):
                    model = p.split(":")[1]
                    break
            devices.append((serial, model))
        return devices
    except Exception:
        return []
def _get_adb_path():
    p = get_scrcpy_path()
    if not p: return shutil.which("adb")
    adb = os.path.join(os.path.dirname(p), "adb.exe" if IS_WINDOWS else "adb")
    if os.path.isfile(adb): return adb
    return shutil.which("adb")

def get_installed_apps(serial):
    """Returns a list of (label, package) for user-installed apps."""
    import subprocess
    try:
        adb = _get_adb_path()
        if not adb: return []
        # Complex shell script to get labels and packages in one go
        cmd_script = 'for p in $(pm list packages -3 | cut -f 2 -d ":"); do label=$(dumpsys package $p | grep -m 1 "label=" | cut -f 2 -d "="); if [ -z "$label" ]; then label=$p; fi; echo "$label|$p"; done'
        r = subprocess.run([adb, "-s", serial, "shell", cmd_script], capture_output=True, text=True, timeout=20)
        
        apps = []
        for line in r.stdout.splitlines():
            if "|" in line:
                label, pkg = line.split("|", 1)
                apps.append((label.strip(), pkg.strip()))
            elif line.strip():
                apps.append((line.strip(), line.strip()))
        
        return sorted(apps, key=lambda x: x[0].lower())
    except Exception:
        return []

def launch_app_on_display(serial, package, display_id):
    """Launches an app on a specific display ID."""
    import subprocess
    try:
        adb = _get_adb_path()
        if not adb: return False
        cmd = [adb, "-s", serial, "shell", "am", "start", "--display", str(display_id), package]
        # Fallback for older Androids or specific activities
        subprocess.run(cmd, capture_output=True)
        return True
    except Exception:
        return False
