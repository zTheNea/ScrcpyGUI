"""
ScrcpyGUI — Native Windows GUI for scrcpy
Allows selecting preconfigured modes (Video, Gaming, Balanced) or custom config.
Launches scrcpy directly from the interface.
Auto-downloads and updates scrcpy from GitHub.
"""
import customtkinter as ctk
import os
import queue
import re
import subprocess
import threading
import time

import scrcpy_manager as mgr
import config_manager as cfg
import history_manager as hist
from command_builder import build_scrcpy_args, format_record_filename
from diagnostics import run_diagnostics
from presets import (
    PRESETS, PRESET_CATEGORIES, VIDEO_CODECS, VIRTUAL_RES_PRESETS, AUDIO_SOURCES, AUDIO_CODECS,
    KEYBOARD_MODES, MOUSE_MODES, GAMEPAD_MODES, ORIENTATION_VALUES,
    CAMERA_FACING, COLORS, MODE_COLORS,
    # v1.4.0 & v1.5.0 (scrcpy 5.0)
    RENDER_FIT_VALUES, RENDER_DRIVER_VALUES, RECORD_FORMATS,
    CAPTURE_ORIENTATION_VALUES, DISPLAY_ORIENTATION_VALUES,
    IME_POLICY_VALUES, VERBOSITY_LEVELS, PAUSE_ON_EXIT_VALUES, CAMERA_AR_VALUES,
    HWDEC_MODES, RECORD_ORIENTATION_VALUES, MIN_SIZE_ALIGNMENT_VALUES,
)
from gui.widgets import (
    InlineAppPicker, CTooltip,
    cfg_group, cfg_group_full, cfg_option_menu,
    cfg_entry, cfg_slider, cfg_switch,
)
from strings import t

# ── Theme ──
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ScrcpyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScrcpyGUI v1.4.0")
        self.geometry("920x740")
        self.minsize(800, 600)
        self.configure(fg_color=COLORS["bg"])

        self.active_mode = ctk.StringVar(value="")
        self.process = None
        self.active_sessions = {}
        self._session_counter = 0
        self._process_lock = threading.Lock()
        self.mode_buttons = {}
        self._scan_generation = 0

        # Performance optimizations
        self._after_update_id = None
        self.log_queue = queue.Queue()
        self._log_updater_running = False
        self._scrcpy_path_cache = mgr.get_scrcpy_path()

        # ── Config variables ──
        self.v_codec = ctk.StringVar(value="h264")
        self.v_res_preset = ctk.StringVar(value="1080p")
        self.v_max_size = ctk.StringVar(value="1920")
        self.v_fps = ctk.IntVar(value=60)
        self.v_bitrate = ctk.IntVar(value=8)
        self.v_audio = ctk.BooleanVar(value=True)
        self.v_audio_buf = ctk.IntVar(value=50)
        self.v_fullscreen = ctk.BooleanVar(value=False)
        self.v_stay_awake = ctk.BooleanVar(value=True)
        self.v_screen_off = ctk.BooleanVar(value=False)
        self.v_keyboard = ctk.StringVar(value="")
        self.v_kb_uhid = ctk.BooleanVar(value=False)
        self.v_mouse = ctk.StringVar(value="")
        self.v_virtual_mouse = ctk.BooleanVar(value=False)
        self.v_gamepad = ctk.StringVar(value="")
        self.v_record = ctk.BooleanVar(value=False)
        self.v_record_file = ctk.StringVar(value="recording.mp4")
        self.v_print_fps = ctk.BooleanVar(value=False)
        self.v_show_touches = ctk.BooleanVar(value=False)
        self.v_crop = ctk.StringVar(value="")
        self.v_device = ctk.StringVar(value="")
        self.v_audio_source = ctk.StringVar(value="output")
        self.v_audio_codec = ctk.StringVar(value="opus")
        self.v_always_on_top = ctk.BooleanVar(value=False)
        self.v_borderless = ctk.BooleanVar(value=False)
        self.v_window_title = ctk.StringVar(value="Scrcpy Mirror")
        self.v_virtual_display = ctk.BooleanVar(value=False)
        self.v_virtual_display_res = ctk.StringVar(value="1280x720")
        self.v_virtual_res_preset = ctk.StringVar(value="1280x720")
        self.v_virtual_display_app = ctk.StringVar(value="")
        self.app_list_data = {}
        self.v_video_source = ctk.StringVar(value="display")
        self.v_camera_id = ctk.StringVar(value="0")
        self.v_camera_facing = ctk.StringVar(value="")
        self.v_camera_fps = ctk.IntVar(value=30)
        self.v_v4l2_device = ctk.StringVar(value="")
        self.v_wifi_ip = ctk.StringVar(value="")
        self.v_wifi_pair_code = ctk.StringVar(value="")
        self.v_display_id = ctk.StringVar(value="0")
        self.v_orientation = ctk.StringVar(value="0")

        self.v_no_video = ctk.BooleanVar(value=False)
        self.v_no_control = ctk.BooleanVar(value=False)
        self.v_audio_dup = ctk.BooleanVar(value=False)
        self.v_audio_bitrate = ctk.IntVar(value=128)
        self.v_disable_screensaver = ctk.BooleanVar(value=False)
        self.v_time_limit = ctk.IntVar(value=0)
        self.v_no_vd_decorations = ctk.BooleanVar(value=False)
        self.v_no_vd_destroy = ctk.BooleanVar(value=False)
        self.v_virtual_dpi = ctk.StringVar(value="")
        self.v_no_clipboard_sync = ctk.BooleanVar(value=False)
        self.v_video_buffer = ctk.IntVar(value=0)
        
        # scrcpy v4.0 & v4.1 variables
        self.v_flex_display = ctk.BooleanVar(value=False)
        self.v_camera_torch = ctk.BooleanVar(value=False)
        self.v_camera_zoom = ctk.StringVar(value="")
        self.v_keep_active = ctk.BooleanVar(value=False)
        self.v_background_color = ctk.StringVar(value="")
        self.v_no_aspect_ratio_lock = ctk.BooleanVar(value=False)
        self.v_otg_mode = ctk.BooleanVar(value=False)
        self.v_ignore_encoder_constraints = ctk.BooleanVar(value=False)
        self.v_no_audio_playback = ctk.BooleanVar(value=False)
        self.v_no_playback = ctk.BooleanVar(value=False)
        self.v_audio_output_buf = ctk.IntVar(value=0)
        self.v_legacy_paste = ctk.BooleanVar(value=False)
        self.v_force_adb_forward = ctk.BooleanVar(value=False)
        self.v_camera_high_speed = ctk.BooleanVar(value=False)
        self.v_kill_adb_on_close = ctk.BooleanVar(value=False)

        # ── Phase 1 variables (v1.4.0) ─────────────────────────────────
        self.v_render_fit = ctk.StringVar(value="")
        self.v_no_video_playback = ctk.BooleanVar(value=False)
        self.v_video_encoder = ctk.StringVar(value="")
        self.v_audio_encoder = ctk.StringVar(value="")
        self.v_record_format = ctk.StringVar(value="")
        self.v_require_audio = ctk.BooleanVar(value=False)
        self.v_capture_orientation = ctk.StringVar(value="0")
        self.v_display_orientation = ctk.StringVar(value="0")
        self.v_render_driver = ctk.StringVar(value="")
        self.v_window_x = ctk.StringVar(value="")
        self.v_window_y = ctk.StringVar(value="")
        self.v_power_off_on_close = ctk.BooleanVar(value=False)
        self.v_no_power_on = ctk.BooleanVar(value=False)
        self.v_shortcut_mod = ctk.StringVar(value="")
        self.v_push_target = ctk.StringVar(value="")

        # ── Phase 2 variables (v1.4.0 Advanced tab) ──────────────────────
        self.v_window_width = ctk.StringVar(value="")
        self.v_window_height = ctk.StringVar(value="")
        self.v_no_window = ctk.BooleanVar(value=False)
        self.v_display_ime_policy = ctk.StringVar(value="")
        self.v_verbosity = ctk.StringVar(value="")
        self.v_pause_on_exit = ctk.StringVar(value="")
        self.v_no_cleanup = ctk.BooleanVar(value=False)
        self.v_no_downsize_on_error = ctk.BooleanVar(value=False)
        self.v_screen_off_timeout = ctk.IntVar(value=0)
        self.v_no_key_repeat = ctk.BooleanVar(value=False)
        self.v_prefer_text = ctk.BooleanVar(value=False)
        self.v_raw_key_events = ctk.BooleanVar(value=False)
        self.v_no_mouse_hover = ctk.BooleanVar(value=False)
        self.v_port = ctk.StringVar(value="")
        self.v_tunnel_host = ctk.StringVar(value="")
        self.v_tunnel_port = ctk.StringVar(value="")
        self.v_no_terminal_title = ctk.BooleanVar(value=False)
        self.v_angle = ctk.IntVar(value=0)
        self.v_camera_ar = ctk.StringVar(value="")
        self.v_camera_size = ctk.StringVar(value="")

        # ── scrcpy 5.0 / 5.0.1 variables ──────────────────────────────
        self.v_hwdec = ctk.StringVar(value="")
        self.v_start_app_force_stop = ctk.BooleanVar(value=False)
        self.v_record_orientation = ctk.StringVar(value="")
        self.v_min_size_alignment = ctk.StringVar(value="")
        self.v_no_mipmaps = ctk.BooleanVar(value=False)

        # Widget references for enabling/disabling
        self.widgets = {}
        self._device_caps_cache = {}
        self._current_device_caps = None

        self._build_ui()
        self._add_traces()
        
        # Load saved config AFTER building UI so widgets exist
        loaded, saved_mode = cfg.load_config(self)
        if loaded and saved_mode and saved_mode in (set(PRESETS) | {"custom"}):
            self._select_mode(saved_mode)
            self._log(t("config_restored"))
        else:
            self._select_mode("desktop")
        
        self._debounced_update()
        
        # Auto-save config on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Confirm close if sessions are active, then save config and quit."""
        from tkinter import messagebox
        with self._process_lock:
            active_count = len(self.active_sessions)
        if active_count > 0:
            recording = self.v_record.get()
            msg_key = "close_confirm_recording" if recording else "close_confirm_msg"
            if not messagebox.askyesno(
                t("close_confirm_title"),
                t(msg_key, count=active_count),
                icon="warning",
            ):
                return
        cfg.save_config(self)
        self.destroy()

    def _add_traces(self):
        """Add traces to variables to update UI state and command preview."""
        vars_to_trace = [
            self.v_video_source, self.v_audio, self.v_virtual_display,
            self.v_keyboard, self.v_mouse, self.v_gamepad, self.v_record,
            self.v_no_control, self.v_no_video, self.v_camera_id, self.v_otg_mode,
            self.v_no_playback
        ]
        for v in vars_to_trace:
            v.trace_add("write", lambda *_: self._debounced_update())
        self.v_mouse.trace_add("write", self._sync_virtual_mouse_from_mouse)
        self.v_keyboard.trace_add("write", self._sync_kb_uhid_from_keyboard)
        
        # Others that only update command
        other_vars = [
            self.v_codec, self.v_fps, self.v_bitrate, self.v_audio_source, self.v_audio_codec, 
            self.v_audio_buf, self.v_display_id, self.v_virtual_display_res, self.v_virtual_display_app,
            self.v_orientation, self.v_audio_bitrate, self.v_audio_dup, self.v_video_buffer,
            self.v_time_limit, self.v_camera_facing, self.v_camera_fps, self.v_virtual_dpi,
            self.v_no_vd_decorations, self.v_no_vd_destroy, self.v_no_clipboard_sync,
            self.v_disable_screensaver, self.v_flex_display, self.v_virtual_mouse, self.v_camera_torch,
            self.v_camera_zoom, self.v_keep_active, self.v_background_color,
            self.v_no_aspect_ratio_lock, self.v_window_title,
            self.v_ignore_encoder_constraints, self.v_no_audio_playback,
            self.v_audio_output_buf, self.v_legacy_paste, self.v_force_adb_forward,
            self.v_camera_high_speed, self.v_kill_adb_on_close,
            # Phase 1
            self.v_render_fit, self.v_video_encoder, self.v_audio_encoder, self.v_record_format,
            self.v_capture_orientation, self.v_display_orientation,
            self.v_render_driver, self.v_window_x, self.v_window_y,
            self.v_shortcut_mod, self.v_push_target,
            # Phase 2
            self.v_window_width, self.v_window_height,
            self.v_display_ime_policy, self.v_verbosity, self.v_pause_on_exit,
            self.v_screen_off_timeout, self.v_port, self.v_tunnel_host, self.v_tunnel_port,
            self.v_angle, self.v_camera_ar, self.v_camera_size,
            # scrcpy 5.0 / 5.0.1
            self.v_hwdec, self.v_start_app_force_stop, self.v_record_orientation,
            self.v_min_size_alignment, self.v_no_mipmaps,
        ]
        for v in other_vars:
            v.trace_add("write", lambda *_: self._debounced_update())

    def _debounced_update(self):
        """Schedule UI updates with a small delay to prevent lag."""
        if self._after_update_id:
            self.after_cancel(self._after_update_id)
        self._after_update_id = self.after(100, self._perform_update)

    def _perform_update(self):
        """Execute the actual UI updates."""
        self._after_update_id = None
        self._update_ui_states()
        self._update_command()

    # ─────────────────────────────────────────────
    #  UI BUILDING — Modern Code Editor / IDE Layout
    # ─────────────────────────────────────────────
    def _build_ui(self):
        # Keyboard shortcut for quick launch
        self.bind("<Control-Return>", lambda _: self._launch())

        # 1. Top Titlebar / Run & Inspector Navigation Bar
        self._build_topbar()

        # 2. Main Workspace (Sidebar + Center Content)
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=10, pady=(6, 4))
        
        self._build_sidebar(self.workspace)
        self._build_center_workspace(self.workspace)

        # 3. Bottom Integrated Terminal / Output Panel (Collapsible)
        self._build_terminal_dock()

        # 4. Bottom Status Bar (VS Code style footer)
        self._build_statusbar()

    def _build_topbar(self):
        """Top Toolbar: Logo, Device Selector, Clean Tools Menu, and Run Button."""
        top = ctk.CTkFrame(self, fg_color=COLORS["card"], height=48, corner_radius=8, border_width=1, border_color=COLORS["border"])
        top.pack(fill="x", padx=10, pady=(8, 0))
        top.pack_propagate(False)
        
        # Left: Branding + Device Selector
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", padx=(10, 0), fill="y")
        
        ctk.CTkLabel(left, text="⚡ Scrcpy", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(left, text="GUI", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).pack(side="left", padx=(0, 10))
        
        self.lbl_dev_status = ctk.CTkLabel(left, text="🟡", font=ctk.CTkFont(size=11))
        self.lbl_dev_status.pack(side="left", padx=(0, 4))
        
        self.device_menu = ctk.CTkOptionMenu(
            left, variable=self.v_device, values=["Buscando..."],
            width=180, height=30, font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg"], button_color=COLORS["border"],
            button_hover_color=COLORS["card_hover"],
            command=self._on_device_selected
        )
        self.device_menu.pack(side="left", padx=(0, 4))
        CTooltip(self.device_menu, "Selecciona el dispositivo Android conectado para duplicar o controlar.")
        
        btn_refresh = ctk.CTkButton(
            left, text="🔄", width=30, height=30, font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=self._refresh_devices
        )
        btn_refresh.pack(side="left")
        CTooltip(btn_refresh, "Volver a buscar dispositivos USB y Wi-Fi.")

        # Center: Unified Device Tools & Displays Count (No more loose cluttered buttons!)
        mid = ctk.CTkFrame(top, fg_color="transparent")
        mid.pack(side="left", expand=True, fill="y", padx=10)
        
        self.tools_menu = ctk.CTkOptionMenu(
            mid,
            values=[
                "🛠️ Herramientas",
                "🎬 Listar Encoders",
                "📷 Listar Cámaras",
                "🖥️ Listar Pantallas",
                "⚡ Activar Modo PC (Freeform)",
            ],
            width=165, height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["bg"], button_color=COLORS["border"],
            button_hover_color=COLORS["card_hover"],
            command=self._on_tool_selected,
        )
        self.tools_menu.pack(side="left", padx=(0, 6), pady=9)
        CTooltip(self.tools_menu, "Herramientas de inspección de hardware y activación de modo escritorio en Android.")
        
        self.lbl_active_displays = ctk.CTkLabel(
            mid, text="🪟 0 abiertas",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["muted"],
        )
        self.lbl_active_displays.pack(side="left", padx=(4, 2), pady=9)

        # Right: Run Button + Updater
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=(0, 10), fill="y")
        
        self.btn_check_update = ctk.CTkButton(
            right, text="🔄", width=32, height=32,
            font=ctk.CTkFont(size=12), fg_color=COLORS["bg"],
            border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=self._check_update
        )
        self.btn_check_update.pack(side="left", padx=(0, 8), pady=8)
        CTooltip(self.btn_check_update, "Comprobar si existe una versión más reciente de scrcpy.")

        self.btn_download = ctk.CTkButton(
            right, text="⬇️ Descargar", width=110, height=32,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORS["green"],
            text_color=COLORS["bg"], hover_color="#059669",
            command=self._start_download
        )
        self.btn_download.pack(side="left", padx=(0, 8), pady=8)
        self.btn_download.pack_forget()

        self.btn_stop = ctk.CTkButton(
            right, text="⏹ Detener (0)", width=115, height=32,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORS["danger"],
            hover_color="#dc2626", corner_radius=6, command=self._stop_all_sessions
        )
        self.btn_stop.pack(side="left", padx=(0, 8), pady=8)
        self.btn_stop.pack_forget()

        self.btn_launch = ctk.CTkButton(
            right, text="▶ Iniciar Espejo", width=155, height=32,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORS["accent"],
            text_color=COLORS["bg"], hover_color=COLORS["accent_hover"], corner_radius=6,
            command=self._launch
        )
        self.btn_launch.pack(side="right", pady=8)
        CTooltip(self.btn_launch, "Iniciar scrcpy con la configuración activa. Atajo: Ctrl + Enter.")

        self.after(500, self._refresh_devices)

    def _on_tool_selected(self, choice):
        """Handle actions from the unified Topbar tools menu."""
        if "Encoders" in choice:
            self._run_inspector("--list-encoders")
        elif "Cámaras" in choice:
            self._run_inspector("--list-cameras")
        elif "Pantallas" in choice:
            self._run_inspector("--list-displays")
        elif "Modo PC" in choice:
            self._enable_pc_mode()
        if hasattr(self, "tools_menu"):
            self.tools_menu.set("🛠️ Herramientas")


    def _build_sidebar(self, parent):
        """Left Sidebar: Search, Categorized Presets, and Version Card."""
        self.sidebar_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], width=245, corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 8))
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar Header
        sb_hdr = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        sb_hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(sb_hdr, text="📁 MODOS & PERFILES", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["muted"]).pack(side="left")
        
        # Quick Search Filter
        self.sidebar_search_var = ctk.StringVar()
        self.sidebar_search_var.trace_add("write", lambda *_: self._filter_sidebar_presets())
        self.sidebar_search_entry = ctk.CTkEntry(
            self.sidebar_frame,
            textvariable=self.sidebar_search_var,
            placeholder_text="🔍 Filtrar perfil...",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg"],
            border_color=COLORS["border"],
        )
        self.sidebar_search_entry.pack(fill="x", padx=10, pady=(0, 6))

        # Presets List (Scrollable)
        self.presets_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.presets_scroll.pack(fill="both", expand=True, padx=4, pady=2)
        
        self.category_headers = {}
        for cat_id, cat_info in PRESET_CATEGORIES.items():
            hdr = ctk.CTkLabel(
                self.presets_scroll, text=cat_info["title"],
                font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"],
                anchor="w"
            )
            hdr.pack(fill="x", padx=8, pady=(8, 2))
            self.category_headers[cat_id] = hdr
            for key in cat_info["keys"]:
                if key in PRESETS:
                    p = PRESETS[key]
                    self._sidebar_item(self.presets_scroll, key, p["label"], p["badge"])
            
        # Divider
        ctk.CTkFrame(self.sidebar_frame, fg_color=COLORS["border"], height=1).pack(fill="x", padx=10, pady=4)
        
        # Custom Mode item
        self._sidebar_item(self.sidebar_frame, "custom", "⚙️ Personalizado", "Avanzado")
        
        # Divider
        ctk.CTkFrame(self.sidebar_frame, fg_color=COLORS["border"], height=1).pack(fill="x", padx=10, pady=4)
        
        # Footer Card with Scrcpy Version & Update Button
        ver_card = ctk.CTkFrame(self.sidebar_frame, fg_color=COLORS["bg"], corner_radius=6, border_width=1, border_color=COLORS["border"])
        ver_card.pack(fill="x", padx=8, pady=(0, 8))
        
        ver = mgr.get_installed_version()
        self.lbl_ver = ctk.CTkLabel(ver_card, text=f"📦 scrcpy {ver or 'no detectado'}", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["green"] if ver else COLORS["danger"])
        self.lbl_ver.pack(padx=8, pady=(6, 2), anchor="w")
        
        self.btn_sidebar_update = ctk.CTkButton(
            ver_card, text="🔍 Buscar actualización", height=24,
            font=ctk.CTkFont(size=10), fg_color=COLORS["card"],
            border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=self._check_update
        )
        self.btn_sidebar_update.pack(fill="x", padx=8, pady=(2, 6))
        
        self.dl_progress = ctk.CTkProgressBar(ver_card, progress_color=COLORS["accent"], height=4)
        self.dl_progress.set(0)
        self.dl_progress.pack(fill="x", padx=8, pady=(0, 6))
        self.dl_progress.pack_forget()

    def _filter_sidebar_presets(self):
        query = self.sidebar_search_var.get().strip().lower() if hasattr(self, "sidebar_search_var") else ""
        for key, item in self.mode_buttons.items():
            if key == "custom":
                continue
            p = PRESETS.get(key)
            if not p:
                continue
            matches = (not query) or (query in p["label"].lower()) or (query in p.get("badge", "").lower())
            if matches:
                item.pack(fill="x", pady=2, padx=4)
            else:
                item.pack_forget()
        for cat_id, hdr in getattr(self, "category_headers", {}).items():
            if query:
                hdr.pack_forget()
            else:
                keys = PRESET_CATEGORIES.get(cat_id, {}).get("keys", [])
                if keys and keys[0] in self.mode_buttons:
                    try:
                        hdr.pack(fill="x", padx=8, pady=(8, 2), before=self.mode_buttons[keys[0]])
                    except Exception:
                        hdr.pack(fill="x", padx=8, pady=(8, 2))

    def _sidebar_item(self, parent, key, label, badge):
        color = MODE_COLORS.get(key, COLORS["text"])
        item = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=6, cursor="hand2", height=34)
        item.pack(fill="x", pady=2, padx=4)
        item.pack_propagate(False)
        
        lbl = ctk.CTkLabel(item, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text"], anchor="w")
        lbl.pack(side="left", padx=(10, 4), fill="x", expand=True)
        
        bdg = ctk.CTkLabel(item, text=badge, font=ctk.CTkFont(size=10), text_color=COLORS["muted"])
        bdg.pack(side="right", padx=(0, 8))

        
        def on_click(_=None):
            self._select_mode(key)
            
        def on_enter(_=None):
            if self.active_mode.get() != key:
                item.configure(fg_color=COLORS["card_hover"])
                
        def on_leave(_=None):
            if self.active_mode.get() != key:
                item.configure(fg_color="transparent")
                
        item.bind("<Button-1>", on_click)
        lbl.bind("<Button-1>", on_click)
        bdg.bind("<Button-1>", on_click)
        item.bind("<Enter>", on_enter)
        item.bind("<Leave>", on_leave)
        
        self.mode_buttons[key] = item

    def _build_center_workspace(self, parent):
        """Center Workspace: Unified Interactive Live Dashboard (Zero-Friction UI)."""
        self.center_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.center_frame.pack(side="left", fill="both", expand=True)
        
        # 1. Main Scrollable Dashboard View
        self.preset_view = ctk.CTkScrollableFrame(self.center_frame, fg_color="transparent")
        self.preset_view.pack(fill="both", expand=True, padx=16, pady=12)
        
        # ── Header: Title, Description, Status and Reset Button ──
        hdr_frame = ctk.CTkFrame(self.preset_view, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 8))
        
        title_row = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        title_row.pack(fill="x")
        
        self.pv_title = ctk.CTkLabel(title_row, text="Modo Activo", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"], anchor="w")
        self.pv_title.pack(side="left")
        
        self.lbl_pv_badge = ctk.CTkLabel(title_row, text="✨ Perfil Activo", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"])
        self.lbl_pv_badge.pack(side="right")
        
        desc_row = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        desc_row.pack(fill="x", pady=(2, 0))
        
        self.pv_desc = ctk.CTkLabel(desc_row, text="", font=ctk.CTkFont(size=12), text_color=COLORS["text2"], anchor="w", wraplength=520, justify="left")
        self.pv_desc.pack(side="left", fill="x", expand=True)
        
        self.btn_reset_preset = ctk.CTkButton(
            desc_row, text="↺ Restablecer valores", width=140, height=26,
            font=ctk.CTkFont(size=10, weight="bold"), fg_color=COLORS["bg"],
            border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"],
            command=self._reset_current_preset_to_default
        )
        self.btn_reset_preset.pack(side="right", padx=(4, 0))
        CTooltip(self.btn_reset_preset, "Restaura los valores por defecto del perfil seleccionado.")

        # ── Bento Grid: Live Quick Controls (2 Columns) ──
        bento_grid = ctk.CTkFrame(self.preset_view, fg_color="transparent")
        bento_grid.pack(fill="x", pady=(0, 10))
        bento_grid.columnconfigure((0, 1), weight=1, uniform="bento")
        
        # Column 0: 🎬 Video & Calidad de Transmisión
        card_vid = ctk.CTkFrame(bento_grid, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        card_vid.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=2)
        
        ctk.CTkLabel(card_vid, text="🎬 Calidad de Video & Rendimiento", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=12, pady=(10, 6))
        
        ctk.CTkLabel(card_vid, text="Resolución Máxima", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(2, 0))
        res_row = ctk.CTkFrame(card_vid, fg_color="transparent")
        res_row.pack(fill="x", padx=12, pady=(2, 4))
        
        self.res_menu = ctk.CTkOptionMenu(
            res_row, variable=self.v_res_preset,
            values=["Original", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "Personalizada"],
            width=115, height=28, font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"], button_color=COLORS["border"],
            command=self._on_res_change
        )
        self.res_menu.pack(side="left", padx=(0, 4))
        self.widgets["display_res_menu"] = self.res_menu
        CTooltip(self.res_menu, "Limita la resolución de captura en Android para optimizar rendimiento o nitidez.")
        
        self.e_res_custom = ctk.CTkEntry(
            res_row, textvariable=self.v_max_size, width=70, height=28,
            font=ctk.CTkFont(size=11), fg_color=COLORS["card"], border_color=COLORS["border"],
            state="disabled"
        )
        self.e_res_custom.pack(side="left", fill="x", expand=True)
        self.widgets["display_res_entry"] = self.e_res_custom
        
        self.slider_fps = self._cfg_slider(card_vid, "Tasa FPS", self.v_fps, 15, 240, tooltip="Límite de fotogramas por segundo. 60 FPS estándar, 90-120 para juegos.")
        self.slider_bitrate = self._cfg_slider(card_vid, "Bitrate (Mbps)", self.v_bitrate, 1, 64, tooltip="Ancho de banda de compresión de video. 8-16 Mbps para 1080p.")
        self.opt_video_codec = self._cfg_option_menu(card_vid, "Códec de Video", self.v_codec, VIDEO_CODECS, tooltip="H264 (máxima compatibilidad), H265 o AV1 (mayor compresión).")
        self.widgets["render_fit"] = self._cfg_option_menu(card_vid, "Ajuste en Ventana", self.v_render_fit, RENDER_FIT_VALUES, tooltip="Modo de escalado: letterbox, fill o contain.")
        ctk.CTkFrame(card_vid, fg_color="transparent", height=6).pack()

        # Column 1: 🔊 Audio & Control UHID
        card_ctrl = ctk.CTkFrame(bento_grid, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        card_ctrl.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=2)
        
        ctk.CTkLabel(card_ctrl, text="🔊 Audio & Control por Hardware", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=12, pady=(10, 6))
        
        self.widgets["audio_switch"] = self._cfg_switch(card_ctrl, "Transmitir Audio de Android", self.v_audio, tooltip="Reenvía el audio del teléfono a los altavoces de tu PC.")
        self.widgets["audio_buf"] = self._cfg_slider(card_ctrl, "Buffer Audio (ms)", self.v_audio_buf, 0, 300, tooltip="Latencia de audio. 20-40ms para gaming, 80-120ms para estabilidad.")
        self.opt_audio_codec = self._cfg_option_menu(card_ctrl, "Códec de Audio", self.v_audio_codec, AUDIO_CODECS, tooltip="OPUS o AAC según compatibilidad de tu Android.")
        
        self.sw_uhid_kb = self._cfg_switch(card_ctrl, "Teclado UHID (Nativo)", self.v_kb_uhid, command=self._on_kb_uhid_toggle, tooltip="Emulación de teclado USB nativo sin capturar el foco de Windows.")
        self.widgets["virtual_mouse"] = self._cfg_switch(card_ctrl, "Ratón Virtual UHID", self.v_virtual_mouse, command=self._on_virtual_mouse_toggle, tooltip="Control de ratón USB nativo sin bloquear el puntero de tu PC.")
        self.widgets["no_control"] = self._cfg_switch(card_ctrl, "Solo Lectura (Mirror puro)", self.v_no_control, tooltip="Solo ver pantalla: desactiva el envío de eventos táctiles y de teclado.")
        
        self.lbl_no_control_warn = ctk.CTkLabel(
            card_ctrl,
            text="🛡️ Solo Lectura activo: Despertar y toques bloqueados automáticamente.",
            font=ctk.CTkFont(size=10), text_color=COLORS["orange"],
            wraplength=230, justify="left"
        )
        ctk.CTkFrame(card_ctrl, fg_color="transparent", height=6).pack()

        # ── Row: Session & Behavior Toggles ──
        card_session = ctk.CTkFrame(self.preset_view, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        card_session.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(card_session, text="⚡ Comportamiento de Pantalla & Ventana", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=12, pady=(10, 6))
        
        row1 = ctk.CTkFrame(card_session, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(0, 6))
        self.widgets["stay_awake"] = self._quick_sw(row1, "Mantener despierto", self.v_stay_awake, tooltip="Impide que el móvil entre en reposo.")
        self.widgets["screen_off"] = self._quick_sw(row1, "Apagar pantalla móvil", self.v_screen_off, tooltip="Apaga la pantalla física para ahorrar batería y calor.")
        self._quick_sw(row1, "Pantalla completa", self.v_fullscreen, tooltip="Inicia en pantalla completa directamente.")

        row2 = ctk.CTkFrame(card_session, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(0, 10))
        self._quick_sw(row2, "Siempre al frente", self.v_always_on_top, tooltip="Fija la ventana de scrcpy por encima de las demás.")
        self.widgets["flex_display"] = self._quick_sw(row2, "Pantalla Flex (v4.0)", self.v_flex_display, tooltip="Resolución adaptable dinámicamente al redimensionar la ventana.")
        self.widgets["touches_switch"] = self._quick_sw(row2, "Mostrar toques", self.v_show_touches, tooltip="Muestra círculos táctiles donde toques en la pantalla.")

        # ── App Selector for Virtual Display Modes ──
        self.pv_app_card = ctk.CTkFrame(self.preset_view, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.pv_app_card.pack(fill="x", pady=(0, 10))
        
        pv_app_hdr = ctk.CTkFrame(self.pv_app_card, fg_color="transparent")
        pv_app_hdr.pack(fill="x", padx=14, pady=(10, 4))
        
        ctk.CTkLabel(pv_app_hdr, text="📱 Aplicación en Pantalla Virtual:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(side="left")
        self.lbl_pv_selected_badge = ctk.CTkLabel(pv_app_hdr, text="🖥️ Escritorio Libre", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"])
        self.lbl_pv_selected_badge.pack(side="right")
        
        self.pv_inline_picker = InlineAppPicker(
            self.pv_app_card,
            on_select=self._on_app_selected,
            selected_pkg_var=self.v_virtual_display_app,
            height=130,
        )
        self.pv_inline_picker.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.widgets["v_app_picker"] = self.pv_inline_picker

        pv_opts_row = ctk.CTkFrame(self.pv_app_card, fg_color="transparent")
        pv_opts_row.pack(fill="x", padx=14, pady=(0, 10))
        self.sw_pv_force_stop = ctk.CTkSwitch(
            pv_opts_row,
            text="🔄 Forzar reinicio limpio de la app (+force-stop)",
            variable=self.v_start_app_force_stop,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text2"],
            progress_color=COLORS["accent"],
            command=self._update_command,
        )
        self.sw_pv_force_stop.pack(side="left")

        # ── Collapsible Advanced Drawer ──
        self._build_advanced_drawer()

    def _build_advanced_drawer(self):
        """Collapsible drawer containing specialized settings (Wi-Fi, Recording, 5.0, Profiles)."""
        self.btn_toggle_advanced = ctk.CTkButton(
            self.preset_view,
            text="⚙️ Más Opciones (Wi-Fi, Grabación, scrcpy 5.0, Guardar Perfil) ▼",
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text2"],
            hover_color=COLORS["card_hover"],
            command=self._toggle_advanced_drawer,
        )
        self.btn_toggle_advanced.pack(fill="x", pady=(0, 10))
        
        self.advanced_drawer_frame = ctk.CTkFrame(self.preset_view, fg_color="transparent")
        self.tabview_frame = self.advanced_drawer_frame  # Legacy reference alias
        self._advanced_drawer_open = False
        
        # Build Tabview inside advanced_drawer_frame
        self.tabview = ctk.CTkTabview(
            self.advanced_drawer_frame, anchor="nw", fg_color="transparent",
            segmented_button_fg_color=COLORS["bg"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color="#06b6d4",
            segmented_button_unselected_color=COLORS["card"],
            segmented_button_unselected_hover_color=COLORS["card_hover"],
            text_color=COLORS["bg"],
            text_color_disabled=COLORS["muted"],
        )
        self.tabview.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.tabview.add("📶 Wi-Fi")
        self.tabview.add("🔴 Grabación")
        self.tabview.add("⚡ Avanzado")
        self.tabview.add("💾 Mis Perfiles")
        self.tabview.add("🪟 Sesiones")

        self._build_tab_wifi(self.tabview.tab("📶 Wi-Fi"))
        self._build_tab_recording(self.tabview.tab("🔴 Grabación"))
        self._build_tab_advanced(self.tabview.tab("⚡ Avanzado"))
        self._build_tab_profiles(self.tabview.tab("💾 Mis Perfiles"))
        self._build_tab_sessions(self.tabview.tab("🪟 Sesiones"))

    def _toggle_advanced_drawer(self):
        if self._advanced_drawer_open:
            self._advanced_drawer_open = False
            self.advanced_drawer_frame.pack_forget()
            self.btn_toggle_advanced.configure(text="⚙️ Más Opciones (Wi-Fi, Grabación, scrcpy 5.0, Guardar Perfil) ▼")
        else:
            self._advanced_drawer_open = True
            self.advanced_drawer_frame.pack(fill="x", pady=(0, 10), before=self.btn_toggle_advanced)
            self.btn_toggle_advanced.configure(text="▲ Ocultar Opciones Avanzadas")

    def _build_tab_recording(self, tab):
        """Dedicated Recording & Capture Tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent")
        cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="rec")

        c0 = self._cfg_group(cols, "🔴 Grabación de Video", 0)
        self.widgets["record_switch"] = self._cfg_switch(c0, "Grabar sesión en video", self.v_record)
        self.widgets["record_entry"] = self._cfg_entry(c0, "Plantilla archivo", self.v_record_file)
        self.widgets["record_format"] = self._cfg_option_menu(c0, "Formato contenedor", self.v_record_format, RECORD_FORMATS)
        self.widgets["record_orientation"] = self._cfg_option_menu(c0, "Orientación de video", self.v_record_orientation, RECORD_ORIENTATION_VALUES)
        ctk.CTkLabel(c0, text="Variables: {device}, {preset}, {date}, {time}", font=ctk.CTkFont(size=9), text_color=COLORS["muted"]).pack(anchor="w", padx=12, pady=(0, 2))
        ctk.CTkButton(
            c0, text="📂 Abrir carpeta de grabaciones", height=28,
            font=ctk.CTkFont(size=11), fg_color=COLORS["card"],
            border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"],
            command=self._open_recordings_folder
        ).pack(fill="x", padx=12, pady=(4, 6))

        c1 = self._cfg_group(cols, "⏱ Opciones de Captura", 1)
        self.widgets["time_limit"] = self._cfg_slider(c1, "Tiempo límite (segundos, 0=infinito)", self.v_time_limit, 0, 600)
        self.widgets["video_buffer"] = self._cfg_slider(c1, "Video Buffer (ms)", self.v_video_buffer, 0, 500)
        self.widgets["push_target"] = self._cfg_entry(c1, "Carpeta destino Drag & Drop", self.v_push_target)
        self._cfg_switch(c1, "🛡️ Forzar ADB Forward", self.v_force_adb_forward)
        self._cfg_switch(c1, "🛑 Detener ADB al salir", self.v_kill_adb_on_close)

    def _sync_res_preset_from_size(self):
        val = str(self.v_max_size.get()).strip()
        inv_map = {
            "0": "Original",
            "3840": "2160p (4K)",
            "2560": "1440p (2K)",
            "1920": "1080p",
            "1280": "720p",
            "854": "480p"
        }
        matched = inv_map.get(val, "Personalizada")
        self.v_res_preset.set(matched)
        if hasattr(self, "res_menu"):
            self.res_menu.set(matched)
        if hasattr(self, "e_res_custom"):
            if matched == "Personalizada":
                self.e_res_custom.configure(state="normal", border_color=COLORS["accent"])
            else:
                self.e_res_custom.configure(state="disabled", border_color=COLORS["border"])

    def _reset_current_preset_to_default(self):
        """Reset current active mode to its predefined preset defaults."""
        curr = self.active_mode.get()
        if curr in PRESETS:
            p = PRESETS[curr]
            self._reset_to_defaults()
            self._apply_preset(p)
            self._sync_res_preset_from_size()
            self._log(f"↺ Valores de [{p['label']}] restablecidos a la configuración oficial.")
        else:
            self._reset_to_defaults()
            self._sync_res_preset_from_size()
            self._log("↺ Valores restablecidos a los valores por defecto.")
        self._debounced_update()

    def _sync_kb_uhid_from_keyboard(self, *args):
        is_uhid = (self.v_keyboard.get() == "uhid")
        if self.v_kb_uhid.get() != is_uhid:
            self.v_kb_uhid.set(is_uhid)

    def _on_kb_uhid_toggle(self):
        target = "uhid" if self.v_kb_uhid.get() else ""
        if self.v_keyboard.get() != target:
            self.v_keyboard.set(target)
        self._update_command()

    def _sync_virtual_mouse_from_mouse(self, *args):
        is_uhid = (self.v_mouse.get() == "uhid")
        if self.v_virtual_mouse.get() != is_uhid:
            self.v_virtual_mouse.set(is_uhid)

    def _on_virtual_mouse_toggle(self):
        target = "uhid" if self.v_virtual_mouse.get() else ""
        if self.v_mouse.get() != target:
            self.v_mouse.set(target)
        self._update_command()

    def _quick_sw(self, parent, text, var, cmd=None, tooltip=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", expand=True)
        sw = ctk.CTkSwitch(f, text=text, variable=var, font=ctk.CTkFont(size=11), text_color=COLORS["text2"], progress_color=COLORS["accent"], command=cmd or self._update_command)
        sw.pack(side="left")
        if tooltip:
            CTooltip(sw, tooltip)
        return sw

    def _select_mode(self, key):
        self.active_mode.set(key)
        for k, item in self.mode_buttons.items():
            if k == key:
                item.configure(fg_color=COLORS["card_hover"], border_width=1, border_color=MODE_COLORS.get(k, COLORS["accent"]))
            else:
                item.configure(fg_color="transparent", border_width=0)
                
        if key == "custom":
            self.pv_title.configure(text="⚙️ Configuración Maestra", text_color=COLORS["orange"])
            self.pv_desc.configure(text="Control total: ajusta resolución, audio, entrada y opciones avanzadas a tu medida.")
            self.lbl_pv_badge.configure(text="Personalizado")
            if not self._advanced_drawer_open:
                self._toggle_advanced_drawer()
        else:
            self._reset_to_defaults()
            p = PRESETS[key]
            self._apply_preset(p)
            color = MODE_COLORS.get(key, COLORS["accent"])
            self.pv_title.configure(text=p["label"], text_color=color)
            self.pv_desc.configure(text=p["desc"])
            self.lbl_pv_badge.configure(text=p.get("badge", "Preset"))
            self._sync_res_preset_from_size()
            
            # Virtual Display app card visibility
            if p.get("virtual_display") or self.v_virtual_display.get():
                self.pv_app_card.pack(fill="x", pady=(0, 10), before=self.btn_toggle_advanced)
                self._update_app_selection_ui()
            else:
                self.pv_app_card.pack_forget()

        self._sync_virtual_mouse_from_mouse()
        self._sync_kb_uhid_from_keyboard()
        self._debounced_update()

    def _update_preset_inspector(self, key, p):
        """Update active mode info and sync UI state."""
        color = MODE_COLORS.get(key, COLORS["accent"])
        if hasattr(self, "pv_title"):
            self.pv_title.configure(text=p["label"], text_color=color)
        if hasattr(self, "pv_desc"):
            self.pv_desc.configure(text=p["desc"])
        if hasattr(self, "lbl_pv_badge"):
            self.lbl_pv_badge.configure(text=p.get("badge", "Preset"))
        self._sync_res_preset_from_size()
        if p.get("virtual_display") or self.v_virtual_display.get():
            if hasattr(self, "pv_app_card"):
                self.pv_app_card.pack(fill="x", pady=(0, 10), before=self.btn_toggle_advanced)
            self._update_app_selection_ui()
        else:
            if hasattr(self, "pv_app_card"):
                self.pv_app_card.pack_forget()

    def _build_terminal_dock(self):
        """Bottom Dock: Integrated Collapsible Terminal & CLI Command Preview."""
        self._dock_expanded = False
        self.dock = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"], height=36)
        self.dock.pack(fill="x", padx=10, pady=(2, 4))
        self.dock.pack_propagate(False)
        
        # Dock Header
        dock_hdr = ctk.CTkFrame(self.dock, fg_color="transparent", height=28)
        dock_hdr.pack(fill="x", padx=10, pady=(4, 2))
        
        ctk.CTkLabel(dock_hdr, text="💻 TERMINAL", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["muted"]).pack(side="left", padx=(0, 8))
        
        # Command preview bar directly in dock header
        self.cmd_label = ctk.CTkLabel(
            dock_hdr, text="$ scrcpy",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["green"], anchor="w",
        )
        self.cmd_label.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_toggle_dock = ctk.CTkButton(
            dock_hdr, text="▲ Consola", width=78, height=22,
            font=ctk.CTkFont(size=10, weight="bold"), fg_color=COLORS["bg"],
            border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"],
            command=self._toggle_dock
        )
        self.btn_toggle_dock.pack(side="right", padx=(4, 0))
        CTooltip(self.btn_toggle_dock, "Expandir o plegar la consola de comandos de scrcpy.")

        btn_copy = ctk.CTkButton(
            dock_hdr, text="📋 Copiar", width=65, height=22,
            font=ctk.CTkFont(size=10), fg_color=COLORS["bg"],
            border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"],
            command=self._copy_command
        )
        btn_copy.pack(side="right", padx=(4, 0))
        CTooltip(btn_copy, "Copiar comando CLI actual al portapapeles.")

        self.btn_clear_log = ctk.CTkButton(
            dock_hdr, text="🗑️", width=30, height=22,
            font=ctk.CTkFont(size=10), fg_color=COLORS["bg"],
            border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"],
            command=self._clear_log
        )
        self.btn_clear_log.pack(side="right")
        CTooltip(self.btn_clear_log, "Limpiar registro de la consola.")

        # Inner text terminal box (hidden until expanded)
        self.log_box = ctk.CTkTextbox(
            self.dock, fg_color=COLORS["bg"], font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["green"], border_width=0, corner_radius=6
        )
        self.log_box.insert("end", t("ready_msg"))
        self.log_box.configure(state="disabled")

    def _toggle_dock(self):
        """Toggle terminal dock between collapsed (36px) and expanded (160px)."""
        if self._dock_expanded:
            self._collapse_dock()
        else:
            self._expand_dock()

    def _expand_dock(self):
        """Expand the terminal dock to show output log."""
        if not self._dock_expanded:
            self._dock_expanded = True
            self.dock.configure(height=160)
            self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))
            if hasattr(self, "btn_toggle_dock"):
                self.btn_toggle_dock.configure(text="▼ Ocultar")

    def _collapse_dock(self):
        """Collapse the terminal dock to header only."""
        if self._dock_expanded:
            self._dock_expanded = False
            self.log_box.pack_forget()
            self.dock.configure(height=36)
            if hasattr(self, "btn_toggle_dock"):
                self.btn_toggle_dock.configure(text="▲ Consola")

    def _build_statusbar(self):
        """VS Code style bottom status bar."""
        self.statusbar = ctk.CTkFrame(self, fg_color=COLORS["card"], height=22, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        ver = mgr.get_installed_version() or "scrcpy"
        self.sb_scrcpy = ctk.CTkLabel(self.statusbar, text=f"⚡ {ver}", font=ctk.CTkFont(size=10), text_color=COLORS["accent"])
        self.sb_scrcpy.pack(side="left", padx=10)
        
        self.sb_dev = ctk.CTkLabel(self.statusbar, text=t("no_device"), font=ctk.CTkFont(size=10), text_color=COLORS["text2"])
        self.sb_dev.pack(side="left", padx=10)
        
        ctk.CTkLabel(self.statusbar, text="UTF-8", font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(side="right", padx=10)
        ctk.CTkLabel(self.statusbar, text="ScrcpyGUI v2.0.0 (Legacy)", font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(side="right", padx=10)

    def _run_inspector(self, flag):
        """Execute a hardware query on the selected device and print results to the log."""
        dev = self.v_device.get()
        self._log(t("inspector_querying", flag=flag, dev=dev))
        
        def task():
            success, output = mgr.run_scrcpy_query(flag, dev)
            self.after(0, lambda: self._log(f"--- [Resultado {flag}] ---\n{output}\n--------------------------"))
            
        threading.Thread(target=task, daemon=True).start()

    def _enable_pc_mode(self):
        """Enable Android freeform windows and external desktop mode via ADB."""
        dev = self.v_device.get()
        self._log(t("pc_mode_activating", dev=dev))
        def task():
            success, msg = mgr.enable_desktop_freeform(dev)
            self.after(0, lambda: self._log(msg))
        threading.Thread(target=task, daemon=True).start()

    def _refresh_devices(self):
        self.device_menu.configure(values=["Buscando..."])
        self.v_device.set("Buscando...")
        if hasattr(self, "lbl_dev_status"):
            self.lbl_dev_status.configure(text="🟡")
        threading.Thread(target=self._check_adb, daemon=True).start()

    def _check_adb(self):
        # First check if ADB is available at all (avoids confusing "Sin dispositivos" when ADB is missing)
        if not mgr.is_adb_available():
            def update_no_adb():
                self.device_menu.configure(values=[t("adb_not_found_device")])
                self.v_device.set(t("adb_not_found_device"))
                self.sb_dev.configure(text=t("no_adb_found"), text_color=COLORS["danger"])
                if hasattr(self, "lbl_dev_status"):
                    self.lbl_dev_status.configure(text="🔴")
                self._log(t("no_adb_found"))
                self._filter_presets(None)
                self._update_command()
            self.after(0, update_no_adb)
            return
        devs = mgr.list_devices()
        unauthorized = mgr.get_unauthorized_count()
        def update():
            if not devs:
                self.device_menu.configure(values=["Sin dispositivos"])
                self.v_device.set("Sin dispositivos")
                self.sb_dev.configure(text="📱 Sin dispositivos", text_color=COLORS["danger"])
                if hasattr(self, "lbl_dev_status"):
                    self.lbl_dev_status.configure(text="🔴")
                if unauthorized > 0:
                    key = "unauthorized_warning_single" if unauthorized == 1 else "unauthorized_warning_plural"
                    self._log(t(key, count=unauthorized))
                self._filter_presets(None)
            else:
                vals = [f"{d[0]} ({d[1]})" for d in devs]
                self.device_menu.configure(values=vals)
                if hasattr(self, "lbl_dev_status"):
                    self.lbl_dev_status.configure(text="🟢")
                if self.v_device.get() not in vals:
                    self.v_device.set(vals[0])
                if unauthorized > 0:
                    key = "unauthorized_warning_single" if unauthorized == 1 else "unauthorized_warning_plural"
                    self._log(t(key, count=unauthorized))
                self._on_device_selected(self.v_device.get())
            self._update_command()
        self.after(0, update)


    def _on_device_selected(self, dev_str):
        """Called whenever the selected device changes to analyze its hardware capabilities.

        Uses a generation counter to discard stale scan results when the user
        switches devices faster than the background scan can complete.
        """
        if not dev_str or "Sin dispositivos" in dev_str or "Buscando" in dev_str:
            self._current_device_caps = None
            self._filter_presets(None)
            return
            
        serial = dev_str.split(" (")[0].strip()
        if not serial:
            return
            
        if serial in self._device_caps_cache:
            self._apply_device_capabilities(self._device_caps_cache[serial])
            return

        self._scan_generation += 1
        gen = self._scan_generation

        self._log(f"🔍 Escaneando capacidades de hardware de {dev_str}...")
        self.sb_dev.configure(text=f"🔍 Analizando {dev_str}...", text_color=COLORS["orange"])
        
        # Disable launch button while scanning to prevent launching with incomplete hardware info
        if hasattr(self, "btn_launch"):
            self.btn_launch.configure(state="disabled", text=t("scanning_hw_start"))
        
        def task():
            caps = mgr.scan_device_capabilities(serial)
            self._device_caps_cache[serial] = caps
            self.after(0, lambda: self._apply_scan_result(gen, caps))
            
        threading.Thread(target=task, daemon=True).start()

    def _apply_scan_result(self, gen, caps):
        """Apply device capabilities only if the scan is still current."""
        if gen != self._scan_generation:
            return  # Stale scan — user already switched device
        self._apply_device_capabilities(caps)

    def _filter_presets(self, caps=None):
        """Show only presets that are fully compatible with the connected device hardware."""
        if not hasattr(self, "mode_buttons"):
            return

        if not caps:
            # Re-pack all presets in definition order when no device is selected
            for key in PRESETS.keys():
                item = self.mode_buttons.get(key)
                if item:
                    item.pack(fill="x", pady=2, padx=4)
            return

        v_codecs = set(caps.get("video_codecs", VIDEO_CODECS))
        a_codecs = set(caps.get("audio_codecs", AUDIO_CODECS))
        supports_vd = caps.get("supports_virtual_display", True)

        visible_keys = []
        hidden_keys = []

        # Unpack all preset buttons first to maintain strict visual ordering
        for key in PRESETS.keys():
            item = self.mode_buttons.get(key)
            if item:
                item.pack_forget()

        # Pack only compatible items in defined sequence
        for key, p in PRESETS.items():
            item = self.mode_buttons.get(key)
            if not item:
                continue

            req_v_codec = p.get("codec", "h264")
            req_a_codec = p.get("audio_codec", "opus")
            requires_vd = p.get("virtual_display", False)

            is_compat = True
            reason = ""

            if req_v_codec and req_v_codec not in v_codecs:
                is_compat = False
                reason = f"Códec de video {req_v_codec.upper()} no soportado por este móvil"
            elif requires_vd and not supports_vd:
                is_compat = False
                reason = "Requiere Android 10+ para pantallas virtuales"
            elif p.get("audio") and req_a_codec and req_a_codec not in a_codecs:
                is_compat = False
                reason = f"Códec de audio {req_a_codec.upper()} no soportado"

            if is_compat:
                item.pack(fill="x", pady=2, padx=4)
                visible_keys.append(key)
            else:
                hidden_keys.append((p.get("label", key), reason))

        if hidden_keys:
            self._log(t("preset_hidden", count=len(hidden_keys)))
            for lbl, r in hidden_keys:
                self._log(t("preset_hidden_item", label=lbl, reason=r))

        # If current active mode is incompatible / hidden, switch to the first compatible preset
        curr = self.active_mode.get()
        if curr in PRESETS and curr not in visible_keys:
            fallback = "desktop" if "desktop" in visible_keys else (visible_keys[0] if visible_keys else "custom")
            self._log(t("preset_fallback", mode=curr, fallback=fallback))
            self._select_mode(fallback)

    def _apply_device_capabilities(self, caps):
        """Adapt the UI options and presets based on the device's real hardware support."""
        self._current_device_caps = caps
        
        # 1. Update status bar
        brand = caps.get("brand", "")
        model = caps.get("model", "Android")
        ver = caps.get("android_version", "14")
        self.sb_dev.configure(text=f"📱 {brand} {model} (Android {ver})", text_color=COLORS["green"])
        
        # 2. Update Video Codecs menu with ONLY supported codecs
        v_codecs = caps.get("video_codecs", VIDEO_CODECS)
        if hasattr(self, "opt_video_codec") and self.opt_video_codec:
            self.opt_video_codec.configure(values=v_codecs)
        if self.v_codec.get() not in v_codecs:
            self.v_codec.set(v_codecs[0] if v_codecs else "h264")
            
        # 3. Update Audio Codecs menu with ONLY supported codecs
        a_codecs = caps.get("audio_codecs", AUDIO_CODECS)
        if hasattr(self, "opt_audio_codec") and self.opt_audio_codec:
            self.opt_audio_codec.configure(values=a_codecs)
        if self.v_audio_codec.get() not in a_codecs:
            self.v_audio_codec.set(a_codecs[0] if a_codecs else "opus")
            
        # 4. Filter and hide incompatible sidebar presets
        self._filter_presets(caps)
            
        # 5. Log Summary in terminal
        v_str = ", ".join(c.upper() for c in v_codecs)
        a_str = ", ".join(c.upper() for c in a_codecs)
        num_cams = len(caps.get("cameras", []))
        num_dsps = len(caps.get("displays", []))
        self._log(f"✅ {brand} {model} (Android {ver}) analizado:")
        self._log(f"   🎬 Códecs Video compatibles: [{v_str}]")
        self._log(f"   🔊 Códecs Audio compatibles: [{a_str}]")
        self._log(f"   📷 Cámaras: {num_cams} | 🖥️ Pantallas: {num_dsps}")
        
        # 6. Adapt active preset if current preset requires an unsupported codec
        curr_mode = self.active_mode.get()
        if curr_mode in PRESETS:
            p_codec = PRESETS[curr_mode].get("codec", "h264")
            if p_codec not in v_codecs:
                self.v_codec.set("h264")
                self._log(f"ℹ️ Códec {p_codec.upper()} no soportado por este móvil, adaptado automáticamente a H264.")
                
        # 7. Fetch apps for inline picker
        self._load_device_apps(caps.get("serial", ""))

        # 8. Update command
        self._update_command()

        # 9. Re-enable launch button now that hardware scan is complete
        if hasattr(self, "btn_launch"):
            self.btn_launch.configure(state="normal", text="▶ Iniciar Scrcpy")

    def _check_update(self):
        self._log(t("checking_updates"))
        if hasattr(self, "btn_check_update"):
            self.btn_check_update.configure(state="disabled", text="Buscando...")
        mgr.check_latest(self._on_check_result)

    def _on_check_result(self, tag, url, err):
        def update():
            if hasattr(self, "btn_check_update"):
                self.btn_check_update.configure(state="normal", text="🔄 Actualizar")
            if err:
                self._log(t("update_error", err=err))
                return
            installed = mgr.get_installed_version()
            self._latest_tag, self._latest_url = tag, url
            if installed == tag:
                self._log(t("latest_version", tag=tag))
                if hasattr(self, "btn_check_update"):
                    self.btn_check_update.configure(text="✅ Al día")
                if hasattr(self, "lbl_ver"):
                    self.lbl_ver.configure(text=f"📦 scrcpy {tag} (al día)", text_color=COLORS["green"])
            else:
                self._log(t("new_version_available", tag=tag, installed=installed or 'ninguna'))
                if hasattr(self, "btn_download"):
                    self.btn_download.configure(text=f"⬇️ Descargar {tag}")
                    self.btn_download.pack(side="left", padx=(0, 8), before=self.btn_launch)
                if hasattr(self, "btn_sidebar_update"):
                    self.btn_sidebar_update.configure(text=f"⬇️ Descargar {tag}", fg_color=COLORS["green"], text_color=COLORS["bg"], command=self._start_download)
                if hasattr(self, "lbl_ver"):
                    self.lbl_ver.configure(text=f"🆕 scrcpy {tag} disponible", text_color=COLORS["accent"])
        self.after(0, update)

    def _start_download(self):
        url, tag = getattr(self, "_latest_url", ""), getattr(self, "_latest_tag", "")
        if not url:
            self._check_update()
            return
        if hasattr(self, "btn_download"):
            self.btn_download.configure(state="disabled", text="Descargando...")
        if hasattr(self, "btn_sidebar_update"):
            self.btn_sidebar_update.configure(state="disabled", text="Descargando...")
        if hasattr(self, "dl_progress"):
            self.dl_progress.set(0)
            self.dl_progress.pack(fill="x", padx=8, pady=(0, 6))
        self._log(t("downloading", tag=tag))
        
        def on_progress(p):
            if p < 0:
                self.after(0, lambda: self._log(t("extracting_files")))
            else:
                if hasattr(self, "dl_progress"):
                    self.after(0, lambda: self.dl_progress.set(p))
                
        def on_done(err):
            def finish():
                if hasattr(self, "dl_progress"):
                    self.dl_progress.pack_forget()
                if err:
                    self._log(t("download_error", err=err))
                    if hasattr(self, "btn_download"):
                        self.btn_download.configure(state="normal", text="⬇️ Reintentar")
                    if hasattr(self, "btn_sidebar_update"):
                        self.btn_sidebar_update.configure(state="normal", text="⬇️ Reintentar")
                else:
                    mgr._save_version(tag, url)
                    self._scrcpy_path_cache = mgr.get_scrcpy_path()
                    if hasattr(self, "sb_scrcpy"):
                        self.sb_scrcpy.configure(text=f"⚡ scrcpy {tag}")
                    if hasattr(self, "lbl_ver"):
                        self.lbl_ver.configure(text=f"📦 scrcpy {tag} (instalado)", text_color=COLORS["green"])
                    if hasattr(self, "btn_download"):
                        self.btn_download.pack_forget()
                    if hasattr(self, "btn_sidebar_update"):
                        self.btn_sidebar_update.configure(state="normal", text="🔍 Buscar actualización", fg_color=COLORS["card"], text_color=COLORS["text"], command=self._check_update)
                    self._log(t("download_success", tag=tag, path=mgr.SCRCPY_DIR))
                    self._update_command()
            self.after(0, finish)
            
        mgr.download_and_install(url, progress_cb=on_progress, done_cb=on_done)

    def _reset_to_defaults(self):
        """Reset all configuration variables to their default values."""
        self.v_video_source.set("display")
        self.v_codec.set("h264")
        self.v_res_preset.set("1080p")
        self.v_max_size.set("1920")
        self.v_fps.set(60)
        self.v_bitrate.set(8)
        self.v_audio.set(True)
        self.v_audio_buf.set(50)
        self.v_video_buffer.set(0)
        self.v_fullscreen.set(False)
        self.v_stay_awake.set(True)
        self.v_screen_off.set(False)
        self.v_keyboard.set("")
        self.v_mouse.set("")
        self.v_virtual_mouse.set(False)
        self.v_gamepad.set("")
        self.v_record.set(False)
        self.v_record_file.set("recording.mp4")
        self.v_print_fps.set(False)
        self.v_show_touches.set(False)
        self.v_crop.set("")
        self.v_audio_source.set("output")
        self.v_audio_codec.set("opus")
        self.v_always_on_top.set(False)
        self.v_borderless.set(False)
        self.v_virtual_display.set(False)
        self.v_virtual_display_res.set("1280x720")
        self.v_virtual_res_preset.set("1280x720")
        self.v_virtual_display_app.set("")
        self.v_camera_id.set("0")
        self.v_camera_facing.set("")
        self.v_camera_fps.set(30)
        self.v_display_id.set("0")
        self.v_orientation.set("0")
        self.v_no_video.set(False)
        self.v_no_control.set(False)
        self.v_audio_dup.set(False)
        self.v_audio_bitrate.set(128)
        self.v_disable_screensaver.set(False)
        self.v_time_limit.set(0)
        self.v_no_vd_decorations.set(False)
        self.v_no_vd_destroy.set(False)
        self.v_virtual_dpi.set("")
        self.v_no_clipboard_sync.set(False)
        self.v_flex_display.set(False)
        self.v_camera_torch.set(False)
        self.v_camera_zoom.set("")
        self.v_keep_active.set(False)
        self.v_background_color.set("")
        self.v_no_aspect_ratio_lock.set(False)
        self.v_otg_mode.set(False)
        self.v_ignore_encoder_constraints.set(False)
        self.v_no_audio_playback.set(False)
        self.v_no_playback.set(False)
        self.v_audio_output_buf.set(0)
        self.v_legacy_paste.set(False)
        self.v_force_adb_forward.set(False)
        self.v_camera_high_speed.set(False)
        self.v_kill_adb_on_close.set(False)
        # Phase 1 & Phase 2
        self.v_render_fit.set("")
        self.v_no_video_playback.set(False)
        self.v_video_encoder.set("")
        self.v_audio_encoder.set("")
        self.v_record_format.set("")
        self.v_require_audio.set(False)
        self.v_capture_orientation.set("0")
        self.v_display_orientation.set("0")
        self.v_render_driver.set("")
        self.v_window_x.set("")
        self.v_window_y.set("")
        self.v_power_off_on_close.set(False)
        self.v_no_power_on.set(False)
        self.v_shortcut_mod.set("")
        self.v_push_target.set("")
        self.v_window_width.set("")
        self.v_window_height.set("")
        self.v_no_window.set(False)
        self.v_display_ime_policy.set("")
        self.v_verbosity.set("")
        self.v_pause_on_exit.set("")
        self.v_no_cleanup.set(False)
        self.v_no_downsize_on_error.set(False)
        self.v_screen_off_timeout.set(0)
        self.v_no_key_repeat.set(False)
        self.v_prefer_text.set(False)
        self.v_raw_key_events.set(False)
        self.v_no_mouse_hover.set(False)
        self.v_port.set("")
        self.v_tunnel_host.set("")
        self.v_tunnel_port.set("")
        self.v_no_terminal_title.set(False)
        self.v_angle.set(0)
        self.v_camera_ar.set("")
        self.v_camera_size.set("")
        # scrcpy 5.0 / 5.0.1
        self.v_hwdec.set("")
        self.v_start_app_force_stop.set(False)
        self.v_record_orientation.set("")
        self.v_min_size_alignment.set("")
        self.v_no_mipmaps.set(False)
        
        # Sync UI components that don't auto-update from trace
        if hasattr(self, "res_menu"): self.res_menu.set("1080p")
        if hasattr(self, "virtual_res_menu"): self.virtual_res_menu.set("1280x720")
        if hasattr(self, "app_menu"): self.app_menu.set("Ninguna")
        self._update_command()

    def _apply_preset(self, p):
        """Apply a preset dict to all GUI variables. Uses .get() with safe defaults."""
        self.v_codec.set(p.get("codec", "h264"))
        self.v_max_size.set(str(p.get("max_size", 1920)))
        self.v_fps.set(p.get("fps", 60))
        self.v_bitrate.set(p.get("bitrate", 8))
        self.v_audio.set(p.get("audio", True))
        self.v_audio_buf.set(p.get("audio_buffer", 50))
        self.v_video_buffer.set(p.get("video_buffer", 0))
        self.v_fullscreen.set(p.get("fullscreen", False))
        self.v_stay_awake.set(p.get("stay_awake", True))
        self.v_screen_off.set(p.get("screen_off", False))
        self.v_keyboard.set(p.get("keyboard", ""))
        self.v_mouse.set(p.get("mouse", ""))
        self.v_virtual_mouse.set(bool(p.get("virtual_mouse", p.get("mouse") == "uhid")))
        self.v_gamepad.set("uhid" if p.get("gamepad") else "")
        self.v_record.set(p.get("record", False))
        self.v_print_fps.set(p.get("print_fps", False))
        self.v_show_touches.set(p.get("show_touches", False))
        self.v_crop.set(p.get("crop", ""))

        # Dynamically apply all matching v_<key> variables from preset
        for key, val in p.items():
            if key in ("label", "desc", "badge", "gamepad", "audio_buffer"):
                continue
            var = getattr(self, f"v_{key}", None)
            if var is not None:
                try:
                    var.set(val)
                except Exception:
                    pass

    # ─────────────────────────────────────────────
    #  TABVIEW — Property Editor for Custom Mode
    # ─────────────────────────────────────────────
    def _build_tabview(self):
        self.tabview_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        # Don't pack yet — only shown when "Personalizado" is selected

        self.tabview = ctk.CTkTabview(self.tabview_frame, anchor="nw", fg_color="transparent",
                                       segmented_button_fg_color=COLORS["bg"],
                                       segmented_button_selected_color=COLORS["accent"],
                                       segmented_button_selected_hover_color="#06b6d4",
                                       segmented_button_unselected_color=COLORS["card"],
                                       segmented_button_unselected_hover_color=COLORS["card_hover"],
                                       text_color=COLORS["bg"],
                                       text_color_disabled=COLORS["muted"])
        self.tabview.pack(fill="both", expand=True, padx=8, pady=4)

        # Create tabs
        self.tabview.add("🎥 Video")
        self.tabview.add("🔊 Audio")
        self.tabview.add("🖥️ Pantalla")
        self.tabview.add("🎛️ Controles")
        self.tabview.add("⚡ Avanzado")
        self.tabview.add("🪟 Pantallas Activas")
        self.tabview.add("📶 Wi-Fi")
        self.tabview.add("💾 Perfiles")

        self._build_tab_video(self.tabview.tab("🎥 Video"))
        self._build_tab_audio(self.tabview.tab("🔊 Audio"))
        self._build_tab_display(self.tabview.tab("🖥️ Pantalla"))
        self._build_tab_controls(self.tabview.tab("🎛️ Controles"))
        self._build_tab_advanced(self.tabview.tab("⚡ Avanzado"))
        self._build_tab_sessions(self.tabview.tab("🪟 Pantallas Activas"))
        self._build_tab_wifi(self.tabview.tab("📶 Wi-Fi"))
        self._build_tab_profiles(self.tabview.tab("💾 Perfiles"))

    def _build_tab_video(self, tab):
        """Video and Camera settings tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent")
        cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="vid")

        # Left column: Video
        c0 = self._cfg_group(cols, "🎬 Video", 0)
        self._cfg_option_menu(c0, "Fuente Video", self.v_video_source, ["display", "camera"])
        self.opt_video_codec = self._cfg_option_menu(c0, "Códec", self.v_codec, VIDEO_CODECS)
        self.widgets["orientation"] = self._cfg_option_menu(c0, "Orientación", self.v_orientation, ORIENTATION_VALUES)
        
        # Resolution
        ctk.CTkLabel(c0, text="Resolución Máxima", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        res_row = ctk.CTkFrame(c0, fg_color="transparent")
        res_row.pack(fill="x", padx=12, pady=(2, 4))
        self.res_menu = ctk.CTkOptionMenu(res_row, variable=self.v_res_preset, values=["Original", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "Personalizada"], width=100, fg_color=COLORS["card"], button_color=COLORS["border"], command=self._on_res_change)
        self.res_menu.pack(side="left", padx=(12, 5))
        self.widgets["display_res_menu"] = self.res_menu
        self.e_res_custom = ctk.CTkEntry(res_row, textvariable=self.v_max_size, width=70, fg_color=COLORS["card"], border_color=COLORS["border"], state="disabled")
        self.e_res_custom.pack(side="left", padx=(0, 12), fill="x", expand=True)
        self.widgets["display_res_entry"] = self.e_res_custom
        
        self._cfg_slider(c0, "FPS", self.v_fps, 15, 240)
        self._cfg_slider(c0, "Bitrate (Mbps)", self.v_bitrate, 1, 64)
        self.widgets["ignore_encoder_constraints"] = self._cfg_switch(c0, "⚡ Ignorar límites encoder", self.v_ignore_encoder_constraints)
        # Video encoder & render options
        self.widgets["video_encoder"] = self._cfg_entry(c0, "📦 Encoder específico", self.v_video_encoder)
        self.widgets["render_fit"] = self._cfg_option_menu(c0, "🖼️ Ajuste pantalla", self.v_render_fit, RENDER_FIT_VALUES)
        self.widgets["hwdec"] = self._cfg_option_menu(c0, "⚡ Decodificación GPU PC (5.0)", self.v_hwdec, HWDEC_MODES)
        self.widgets["no_video_playback"] = self._cfg_switch(c0, "💻 Sin reproducción local", self.v_no_video_playback)

        # Right column: Camera
        c1 = self._cfg_group(cols, "📷 Cámara", 1)
        self.widgets["camera_id"] = self._cfg_entry(c1, "Cámara ID", self.v_camera_id)
        self.widgets["camera_facing"] = self._cfg_option_menu(c1, "Cámara Cara", self.v_camera_facing, CAMERA_FACING)
        self.widgets["camera_ar"] = self._cfg_option_menu(c1, "Aspect Ratio Cámara", self.v_camera_ar, CAMERA_AR_VALUES)
        self.widgets["camera_size"] = self._cfg_entry(c1, "Resolución Cámara (WxH)", self.v_camera_size)
        self.widgets["camera_fps"] = self._cfg_slider(c1, "Cámara FPS", self.v_camera_fps, 15, 240)
        self.widgets["camera_torch"] = self._cfg_switch(c1, "🔦 Flash de Cámara", self.v_camera_torch)
        self.widgets["camera_high_speed"] = self._cfg_switch(c1, "🚀 High-Speed (120fps+)", self.v_camera_high_speed)
        self.widgets["camera_zoom"] = self._cfg_entry(c1, "Zoom de Cámara", self.v_camera_zoom)
        self.widgets["crop_entry"] = self._cfg_entry(c1, "Crop (WxH:X:Y)", self.v_crop)
        self.widgets["no_video"] = self._cfg_switch(c1, "🚫 Sin video", self.v_no_video)

    def _build_tab_audio(self, tab):
        """Audio settings tab with 2-column balanced layout."""
        cols = ctk.CTkFrame(tab, fg_color="transparent")
        cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="aud")

        # Left: General Audio
        c0 = self._cfg_group(cols, "🔊 Captura de Audio", 0)
        self.widgets["audio_switch"] = self._cfg_switch(c0, "Audio activado", self.v_audio)
        self.widgets["audio_source"] = self._cfg_option_menu(c0, "Fuente Audio", self.v_audio_source, AUDIO_SOURCES)
        self.opt_audio_codec = self._cfg_option_menu(c0, "Codec Audio", self.v_audio_codec, AUDIO_CODECS)
        self.widgets["audio_bitrate"] = self._cfg_slider(c0, "Audio Bitrate (K)", self.v_audio_bitrate, 32, 320)
        self.widgets["require_audio"] = self._cfg_switch(c0, "⚠️ Exigir audio (no silenciar)", self.v_require_audio)

        # Right: Buffers & Output
        c1 = self._cfg_group(cols, "🎛️ Buffers & Reproducción", 1)
        self.widgets["audio_buf"] = self._cfg_slider(c1, "Buffer captura (ms)", self.v_audio_buf, 0, 500)
        self.widgets["audio_output_buf"] = self._cfg_slider(c1, "Buffer salida PC (ms)", self.v_audio_output_buf, 0, 500)
        self.widgets["audio_dup"] = self._cfg_switch(c1, "🔊 Duplicar audio (PC + Móvil)", self.v_audio_dup)
        self.widgets["no_audio_playback"] = self._cfg_switch(c1, "🚫 Sin audio local (Solo capturar)", self.v_no_audio_playback)
        self.widgets["audio_encoder"] = self._cfg_entry(c1, "Encoder de audio", self.v_audio_encoder)

    def _build_tab_display(self, tab):
        """Display, Virtual Display, and Window settings tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent"); cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="dsp")

        # Left: Window
        c0 = self._cfg_group(cols, "🪟 Ventana", 0)
        self._cfg_switch(c0, "Pantalla completa", self.v_fullscreen)
        self._cfg_switch(c0, "Siempre al frente", self.v_always_on_top)
        self._cfg_switch(c0, "Sin bordes", self.v_borderless)
        self._cfg_switch(c0, "🚫 Sin ventana video", self.v_no_playback)
        self._cfg_entry(c0, "Color Fondo (Hex)", self.v_background_color)
        self._cfg_switch(c0, "Sin Aspect Ratio Lock", self.v_no_aspect_ratio_lock)
        self.widgets["render_driver"] = self._cfg_option_menu(c0, "Driver Render", self.v_render_driver, RENDER_DRIVER_VALUES)
        self.widgets["capture_orientation"] = self._cfg_option_menu(c0, "Orientación Captura", self.v_capture_orientation, CAPTURE_ORIENTATION_VALUES)
        self.widgets["display_orientation"] = self._cfg_option_menu(c0, "Orientación Pantalla", self.v_display_orientation, DISPLAY_ORIENTATION_VALUES)

        # Window initial position
        _wpos_lbl = ctk.CTkLabel(c0, text="Posición inicial (X / Y)", font=ctk.CTkFont(size=11), text_color=COLORS["text2"])
        _wpos_lbl.pack(anchor="w", padx=12, pady=(6, 0))
        _wpos_row = ctk.CTkFrame(c0, fg_color="transparent")
        _wpos_row.pack(fill="x", padx=12, pady=(2, 4))
        ctk.CTkEntry(_wpos_row, textvariable=self.v_window_x, placeholder_text="X", width=70, fg_color=COLORS["card"], border_color=COLORS["border"]).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(_wpos_row, textvariable=self.v_window_y, placeholder_text="Y", width=70, fg_color=COLORS["card"], border_color=COLORS["border"]).pack(side="left")

        self.widgets["disable_screensaver"] = self._cfg_switch(c0, "🛡️ Desactivar screensaver", self.v_disable_screensaver)
        self.widgets["display_id"] = self._cfg_entry(c0, "Display ID (0=Principal)", self.v_display_id)

        # Quick settings inside display tab
        self.widgets["screen_off"] = self._cfg_switch(c0, "📱 Apagar pantalla", self.v_screen_off, tooltip="Apaga la pantalla física del móvil.")
        self.widgets["stay_awake"] = self._cfg_switch(c0, "💡 Mantener despierto", self.v_stay_awake, tooltip="Evita que el móvil entre en reposo.")


        # Right: Virtual Display
        c1 = self._cfg_group(cols, "🖥️ Pantalla Virtual", 1)
        self.widgets["v_display_switch"] = self._cfg_switch(c1, "🖥️ Nueva Pantalla Virtual", self.v_virtual_display)
        self.widgets["flex_display"] = self._cfg_switch(c1, "📐 Pantalla Flex (v4.0)", self.v_flex_display)

        # Virtual Resolution
        ctk.CTkLabel(c1, text="Resolución Virtual", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        v_res_row = ctk.CTkFrame(c1, fg_color="transparent")
        v_res_row.pack(fill="x", padx=12, pady=(2, 4))
        self.virtual_res_menu = ctk.CTkOptionMenu(v_res_row, variable=self.v_virtual_res_preset, values=VIRTUAL_RES_PRESETS, width=100, fg_color=COLORS["card"], button_color=COLORS["border"], command=self._on_v_res_change)
        self.virtual_res_menu.pack(side="left", padx=(0, 5))
        self.widgets["v_res_menu"] = self.virtual_res_menu
        self.e_v_res_custom = ctk.CTkEntry(v_res_row, textvariable=self.v_virtual_display_res, width=70, fg_color=COLORS["card"], border_color=COLORS["border"], state="disabled")
        self.e_v_res_custom.pack(side="left", fill="x", expand=True)
        self.widgets["v_res_entry"] = self.e_v_res_custom

        # App selector
        ctk.CTkLabel(c1, text="🚀 App en Pantalla Virtual (Auto-arranque)", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 2))
        self.tab_inline_picker = InlineAppPicker(
            c1,
            on_select=self._on_app_selected,
            selected_pkg_var=self.v_virtual_display_app,
            height=110,
        )
        self.tab_inline_picker.pack(fill="x", padx=12, pady=(0, 6))
        self.widgets["v_app_picker"] = self.tab_inline_picker
        self.widgets["v_force_stop"] = self._cfg_switch(c1, "🔄 Reiniciar app limpia (+force-stop)", self.v_start_app_force_stop)

        self.v_virtual_display_res.set("1280x720")
        self.widgets["vd_dpi"] = self._cfg_entry(c1, "DPI Virtual Display", self.v_virtual_dpi)
        self.widgets["vd_no_decorations"] = self._cfg_switch(c1, "Sin decoraciones VD", self.v_no_vd_decorations)
        self.widgets["vd_no_destroy"] = self._cfg_switch(c1, "Conservar apps al cerrar", self.v_no_vd_destroy)

        if not False:  # IS_WINDOWS placeholder, runtime check below
            pass  # v4l2 moved to Advanced tab

    def _build_tab_controls(self, tab):
        """Controls and Recording tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent"); cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="ctrl")

        c0 = self._cfg_group(cols, "🕹️ Controles de Entrada", 0)
        self.widgets["kb_menu"] = self._cfg_option_menu(c0, "Teclado", self.v_keyboard, KEYBOARD_MODES)
        self.widgets["mouse_menu"] = self._cfg_option_menu(c0, "Ratón", self.v_mouse, MOUSE_MODES)
        self.widgets["gamepad_menu"] = self._cfg_option_menu(c0, "Gamepad", self.v_gamepad, GAMEPAD_MODES)
        self.widgets["no_control"] = self._cfg_switch(c0, "🚧 Solo lectura", self.v_no_control)
        self.widgets["otg_mode"] = self._cfg_switch(c0, "🔌 Modo OTG (Hardware)", self.v_otg_mode)
        self.widgets["keep_active"] = self._cfg_switch(c0, "🔥 Mantener Activo (v4.0)", self.v_keep_active)
        self.widgets["legacy_paste"] = self._cfg_switch(c0, "📋 Pegado legacy", self.v_legacy_paste)
        self.widgets["no_clipboard"] = self._cfg_switch(c0, "🚧 Sin clipboard sync", self.v_no_clipboard_sync)
        self.widgets["touches_switch"] = self._cfg_switch(c0, "Mostrar toques", self.v_show_touches)
        self._cfg_switch(c0, "📊 Mostrar FPS", self.v_print_fps)
        # Power management
        self.widgets["power_off_on_close"] = self._cfg_switch(c0, "⏻ Apagar pantalla al cerrar", self.v_power_off_on_close)
        self.widgets["no_power_on"] = self._cfg_switch(c0, "🔌 No encender al iniciar", self.v_no_power_on)
        # Shortcut mod
        self.widgets["shortcut_mod"] = self._cfg_entry(c0, "Modificador atajos (MOD)", self.v_shortcut_mod)

        c1 = self._cfg_group(cols, "🔴 Grabación & Conexión", 1)
        self.widgets["record_switch"] = self._cfg_switch(c1, "🔴 Grabar sesión", self.v_record)
        self.widgets["record_entry"] = self._cfg_entry(c1, "Archivo rec", self.v_record_file)
        self.widgets["record_format"] = self._cfg_option_menu(c1, "Formato Grabación", self.v_record_format, RECORD_FORMATS)
        self.widgets["record_orientation"] = self._cfg_option_menu(c1, "📐 Orientación Grabación", self.v_record_orientation, RECORD_ORIENTATION_VALUES)
        ctk.CTkLabel(c1, text="Variables: {device}, {preset}, {date}, {time}", font=ctk.CTkFont(size=9), text_color=COLORS["muted"]).pack(anchor="w", padx=12, pady=(0, 2))
        ctk.CTkButton(
            c1, text="📂 Abrir carpeta de grabaciones", height=26,
            font=ctk.CTkFont(size=10), fg_color=COLORS["card"],
            border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"],
            command=self._open_recordings_folder
        ).pack(fill="x", padx=12, pady=(0, 4))
        self.widgets["time_limit"] = self._cfg_slider(c1, "⏱ Tiempo límite (s)", self.v_time_limit, 0, 600)
        self.widgets["video_buffer"] = self._cfg_slider(c1, "Video Buffer (ms)", self.v_video_buffer, 0, 500)
        self._cfg_switch(c1, "🛡️ Forzar ADB Forward", self.v_force_adb_forward)
        self._cfg_switch(c1, "🛑 Detener ADB al salir", self.v_kill_adb_on_close)
        # Drag & Drop target
        self.widgets["push_target"] = self._cfg_entry(c1, "Carpeta destino D&D", self.v_push_target)

    def _build_tab_wifi(self, tab):
        """Wi-Fi / Wireless connection tab in 2-column balanced layout."""
        cols = ctk.CTkFrame(tab, fg_color="transparent")
        cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="wifi")

        # Left Column: Connect
        c0 = self._cfg_group(cols, "📶 Conexión Directa (TCP/IP)", 0)
        ctk.CTkLabel(c0, text="Dirección IP y Puerto:", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 2))
        self.e_wifi_ip = ctk.CTkEntry(c0, placeholder_text="192.168.1.10:5555", textvariable=self.v_wifi_ip, height=34, font=ctk.CTkFont(size=12))
        self.e_wifi_ip.pack(fill="x", padx=12, pady=(0, 10))
        
        btn_row = ctk.CTkFrame(c0, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(btn_row, text="🔗 Conectar", height=32, fg_color=COLORS["accent"], text_color=COLORS["bg"], font=ctk.CTkFont(size=12, weight="bold"), command=self._wifi_connect).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="⚡ Auto-USB", height=32, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=11), command=self._wifi_enable_tcpip).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Right Column: Pairing
        c1 = self._cfg_group(cols, "🔐 Emparejamiento (Android 11+)", 1)
        ctk.CTkLabel(c1, text="Código de Emparejamiento:", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 2))
        self.e_wifi_code = ctk.CTkEntry(c1, placeholder_text="Código de 6 dígitos", textvariable=self.v_wifi_pair_code, height=34, font=ctk.CTkFont(size=12))
        self.e_wifi_code.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(c1, text="🔑 Validar Código", height=32, fg_color=COLORS["purple"], font=ctk.CTkFont(size=12, weight="bold"), command=self._wifi_pair).pack(fill="x", padx=12, pady=(0, 10))

    def _build_tab_profiles(self, tab):
        """User profiles tab — save, load, and delete configurations."""
        cols = ctk.CTkFrame(tab, fg_color="transparent")
        cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="prof")

        # Left Column: Save
        c0 = self._cfg_group(cols, "💾 Guardar Perfil Actual", 0)
        ctk.CTkLabel(c0, text="Nombre del Perfil:", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 2))
        self.v_profile_name = ctk.StringVar(value="")
        ctk.CTkEntry(c0, textvariable=self.v_profile_name, placeholder_text="Ej: Gaming 120Hz HyperOS", height=34, font=ctk.CTkFont(size=12)).pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(c0, text="💾 Guardar Configuración", height=32, fg_color=COLORS["green"], text_color=COLORS["bg"], font=ctk.CTkFont(size=12, weight="bold"), command=self._save_profile).pack(fill="x", padx=12, pady=(0, 10))

        # Right Column: List
        c1 = self._cfg_group(cols, "📂 Perfiles Guardados", 1)
        self.profiles_list_frame = ctk.CTkScrollableFrame(c1, fg_color="transparent", height=140)
        self.profiles_list_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self._refresh_profiles_list()

        # Bottom: History
        hist_box = self._cfg_group_full(tab, t("history_title"))
        self.history_list_frame = ctk.CTkScrollableFrame(hist_box, fg_color="transparent", height=130)
        self.history_list_frame.pack(fill="both", expand=True, padx=8, pady=(2, 4))
        
        hist_btn_row = ctk.CTkFrame(hist_box, fg_color="transparent")
        hist_btn_row.pack(fill="x", padx=8, pady=(0, 4))
        ctk.CTkButton(
            hist_btn_row, text=t("history_clear"), width=120, height=24,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"], font=ctk.CTkFont(size=10),
            command=self._clear_history
        ).pack(side="right")
        self._refresh_history_list()

    def _refresh_profiles_list(self):
        """Rebuild the profiles list UI."""
        if not hasattr(self, "profiles_list_frame"):
            return
        for w in self.profiles_list_frame.winfo_children():
            w.destroy()
        
        profiles = cfg.list_profiles()
        if not profiles:
            ctk.CTkLabel(self.profiles_list_frame, text="No hay perfiles guardados.", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(anchor="w", pady=4)
            return
        
        for name in profiles:
            row = ctk.CTkFrame(self.profiles_list_frame, fg_color=COLORS["bg"], corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"  📁 {name}", font=ctk.CTkFont(size=12), text_color=COLORS["text"], anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=6)
            ctk.CTkButton(row, text="📂 Cargar", width=80, height=28, fg_color=COLORS["accent"], text_color=COLORS["bg"], font=ctk.CTkFont(size=11), command=lambda n=name: self._load_profile(n)).pack(side="right", padx=(0, 6), pady=4)
            ctk.CTkButton(row, text="🗑️", width=32, height=28, fg_color=COLORS["danger"], hover_color="#dc2626", font=ctk.CTkFont(size=11), command=lambda n=name: self._delete_profile(n)).pack(side="right", padx=(0, 4), pady=4)

    def _save_profile(self):
        name = self.v_profile_name.get().strip()
        if not name:
            self._log(t("profile_name_empty"))
            return
        cfg.save_profile(self, name)
        self._log(t("profile_saved", name=name))
        self.v_profile_name.set("")
        self._refresh_profiles_list()

    def _load_profile(self, name):
        if cfg.load_profile(self, name):
            self._log(t("profile_loaded", name=name))
            self._debounced_update()
        else:
            self._log(t("profile_load_error", name=name))

    def _delete_profile(self, name):
        if cfg.delete_profile(name):
            self._log(t("profile_deleted", name=name))
            self._refresh_profiles_list()

    def _refresh_history_list(self):
        """Rebuild the session history UI."""
        if not hasattr(self, "history_list_frame"):
            return
        for w in self.history_list_frame.winfo_children():
            w.destroy()
        
        entries = hist.get_history(10)
        if not entries:
            ctk.CTkLabel(self.history_list_frame, text=t("history_empty"), font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(anchor="w", pady=6)
            return
            
        for item in entries:
            row = ctk.CTkFrame(self.history_list_frame, fg_color=COLORS["bg"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            lbl_txt = f"⏱ {item.get('timestamp', '')} | 📱 {item.get('device', '')} | [{item.get('preset', '')}]"
            ctk.CTkLabel(row, text=lbl_txt, font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["accent"], anchor="w").pack(side="left", padx=8, pady=4)
            cmd_prev = item.get("command", "")
            if len(cmd_prev) > 36:
                cmd_prev = cmd_prev[:33] + "..."
            ctk.CTkLabel(row, text=cmd_prev, font=ctk.CTkFont(size=9), text_color=COLORS["text2"], anchor="w").pack(side="left", fill="x", expand=True, padx=4)
            
            cfg_data = item.get("config")
            if cfg_data:
                ctk.CTkButton(
                    row, text=t("history_load"), width=75, height=24,
                    fg_color=COLORS["card"], text_color=COLORS["text"], font=ctk.CTkFont(size=10),
                    command=lambda c=cfg_data: self._load_history_config(c)
                ).pack(side="right", padx=(0, 4), pady=3)

    def _load_history_config(self, cfg_data: dict):
        for k, v in cfg_data.items():
            var = getattr(self, f"v_{k}", None)
            if var is not None:
                try:
                    var.set(v)
                except Exception:
                    pass
        self._debounced_update()
        self._log("Configuración cargada desde el historial.")

    def _clear_history(self):
        hist.clear_history()
        self._refresh_history_list()
        self._log("Historial de sesiones vaciado.")

    def _build_tab_advanced(self, tab):
        """Advanced options tab — Phase 2: lesser-used but powerful scrcpy 4.1 options."""
        from gui.widgets import cfg_group
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        scroll.columnconfigure((0, 1), weight=1, uniform="adv")

        # Left column
        c0 = cfg_group(scroll, "🦟 Ventana & Renderizado", 0)
        _wsize_lbl = ctk.CTkLabel(c0, text="Tamaño ventana (W / H)", font=ctk.CTkFont(size=11), text_color=COLORS["text2"])
        _wsize_lbl.pack(anchor="w", padx=12, pady=(6, 0))
        _wsize_row = ctk.CTkFrame(c0, fg_color="transparent")
        _wsize_row.pack(fill="x", padx=12, pady=(2, 4))
        ctk.CTkEntry(_wsize_row, textvariable=self.v_window_width, placeholder_text="Width", width=70, fg_color=COLORS["card"], border_color=COLORS["border"]).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(_wsize_row, textvariable=self.v_window_height, placeholder_text="Height", width=70, fg_color=COLORS["card"], border_color=COLORS["border"]).pack(side="left")
        self.widgets["no_window"] = self._cfg_switch(c0, "🖥️ Sin ventana (Headless total)", self.v_no_window)
        self.widgets["no_mipmaps"] = self._cfg_switch(c0, "⚡ Sin mipmaps OpenGL", self.v_no_mipmaps)
        self.widgets["min_size_alignment"] = self._cfg_option_menu(c0, "📐 Alineación mín. tamaño (5.0)", self.v_min_size_alignment, MIN_SIZE_ALIGNMENT_VALUES)
        self.widgets["angle"] = self._cfg_slider(c0, "Rotación personalizada (°)", self.v_angle, 0, 359)

        c1 = cfg_group(scroll, "⚙️ Proceso & Comportamiento", 1)
        self.widgets["verbosity"] = self._cfg_option_menu(c1, "Nivel de log", self.v_verbosity, VERBOSITY_LEVELS)
        self.widgets["pause_on_exit"] = self._cfg_option_menu(c1, "Pausa al salir", self.v_pause_on_exit, PAUSE_ON_EXIT_VALUES)
        self.widgets["no_cleanup"] = self._cfg_switch(c1, "🧹 No limpiar servidor al salir", self.v_no_cleanup)
        self.widgets["no_downsize"] = self._cfg_switch(c1, "🚫 No reducir res. al fallar", self.v_no_downsize_on_error)
        self.widgets["screen_off_timeout"] = self._cfg_slider(c1, "Timeout pantalla (s)", self.v_screen_off_timeout, 0, 300)
        self.widgets["no_terminal_title"] = self._cfg_switch(c1, "🖥️ No actualizar título terminal (4.1)", self.v_no_terminal_title)

        # Second row
        c2 = cfg_group(scroll, "⌨️ Input Avanzado", 0)
        self.widgets["no_key_repeat"] = self._cfg_switch(c2, "⏸️ Sin repetición de tecla", self.v_no_key_repeat)
        self.widgets["prefer_text"] = self._cfg_switch(c2, "📝 Inyectar como texto", self.v_prefer_text)
        self.widgets["raw_key_events"] = self._cfg_switch(c2, "⌨️ Raw key events", self.v_raw_key_events)
        self.widgets["no_mouse_hover"] = self._cfg_switch(c2, "🖱️ Sin hover del ratón", self.v_no_mouse_hover)

        c3 = cfg_group(scroll, "📡 Conexión Avanzada", 1)
        self.widgets["port"] = self._cfg_entry(c3, "Puerto TCP local", self.v_port)
        self.widgets["tunnel_host"] = self._cfg_entry(c3, "Tunnel host (IP)", self.v_tunnel_host)
        self.widgets["tunnel_port"] = self._cfg_entry(c3, "Tunnel port", self.v_tunnel_port)
        if not mgr.IS_WINDOWS:
            _l = ctk.CTkFrame(c3, fg_color=COLORS["border"], corner_radius=6)
            _l.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(_l, text="🐧 Sólo Linux", font=ctk.CTkFont(size=9, weight="bold"), text_color=COLORS["accent"]).pack(pady=(2, 0))
            self._cfg_entry(_l, "V4L2 Sink", self.v_v4l2_device)

    # ─────────────────────────────────────────────
    #  HELPER BUILDERS (Delegated to gui/widgets.py)
    # ─────────────────────────────────────────────

    def _cfg_group(self, parent, title, col):
        return cfg_group(parent, title, col)

    def _cfg_group_full(self, parent, title):
        return cfg_group_full(parent, title)

    def _cfg_option_menu(self, parent, label, var, values, tooltip=None):
        return cfg_option_menu(parent, label, var, values, command=lambda _: self._update_command(), tooltip=tooltip)

    def _cfg_entry(self, parent, label, var, tooltip=None):
        return cfg_entry(parent, label, var, on_change=self._update_command, tooltip=tooltip)

    def _cfg_slider(self, parent, label, var, from_, to, tooltip=None):
        return cfg_slider(parent, label, var, from_, to, on_change=self._update_command, tooltip=tooltip)

    def _cfg_switch(self, parent, label, var, command=None, tooltip=None):
        cmd = command if command is not None else self._update_command
        return cfg_switch(parent, label, var, command=cmd, tooltip=tooltip)



    def _build_tab_sessions(self, tab):
        """Display & Multi-Instance Session Manager Tab."""
        # Top toolbar
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=6, pady=(4, 8))
        
        ctk.CTkLabel(
            toolbar, text="🪟 Gestor de Pantallas y Sesiones Abiertas",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"]
        ).pack(side="left", padx=4)
        
        self.btn_stop_all = ctk.CTkButton(
            toolbar, text="⏹ Detener Todas", width=120, height=28,
            fg_color=COLORS["danger"], hover_color="#dc2626", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._stop_all_sessions
        )
        self.btn_stop_all.pack(side="right", padx=4)

        self.btn_new_display = ctk.CTkButton(
            toolbar, text="➕ Nueva Pantalla Virtual", width=160, height=28,
            fg_color=COLORS["accent"], text_color=COLORS["bg"], font=ctk.CTkFont(size=11, weight="bold"),
            hover_color="#06b6d4", command=self._create_new_virtual_display
        )
        self.btn_new_display.pack(side="right", padx=4)

        # Scrollable list of active session cards
        self.sessions_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.sessions_scroll.pack(fill="both", expand=True, padx=6, pady=4)
        
        self._update_sessions_ui()

    def _update_sessions_ui(self):
        """Refresh the session manager tab and topbar session count badge."""
        if not hasattr(self, "sessions_scroll"):
            return
            
        with self._process_lock:
            sessions = list(self.active_sessions.values())

        # Update topbar badge and stop button
        num = len(sessions)
        if hasattr(self, "lbl_active_displays"):
            if num > 0:
                self.lbl_active_displays.configure(text=f"🪟 {num} abierta{'s' if num > 1 else ''}", text_color=COLORS["green"])
            else:
                self.lbl_active_displays.configure(text="🪟 0 abiertas", text_color=COLORS["muted"])

        if hasattr(self, "btn_stop"):
            if num > 0:
                self.btn_stop.pack(side="right", padx=(0, 6), pady=9)
            else:
                self.btn_stop.pack_forget()

        if hasattr(self, "btn_stop_all"):
            self.btn_stop_all.configure(state="normal" if num > 0 else "disabled")

        for child in self.sessions_scroll.winfo_children():
            child.destroy()

        if not sessions:
            empty_frame = ctk.CTkFrame(self.sessions_scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
            empty_frame.pack(fill="x", padx=10, pady=20)
            ctk.CTkLabel(empty_frame, text="🖥️", font=ctk.CTkFont(size=36)).pack(pady=(16, 4))
            ctk.CTkLabel(empty_frame, text="No hay pantallas abiertas actualmente", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"]).pack()
            ctk.CTkLabel(empty_frame, text="Haz clic en '+ Nueva Pantalla Virtual' o inicia cualquier preset para comenzar.", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(pady=(2, 16))
            return

        for s in sessions:
            sid = s["id"]
            title = s["title"]
            app = s.get("app_pkg", "")
            pid = s.get("proc").pid if s.get("proc") else "--"
            st_time = s.get("start_time", "")
            mode = s.get("mode", "virtual")
            
            card = ctk.CTkFrame(self.sessions_scroll, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"], height=58)
            card.pack(fill="x", pady=4, padx=4)
            card.pack_propagate(False)
            
            # Left: Icon + Title + Meta
            left_f = ctk.CTkFrame(card, fg_color="transparent")
            left_f.pack(side="left", fill="both", expand=True, padx=12, pady=6)
            
            title_row = ctk.CTkFrame(left_f, fg_color="transparent")
            title_row.pack(fill="x")
            
            bdg = ctk.CTkLabel(title_row, text="● ACTIVA", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["green"])
            bdg.pack(side="left", padx=(0, 6))
            
            lbl_title = ctk.CTkLabel(title_row, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"], anchor="w")
            lbl_title.pack(side="left", fill="x")
            
            lbl_sub = ctk.CTkLabel(
                left_f,
                text=f"PID: {pid} | Modo: {str(mode).upper()} | Iniciada: {st_time}" + (f" | App: {app}" if app else ""),
                font=ctk.CTkFont(size=10), text_color=COLORS["muted"], anchor="w"
            )
            lbl_sub.pack(anchor="w")
            
            # Right: Close button
            btn_close = ctk.CTkButton(
                card, text="⏹ Cerrar", width=80, height=28,
                fg_color=COLORS["card_hover"], hover_color=COLORS["danger"],
                border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=11),
                command=lambda s_id=sid: self._stop_session(s_id)
            )
            btn_close.pack(side="right", padx=12, pady=12)

    def _clear_log(self):
        """Clear all messages from the log console."""
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ─────────────────────────────────────────────
    #  RESOLUTION HANDLERS
    # ─────────────────────────────────────────────
    def _on_res_change(self, val):
        if val == "Personalizada":
            self.e_res_custom.configure(state="normal", border_color=COLORS["accent"])
        else:
            self.e_res_custom.configure(state="disabled", border_color=COLORS["border"])
            res_map = {"Original": "0", "2160p (4K)": "3840", "1440p (2K)": "2560", "1080p": "1920", "720p": "1280", "480p": "854"}
            self.v_max_size.set(res_map.get(val, "1920"))
        self._debounced_update()

    def _on_v_res_change(self, val):
        if val == "Personalizada":
            self.e_v_res_custom.configure(state="normal", border_color=COLORS["accent"])
        else:
            self.e_v_res_custom.configure(state="disabled", border_color=COLORS["border"])
            if "x" in val:
                res = val.split(" ")[0]
                self.v_virtual_display_res.set(res)
        self._debounced_update()

    # ─────────────────────────────────────────────
    #  UI STATE MANAGEMENT
    # ─────────────────────────────────────────────
    def _set_widget_state(self, key, state):
        """Helper to only configure widget if state actually changes."""
        if key in self.widgets:
            widget = self.widgets[key]
            if hasattr(widget, "set_state"):
                try:
                    widget.set_state(state)
                except Exception:
                    pass
            else:
                try:
                    current = widget.cget("state")
                    if current != state:
                        widget.configure(state=state)
                except Exception:
                    pass

    def _update_ui_states(self):
        """Enable or disable widgets based on exclusionary logic from scrcpy documentation."""
        if not hasattr(self, 'widgets') or not self.widgets: return

        is_camera = self.v_video_source.get() == "camera"
        audio_enabled = self.v_audio.get()
        v_display_enabled = self.v_virtual_display.get()
        no_control = self.v_no_control.get()
        otg_enabled = self.v_otg_mode.get()

        # If OTG is enabled, operate headless (no video stream) with optional audio forwarding
        if otg_enabled:
            is_camera = False
            v_display_enabled = False
            self.v_no_video.set(True)

        # Camera Mode Exclusions
        cam_state = "disabled" if is_camera else "normal"
        for key in ["display_res_menu", "display_res_entry", "display_id", "v_display_switch", "crop_entry"]:
            self._set_widget_state(key, cam_state)

        # Camera-specific controls
        cam_only_state = "normal" if is_camera else "disabled"
        for key in ["camera_id", "camera_facing", "camera_fps", "camera_torch", "camera_zoom"]:
            self._set_widget_state(key, cam_only_state)

        # Mutual exclusivity for camera facing/id
        if is_camera:
            cid = self.v_camera_id.get().strip()
            if cid and cid != "0":
                self._set_widget_state("camera_facing", "disabled")

        # Controls disabled when camera or no_control
        ctrl_state = "disabled" if (is_camera or no_control) else "normal"
        for key in ["kb_menu", "mouse_menu", "gamepad_menu", "stay_awake", "screen_off", "keep_active", "touches_switch"]:
            self._set_widget_state(key, ctrl_state)

        # Sync quick preset switches
        if hasattr(self, "qsw_stay_awake"):
            try:
                self.qsw_stay_awake.configure(state=ctrl_state)
            except Exception:
                pass
        if hasattr(self, "qsw_screen_off"):
            try:
                self.qsw_screen_off.configure(state=ctrl_state)
            except Exception:
                pass
        if hasattr(self, "sw_uhid_kb"):
            try:
                self.sw_uhid_kb.configure(state=ctrl_state)
            except Exception:
                pass
        if hasattr(self, "lbl_no_control_warn"):
            if no_control:
                self.lbl_no_control_warn.pack(fill="x", padx=12, pady=(4, 0))
            else:
                self.lbl_no_control_warn.pack_forget()


        if is_camera:
            self.v_keyboard.set("disabled")
            self.v_mouse.set("disabled")
            self.v_gamepad.set("disabled")
        elif otg_enabled:
            if not self.v_keyboard.get() or self.v_keyboard.get() == "disabled":
                self.v_keyboard.set("uhid")
            if not self.v_mouse.get() or self.v_mouse.get() == "disabled":
                self.v_mouse.set("uhid")

        # Audio Exclusions
        aud_state = "normal" if audio_enabled else "disabled"
        for key in ["audio_source", "audio_codec", "audio_buf", "audio_dup", "audio_bitrate"]:
            self._set_widget_state(key, aud_state)

        # Virtual Display Exclusions
        vd_state = "normal" if v_display_enabled and not is_camera else "disabled"
        for key in ["v_res_menu", "v_res_entry", "v_app_picker", "v_app_clear", "vd_dpi", "vd_no_decorations", "vd_no_destroy", "flex_display"]:
            self._set_widget_state(key, vd_state)
        
        # Virtual Display vs Display ID
        if not is_camera and v_display_enabled:
            self._set_widget_state("display_id", "disabled")
            self.v_display_id.set("0")

        # Record-related
        rec_enabled = self.v_record.get()
        rec_state = "normal" if rec_enabled else "disabled"
        for key in ["record_entry", "time_limit"]:
            self._set_widget_state(key, rec_state)

    # ─────────────────────────────────────────────
    #  APP MANAGEMENT (Inline for Virtual Display)
    # ─────────────────────────────────────────────
    def _load_device_apps(self, serial: str):
        """Fetch and populate installed apps into the inline pickers."""
        if not serial or "Sin dispositivos" in serial or "Buscando" in serial:
            return
        if hasattr(self, "pv_inline_picker"):
            self.pv_inline_picker.set_loading()
        if hasattr(self, "tab_inline_picker"):
            self.tab_inline_picker.set_loading()
            
        def task():
            apps = mgr.get_installed_apps(serial)
            self.app_list_data = apps
            def update():
                if hasattr(self, "pv_inline_picker"):
                    self.pv_inline_picker.set_apps(apps)
                if hasattr(self, "tab_inline_picker"):
                    self.tab_inline_picker.set_apps(apps)
            self.after(0, update)
        threading.Thread(target=task, daemon=True).start()

    def _on_app_selected(self, pkg, name):
        self.v_virtual_display_app.set(pkg)
        self._update_app_selection_ui(name)
        if pkg:
            self._log(t("app_selected", name=name, pkg=pkg))
        else:
            self._log(t("app_none"))
        self._debounced_update()

    def _clear_selected_app(self):
        self.v_virtual_display_app.set("")
        self._update_app_selection_ui()
        self._log(t("app_cleared"))
        self._debounced_update()

    def _update_app_selection_ui(self, name_hint=None):
        pkg = self.v_virtual_display_app.get().strip()
        if not pkg:
            text = "🖥️ Escritorio Libre"
            color = COLORS["muted"]
        else:
            name = name_hint or pkg.split(".")[-1].capitalize()
            text = f"📱 {name} ({pkg})"
            color = COLORS["accent"]
            
        if hasattr(self, "lbl_pv_selected_badge"):
            self.lbl_pv_selected_badge.configure(text=text, text_color=color)
        if hasattr(self, "pv_inline_picker"):
            self.pv_inline_picker._render_items()
        if hasattr(self, "tab_inline_picker"):
            self.tab_inline_picker._render_items()

    # ─────────────────────────────────────────────
    #  COMMAND BUILDING
    # ─────────────────────────────────────────────
    def _get_config_dict(self):
        """Collect all tkinter variables into a plain dict for command_builder."""
        cfg_dict = {"device": self.v_device.get()}
        for k in cfg.CONFIG_KEYS:
            var = getattr(self, f"v_{k}", None)
            if var is not None:
                cfg_dict[k] = var.get()
        return cfg_dict

    def _build_args(self):
        return build_scrcpy_args(self._get_config_dict(), is_windows=mgr.IS_WINDOWS)

    def _update_command(self):
        args = self._build_args()
        exe = self._scrcpy_path_cache or "scrcpy"
        try:
            w = max(700, int(self.winfo_width() * 0.82))
        except Exception:
            w = 800
        self.cmd_label.configure(text=" ".join([os.path.basename(exe)] + args), wraplength=w)

    def _copy_command(self):
        args = self._build_args()
        exe = mgr.get_scrcpy_path() or "scrcpy"
        self.clipboard_clear()
        self.clipboard_append(" ".join([exe] + args))
        self._log(t("cmd_copied"))

    # ─────────────────────────────────────────────
    #  LOGGING
    # ─────────────────────────────────────────────
    def _schedule_log_updater(self):
        """Start the periodic log updater (only while scrcpy is running)."""
        if self._log_updater_running:
            return
        self._log_updater_running = True
        self._process_log_queue()

    def _stop_log_updater(self):
        """Stop the periodic log updater."""
        self._log_updater_running = False

    def _process_log_queue(self):
        """Batch process logs from the queue to the text box."""
        if not self._log_updater_running:
            return
        
        batch = []
        try:
            while len(batch) < 50:
                batch.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        
        if batch:
            self._insert_log_batch(batch)
            
        self.after(100, self._process_log_queue)

    def _insert_log_batch(self, messages):
        """Insert a batch of messages into the log text box."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", "\n".join(messages) + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _log(self, msg):
        """Add a message to the log.

        When the log updater is running (scrcpy active), messages are queued
        and processed in batches.  Otherwise they are inserted directly.
        """
        if self._log_updater_running:
            self.log_queue.put(msg)
        else:
            self._insert_log_batch([msg])

    # ─────────────────────────────────────────────
    #  LAUNCH / STOP (MULTI-INSTANCE SESSIONS)
    # ─────────────────────────────────────────────
    def _launch(self):
        """Launch a new scrcpy session / virtual display instance."""
        scrcpy_path = mgr.get_scrcpy_path()
        if not scrcpy_path:
            self._log(t("launch_no_scrcpy"))
            return

        self._session_counter += 1
        session_id = f"display_{self._session_counter}"
        
        cfg_dict = self._get_config_dict()
        
        # Pre-launch diagnostics
        issues = run_diagnostics(cfg_dict, self._current_device_caps)
        has_error = False
        for issue in issues:
            self._log(str(issue))
            if issue.level == "error":
                has_error = True
        if has_error:
            self._log(t("diag_error_cancel"))
            return

        # Build distinctive window title
        pkg = cfg_dict.get("virtual_display_app", "").strip()
        if pkg:
            app_name = pkg.split(".")[-1].capitalize()
            title = f"Scrcpy - {app_name} (Pantalla #{self._session_counter})"
        elif cfg_dict.get("virtual_display"):
            title = f"Scrcpy - Pantalla Virtual #{self._session_counter}"
        else:
            title = f"Scrcpy Mirror #{self._session_counter}"
            
        cfg_dict["window_title"] = title
        args = [scrcpy_path] + build_scrcpy_args(cfg_dict, is_windows=mgr.IS_WINDOWS)
        
        # Record session in history
        hist.record_session(
            device=cfg_dict.get("device", ""),
            preset=self.active_mode.get(),
            args=args[1:],
            config=cfg_dict,
            command=" ".join(args),
            success=True,
        )
        self.after(0, self._refresh_history_list)

        self._log(f"▶ [{title}] Ejecutando: {' '.join(args)}")
        self._schedule_log_updater()
        
        def run():
            try:
                kwargs = {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "cwd": os.path.dirname(scrcpy_path),
                    "bufsize": 1
                }
                if mgr.IS_WINDOWS:
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                
                proc = subprocess.Popen(args, **kwargs)
                session_info = {
                    "id": session_id,
                    "title": title,
                    "app_pkg": pkg,
                    "proc": proc,
                    "mode": self.active_mode.get(),
                    "start_time": time.strftime("%H:%M:%S"),
                    "is_virtual": cfg_dict.get("virtual_display", False),
                }
                with self._process_lock:
                    self.active_sessions[session_id] = session_info
                
                self.after(0, self._update_sessions_ui)
                
                lines_log = []
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        l = line.rstrip()
                        lines_log.append(l)
                        self._log(f"[{session_id}] {l}")
                
                proc.wait()
                if proc.returncode != 0:
                    self._log(f"⏹ [{title}] terminó (código {proc.returncode})")
                    hint = self._diagnose_exit_reason(lines_log)
                    if hint:
                        self._log(f"💡 Diagnóstico UX: {hint}")
                    self.after(0, self._expand_dock)
                else:
                    self._log(f"⏹ [{title}] sesión finalizada.")
            except Exception as e:
                self._log(f"❌ [{title}] Error: {e}")
                self.after(0, self._expand_dock)
            finally:
                with self._process_lock:
                    self.active_sessions.pop(session_id, None)
                self.after(0, self._update_sessions_ui)
                
        threading.Thread(target=run, daemon=True).start()

    def _diagnose_exit_reason(self, lines: list[str]) -> Optional[str]:
        """Analyze log lines to return an actionable UX diagnostic suggestion."""
        combined = " ".join(lines).lower()
        if "cannot request to stay awake if control is disabled" in combined:
            return "scrcpy requiere control activo para mantener el móvil despierto. Desactiva 'Mantener despierto' o activa el control en '🎛️ Controles'."
        if "cannot request to show touches if control is disabled" in combined:
            return "Desactiva 'Mostrar toques' o activa el control en '🎛️ Controles'."
        if "cannot keep device active if control is disabled" in combined:
            return "Desactiva 'Mantener activo' o activa el control en '🎛️ Controles'."
        if "scrcpy-server" in combined and ("not exist" in combined or "no such file" in combined):
            return "Falta scrcpy-server. Usa el botón '⬇️ Descargar' para reinstalar los binarios."
        if "unauthorized" in combined:
            return "El dispositivo no está autorizado. Desbloquea la pantalla de tu móvil y acepta la depuración USB."
        if "device offline" in combined or "device not found" in combined:
            return "Dispositivo no detectado o desconectado. Verifica el cable USB."
        if "could not open video stream" in combined or "mediacodec" in combined:
            return "El encoder de tu móvil no soportó esa resolución o códec. Prueba H264 a 1080p."
        return None


    def _stop_session(self, session_id):
        """Terminate a specific running session/virtual display."""
        with self._process_lock:
            session = self.active_sessions.get(session_id)
        if not session:
            return
        proc = session.get("proc")
        title = session.get("title", session_id)
        self._log(f"⏹ Deteniendo [{title}]...")
        # If process is already done, clean up immediately to prevent ghost sessions
        if proc is None or proc.poll() is not None:
            with self._process_lock:
                self.active_sessions.pop(session_id, None)
            self.after(0, self._update_sessions_ui)
            return
        def force_kill():
            try:
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
                                user32.PostMessageW(hwnd, 0x0010, 0, 0)
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
            except Exception as e:
                self._log(f"⚠️ Error al detener {title}: {e}")
        threading.Thread(target=force_kill, daemon=True).start()

    def _stop_all_sessions(self):
        """Terminate all active scrcpy sessions cleanly."""
        with self._process_lock:
            session_ids = list(self.active_sessions.keys())
        if not session_ids:
            self._log("ℹ️ No hay sesiones activas para detener.")
            return
        self._log(f"⏹ Deteniendo todas las {len(session_ids)} pantallas abiertas...")
        for sid in session_ids:
            self._stop_session(sid)

    def _create_new_virtual_display(self):
        """Immediately spawn a new virtual display instance without popup dialogs."""
        dev = self.v_device.get().split(" (")[0]
        if not dev or "Buscando" in dev or "Sin dispositivos" in dev:
            self._log(t("connect_device_for_vd"))
            return
            
        self.v_virtual_display.set(True)
        self.v_flex_display.set(True)
        if not self.v_virtual_dpi.get():
            self.v_virtual_dpi.set("220")
        if not self.v_virtual_display_res.get():
            self.v_virtual_display_res.set("1920x1080")
        self._launch()

    def _open_recordings_folder(self):
        """Open the directory where recordings are saved in the system file explorer."""
        rec_file = self.v_record_file.get().strip() or "recording.mp4"
        folder = os.path.dirname(os.path.abspath(rec_file))
        if not os.path.isdir(folder):
            folder = os.path.expanduser("~")
        try:
            if mgr.IS_WINDOWS:
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            self._log(t("open_folder_error", err=e))

    # ─────────────────────────────────────────────
    #  WIRELESS
    # ─────────────────────────────────────────────
    def _wifi_connect(self):
        ip = self.v_wifi_ip.get().strip()
        if not ip: self._log("⚠️ Ingresa una IP válida"); return
        self._log(f"📡 Intentando conectar a {ip}...")
        def run():
            res = mgr.connect_wifi(ip)
            self.after(0, lambda: (self._log(f"ℹ️ {res}"), self._refresh_devices()))
        threading.Thread(target=run, daemon=True).start()

    def _wifi_pair(self):
        ip = self.v_wifi_ip.get().strip()
        code = self.v_wifi_pair_code.get().strip()
        if not ip or not code: self._log("⚠️ Ingresa IP:Puerto y Código"); return
        self._log(f"🔐 Emparejando con {ip}...")
        def run():
            res = mgr.pair_wifi(ip, code)
            self.after(0, lambda: (self._log(f"ℹ️ {res}"), self._refresh_devices()))
        threading.Thread(target=run, daemon=True).start()

    def _wifi_enable_tcpip(self):
        dev = self.v_device.get().split(" (")[0]
        if not dev or "Buscando" in dev or "Sin dispositivos" in dev:
            self._log(t("connect_usb_first")); return
        self._log(t("wifi_auto_usb", dev=dev))
        def run():
            res = mgr.enable_tcpip(dev)
            def done():
                self._log(f"ℹ️ {res}")
                if "Conectado" in res:
                    # Use regex to extract IP safely (avoids IndexError from fragile string split)
                    ip_match = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', res)
                    if ip_match:
                        self.v_wifi_ip.set(f"{ip_match.group(1)}:5555")
                    self._log(t("wifi_disconnect_cable"))
                self._refresh_devices()
            self.after(0, done)
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    import sys
    if "--legacy" in sys.argv:
        ScrcpyGUI().mainloop()
    else:
        try:
            from PySide6.QtWidgets import QApplication
            from ui.app_window import AppWindow

            app = QApplication(sys.argv)
            app.setStyle("Fusion")
            win = AppWindow()
            win.show()
            sys.exit(app.exec())
        except ImportError:
            ScrcpyGUI().mainloop()
