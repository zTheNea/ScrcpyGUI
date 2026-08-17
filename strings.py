"""UI strings and translation dictionary for ScrcpyGUI (Default: Spanish)."""
from __future__ import annotations

STRINGS: dict[str, str] = {
    # App
    "app_title": "ScrcpyGUI v1.3.0",
    "system_windows": "Sistema: Windows",
    "system_other": "Sistema: Linux/macOS",
    
    # Updater
    "download_scrcpy": "⬇️ Descargar scrcpy",
    "check_update": "🔍 Buscar actualización",
    "use_package_manager": "(Usa tu gestor de paquetes)",
    "scrcpy_installed": "✅ scrcpy {ver} — {path}",
    "scrcpy_not_found_win": "❌ scrcpy no encontrado",
    "scrcpy_not_found_other": "❌ scrcpy no instalado. Instálalo con: sudo apt install scrcpy",
    "checking_updates": "🔍 Buscando actualizaciones...",
    "update_error": "⚠️ Error: {err}",
    "latest_version": "✅ scrcpy {tag} — Ya tienes la última versión",
    "new_version_available": "🆕 Nueva versión disponible: {tag}",
    "downloading_scrcpy": "⬇️ Descargando scrcpy...",
    "extracting_files": "📦 Extrayendo archivos...",
    "retry": "⬇️ Reintentar",
    "download_success": "✅ scrcpy {tag} instalado en {path}",
    
    # Devices & Inspector
    "device_label": "📱 Dispositivo:",
    "searching": "Buscando...",
    "no_devices": "Sin dispositivos",
    "refresh": "🔄 Refrescar",
    "inspector_title": "🔍 Inspector de Hardware:",
    "btn_list_encoders": "🎬 Encoders",
    "btn_list_cameras": "📷 Cámaras",
    "btn_list_displays": "🖥️ Pantallas",
    "btn_list_cam_sizes": "📐 Res. Cam",
    
    # Modes
    "select_mode": "Selecciona un Modo",
    "select_mode_desc": "Elige un perfil optimizado o crea tu configuración",
    "custom_mode_title": "⚙️  Personalizado",
    "custom_mode_desc": "Configura cada parámetro",
    "custom_mode_badge": "Avanzado",
    
    # Tabs
    "tab_video": "🎥 Video",
    "tab_audio": "🔊 Audio",
    "tab_display": "🖥️ Pantalla",
    "tab_controls": "🎛️ Controles",
    "tab_wifi": "📶 Wi-Fi",
    "tab_profiles": "💾 Perfiles",
    
    # New v4.1 Options
    "ignore_encoder_constraints": "⚡ Ignorar límites de encoder",
    "no_audio_playback": "🚫 Sin audio local (Solo capturar)",
    "no_playback": "🚫 Sin ventana de video local",
    "audio_output_buf": "Buffer salida PC (ms)",
    "legacy_paste": "📋 Pegado legacy (Pulsaciones)",
    "force_adb_forward": "🛡️ Forzar ADB Forward",
    "camera_high_speed": "🚀 Cámara High-Speed (120fps+)",
    "kill_adb_on_close": "🛑 Detener ADB al salir",
    
    # Actions
    "copy_cmd": "📋 Copiar",
    "launch_btn": "🚀  Iniciar Scrcpy",
    "stop_btn": "⏹  Detener",
    "stopping": "⌛ Deteniendo...",
    "finished_btn": "✅ Terminado — Click para reiniciar",
    
    # Logs & Messages
    "ready_msg": "Listo. Selecciona un modo e inicia.\n",
    "config_restored": "💾 Configuración anterior restaurada.",
    "cmd_copied": "📋 Comando copiado.",
    "scrcpy_running": "⚠️ scrcpy ya está en ejecución.",
    "connect_device_first": "⚠️ Conecta un dispositivo primero.",
    "enter_ip": "⚠️ Ingresa una IP válida",
    "enter_ip_code": "⚠️ Ingresa IP:Puerto y Código",
    "connect_usb_first": "⚠️ Conecta el teléfono por USB primero",
}

def t(key: str, **kwargs: str) -> str:
    """Retrieve string by key and format with optional kwargs."""
    text = STRINGS.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
