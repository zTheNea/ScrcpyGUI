"""Background services for Scrcpy Studio: async runner, devices, sessions."""
from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, Signal

import history_manager as hist
import scrcpy_manager as mgr
from command_builder import build_scrcpy_args
from diagnostics import run_diagnostics


from concurrent.futures import ThreadPoolExecutor
from engine.adb import get_adb_gateway, clean_app_name, BatteryStatus, DisplayMetrics, InstalledApp


# ── Async worker pool helper ────────────────────────────────────────
class _Runner(QObject):
    _done = Signal(object, object)

    def __init__(self):
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="StudioWorker")
        self._done.connect(lambda cb, res: cb(res) if cb else None)

    def run(self, fn: Callable[[], Any], cb: Optional[Callable[[Any], None]] = None):
        def work():
            try:
                res = fn()
            except Exception as exc:  # surface errors to the UI thread
                res = exc
            self._done.emit(cb, res)
        self._executor.submit(work)


_runner: Optional[_Runner] = None


def run_async(fn: Callable[[], Any], cb: Optional[Callable[[Any], None]] = None) -> None:
    """Run *fn* in worker pool; deliver its result to *cb* on the UI thread."""
    global _runner
    if _runner is None:
        _runner = _Runner()
    _runner.run(fn, cb)



# ── Human-friendly error diagnosis ──────────────────────────────────
@dataclass
class Diagnosis:
    message: str
    fix: dict[str, Any] = field(default_factory=dict)   # state changes to apply
    fix_label: str = "Corregir y reintentar"
    action: str = ""   # optional: "download" | "refresh"


def diagnose_exit(lines: list[str]) -> Optional[Diagnosis]:
    """Translate scrcpy's output into an actionable diagnosis."""
    text = " ".join(lines).lower()
    needs_ctrl = {"stay_awake": False, "keep_active": False, "show_touches": False,
                  "screen_off": False}
    if "stay awake if control is disabled" in text:
        return Diagnosis("scrcpy no puede mantener el móvil despierto en modo Solo lectura.", needs_ctrl)
    if "show touches if control is disabled" in text:
        return Diagnosis("scrcpy no puede mostrar toques en modo Solo lectura.", needs_ctrl)
    if "keep device active if control is disabled" in text:
        return Diagnosis("scrcpy no puede mantener el móvil activo en modo Solo lectura.", needs_ctrl)
    if "scrcpy-server" in text and ("not exist" in text or "no such file" in text):
        return Diagnosis("Falta el archivo scrcpy-server. Reinstala scrcpy.",
                         fix_label="Reinstalar scrcpy", action="download")
    if "unauthorized" in text:
        return Diagnosis("Tu móvil no ha autorizado este PC. Desbloquéalo y acepta la depuración USB.",
                         fix_label="Reintentar", action="refresh")
    if "device offline" in text or "device not found" in text or "no devices" in text:
        return Diagnosis("No se detecta el dispositivo. Revisa el cable o la conexión Wi-Fi.",
                         fix_label="Buscar dispositivos", action="refresh")
    if "could not open video stream" in text or "mediacodec" in text or "encoder" in text and "failed" in text:
        return Diagnosis("El encoder del móvil no soporta esa resolución o códec. Probemos con H.264 a 1080p.",
                         {"codec": "h264", "max_size": "1920"})
    if "0 fps" in text or ("display turned off" in text and ("fps" in text or "tcpip" in text or "frames skipped" in text)):
        return Diagnosis("La transmisión Wi-Fi se congeló (0 FPS). Al apagar la pantalla, Android suspende la antena Wi-Fi.",
                         {"screen_off": False, "bitrate": 8, "fps": 60, "video_buffer": 30, "audio_buf": 80, "keyboard": "sdk", "mouse": "sdk"},
                         fix_label="Mantener pantalla y optimizar Wi-Fi")
    if "uhid" in text and ("fail" in text or "warn" in text or "not support" in text or "red" in text):
        return Diagnosis("El control por hardware UHID falló sobre Wi-Fi. Cambiemos a modo SDK estándar.",
                         {"keyboard": "sdk", "mouse": "sdk", "virtual_mouse": False},
                         fix_label="Usar modo SDK")
    if "connection reset" in text or "broken pipe" in text or "connection refused" in text:
        return Diagnosis("Se perdió la conexión TCP/IP con el dispositivo. Verifica que el móvil siga conectado a la misma red Wi-Fi.",
                         fix_label="Buscar dispositivos", action="refresh")
    if "tcpip" in text or "192.168." in text or "10." in text or "172." in text:
        return Diagnosis("La sesión Wi-Fi se cerró inesperadamente. Apliquemos valores estables para conexión inalámbrica.",
                         {"screen_off": False, "bitrate": 8, "fps": 60, "video_buffer": 30, "audio_buf": 80, "keyboard": "sdk", "mouse": "sdk"},
                         fix_label="Aplicar valores seguros para Wi-Fi")
    return None


# ── Devices ─────────────────────────────────────────────────────────
@dataclass
class DeviceInfo:
    serial: str
    model: str
    wifi: bool = False
    battery: Any = None           # dict with level, charging, powered or int
    latency: Optional[float] = None  # ms roundtrip ping for Wi-Fi
    screen: Optional[dict] = None    # physical res and fps
    caps: Optional[dict] = None

    @property
    def title(self) -> str:
        if self.caps:
            brand = self.caps.get("brand", "")
            model = self.caps.get("model", self.model)
            return f"{brand} {model}".strip()
        return self.model or self.serial

    @property
    def android(self) -> str:
        return str(self.caps.get("android_version", "")) if self.caps else ""


def read_battery(serial: str) -> dict:
    """Read detailed battery state (level %, charging status, power source)."""
    b = get_adb_gateway().get_battery_status(serial)
    return {"level": b.level, "charging": b.charging, "powered": b.power_source}


def measure_latency(serial: str) -> Optional[float]:
    """Measure roundtrip latency to the Android device via ADB in milliseconds."""
    return get_adb_gateway().measure_latency(serial)


def read_screen_metrics(serial: str) -> dict:
    """Retrieve physical display resolution and refresh rate via ADB."""
    m = get_adb_gateway().get_screen_metrics(serial)
    return {"res": m.resolution, "fps": m.refresh_rate}


def capture_quick_preview(serial: str) -> Optional[bytes]:
    """Capture raw PNG screenshot bytes from device via ADB screencap."""
    return get_adb_gateway().capture_quick_preview(serial)



def scan_devices() -> dict:
    """Blocking: list devices (run via ``run_async``)."""
    if not mgr.is_adb_available():
        return {"adb": False, "devices": [], "unauthorized": 0}
    devs = [DeviceInfo(s, m, wifi=(":" in s)) for s, m in mgr.list_devices()]
    return {"adb": True, "devices": devs, "unauthorized": mgr.get_unauthorized_count()}


def scan_details(serial: str) -> dict:
    """Blocking: hardware capabilities + battery + latency + screen + apps for one device."""
    caps = mgr.scan_device_capabilities(serial)
    apps = mgr.get_installed_apps(serial)
    battery = read_battery(serial)
    latency = measure_latency(serial) if ":" in serial else None
    screen = read_screen_metrics(serial)
    return {
        "serial": serial,
        "caps": caps,
        "battery": battery,
        "latency": latency,
        "screen": screen,
        "apps": apps,
    }


def scan_apps(serial: str) -> list[tuple[str, str]]:
    """Blocking: fetch installed apps for one device."""
    return mgr.get_installed_apps(serial)


# ── Sessions ────────────────────────────────────────────────────────
@dataclass
class Session:
    sid: str
    title: str
    proc: Any
    mode: str
    started: str
    app: str = ""
    virtual: bool = False


class SessionManager(QObject):
    """Launches/stops scrcpy processes and streams their output."""

    log = Signal(str)
    changed = Signal()
    failed = Signal(object)    # Diagnosis
    started = Signal(str)
    recorded = Signal(str, str)  # (sid, full_filepath) when a recording completes

    def __init__(self):
        super().__init__()
        self.sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._counter = 0

    def count(self) -> int:
        with self._lock:
            return len(self.sessions)

    def preflight(self, cfg: dict, caps: Optional[dict]) -> tuple[bool, list[str]]:
        issues = run_diagnostics(cfg, caps)
        return (not any(i.level == "error" for i in issues)), [str(i) for i in issues]

    def start(self, cfg: dict, caps: Optional[dict] = None) -> bool:
        exe = mgr.get_scrcpy_path()
        if not exe:
            self.failed.emit(Diagnosis("scrcpy no está instalado.", fix_label="Descargar scrcpy", action="download"))
            return False
        ok, msgs = self.preflight(cfg, caps)
        for m in msgs:
            self.log.emit(m)
        if not ok:
            self.log.emit("⛔ Lanzamiento cancelado: corrige los errores indicados arriba.")
            return False
        self._counter += 1
        sid = f"display_{self._counter}"
        pkg = str(cfg.get("virtual_display_app", "")).strip()
        if pkg:
            title = f"Scrcpy - {pkg.split('.')[-1].capitalize()} (#{self._counter})"
        elif cfg.get("virtual_display"):
            title = f"Scrcpy - Pantalla Virtual #{self._counter}"
        else:
            title = f"Scrcpy Mirror #{self._counter}"
        cfg = dict(cfg, window_title=title)
        args = [exe] + build_scrcpy_args(cfg, is_windows=mgr.IS_WINDOWS, scrcpy_version=mgr.get_installed_version())
        try:
            hist.record_session(device=cfg.get("device", ""), preset=cfg.get("active_mode", ""),
                                args=args[1:], config=cfg, command=" ".join(args), success=True)
        except Exception:
            pass
        self.log.emit(f"▶ [{title}] {' '.join(args)}")
        threading.Thread(target=self._run, args=(sid, title, args, exe, cfg, pkg), daemon=True).start()
        return True

    def _run(self, sid, title, args, exe, cfg, pkg):
        lines: list[str] = []
        record_path = ""
        for a in args:
            if a.startswith("--record="):
                record_path = a.split("=", 1)[1].strip()
                break

        try:
            kw = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT, "text": True,
                  "cwd": os.path.dirname(exe), "bufsize": 1, "errors": "replace"}
            if mgr.IS_WINDOWS:
                kw["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(args, **kw)
            with self._lock:
                self.sessions[sid] = Session(sid, title, proc, cfg.get("active_mode", ""),
                                             time.strftime("%H:%M:%S"), pkg,
                                             bool(cfg.get("virtual_display")))
            self.changed.emit()
            self.started.emit(title)
            for line in iter(proc.stdout.readline, ""):
                if line.strip():
                    lines.append(line.rstrip())
                    self.log.emit(f"[{sid}] {line.rstrip()}")
            proc.wait()
            if proc.returncode not in (0, None) and proc.returncode > 0:
                self.log.emit(f"⏹ [{title}] terminó con código {proc.returncode}")
                diag = diagnose_exit(lines)
                self.failed.emit(diag or Diagnosis(
                    f"La sesión terminó inesperadamente (código {proc.returncode}). Revisa la consola.",
                    fix_label="Ver consola", action="console"))
            else:
                self.log.emit(f"⏹ [{title}] sesión finalizada.")

            # Validate recording file completion and notify
            if record_path and os.path.exists(record_path):
                sz = os.path.getsize(record_path)
                if sz > 0:
                    mb = sz / (1024 * 1024)
                    self.log.emit(f"🎬 Grabación guardada exitosamente: {record_path} ({mb:.2f} MB)")
                    self.recorded.emit(sid, record_path)
                else:
                    self.log.emit(f"⚠️ El archivo de grabación quedó vacío (0 bytes).")
        except Exception as exc:
            self.log.emit(f"❌ [{title}] Error: {exc}")
            self.failed.emit(Diagnosis(f"No se pudo iniciar scrcpy: {exc}", fix_label="Ver consola", action="console"))
        finally:
            with self._lock:
                self.sessions.pop(sid, None)
            self.changed.emit()

    def stop(self, sid: str) -> None:
        with self._lock:
            s = self.sessions.get(sid)
        if not s:
            return
        proc = s.proc

        def graceful_kill():
            try:
                if proc.poll() is not None:
                    return
                if mgr.IS_WINDOWS:
                    try:
                        import ctypes
                        from ctypes import wintypes
                        user32 = ctypes.windll.user32
                        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

                        def enum_cb(hwnd, _):
                            lpdw = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw))
                            if lpdw.value == proc.pid:
                                user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                            return True

                        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
                    except Exception:
                        pass
                    try:
                        import signal
                        os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
                    except Exception:
                        pass
                else:
                    try:
                        import signal
                        proc.send_signal(signal.SIGINT)
                    except Exception:
                        pass

                # Give scrcpy time to flush media packets and write trailer
                for _ in range(35):
                    if proc.poll() is not None:
                        return
                    time.sleep(0.1)

                proc.terminate()
                for _ in range(15):
                    if proc.poll() is not None:
                        return
                    time.sleep(0.1)
                if proc.poll() is None:
                    proc.kill()
            except Exception as exc:
                self.log.emit(f"⚠️ Error al detener {s.title}: {exc}")
        threading.Thread(target=graceful_kill, daemon=True).start()

    def stop_all(self) -> None:
        with self._lock:
            ids = list(self.sessions)
        for sid in ids:
            self.stop(sid)


def restart_adb_server(callback: Optional[Callable[[bool, str], None]] = None) -> None:
    """Kill and restart ADB server in background worker pool."""
    def work():
        return get_adb_gateway().restart_server()

    def done(res):
        if callback:
            ok, msg = res
            callback(ok, msg)

    run_async(work, on_done=done)


