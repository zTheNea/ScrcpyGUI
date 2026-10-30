"""Unified ADB Gateway and communication service for Scrcpy Studio.

Consolidates all ADB subprocess execution, device discovery, hardware caching,
telemetry gathering (battery, latency, screen metrics) and app scanning.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Optional

from paths import IS_WINDOWS, SCRCPY_DIR

logger = logging.getLogger(__name__)


# ── DTOs (Data Transfer Objects) ────────────────────────────────────
@dataclass
class DeviceRecord:
    serial: str
    model: str
    state: str = "device"
    brand: str = ""
    is_wifi: bool = False

    @property
    def is_online(self) -> bool:
        return self.state == "device"

    @property
    def is_wireless(self) -> bool:
        return self.is_wifi or ":" in self.serial

    @property
    def display_name(self) -> str:
        if self.state != "device":
            return f"{self.serial} ({self.state})"
        if self.brand and self.model:
            if self.model.lower().startswith(self.brand.lower()):
                return f"{self.serial} ({self.model})"
            return f"{self.serial} ({self.brand} {self.model})"
        return f"{self.serial} ({self.model})" if self.model else self.serial


@dataclass
class BatteryStatus:
    level: Optional[int] = None
    charging: bool = False
    power_source: str = "none"  # "ac" | "usb" | "wireless" | "none"
    temperature: Optional[float] = None
    health: str = ""

    @property
    def summary(self) -> str:
        if self.level is None:
            return "Batería no disponible"
        charge_str = " (Cargando)" if self.charging else ""
        temp_str = f" - {self.temperature:.1f}°C" if self.temperature is not None else ""
        return f"{self.level}%{charge_str}{temp_str}"


@dataclass
class DisplayMetrics:
    resolution: str = ""
    refresh_rate: str = ""
    density: Optional[int] = None

    @property
    def width(self) -> Optional[int]:
        if "x" in self.resolution:
            try:
                return int(self.resolution.split("x")[0])
            except ValueError:
                pass
        return None

    @property
    def height(self) -> Optional[int]:
        if "x" in self.resolution:
            try:
                return int(self.resolution.split("x")[1])
            except ValueError:
                pass
        return None

    @property
    def summary(self) -> str:
        parts = []
        if self.resolution:
            parts.append(self.resolution)
        if self.refresh_rate:
            parts.append(f"{self.refresh_rate}Hz")
        if self.density:
            parts.append(f"{self.density} DPI")
        return " @ ".join(parts) if parts else "Pantalla no detectada"


@dataclass
class InstalledApp:
    friendly_name: str
    package: str


# Common friendly names dictionary for instant offline resolution
COMMON_APPS: dict[str, str] = {
    "com.brave.browser": "Brave Browser",
    "com.android.chrome": "Google Chrome",
    "org.mozilla.firefox": "Firefox",
    "com.google.android.youtube": "YouTube",
    "com.whatsapp": "WhatsApp",
    "org.telegram.messenger": "Telegram",
    "com.instagram.android": "Instagram",
    "com.spotify.music": "Spotify",
    "com.netflix.mediaclient": "Netflix",
    "com.facebook.katana": "Facebook",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.gm": "Gmail",
    "com.google.android.apps.photos": "Google Fotos",
    "com.android.settings": "Ajustes del Sistema",
    "com.android.camera": "Cámara",
    "com.android.gallery3d": "Galería",
    "com.android.calculator2": "Calculadora",
    "flar2.devcheck": "DevCheck Hardware",
}


def clean_app_name(package: str) -> str:
    """Translate package name into human-readable app label."""
    if not package:
        return ""
    if package in COMMON_APPS:
        return COMMON_APPS[package]
    parts = package.split(".")
    base = parts[-1].capitalize() if parts else package
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)
    base = base.replace("_", " ").replace("-", " ")
    return base.strip()


class ADBGateway:
    """Thread-safe, caching gateway for all ADB device interactions."""

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._apps_cache: dict[str, list[InstalledApp]] = {}
        self._last_unauthorized_count: int = 0

    def clear_cache(self, serial: Optional[str] = None) -> None:
        """Clear hardware properties and apps cache."""
        if serial:
            clean = serial.split(" (")[0].strip()
            self._cache.pop(clean, None)
            self._cache.pop(serial, None)
            for k in list(self._apps_cache.keys()):
                if k.startswith(clean) or k.startswith(serial):
                    self._apps_cache.pop(k, None)
        else:
            self._cache.clear()
            self._apps_cache.clear()

    @staticmethod
    def get_subprocess_kwargs() -> dict[str, Any]:
        """Return subprocess kwargs (hiding console window on Windows)."""
        kw: dict[str, Any] = {}
        if IS_WINDOWS:
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        return kw

    @classmethod
    def get_adb_path(cls) -> Optional[str]:
        """Resolve path to adb binary: local scrcpy folder > PATH > None."""
        local_name = "adb.exe" if IS_WINDOWS else "adb"
        local = os.path.join(SCRCPY_DIR, local_name)
        if os.path.isfile(local):
            return local
        return shutil.which("adb")

    def is_available(self) -> bool:
        """Return True if ADB binary is found on system."""
        return self.get_adb_path() is not None

    def get_unauthorized_count(self) -> int:
        return self._last_unauthorized_count

    def run_cmd(self, args: list[str], timeout: int = 8) -> subprocess.CompletedProcess[str]:
        """Execute an adb command safely with standard timeouts and hidden window."""
        adb = self.get_adb_path() or "adb"
        full_cmd = [adb] + args
        return subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            **self.get_subprocess_kwargs()
        )

    # ── Device discovery & hardware properties ──────────────────────
    def get_device_properties(self, serial: str) -> dict[str, Any]:
        """Fetch and cache static hardware props (brand, model, sdk, android_version)."""
        if serial in self._cache:
            return self._cache[serial]

        info: dict[str, Any] = {"brand": "", "model": "", "sdk": 0, "android_version": ""}
        try:
            res = self.run_cmd(["-s", serial, "shell", "getprop"], timeout=4)
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.splitlines():
                    if "[ro.product.brand]" in line:
                        m = re.search(r"\[ro\.product\.brand\]:\s*\[(.*?)\]", line)
                        if m:
                            info["brand"] = m.group(1).capitalize()
                    elif "[ro.product.model]" in line:
                        m = re.search(r"\[ro\.product\.model\]:\s*\[(.*?)\]", line)
                        if m:
                            info["model"] = m.group(1)
                    elif "[ro.build.version.release]" in line:
                        m = re.search(r"\[ro\.build\.version\.release\]:\s*\[(.*?)\]", line)
                        if m:
                            info["android_version"] = m.group(1)
                    elif "[ro.build.version.sdk]" in line:
                        m = re.search(r"\[ro\.build\.version\.sdk\]:\s*\[(.*?)\]", line)
                        if m:
                            try:
                                info["sdk"] = int(m.group(1))
                            except ValueError:
                                pass
        except Exception as e:
            logger.debug("Error reading properties for %s: %s", serial, e)

        if info["model"] or info["brand"]:
            self._cache[serial] = info
        return info

    def get_device_model(self, serial: str) -> str:
        """Return friendly model name with hardware cache."""
        info = self.get_device_properties(serial)
        brand = info.get("brand", "")
        model = info.get("model", "")
        if brand and model:
            if model.lower().startswith(brand.lower()):
                return model
            return f"{brand} {model}"
        return model or "Dispositivo Android"

    def list_devices(self) -> list[DeviceRecord]:
        """List all connected ADB devices with model name and connection type."""
        self._last_unauthorized_count = 0
        devices: list[DeviceRecord] = []
        try:
            res = self.run_cmd(["devices", "-l"], timeout=5)
            if res.returncode != 0 or not res.stdout:
                return []

            lines = res.stdout.strip().splitlines()[1:]
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if "unauthorized" in line_str:
                    self._last_unauthorized_count += 1
                    continue
                if "offline" in line_str:
                    continue

                parts = line_str.split()
                serial = parts[0]
                is_wifi = bool(re.search(r":\d{4,5}\b", serial)) or ("." in serial and ":" in serial)

                # Get properties (cached)
                info = self.get_device_properties(serial)
                model = self.get_device_model(serial)

                # Fallback to model: tag from adb devices -l if empty
                if not model or model == "Dispositivo Android":
                    for p in parts:
                        if p.startswith("model:"):
                            model = p.split(":", 1)[1].replace("_", " ")
                            break

                devices.append(DeviceRecord(
                    serial=serial,
                    model=model,
                    state="device",
                    brand=info.get("brand", ""),
                    is_wifi=is_wifi,
                ))
        except Exception as e:
            logger.error("Error listing ADB devices: %s", e)

        return devices

    devices = list_devices

    # ── Wi-Fi & Pairing ─────────────────────────────────────────────
    def connect_wifi(self, ip_port: str) -> tuple[bool, str]:
        """Connect to Android over TCP/IP (`adb connect ip:port`)."""
        try:
            res = self.run_cmd(["connect", ip_port], timeout=10)
            out = res.stdout.strip() or res.stderr.strip()
            ok = "connected" in out.lower() and "unable" not in out.lower()
            return ok, out
        except Exception as e:
            return False, str(e)

    def pair_wifi(self, ip_port: str, code: str) -> tuple[bool, str]:
        """Pair with Android 11+ wireless host (`adb pair ip:port code`)."""
        try:
            res = self.run_cmd(["pair", ip_port, code], timeout=15)
            out = res.stdout.strip() or res.stderr.strip()
            ok = "successfully paired" in out.lower()
            return ok, out
        except Exception as e:
            return False, str(e)

    def enable_tcpip(self, serial: str, port: int = 5555) -> tuple[bool, str]:
        """Restart adb in TCP/IP mode on target port (`adb -s serial tcpip 5555`)."""
        try:
            res = self.run_cmd(["-s", serial, "tcpip", str(port)], timeout=6)
            out = res.stdout.strip() or res.stderr.strip()
            ok = res.returncode == 0
            return ok, out
        except Exception as e:
            return False, str(e)

    def get_device_ip(self, serial: str) -> Optional[str]:
        """Auto-detect wireless IPv4 of a USB-connected device."""
        # Clean serial
        clean_serial = serial.split(" (")[0].strip()
        methods = [
            ["-s", clean_serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
            ["-s", clean_serial, "shell", "ip", "addr", "show", "wlan0"],
            ["-s", clean_serial, "shell", "ifconfig", "wlan0"],
            ["-s", clean_serial, "shell", "ip", "route"],
        ]
        for cmd in methods:
            try:
                res = self.run_cmd(cmd, timeout=3)
                if res.returncode == 0 and res.stdout:
                    # Match IPv4 addresses excluding 127.0.0.1
                    ips = re.findall(r"\b(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b", res.stdout)
                    if ips:
                        return ips[0]
            except Exception:
                pass
        return None

    # ── Telemetry & Metrics ─────────────────────────────────────────
    def get_battery_status(self, serial: str) -> BatteryStatus:
        """Fetch battery level %, charging status, power source, temp, and health."""
        try:
            res = self.run_cmd(["-s", serial, "shell", "dumpsys", "battery"], timeout=4)
            out = res.stdout
            m_level = re.search(r"level:\s*(\d+)", out)
            level = int(m_level.group(1)) if m_level else None

            m_status = re.search(r"status:\s*(\d+)", out)
            status = int(m_status.group(1)) if m_status else 1
            charging = (status in (2, 5))

            power = "none"
            if "AC powered: true" in out:
                power = "ac"
            elif "USB powered: true" in out:
                power = "usb"
            elif "Wireless powered: true" in out:
                power = "wireless"

            m_temp = re.search(r"temperature:\s*(\d+)", out)
            temp = (int(m_temp.group(1)) / 10.0) if m_temp else None

            health_map = {1: "Unknown", 2: "Good", 3: "Overheat", 4: "Dead", 5: "Over Voltage", 6: "Unspecified Failure", 7: "Cold"}
            m_health = re.search(r"health:\s*(\d+)", out)
            health = health_map.get(int(m_health.group(1)), "Unknown") if m_health else ""

            return BatteryStatus(level=level, charging=charging, power_source=power, temperature=temp, health=health)
        except Exception:
            return BatteryStatus()

    def get_battery(self, serial: str) -> BatteryStatus:
        """Convenience alias for get_battery_status."""
        return self.get_battery_status(serial)

    def measure_latency(self, serial: str) -> Optional[float]:
        """Measure roundtrip round-ping latency to the Android device in ms."""
        try:
            t0 = time.perf_counter()
            res = self.run_cmd(["-s", serial, "shell", "echo", "1"], timeout=2)
            if res.returncode == 0:
                return round((time.perf_counter() - t0) * 1000, 1)
        except Exception:
            pass
        return None

    def get_screen_metrics(self, serial: str) -> DisplayMetrics:
        """Retrieve physical display resolution, refresh rate and density."""
        metrics = DisplayMetrics()
        try:
            out_wm = self.run_cmd(["-s", serial, "shell", "wm", "size"], timeout=3).stdout
            m_res = re.search(r"Physical size:\s*(\d+x\d+)", out_wm)
            if m_res:
                metrics.resolution = m_res.group(1)

            out_den = self.run_cmd(["-s", serial, "shell", "wm", "density"], timeout=3).stdout
            m_den = re.search(r"Physical density:\s*(\d+)", out_den) or re.search(r"density:\s*(\d+)", out_den)
            if m_den:
                try:
                    metrics.density = int(m_den.group(1))
                except ValueError:
                    pass

            out_dsp = self.run_cmd(["-s", serial, "shell", "dumpsys", "display"], timeout=3).stdout
            m_fps = re.search(r"fps[:=\s]*(\d+)", out_dsp)
            if m_fps:
                metrics.refresh_rate = m_fps.group(1)
        except Exception:
            pass
        return metrics

    def capture_quick_preview(self, serial: str) -> Optional[bytes]:
        """Capture raw PNG screenshot bytes from device via exec-out screencap."""
        adb = self.get_adb_path() or "adb"
        try:
            res = subprocess.run(
                [adb, "-s", serial, "exec-out", "screencap", "-p"],
                capture_output=True,
                timeout=5,
                **self.get_subprocess_kwargs()
            )
            if res.returncode == 0 and len(res.stdout) > 100:
                return res.stdout
        except Exception:
            pass
        return None

    # ── Installed Applications ──────────────────────────────────────
    def list_installed_apps(self, serial: str, third_party_only: bool = True, force_refresh: bool = False) -> list[InstalledApp]:
        """List third-party and launchable packages with friendly names, cached per device."""
        clean_serial = serial.split(" (")[0].strip()
        cache_key = f"{clean_serial}:{third_party_only}"
        if not force_refresh and cache_key in self._apps_cache:
            return list(self._apps_cache[cache_key])

        discovered: set[str] = set()
        cmd = ["-s", clean_serial, "shell", "pm", "list", "packages"]
        if third_party_only:
            cmd.append("-3")
        res = self.run_cmd(cmd, timeout=4)
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                pkg = line.replace("package:", "").strip()
                if pkg and "." in pkg:
                    discovered.add(pkg)

        # Strategy 2: launcher apps if strategy 1 yielded very few
        if len(discovered) < 2 and third_party_only:
            res = self.run_cmd(
                ["-s", clean_serial, "shell", "cmd", "package", "query-intent-activities",
                 "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER"],
                timeout=4
            )
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.splitlines():
                    if "packageName=" in line:
                        pkg = line.split("packageName=")[-1].split()[0].strip()
                        if pkg and "." in pkg:
                            discovered.add(pkg)

        apps: list[InstalledApp] = []
        for pkg in discovered:
            apps.append(InstalledApp(friendly_name=clean_app_name(pkg), package=pkg))

        sorted_apps = sorted(apps, key=lambda a: a.friendly_name.lower())
        self._apps_cache[cache_key] = sorted_apps
        return sorted_apps

    def get_installed_apps(self, serial: str, third_party_only: bool = True, force_refresh: bool = False) -> list[InstalledApp]:
        """Convenience alias for list_installed_apps."""
        return self.list_installed_apps(serial, third_party_only=third_party_only, force_refresh=force_refresh)

        # Strategy 1: third-party (-3)
        res = self.run_cmd(["-s", clean_serial, "shell", "pm", "list", "packages", "-3"], timeout=4)
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                pkg = line.replace("package:", "").strip()
                if pkg and "." in pkg:
                    discovered.add(pkg)

        # Strategy 2: launcher apps if strategy 1 yielded very few
        if len(discovered) < 2:
            res = self.run_cmd(
                ["-s", clean_serial, "shell", "cmd", "package", "query-intent-activities",
                 "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER"],
                timeout=4
            )
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.splitlines():
                    if "packageName=" in line:
                        pkg = line.split("packageName=")[-1].split()[0].strip()
                        if pkg and "." in pkg:
                            discovered.add(pkg)

        apps: list[InstalledApp] = []
        for pkg in discovered:
            apps.append(InstalledApp(friendly_name=clean_app_name(pkg), package=pkg))

        return sorted(apps, key=lambda a: a.friendly_name.lower())

    # ── Server management ───────────────────────────────────────────
    def restart_server(self) -> tuple[bool, str]:
        """Kill and restart ADB server."""
        try:
            self.run_cmd(["kill-server"], timeout=8)
            res = self.run_cmd(["start-server"], timeout=12)
            if res.returncode == 0:
                self._cache.clear()
                return True, "Servidor ADB reiniciado correctamente."
            return False, f"Fallo al iniciar servidor ADB (código {res.returncode}): {res.stderr.strip()}"
        except Exception as e:
            return False, f"Error durante el reinicio de ADB: {e}"


# Singleton gateway instance
_gateway_instance: Optional[ADBGateway] = None


def get_adb_gateway() -> ADBGateway:
    """Return the global ADBGateway singleton."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ADBGateway()
    return _gateway_instance
