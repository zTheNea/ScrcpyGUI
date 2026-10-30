"""UI strings and translation dictionary for ScrcpyGUI (Default: Spanish).

All user-facing text should be retrieved via ``t(key, **kwargs)`` so that
future translations can be added by swapping this dictionary.
"""
from __future__ import annotations

STRINGS: dict[str, str] = {
    # App
    "app_title": "Scrcpy Studio v2.0.0",
    "system_windows": "Sistema: Windows",
    "system_other": "Sistema: Linux/macOS",

    # Updater
    "download_scrcpy": "⬇️ Descargar scrcpy",
    "check_update": "🔍 Buscar actualización",
    "use_package_manager": "(Usa tu gestor de paquetes)",
    "scrcpy_installed": "✅ scrcpy {ver} — {path}",
    "scrcpy_not_found": "❌ scrcpy.exe no encontrado.",
    "scrcpy_not_found_other": "❌ scrcpy no instalado. Instálalo con: sudo apt install scrcpy",
    "checking_updates": "🔍 Buscando actualizaciones de scrcpy en GitHub...",
    "update_error": "⚠️ Error al buscar actualización: {err}",
    "latest_version": "✅ scrcpy {tag} — Ya tienes la versión más reciente.",
    "new_version_available": "🆕 Nueva versión disponible: {tag} (instalada: {installed})",
    "downloading": "⬇️ Descargando scrcpy {tag} desde GitHub...",
    "extracting_files": "📦 Extrayendo binarios de scrcpy...",
    "download_error": "❌ Error al descargar: {err}",
    "download_success": "✅ scrcpy {tag} instalado correctamente en {path}.",
    "retry": "⬇️ Reintentar",

    # Devices & Inspector
    "device_label": "📱 Dispositivo:",
    "searching": "Buscando...",
    "no_device": "📱 Sin dispositivo",
    "no_devices": "Sin dispositivos",
    "refresh": "🔄 Refrescar",
    "scanning_hw": "🔍 Escaneando capacidades de hardware de {dev}...",
    "scan_result": "✅ {brand} {model} (Android {ver}) analizado:",
    "scan_video_codecs": "   🎬 Códecs Video compatibles: [{codecs}]",
    "scan_audio_codecs": "   🔊 Códecs Audio compatibles: [{codecs}]",
    "scan_cams_displays": "   📷 Cámaras: {cams} | 🖥️ Pantallas: {dsps}",
    "codec_unsupported": "ℹ️ Códec {codec} no soportado por este móvil, adaptado automáticamente a H264.",
    "preset_hidden": "🛡️ Ocultados {count} presets incompatibles con el hardware de tu dispositivo:",
    "preset_hidden_item": "   ✖ {label} ({reason})",
    "preset_fallback": "ℹ️ Modo '{mode}' oculto por incompatibilidad. Cambiado automáticamente a '{fallback}'.",

    # Inspector buttons
    "btn_list_encoders": "🎬 Encoders",
    "btn_list_cameras": "📷 Cámaras",
    "btn_list_displays": "🖥️ Pantallas",
    "btn_pc_mode": "⚡ Modo PC",
    "inspector_querying": "🔍 Consultando {flag} en {dev}...",
    "pc_mode_activating": "⚡ Activando soporte de Ventanas Libres y Modo Escritorio en {dev}...",

    # Modes
    "select_mode": "Selecciona un Modo",
    "select_mode_desc": "Elige un perfil optimizado o crea tu configuración",
    "custom_mode_title": "⚙️ Personalizado",
    "custom_mode_badge": "Avanzado",

    # Tabs
    "tab_video": "🎥 Video",
    "tab_audio": "🔊 Audio",
    "tab_display": "🖥️ Pantalla",
    "tab_controls": "🎛️ Controles",
    "tab_sessions": "🪟 Pantallas Activas",
    "tab_wifi": "📶 Wi-Fi",
    "tab_profiles": "💾 Perfiles",

    # Actions
    "copy_cmd": "📋 Copiar CLI",
    "launch_btn": "▶ Iniciar Scrcpy",
    "stop_btn": "⏹ Detener Todo",
    "cmd_copied": "📋 Comando copiado.",
    "config_restored": "💾 Configuración anterior restaurada.",
    "ready_msg": "$ scrcpy listo. Selecciona un modo en el panel lateral y pulsa ▶ Iniciar.\n",

    # Sessions
    "no_sessions": "No hay sesiones activas para detener.",
    "stopping_all": "⏹ Deteniendo todas las {count} pantallas abiertas...",
    "session_finished": "⏹ [{title}] terminó (código {code})",
    "session_error": "❌ [{title}] Error: {err}",
    "session_stopping": "⏹ Deteniendo [{title}]...",

    # App Picker
    "app_selected": "📱 Aplicación seleccionada para Pantalla Virtual: {name} ({pkg})",
    "app_none": "🖥️ Pantalla Virtual en modo Escritorio Libre (sin autoarranque).",
    "app_cleared": "🗑️ Selección de app eliminada (Modo Escritorio Libre).",
    "connect_device_for_apps": "⚠️ Conecta un dispositivo primero para listar aplicaciones.",
    "connect_device_for_vd": "⚠️ Conecta un dispositivo primero para crear una pantalla virtual.",

    # Wi-Fi
    "enter_ip": "⚠️ Ingresa una IP válida",
    "enter_ip_code": "⚠️ Ingresa IP:Puerto y Código",
    "connect_usb_first": "⚠️ Conecta el teléfono por USB primero",
    "wifi_connecting": "📡 Intentando conectar a {ip}...",
    "wifi_pairing": "🔐 Emparejando con {ip}...",
    "wifi_auto_usb": "⚡ Automatizando paso a Wi-Fi para {dev}...",
    "wifi_disconnect_cable": "✅ Ya puedes desconectar el cable USB.",

    # Profiles
    "profile_name_empty": "⚠️ Escribe un nombre para el perfil.",
    "profile_saved": "💾 Perfil '{name}' guardado.",
    "profile_loaded": "📂 Perfil '{name}' cargado.",
    "profile_load_error": "⚠️ Error al cargar el perfil '{name}'.",
    "profile_deleted": "🗑️ Perfil '{name}' eliminado.",

    # ADB & Device errors
    "no_adb_found": "⚠️ ADB no encontrado en el sistema. Instala scrcpy o Android Platform Tools.",
    "adb_not_found_device": "ADB no encontrado",
    "unauthorized_warning_single": "⚠️ 1 dispositivo conectado pero no autorizado. Acepta el diálogo 'Depuración USB' en el teléfono.",
    "unauthorized_warning_plural": "⚠️ {count} dispositivos conectados pero no autorizados. Acepta el diálogo 'Depuración USB' en cada teléfono.",

    # Launch
    "launch_no_scrcpy": "❌ scrcpy no encontrado. Usa 'Buscar actualización' para descargarlo o instálalo manualmente.",
    "session_launched": "▶ [{title}] Ejecutando: {cmd}",

    # Hardware scan
    "scanning_hw_start": "🔍 Analizando...",

    # Close confirmation
    "close_confirm_title": "Cerrar ScrcpyGUI",
    "close_confirm_msg": "Hay {count} sesión(es) de scrcpy activa(s).\n¿Deseas cerrar de todas formas?",
    "close_confirm_recording": "Hay {count} sesión(es) activa(s) y una grabación en curso que podría perderse.\n¿Deseas cerrar de todas formas?",

    # Recordings folder
    "open_folder_error": "⚠️ No se pudo abrir la carpeta: {err}",

    # ── Phase 1 / 2 new labels ──────────────────────────────────────────────
    # Video tab
    "render_fit_label": "Ajuste de Pantalla",
    "no_video_playback_label": "💻 Sin reproducción local (Headless)",
    "video_encoder_label": "Encoder específico",
    "capture_orient_label": "Orientación Captura",
    "display_orient_label": "Orientación Pantalla PC",
    "render_driver_label": "Driver renderizado",
    "window_pos_label": "Posición ventana (X / Y)",
    "window_size_label": "Tamaño ventana (W / H)",
    # Audio tab
    "record_format_label": "Formato grabación",
    "require_audio_label": "🔴 Requerir audio (falla si no)",
    # Camera extras
    "camera_ar_label": "Aspect Ratio cámara",
    "camera_size_label": "Resolución cámara (WxH)",
    # Controls
    "power_off_on_close_label": "⏻ Apagar pantalla al cerrar",
    "no_power_on_label": "🔌 No encender pantalla al iniciar",
    "shortcut_mod_label": "Modificador atajos (MOD)",
    "push_target_label": "Carpeta destino D&D",
    # Advanced tab groups
    "adv_tab_name": "⚡ Avanzado",
    "adv_window_group": "🦟 Ventana & Renderizado",
    "adv_process_group": "⚙️ Proceso & Comportamiento",
    "adv_input_group": "⌨️ Input Avanzado",
    "adv_connect_group": "📡 Conexión Avanzada",
    # Advanced options
    "no_window_label": "🖥️ Sin ventana (Headless total)",
    "display_ime_label": "Política IME (teclado virtual)",
    "verbosity_label": "Nivel de log",
    "pause_on_exit_label": "Pausa al salir",
    "no_cleanup_label": "🧹 No limpiar servidor al salir",
    "no_downsize_label": "🚫 No reducir res. al fallar",
    "screen_off_timeout_label": "Timeout pantalla (s)",
    "no_key_repeat_label": "⏸️ Sin repetición de tecla",
    "prefer_text_label": "Inyectar como texto",
    "raw_key_events_label": "Raw key events",
    "no_mouse_hover_label": "🚫 Sin hover del ratón",
    "port_label": "Puerto TCP local",
    "tunnel_host_label": "Tunnel host (IP)",
    "tunnel_port_label": "Tunnel port",
    "no_terminal_title_label": "No actualizar título terminal",
    "angle_label": "Rotación personalizada (°)",
    # History & Diagnostics
    "history_title": "📜 Historial de Sesiones Recientes",
    "history_clear": "🗑️ Limpiar Historial",
    "history_empty": "No hay sesiones registradas aún.",
    "history_relaunch": "▶ Relanzar",
    "history_load": "⚙️ Cargar Config",
    "diag_error_cancel": "❌ Lanzamiento cancelado debido a errores de configuración.",
}


def t(key: str, **kwargs: str) -> str:
    """Retrieve string by key and format with optional kwargs.

    If the key is missing, the key itself is returned as fallback.
    """
    text = STRINGS.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
