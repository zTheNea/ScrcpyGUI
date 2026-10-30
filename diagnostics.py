"""Pre-launch diagnostics and compatibility checker for ScrcpyGUI.

Inspects the current configuration and target device capabilities to identify
potential compatibility conflicts, deprecations, or suboptimal settings before
launching scrcpy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from paths import IS_WINDOWS


@dataclass
class DiagnosticIssue:
    level: Literal["error", "warning", "info"]
    title: str
    message: str
    field: str = ""

    def __str__(self) -> str:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.level, "•")
        return f"{icon} [{self.title}] {self.message}"


def _parse_sdk(device_info: dict[str, Any] | None) -> int:
    if not device_info:
        return 0
    sdk_val = device_info.get("sdk") or device_info.get("ro.build.version.sdk")
    try:
        return int(sdk_val)
    except (TypeError, ValueError):
        pass
    ver_val = str(device_info.get("android_version") or device_info.get("ro.build.version.release", "")).strip()
    # Map common Android major versions to SDK level
    version_map = {
        "4.4": 19, "5.0": 21, "5.1": 22, "6.0": 23, "7.0": 24, "7.1": 25,
        "8.0": 26, "8.1": 27, "9": 28, "10": 29, "11": 30, "12": 31,
        "13": 33, "14": 34, "15": 35,
    }
    for k, v in version_map.items():
        if ver_val.startswith(k):
            return v
    return 0


def run_diagnostics(
    cfg: dict[str, Any],
    device_info: dict[str, Any] | None = None,
) -> list[DiagnosticIssue]:
    """Analyze configuration and optional device info, returning a list of issues."""
    issues: list[DiagnosticIssue] = []

    dev_str = str(cfg.get("device", "")).strip()
    is_network_device = bool(re.search(r":\d{4,5}\b", dev_str)) or ("." in dev_str.split(" ")[0] and ":" in dev_str)
    sdk = _parse_sdk(device_info)

    # 1. Total blackout check: no video and no audio
    no_vid = cfg.get("no_video", False)
    has_audio = cfg.get("audio", True)
    if no_vid and not has_audio and not cfg.get("otg_mode"):
        issues.append(DiagnosticIssue(
            level="error",
            title="Sin Transmisión",
            message="Tanto el video como el audio están desactivados. scrcpy no mostrará ni transmitirá nada.",
            field="video",
        ))

    # 2. OTG requires USB
    if cfg.get("otg_mode"):
        if is_network_device:
            issues.append(DiagnosticIssue(
                level="warning",
                title="OTG sobre Wi-Fi",
                message="El modo OTG (USB HID físico) requiere conexión por cable USB. No funciona sobre Wi-Fi/TCP-IP.",
                field="otg_mode",
            ))

    # 3. UHID over Wi-Fi
    kb = str(cfg.get("keyboard", ""))
    ms = str(cfg.get("mouse", ""))
    if cfg.get("virtual_mouse") is False and ms == "uhid":
        ms = ""
    elif cfg.get("virtual_mouse") is True and not ms:
        ms = "uhid"
    gp = str(cfg.get("gamepad", ""))
    if (kb == "uhid" or ms == "uhid" or gp == "uhid") and is_network_device:
        issues.append(DiagnosticIssue(
            level="warning",
            title="UHID sobre Red",
            message="El control por hardware UHID puede fallar o tener alta latencia sobre Wi-Fi. Se recomienda conexión USB o modo 'sdk'.",
            field="keyboard",
        ))

    # 3b. Screen off over Wi-Fi
    if is_network_device and cfg.get("screen_off"):
        issues.append(DiagnosticIssue(
            level="warning",
            title="Apagar Pantalla sobre Wi-Fi",
            message="Al apagar la pantalla por Wi-Fi, Android puede suspender el adaptador inalámbrico y congelar la transmisión (0 FPS). Se recomienda mantener la pantalla encendida o conectar por USB.",
            field="screen_off",
        ))

    # 4. Android version checks
    codec = str(cfg.get("codec", "h264")).lower()
    if sdk > 0:
        if codec == "h265" and sdk < 21:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Códec H.265 no compatible",
                message="H.265 (HEVC) requiere Android 5.0+ (API 21). Tu dispositivo tiene API < 21.",
                field="codec",
            ))
        elif codec == "vp9" and sdk < 26:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Códec VP9 requiere Android 8+",
                message="El códec VP9 por hardware requiere Android 8.0+ (API 26) para un rendimiento fluido.",
                field="codec",
            ))
        elif codec == "av1" and sdk < 34:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Códec AV1 requiere Android 14+",
                message="La codificación por hardware AV1 suele requerir Android 14+ (API 34) y hardware compatible.",
                field="codec",
            ))

        # Camera requires Android 12+
        if str(cfg.get("video_source", "")).lower() == "camera" and sdk < 31:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Cámara requiere Android 12+",
                message="El streaming de cámara en scrcpy requiere Android 12+ (API 31).",
                field="video_source",
            ))

        # Virtual display requires Android 10+
        if cfg.get("virtual_display") and sdk < 29:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Pantalla Virtual requiere Android 10+",
                message="La creación de pantallas virtuales (--new-display) requiere Android 10+ (API 29).",
                field="virtual_display",
            ))

        # Flex display requires Android 14+
        if cfg.get("flex_display") and sdk < 34:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Pantalla Flex requiere Android 14+",
                message="La pantalla redimensionable flexible (--flex-display) requiere Android 14+ (API 34).",
                field="flex_display",
            ))

        # Internal audio capture requires Android 11+
        if has_audio and str(cfg.get("audio_source", "output")).lower() == "output" and sdk < 30:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Captura de Audio Interno",
                message="La captura de audio interno (output) requiere Android 11+ (API 30). En versiones anteriores usa fuente 'mic' o desactiva el audio.",
                field="audio_source",
            ))

    # 5. Recording filename check
    if cfg.get("record"):
        rec_file = str(cfg.get("record_file", "")).strip()
        if not rec_file:
            issues.append(DiagnosticIssue(
                level="warning",
                title="Nombre de grabación vacío",
                message="La grabación está activada pero no se especificó un nombre de archivo.",
                field="record_file",
            ))

    # 6. Headless without purpose
    if cfg.get("no_window") and not cfg.get("record") and not cfg.get("no_video_playback") and not cfg.get("v4l2_device"):
        issues.append(DiagnosticIssue(
            level="info",
            title="Modo sin ventana",
            message="scrcpy correrá sin ventana (--no-window) y no hay grabación activa. La sesión será invisible.",
            field="no_window",
        ))

    # 7. High FPS with low bitrate
    fps = 0
    try:
        fps = int(cfg.get("fps", 0))
    except (ValueError, TypeError):
        pass
    bitrate = 0
    try:
        bitrate = int(cfg.get("bitrate", 8))
    except (ValueError, TypeError):
        pass
    if fps >= 90 and 0 < bitrate < 4:
        issues.append(DiagnosticIssue(
            level="info",
            title="Bitrate bajo para FPS altos",
            message=f"{fps} FPS con sólo {bitrate} Mbps puede producir artefactos visuales o compresión borrosa.",
            field="bitrate",
        ))

    # 8. Control-dependent options with no_control
    has_no_control = bool(cfg.get("no_control") or str(cfg.get("video_source", "")).lower() == "camera")
    if has_no_control:
        conflict_items = []
        if cfg.get("stay_awake"):
            conflict_items.append("Mantener despierto")
        if cfg.get("screen_off"):
            conflict_items.append("Apagar pantalla")
        if cfg.get("power_off_on_close"):
            conflict_items.append("Apagar al cerrar")
        if cfg.get("show_touches"):
            conflict_items.append("Mostrar toques")
        if cfg.get("keep_active"):
            conflict_items.append("Mantener activo")
        if cfg.get("virtual_display_app"):
            conflict_items.append("Auto-arranque de app")
        if conflict_items:
            issues.append(DiagnosticIssue(
                level="info",
                title="Opciones omitidas por Solo Lectura",
                message=f"En modo sin control (--no-control), scrcpy no permite modificar el estado del dispositivo ni enviar comandos. Se omitirán: {', '.join(conflict_items)}.",
                field="no_control",
            ))

    # 9. Hardware decoding OS compatibility (scrcpy 5.0+)
    hwdec = str(cfg.get("hwdec", "")).strip().lower()
    if hwdec == "vaapi" and IS_WINDOWS:
        issues.append(DiagnosticIssue(
            level="warning",
            title="VA-API no soportado en Windows",
            message="El decodificador por hardware 'vaapi' solo está disponible en Linux. En Windows utiliza 'd3d11va' o 'auto'.",
            field="hwdec",
        ))
    elif hwdec == "d3d11va" and not IS_WINDOWS:
        issues.append(DiagnosticIssue(
            level="warning",
            title="D3D11VA solo para Windows",
            message="El decodificador 'd3d11va' requiere DirectX 11 y solo funciona en Windows. En Linux utiliza 'vaapi' o 'auto'.",
            field="hwdec",
        ))

    return issues
