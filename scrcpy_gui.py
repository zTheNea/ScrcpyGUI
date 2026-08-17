"""
ScrcpyGUI — Native Windows GUI for scrcpy
Allows selecting preconfigured modes (Video, Gaming, Balanced) or custom config.
Launches scrcpy directly from the interface.
Auto-downloads and updates scrcpy from GitHub.
"""
import customtkinter as ctk
import os
import queue
import subprocess
import threading
import time

import scrcpy_manager as mgr
import config_manager as cfg
from command_builder import build_scrcpy_args
from presets import (
    PRESETS, VIDEO_CODECS, VIRTUAL_RES_PRESETS, AUDIO_SOURCES, AUDIO_CODECS,
    KEYBOARD_MODES, MOUSE_MODES, GAMEPAD_MODES, ORIENTATION_VALUES,
    CAMERA_FACING, COLORS, MODE_COLORS,
)

# ── Theme ──
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AppPickerModal(ctk.CTkToplevel):
    """Modern Searchable App Picker Dialog for Virtual Display."""
    def __init__(self, parent, apps_list, on_select):
        super().__init__(parent)
        self.title("📱 Seleccionar Aplicación")
        self.geometry("480x520")
        self.minsize(400, 400)
        self.configure(fg_color=COLORS["bg"])
        self.transient(parent)
        self.grab_set()
        
        self.apps_list = apps_list # list of (friendly_name, package)
        self.on_select = on_select
        self.filtered_apps = list(apps_list)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(hdr, text="📱 Seleccionar Aplicación", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(hdr, text="Elige qué aplicación se abrirá en la pantalla virtual:", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(anchor="w", pady=(2, 0))

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(4, 8))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="🔍 Buscar app por nombre o paquete...",
            height=36, font=ctk.CTkFont(size=12),
            fg_color=COLORS["card"], border_color=COLORS["border"]
        )
        self.search_entry.pack(fill="x")
        self.search_entry.focus()

        # Scrollable List
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Bottom Bar (Cancel / Desktop default)
        btm = ctk.CTkFrame(self, fg_color="transparent")
        btm.pack(fill="x", padx=16, pady=(0, 14))
        
        ctk.CTkButton(
            btm, text="🖥️ Ninguna (Escritorio Libre)", height=32,
            fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=lambda: self._select("", "Ninguna")
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btm, text="Cerrar", width=80, height=32,
            fg_color=COLORS["border"], hover_color=COLORS["card_hover"],
            command=self.destroy
        ).pack(side="right")

        self._render_items()

    def _on_search_change(self, *args):
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_apps = list(self.apps_list)
        else:
            self.filtered_apps = [
                (name, pkg) for name, pkg in self.apps_list
                if query in name.lower() or query in pkg.lower()
            ]
        self._render_items()

    def _render_items(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not self.filtered_apps:
            ctk.CTkLabel(self.list_frame, text="No se encontraron aplicaciones coincidentes.", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(pady=20)
            return

        display_list = self.filtered_apps[:50]
        for name, pkg in display_list:
            card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"], corner_radius=6, border_width=1, border_color=COLORS["border"], height=42, cursor="hand2")
            card.pack(fill="x", pady=2)
            card.pack_propagate(False)

            lbl_name = ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"], anchor="w")
            lbl_name.pack(side="left", padx=(10, 4))

            lbl_pkg = ctk.CTkLabel(card, text=f"({pkg})", font=ctk.CTkFont(size=10), text_color=COLORS["muted"], anchor="w")
            lbl_pkg.pack(side="left", padx=(0, 8))

            def on_click(p=pkg, n=name):
                self._select(p, n)

            def on_enter(e, c=card):
                c.configure(fg_color=COLORS["card_hover"], border_color=COLORS["accent"])

            def on_leave(e, c=card):
                c.configure(fg_color=COLORS["card"], border_color=COLORS["border"])

            card.bind("<Button-1>", lambda e, p=pkg, n=name: on_click(p, n))
            lbl_name.bind("<Button-1>", lambda e, p=pkg, n=name: on_click(p, n))
            lbl_pkg.bind("<Button-1>", lambda e, p=pkg, n=name: on_click(p, n))
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

        if len(self.filtered_apps) > 50:
            rem = len(self.filtered_apps) - 50
            ctk.CTkLabel(
                self.list_frame,
                text=f"➕ Mostrando 50 de {len(self.filtered_apps)} apps ({rem} más ocultas. Escribe en el buscador para filtrar)",
                font=ctk.CTkFont(size=10), text_color=COLORS["muted"]
            ).pack(pady=8)

    def _select(self, pkg, name):
        try:
            self.grab_release()
        except Exception:
            pass
        self.on_select(pkg, name)
        self.destroy()


class ScrcpyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScrcpyGUI v1.3.0")
        self.geometry("920x740")
        self.minsize(800, 600)
        self.configure(fg_color=COLORS["bg"])

        self.active_mode = ctk.StringVar(value="")
        self.process = None
        self._process_lock = threading.Lock()
        self.mode_buttons = {}

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
        self.v_mouse = ctk.StringVar(value="")
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
            self._log("💾 Configuración anterior restaurada.")
        else:
            self._select_mode("desktop")
        
        self._debounced_update()
        
        # Auto-save config on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Save config and close the application."""
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
        
        # Others that only update command
        other_vars = [
            self.v_codec, self.v_fps, self.v_bitrate, self.v_audio_source, self.v_audio_codec, 
            self.v_audio_buf, self.v_display_id, self.v_virtual_display_res, self.v_virtual_display_app,
            self.v_orientation, self.v_audio_bitrate, self.v_audio_dup, self.v_video_buffer,
            self.v_time_limit, self.v_camera_facing, self.v_camera_fps, self.v_virtual_dpi,
            self.v_no_vd_decorations, self.v_no_vd_destroy, self.v_no_clipboard_sync,
            self.v_disable_screensaver, self.v_flex_display, self.v_camera_torch,
            self.v_camera_zoom, self.v_keep_active, self.v_background_color,
            self.v_no_aspect_ratio_lock, self.v_window_title,
            self.v_ignore_encoder_constraints, self.v_no_audio_playback,
            self.v_audio_output_buf, self.v_legacy_paste, self.v_force_adb_forward,
            self.v_camera_high_speed, self.v_kill_adb_on_close
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
        # 1. Top Titlebar / Run & Inspector Navigation Bar
        self._build_topbar()

        # 2. Main Workspace (Sidebar + Center Content)
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=10, pady=(6, 4))
        
        self._build_sidebar(self.workspace)
        self._build_center_workspace(self.workspace)

        # 3. Bottom Integrated Terminal / Output Panel
        self._build_terminal_dock()

        # 4. Bottom Status Bar (VS Code style footer)
        self._build_statusbar()

    def _build_topbar(self):
        """Top Toolbar: Logo, Device Selector, Inspector Tools, and Run Button."""
        top = ctk.CTkFrame(self, fg_color=COLORS["card"], height=48, corner_radius=8, border_width=1, border_color=COLORS["border"])
        top.pack(fill="x", padx=10, pady=(8, 0))
        top.pack_propagate(False)
        
        # Left: Branding + Device Selector
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", padx=(10, 0), fill="y")
        
        ctk.CTkLabel(left, text="⚡ Scrcpy", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["orange"]).pack(side="left")
        ctk.CTkLabel(left, text="GUI", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).pack(side="left", padx=(0, 14))
        
        ctk.CTkLabel(left, text="📱", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 4))
        self.device_menu = ctk.CTkOptionMenu(
            left, variable=self.v_device, values=["Buscando..."],
            width=180, height=28, font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg"], button_color=COLORS["border"],
            button_hover_color=COLORS["card_hover"],
            command=self._on_device_selected
        )
        self.device_menu.pack(side="left", padx=(0, 4))
        
        ctk.CTkButton(
            left, text="🔄", width=28, height=28, font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=self._refresh_devices
        ).pack(side="left")

        # Center: Inspector Tools
        mid = ctk.CTkFrame(top, fg_color="transparent")
        mid.pack(side="left", expand=True, fill="y", padx=10)
        
        ctk.CTkButton(mid, text="🎬 Encoders", width=80, height=26, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=10), hover_color=COLORS["card_hover"], command=lambda: self._run_inspector("--list-encoders")).pack(side="left", padx=2, pady=10)
        ctk.CTkButton(mid, text="📷 Cámaras", width=80, height=26, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=10), hover_color=COLORS["card_hover"], command=lambda: self._run_inspector("--list-cameras")).pack(side="left", padx=2, pady=10)
        ctk.CTkButton(mid, text="🖥️ Pantallas", width=80, height=26, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=10), hover_color=COLORS["card_hover"], command=lambda: self._run_inspector("--list-displays")).pack(side="left", padx=2, pady=10)
        ctk.CTkButton(mid, text="⚡ Modo PC", width=80, height=26, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["accent"], text_color=COLORS["accent"], font=ctk.CTkFont(size=10, weight="bold"), hover_color=COLORS["card_hover"], command=self._enable_pc_mode).pack(side="left", padx=2, pady=10)

        # Right: Run Button + Updater
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=(0, 10), fill="y")
        
        self.btn_check_update = ctk.CTkButton(
            right, text="🔄 Actualizar", width=100, height=30,
            font=ctk.CTkFont(size=11), fg_color=COLORS["card"],
            border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["card_hover"], command=self._check_update
        )
        self.btn_check_update.pack(side="left", padx=(0, 8), pady=9)

        self.btn_download = ctk.CTkButton(
            right, text="⬇️ Descargar", width=110, height=30,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORS["green"],
            text_color=COLORS["bg"], hover_color="#059669",
            command=self._start_download
        )
        self.btn_download.pack(side="left", padx=(0, 8), pady=9)
        self.btn_download.pack_forget()

        self.btn_launch = ctk.CTkButton(
            right, text="▶ Iniciar Scrcpy", width=135, height=30,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORS["accent"],
            text_color=COLORS["bg"], hover_color="#06b6d4", corner_radius=6,
            command=self._launch
        )
        self.btn_launch.pack(side="right", pady=9)
        
        self.btn_stop = ctk.CTkButton(
            right, text="⏹ Detener", width=135, height=30,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORS["danger"],
            hover_color="#dc2626", corner_radius=6, command=self._stop
        )
        self.btn_stop.pack(side="right", pady=9)
        self.btn_stop.pack_forget()

        self.after(500, self._refresh_devices)

    def _build_sidebar(self, parent):
        """Left Sidebar: Presets and Modes Explorer Tree + Version Card."""
        self.sidebar_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], width=240, corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 8))
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar Header
        sb_hdr = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        sb_hdr.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(sb_hdr, text="📁 MODOS & PERFILES", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"]).pack(side="left")
        
        # Presets List (Scrollable)
        self.presets_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.presets_scroll.pack(fill="both", expand=True, padx=4, pady=2)
        
        for key, p in PRESETS.items():
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
        self.lbl_ver = ctk.CTkLabel(ver_card, text=f"📦 scrcpy {ver or 'no detectado'}", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["green"] if ver else COLORS["danger"])
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

    def _sidebar_item(self, parent, key, label, badge):
        color = MODE_COLORS.get(key, COLORS["text"])
        item = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=6, cursor="hand2", height=34)
        item.pack(fill="x", pady=2, padx=4)
        item.pack_propagate(False)
        
        lbl = ctk.CTkLabel(item, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text"], anchor="w")
        lbl.pack(side="left", padx=(10, 4), fill="x", expand=True)
        
        bdg = ctk.CTkLabel(item, text=badge, font=ctk.CTkFont(size=9), text_color=COLORS["muted"])
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
        """Center Workspace: Shows Preset Inspector Card or Custom Tabview."""
        self.center_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.center_frame.pack(side="left", fill="both", expand=True)
        
        # 1. Preset Inspector View (Shown when a preset is selected)
        self.preset_view = ctk.CTkScrollableFrame(self.center_frame, fg_color="transparent")
        self.preset_view.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Header of preset
        self.pv_title = ctk.CTkLabel(self.preset_view, text="", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"], anchor="w")
        self.pv_title.pack(fill="x", pady=(0, 2))
        
        self.pv_desc = ctk.CTkLabel(self.preset_view, text="", font=ctk.CTkFont(size=12), text_color=COLORS["text2"], anchor="w", wraplength=600, justify="left")
        self.pv_desc.pack(fill="x", pady=(0, 14))
        
        # 4 Stat Cards
        self.pv_stats = ctk.CTkFrame(self.preset_view, fg_color="transparent")
        self.pv_stats.pack(fill="x", pady=(0, 16))
        self.pv_stats.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        
        self.stat_codec = self._stat_box(self.pv_stats, "Códec Video", "--", 0)
        self.stat_res = self._stat_box(self.pv_stats, "Resolución", "--", 1)
        self.stat_fps = self._stat_box(self.pv_stats, "Tasa FPS", "--", 2)
        self.stat_bitrate = self._stat_box(self.pv_stats, "Bitrate", "--", 3)
        
        # Features & Details Card
        self.pv_details_card = ctk.CTkFrame(self.preset_view, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.pv_details_card.pack(fill="x", pady=(0, 14))
        
        ctk.CTkLabel(self.pv_details_card, text="✨ Características de este modo:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(10, 6))
        self.pv_features = ctk.CTkLabel(self.pv_details_card, text="", font=ctk.CTkFont(size=11), text_color=COLORS["text2"], anchor="w", justify="left")
        self.pv_features.pack(anchor="w", padx=14, pady=(0, 12))
        
        # App Selector for Virtual Display Modes
        self.pv_app_card = ctk.CTkFrame(self.preset_view, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.pv_app_card.pack(fill="x", pady=(0, 14))
        
        ctk.CTkLabel(self.pv_app_card, text="📱 Aplicación vinculada a la Pantalla Virtual:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(10, 4))
        
        app_row_pv = ctk.CTkFrame(self.pv_app_card, fg_color="transparent")
        app_row_pv.pack(fill="x", padx=14, pady=(0, 10))
        
        self.btn_pv_select_app = ctk.CTkButton(
            app_row_pv, text="🔍 Seleccionar App a abrir...", height=32,
            font=ctk.CTkFont(size=11), fg_color=COLORS["card"],
            border_width=1, border_color=COLORS["accent"], text_color=COLORS["accent"],
            hover_color=COLORS["card_hover"], command=self._open_app_picker
        )
        self.btn_pv_select_app.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_pv_clear_app = ctk.CTkButton(
            app_row_pv, text="❌", width=32, height=32,
            fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["danger"], command=self._clear_selected_app
        )
        self.btn_pv_clear_app.pack(side="left")

        # Quick Toggles for the preset
        toggles_card = ctk.CTkFrame(self.preset_view, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        toggles_card.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(toggles_card, text="⚡ Opciones rápidas de sesión:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(10, 8))
        
        tog_row = ctk.CTkFrame(toggles_card, fg_color="transparent")
        tog_row.pack(fill="x", padx=14, pady=(0, 10))
        
        self._quick_sw(tog_row, "Mantener despierto", self.v_stay_awake)
        self._quick_sw(tog_row, "Apagar pantalla móvil", self.v_screen_off)
        self._quick_sw(tog_row, "Pantalla completa", self.v_fullscreen)
        self._quick_sw(tog_row, "Siempre visible", self.v_always_on_top)
        self._quick_sw(tog_row, "Pantalla Flex (v4.0)", self.v_flex_display)

        # 2. Custom Tabview (Hidden until "Personalizado" is selected)
        self._build_tabview()

    def _stat_box(self, parent, title, val, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(padx=10, pady=(8, 2))
        lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent"])
        lbl.pack(padx=10, pady=(0, 8))
        return lbl

    def _quick_sw(self, parent, text, var):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", expand=True)
        sw = ctk.CTkSwitch(f, text=text, variable=var, font=ctk.CTkFont(size=11), text_color=COLORS["text2"], progress_color=COLORS["accent"], command=self._update_command)
        sw.pack(side="left")

    def _select_mode(self, key):
        self.active_mode.set(key)
        for k, item in self.mode_buttons.items():
            if k == key:
                item.configure(fg_color=COLORS["card_hover"], border_width=1, border_color=MODE_COLORS.get(k, COLORS["accent"]))
            else:
                item.configure(fg_color="transparent", border_width=0)
                
        if key == "custom":
            self.preset_view.pack_forget()
            self.tabview_frame.pack(fill="both", expand=True, padx=8, pady=8)
        else:
            self.tabview_frame.pack_forget()
            self.preset_view.pack(fill="both", expand=True, padx=16, pady=12)
            self._reset_to_defaults()
            p = PRESETS[key]
            self._apply_preset(p)
            self._update_preset_inspector(key, p)
            if p.get("prompt_app") and not self.v_virtual_display_app.get().strip():
                self.after(150, self._open_app_picker)
            
        self._debounced_update()

    def _update_preset_inspector(self, key, p):
        """Update the center inspector with preset details."""
        color = MODE_COLORS.get(key, COLORS["accent"])
        self.pv_title.configure(text=p["label"], text_color=color)
        self.pv_desc.configure(text=p["desc"])
        
        self.stat_codec.configure(text=p["codec"].upper())
        self.stat_res.configure(text="Original" if p["max_size"] == 0 else f"{p['max_size']}px")
        self.stat_fps.configure(text=f"{p['fps']} FPS")
        self.stat_bitrate.configure(text=f"{p['bitrate']} Mbps")
        
        features = []
        if p.get("virtual_display"):
            res_txt = p.get('virtual_display_res', '1920x1080')
            dpi_txt = p.get('virtual_dpi', '220')
            features.append(f"• Pantalla Virtual secundaria a {res_txt} con DPI {dpi_txt}")
            if p.get("flex_display") or self.v_flex_display.get():
                features.append("• Pantalla Flex activa (adaptable al redimensionar la ventana en PC)")
            self.pv_app_card.pack(fill="x", pady=(0, 14), before=self.pv_details_card)
            self._update_app_button_label()
        else:
            self.pv_app_card.pack_forget()

        if p.get("keyboard") == "uhid" or p.get("mouse") == "uhid":
            features.append("• Control por hardware nativo UHID (Teclado y ratón)")
        if p.get("audio"):
            features.append(f"• Audio en tiempo real ({p.get('audio_codec', 'opus').upper()}) con buffer de {p.get('audio_buffer', 50)}ms")
        else:
            features.append("• Audio desactivado para máxima reducción de latencia")
        if p.get("otg_mode"):
            features.append("• Modo físico OTG puro (emulación de periférico USB)")
        if not features:
            features.append("• Modo balanceado optimizado para baja latencia")
            
        self.pv_features.configure(text="\n".join(features))

    def _build_terminal_dock(self):
        """Bottom Dock: Integrated Terminal & CLI Command Preview."""
        self.dock = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8, border_width=1, border_color=COLORS["border"], height=125)
        self.dock.pack(fill="x", padx=10, pady=(2, 4))
        self.dock.pack_propagate(False)
        
        # Dock Header
        dock_hdr = ctk.CTkFrame(self.dock, fg_color="transparent", height=26)
        dock_hdr.pack(fill="x", padx=10, pady=(6, 2))
        
        ctk.CTkLabel(dock_hdr, text="💻 TERMINAL & COMANDO", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"]).pack(side="left")
        
        self.btn_clear_log = ctk.CTkButton(dock_hdr, text="🗑️ Limpiar", width=60, height=20, font=ctk.CTkFont(size=10), fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"], command=self._clear_log)
        self.btn_clear_log.pack(side="right", padx=(4, 0))
        
        ctk.CTkButton(dock_hdr, text="📋 Copiar CLI", width=75, height=20, font=ctk.CTkFont(size=10), fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"], command=self._copy_command).pack(side="right")
        
        # Inner text terminal box
        self.log_box = ctk.CTkTextbox(self.dock, fg_color=COLORS["bg"], font=ctk.CTkFont(family="Consolas", size=10), text_color=COLORS["green"], border_width=0, corner_radius=6)
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.log_box.insert("end", "$ scrcpy listo. Selecciona un modo en el panel lateral y pulsa ▶ Iniciar.\n")
        self.log_box.configure(state="disabled")

        # Fake cmd label for updating text internally
        self.cmd_label = ctk.CTkLabel(self.dock, text="scrcpy")

    def _build_statusbar(self):
        """VS Code style bottom status bar."""
        self.statusbar = ctk.CTkFrame(self, fg_color=COLORS["card"], height=22, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        ver = mgr.get_installed_version() or "scrcpy"
        self.sb_scrcpy = ctk.CTkLabel(self.statusbar, text=f"⚡ {ver}", font=ctk.CTkFont(size=10), text_color=COLORS["accent"])
        self.sb_scrcpy.pack(side="left", padx=10)
        
        self.sb_dev = ctk.CTkLabel(self.statusbar, text="📱 Sin dispositivo", font=ctk.CTkFont(size=10), text_color=COLORS["text2"])
        self.sb_dev.pack(side="left", padx=10)
        
        ctk.CTkLabel(self.statusbar, text="UTF-8", font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(side="right", padx=10)
        ctk.CTkLabel(self.statusbar, text="ScrcpyGUI v1.3.0", font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(side="right", padx=10)

    def _run_inspector(self, flag):
        """Execute a hardware query on the selected device and print results to the log."""
        dev = self.v_device.get()
        self._log(f"🔍 Consultando {flag} en {dev}...")
        
        def task():
            success, output = mgr.run_scrcpy_query(flag, dev)
            self.after(0, lambda: self._log(f"--- [Resultado {flag}] ---\n{output}\n--------------------------"))
            
        threading.Thread(target=task, daemon=True).start()

    def _enable_pc_mode(self):
        """Enable Android freeform windows and external desktop mode via ADB."""
        dev = self.v_device.get()
        self._log(f"⚡ Activando soporte de Ventanas Libres y Modo Escritorio en {dev}...")
        def task():
            success, msg = mgr.enable_desktop_freeform(dev)
            self.after(0, lambda: self._log(msg))
        threading.Thread(target=task, daemon=True).start()

    def _refresh_devices(self):
        self.device_menu.configure(values=["Buscando..."])
        self.v_device.set("Buscando...")
        threading.Thread(target=self._check_adb, daemon=True).start()

    def _check_adb(self):
        devs = mgr.list_devices()
        def update():
            if not devs:
                self.device_menu.configure(values=["Sin dispositivos"])
                self.v_device.set("Sin dispositivos")
                self.sb_dev.configure(text="📱 Sin dispositivos", text_color=COLORS["danger"])
            else:
                vals = [f"{d[0]} ({d[1]})" for d in devs]
                self.device_menu.configure(values=vals)
                if self.v_device.get() not in vals:
                    self.v_device.set(vals[0])
                self._on_device_selected(self.v_device.get())
            self._update_command()
        self.after(0, update)

    def _on_device_selected(self, dev_str):
        """Called whenever the selected device changes to analyze its hardware capabilities."""
        if not dev_str or "Sin dispositivos" in dev_str or "Buscando" in dev_str:
            self._current_device_caps = None
            return
            
        serial = dev_str.split(" (")[0].strip()
        if not serial:
            return
            
        if serial in self._device_caps_cache:
            self._apply_device_capabilities(self._device_caps_cache[serial])
            return

        self._log(f"🔍 Escaneando capacidades de hardware de {dev_str}...")
        self.sb_dev.configure(text=f"🔍 Analizando {dev_str}...", text_color=COLORS["orange"])
        
        def task():
            caps = mgr.scan_device_capabilities(serial)
            self._device_caps_cache[serial] = caps
            self.after(0, lambda: self._apply_device_capabilities(caps))
            
        threading.Thread(target=task, daemon=True).start()

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
            
        # 4. Log Summary in terminal
        v_str = ", ".join(c.upper() for c in v_codecs)
        a_str = ", ".join(c.upper() for c in a_codecs)
        num_cams = len(caps.get("cameras", []))
        num_dsps = len(caps.get("displays", []))
        self._log(f"✅ {brand} {model} (Android {ver}) analizado:")
        self._log(f"   🎬 Códecs Video compatibles: [{v_str}]")
        self._log(f"   🔊 Códecs Audio compatibles: [{a_str}]")
        self._log(f"   📷 Cámaras: {num_cams} | 🖥️ Pantallas: {num_dsps}")
        
        # 5. Adapt active preset if current preset requires an unsupported codec
        curr_mode = self.active_mode.get()
        if curr_mode in PRESETS:
            p_codec = PRESETS[curr_mode].get("codec", "h264")
            if p_codec not in v_codecs:
                self.v_codec.set("h264")
                self._log(f"ℹ️ Códec {p_codec.upper()} no soportado por este móvil, adaptado automáticamente a H264.")
                
        # 6. Update command
        self._update_command()

    def _check_update(self):
        self._log("🔍 Buscando actualizaciones de scrcpy en GitHub...")
        if hasattr(self, "btn_check_update"):
            self.btn_check_update.configure(state="disabled", text="Buscando...")
        mgr.check_latest(self._on_check_result)

    def _on_check_result(self, tag, url, err):
        def update():
            if hasattr(self, "btn_check_update"):
                self.btn_check_update.configure(state="normal", text="🔄 Actualizar")
            if err:
                self._log(f"⚠️ Error al buscar actualización: {err}")
                return
            installed = mgr.get_installed_version()
            self._latest_tag, self._latest_url = tag, url
            if installed == tag:
                self._log(f"✅ scrcpy {tag} — Ya tienes la versión más reciente.")
                if hasattr(self, "btn_check_update"):
                    self.btn_check_update.configure(text="✅ Al día")
                if hasattr(self, "lbl_ver"):
                    self.lbl_ver.configure(text=f"📦 scrcpy {tag} (al día)", text_color=COLORS["green"])
            else:
                self._log(f"🆕 Nueva versión disponible: {tag} (instalada: {installed or 'ninguna'})")
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
        self._log(f"⬇️ Descargando scrcpy {tag} desde GitHub...")
        
        def on_progress(p):
            if p < 0:
                self.after(0, lambda: self._log("📦 Extrayendo binarios de scrcpy..."))
            else:
                if hasattr(self, "dl_progress"):
                    self.after(0, lambda: self.dl_progress.set(p))
                
        def on_done(err):
            def finish():
                if hasattr(self, "dl_progress"):
                    self.dl_progress.pack_forget()
                if err:
                    self._log(f"❌ Error al descargar: {err}")
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
                    self._log(f"✅ scrcpy {tag} instalado correctamente en {mgr.SCRCPY_DIR}.")
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
        
        # Sync UI components that don't auto-update from trace
        if hasattr(self, "res_menu"): self.res_menu.set("1080p")
        if hasattr(self, "virtual_res_menu"): self.virtual_res_menu.set("1280x720")
        if hasattr(self, "app_menu"): self.app_menu.set("Ninguna")
        self._update_command()

    def _apply_preset(self, p):
        self.v_codec.set(p["codec"])
        self.v_max_size.set(str(p["max_size"]))
        self.v_fps.set(p["fps"])
        self.v_bitrate.set(p["bitrate"])
        self.v_audio.set(p["audio"])
        self.v_audio_buf.set(p["audio_buffer"])
        self.v_video_buffer.set(p["video_buffer"])
        self.v_fullscreen.set(p["fullscreen"])
        self.v_stay_awake.set(p["stay_awake"])
        self.v_screen_off.set(p["screen_off"])
        self.v_keyboard.set(p["keyboard"])
        self.v_mouse.set(p["mouse"])
        self.v_gamepad.set("uhid" if p.get("gamepad") else "")
        self.v_record.set(p["record"])
        self.v_print_fps.set(p["print_fps"])
        self.v_show_touches.set(p["show_touches"])
        self.v_crop.set(p["crop"])
        if "otg_mode" in p:
            self.v_otg_mode.set(p["otg_mode"])
        if "keep_active" in p:
            self.v_keep_active.set(p["keep_active"])
        if "audio_codec" in p:
            self.v_audio_codec.set(p["audio_codec"])
        if "audio_bitrate" in p:
            self.v_audio_bitrate.set(p["audio_bitrate"])
        if "no_audio_playback" in p:
            self.v_no_audio_playback.set(p["no_audio_playback"])
        if "virtual_display" in p:
            self.v_virtual_display.set(p["virtual_display"])
        if "virtual_display_res" in p:
            self.v_virtual_display_res.set(p["virtual_display_res"])
        if "virtual_dpi" in p:
            self.v_virtual_dpi.set(p["virtual_dpi"])
        if "flex_display" in p:
            self.v_flex_display.set(p["flex_display"])

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
        self.tabview.add("📶 Wi-Fi")
        self.tabview.add("💾 Perfiles")

        self._build_tab_video(self.tabview.tab("🎥 Video"))
        self._build_tab_audio(self.tabview.tab("🔊 Audio"))
        self._build_tab_display(self.tabview.tab("🖥️ Pantalla"))
        self._build_tab_controls(self.tabview.tab("🎛️ Controles"))
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

        # Right column: Camera
        c1 = self._cfg_group(cols, "📷 Cámara", 1)
        self.widgets["camera_id"] = self._cfg_entry(c1, "Cámara ID", self.v_camera_id)
        self.widgets["camera_facing"] = self._cfg_option_menu(c1, "Cámara Cara", self.v_camera_facing, CAMERA_FACING)
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

        # Right: Buffers & Output
        c1 = self._cfg_group(cols, "🎛️ Buffers & Reproducción", 1)
        self.widgets["audio_buf"] = self._cfg_slider(c1, "Buffer captura (ms)", self.v_audio_buf, 0, 500)
        self.widgets["audio_output_buf"] = self._cfg_slider(c1, "Buffer salida PC (ms)", self.v_audio_output_buf, 0, 500)
        self.widgets["audio_dup"] = self._cfg_switch(c1, "🔊 Duplicar audio (PC + Móvil)", self.v_audio_dup)
        self.widgets["no_audio_playback"] = self._cfg_switch(c1, "🚫 Sin audio local (Solo capturar)", self.v_no_audio_playback)

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
        self.widgets["disable_screensaver"] = self._cfg_switch(c0, "🛡️ Desactivar screensaver", self.v_disable_screensaver)
        self.widgets["display_id"] = self._cfg_entry(c0, "Display ID (0=Principal)", self.v_display_id)

        # Quick settings inside display tab
        self._cfg_switch(c0, "📱 Apagar pantalla", self.v_screen_off)
        self._cfg_switch(c0, "💡 Mantener despierto", self.v_stay_awake)

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
        ctk.CTkLabel(c1, text="🚀 App en Pantalla Virtual (Auto-arranque)", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        app_row = ctk.CTkFrame(c1, fg_color="transparent")
        app_row.pack(fill="x", padx=12, pady=(2, 4))
        
        self.btn_open_app_picker = ctk.CTkButton(
            app_row, text="🔍 Seleccionar App (Ninguna)...", height=32,
            fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text2"], hover_color=COLORS["card_hover"],
            command=self._open_app_picker
        )
        self.btn_open_app_picker.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.widgets["v_app_picker"] = self.btn_open_app_picker

        self.btn_clear_app = ctk.CTkButton(
            app_row, text="❌", width=32, height=32,
            fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["danger"], command=self._clear_selected_app
        )
        self.btn_clear_app.pack(side="left")
        self.widgets["v_app_clear"] = self.btn_clear_app

        self.v_virtual_display_res.set("1280x720")
        self.widgets["vd_dpi"] = self._cfg_entry(c1, "DPI Virtual Display", self.v_virtual_dpi)
        self.widgets["vd_no_decorations"] = self._cfg_switch(c1, "Sin decoraciones VD", self.v_no_vd_decorations)
        self.widgets["vd_no_destroy"] = self._cfg_switch(c1, "Conservar apps al cerrar", self.v_no_vd_destroy)

        if not mgr.IS_WINDOWS:
            l_frame = ctk.CTkFrame(c1, fg_color=COLORS["border"], corner_radius=6)
            l_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(l_frame, text="🐧 Sólo Linux", font=ctk.CTkFont(size=9, weight="bold"), text_color=COLORS["accent"]).pack(pady=(2,0))
            self._cfg_entry(l_frame, "V4L2 Sink", self.v_v4l2_device)

    def _build_tab_controls(self, tab):
        """Controls and Recording tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent"); cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="ctrl")

        c0 = self._cfg_group(cols, "🕹️ Controles de Entrada", 0)
        self.widgets["kb_menu"] = self._cfg_option_menu(c0, "Teclado", self.v_keyboard, KEYBOARD_MODES)
        self.widgets["mouse_menu"] = self._cfg_option_menu(c0, "Ratón", self.v_mouse, MOUSE_MODES)
        self.widgets["gamepad_menu"] = self._cfg_option_menu(c0, "Gamepad", self.v_gamepad, GAMEPAD_MODES)
        self.widgets["no_control"] = self._cfg_switch(c0, "🚫 Solo lectura", self.v_no_control)
        self.widgets["otg_mode"] = self._cfg_switch(c0, "🔌 Modo OTG (Hardware)", self.v_otg_mode)
        self.widgets["keep_active"] = self._cfg_switch(c0, "🔥 Mantener Activo (v4.0)", self.v_keep_active)
        self.widgets["legacy_paste"] = self._cfg_switch(c0, "📋 Pegado legacy", self.v_legacy_paste)
        self.widgets["no_clipboard"] = self._cfg_switch(c0, "🚫 Sin clipboard sync", self.v_no_clipboard_sync)
        self.widgets["touches_switch"] = self._cfg_switch(c0, "Mostrar toques", self.v_show_touches)
        self._cfg_switch(c0, "📊 Mostrar FPS", self.v_print_fps)

        c1 = self._cfg_group(cols, "🔴 Grabación & Conexión", 1)
        self.widgets["record_switch"] = self._cfg_switch(c1, "🔴 Grabar sesión", self.v_record)
        self.widgets["record_entry"] = self._cfg_entry(c1, "Archivo rec", self.v_record_file)
        self.widgets["time_limit"] = self._cfg_slider(c1, "⏱ Tiempo límite (s)", self.v_time_limit, 0, 600)
        self.widgets["video_buffer"] = self._cfg_slider(c1, "Video Buffer (ms)", self.v_video_buffer, 0, 500)
        self._cfg_switch(c1, "🛡️ Forzar ADB Forward", self.v_force_adb_forward)
        self._cfg_switch(c1, "🛑 Detener ADB al salir", self.v_kill_adb_on_close)

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

    def _refresh_profiles_list(self):
        """Rebuild the profiles list UI."""
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
            self._log("⚠️ Escribe un nombre para el perfil.")
            return
        cfg.save_profile(self, name)
        self._log(f"💾 Perfil '{name}' guardado.")
        self.v_profile_name.set("")
        self._refresh_profiles_list()

    def _load_profile(self, name):
        if cfg.load_profile(self, name):
            self._log(f"📂 Perfil '{name}' cargado.")
            self._debounced_update()
        else:
            self._log(f"⚠️ Error al cargar el perfil '{name}'.")

    def _delete_profile(self, name):
        if cfg.delete_profile(name):
            self._log(f"🗑️ Perfil '{name}' eliminado.")
            self._refresh_profiles_list()

    # ─────────────────────────────────────────────
    #  HELPER BUILDERS
    # ─────────────────────────────────────────────
    def _cfg_group(self, parent, title, col):
        f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10); f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(fill="x", padx=10, pady=(10, 6))
        return f

    def _cfg_group_full(self, parent, title):
        """Full-width group (no grid)."""
        f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10)
        f.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(fill="x", padx=10, pady=(10, 6))
        return f

    def _cfg_option_menu(self, parent, label, var, values):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        m = ctk.CTkOptionMenu(parent, variable=var, values=values, width=180, fg_color=COLORS["card"], button_color=COLORS["border"], command=lambda _: self._update_command())
        m.pack(padx=12, pady=(2, 4), anchor="w")
        return m

    def _cfg_entry(self, parent, label, var):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        e = ctk.CTkEntry(parent, textvariable=var, width=180, fg_color=COLORS["card"], border_color=COLORS["border"])
        e.pack(padx=12, pady=(2, 4), anchor="w"); var.trace_add("write", lambda *_: self._update_command())
        return e

    def _cfg_slider(self, parent, label, var, from_, to):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=12, pady=(6, 4))
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
        val_label = ctk.CTkLabel(row, text=str(var.get()), font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"], width=40); val_label.pack(side="right")
        def on_slide(v): var.set(int(float(v))); val_label.configure(text=str(int(float(v)))); self._update_command()
        s = ctk.CTkSlider(parent, from_=from_, to=to, variable=var, width=180, command=on_slide, progress_color=COLORS["accent"], button_color=COLORS["accent"])
        s.pack(padx=12, anchor="w")
        return s

    def _cfg_switch(self, parent, label, var):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
        sw = ctk.CTkSwitch(row, text="", variable=var, width=40, progress_color=COLORS["accent"], command=self._update_command)
        sw.pack(side="right")
        return sw

    def _build_dock(self, parent):
        # 1. Full-width command bar
        cmd_card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        cmd_card.pack(fill="x", pady=(0, 4))
        
        cmd_inner = ctk.CTkFrame(cmd_card, fg_color="transparent")
        cmd_inner.pack(fill="x", padx=12, pady=6)
        
        ctk.CTkLabel(cmd_inner, text="💻 Comando:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["muted"]).pack(side="left", padx=(0, 8))
        self.cmd_label = ctk.CTkLabel(cmd_inner, text="scrcpy", font=ctk.CTkFont(family="Consolas", size=10), text_color=COLORS["green"], anchor="w", wraplength=1100, justify="left")
        self.cmd_label.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(cmd_inner, text="📋 Copiar", width=65, height=22, fg_color=COLORS["border"], hover_color=COLORS["card_hover"], font=ctk.CTkFont(size=10), command=self._copy_command).pack(side="right", padx=(8, 0))
        
        # 2. Action Toolbar & Log Header Row
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 3))
        
        # Left Actions
        self.btn_launch = ctk.CTkButton(toolbar, text="🚀 Iniciar Scrcpy", width=160, height=30, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORS["accent"], text_color=COLORS["bg"], hover_color="#06b6d4", corner_radius=8, command=self._launch)
        self.btn_launch.pack(side="left", padx=(0, 6))
        
        self.btn_stop = ctk.CTkButton(toolbar, text="⏹ Detener", width=160, height=30, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORS["danger"], hover_color="#dc2626", corner_radius=8, command=self._stop)
        self.btn_stop.pack(side="left", padx=(0, 6))
        self.btn_stop.pack_forget()
        
        self.btn_quick_refresh = ctk.CTkButton(toolbar, text="🔄 Actualizar", width=110, height=30, font=ctk.CTkFont(size=11), fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"], command=self._refresh_devices)
        self.btn_quick_refresh.pack(side="left")
        
        # Right Log Controls
        self.btn_clear_log = ctk.CTkButton(toolbar, text="🗑️ Limpiar", width=65, height=30, font=ctk.CTkFont(size=10), fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["card_hover"], command=self._clear_log)
        self.btn_clear_log.pack(side="right")
        
        ctk.CTkLabel(toolbar, text="📜 Salida & Diagnóstico:", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(side="right", padx=(0, 8))
        
        # 3. Full-width Console Output Box
        self.log_box = ctk.CTkTextbox(parent, height=75, fg_color=COLORS["card"], font=ctk.CTkFont(family="Consolas", size=10), text_color=COLORS["text2"], border_width=1, border_color=COLORS["border"], corner_radius=8)
        self.log_box.pack(fill="x")
        self.log_box.insert("end", "Listo. Selecciona un modo e inicia.\n")
        self.log_box.configure(state="disabled")
        
        if not mgr.get_scrcpy_path():
            self._log("⚠️ scrcpy no encontrado. Usa 'Descargar scrcpy' arriba.")

        self._update_ui_states()
        self._update_command()

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
            try:
                current = widget.cget("state")
                if current != state:
                    widget.configure(state=state)
            except Exception:
                widget.configure(state=state)

    def _update_ui_states(self):
        """Enable or disable widgets based on exclusionary logic from scrcpy documentation."""
        if not hasattr(self, 'widgets') or not self.widgets: return

        is_camera = self.v_video_source.get() == "camera"
        audio_enabled = self.v_audio.get()
        v_display_enabled = self.v_virtual_display.get()
        no_control = self.v_no_control.get()
        otg_enabled = self.v_otg_mode.get()

        # If OTG is enabled, it acts as a physical keyboard/mouse, no video/audio.
        if otg_enabled:
            is_camera = False
            audio_enabled = False
            v_display_enabled = False
            self.v_no_video.set(True)
            self.v_audio.set(False)

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

        # Controls disabled when camera or no_control or otg_enabled
        # Wait, OTG needs controls (it IS a control mode), but Scrcpy auto-selects AOA or HID.
        # We can disable the manual kb/mouse selectors when OTG is enabled, or let the user choose them.
        # Let's just disable them when no_control or camera is active.
        ctrl_state = "disabled" if (is_camera or no_control or otg_enabled) else "normal"
        for key in ["kb_menu", "mouse_menu", "gamepad_menu"]:
            self._set_widget_state(key, ctrl_state)

        if is_camera or otg_enabled:
            self.v_keyboard.set("disabled" if is_camera else "")
            self.v_mouse.set("disabled" if is_camera else "")
            self.v_gamepad.set("disabled" if is_camera else "")

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
    #  APP MANAGEMENT (for Virtual Display)
    # ─────────────────────────────────────────────
    def _open_app_picker(self):
        dev = self.v_device.get().split(" (")[0]
        if not dev or "Buscando" in dev or "Sin dispositivos" in dev:
            self._log("⚠️ Conecta un dispositivo primero para listar aplicaciones.")
            return

        self.btn_open_app_picker.configure(text="⌛ Obteniendo apps del móvil...")
        
        def task():
            apps = mgr.get_installed_apps(dev)
            self.app_list_data = apps
            def show():
                self._update_app_button_label()
                AppPickerModal(self, apps, self._on_app_selected)
            self.after(0, show)

        threading.Thread(target=task, daemon=True).start()

    def _on_app_selected(self, pkg, name):
        self.v_virtual_display_app.set(pkg)
        self._update_app_button_label(name)
        if pkg:
            self._log(f"📱 Aplicación seleccionada para Pantalla Virtual: {name} ({pkg})")
        else:
            self._log("🖥️ Pantalla Virtual en modo Escritorio Libre (sin autoarranque).")
        self._debounced_update()

    def _clear_selected_app(self):
        self.v_virtual_display_app.set("")
        self._update_app_button_label()
        self._log("🗑️ Selección de app eliminada (Modo Escritorio Libre).")
        self._debounced_update()

    def _update_app_button_label(self, name_hint=None):
        pkg = self.v_virtual_display_app.get().strip()
        if not pkg:
            text = "🔍 Seleccionar App a abrir..."
            color = COLORS["text2"]
        else:
            name = name_hint or pkg.split(".")[-1].capitalize()
            text = f"📱 {name} ({pkg})"
            color = COLORS["accent"]
            
        if hasattr(self, "btn_open_app_picker"):
            self.btn_open_app_picker.configure(text=text, text_color=color)
        if hasattr(self, "btn_pv_select_app"):
            self.btn_pv_select_app.configure(text=text, text_color=color)

    # ─────────────────────────────────────────────
    #  COMMAND BUILDING
    # ─────────────────────────────────────────────
    def _get_config_dict(self):
        """Collect all tkinter variables into a plain dict for command_builder."""
        return {
            "device": self.v_device.get(),
            "otg_mode": self.v_otg_mode.get(),
            "no_video": self.v_no_video.get(),
            "video_source": self.v_video_source.get(),
            "camera_torch": self.v_camera_torch.get(),
            "camera_zoom": self.v_camera_zoom.get(),
            "camera_id": self.v_camera_id.get(),
            "camera_facing": self.v_camera_facing.get(),
            "camera_fps": self.v_camera_fps.get(),
            "max_size": self.v_max_size.get(),
            "display_id": self.v_display_id.get(),
            "codec": self.v_codec.get(),
            "fps": self.v_fps.get(),
            "bitrate": self.v_bitrate.get(),
            "orientation": self.v_orientation.get(),
            "audio": self.v_audio.get(),
            "audio_source": self.v_audio_source.get(),
            "audio_codec": self.v_audio_codec.get(),
            "audio_buf": self.v_audio_buf.get(),
            "audio_bitrate": self.v_audio_bitrate.get(),
            "audio_dup": self.v_audio_dup.get(),
            "video_buffer": self.v_video_buffer.get(),
            "fullscreen": self.v_fullscreen.get(),
            "always_on_top": self.v_always_on_top.get(),
            "borderless": self.v_borderless.get(),
            "disable_screensaver": self.v_disable_screensaver.get(),
            "stay_awake": self.v_stay_awake.get(),
            "screen_off": self.v_screen_off.get(),
            "keep_active": self.v_keep_active.get(),
            "background_color": self.v_background_color.get(),
            "no_aspect_ratio_lock": self.v_no_aspect_ratio_lock.get(),
            "virtual_display": self.v_virtual_display.get(),
            "virtual_display_res": self.v_virtual_display_res.get(),
            "virtual_dpi": self.v_virtual_dpi.get(),
            "flex_display": self.v_flex_display.get(),
            "virtual_display_app": self.v_virtual_display_app.get(),
            "no_vd_decorations": self.v_no_vd_decorations.get(),
            "no_vd_destroy": self.v_no_vd_destroy.get(),
            "v4l2_device": self.v_v4l2_device.get(),
            "no_control": self.v_no_control.get(),
            "keyboard": self.v_keyboard.get(),
            "mouse": self.v_mouse.get(),
            "gamepad": self.v_gamepad.get(),
            "no_clipboard_sync": self.v_no_clipboard_sync.get(),
            "record": self.v_record.get(),
            "record_file": self.v_record_file.get(),
            "time_limit": self.v_time_limit.get(),
            "print_fps": self.v_print_fps.get(),
            "show_touches": self.v_show_touches.get(),
            "crop": self.v_crop.get(),
            "window_title": self.v_window_title.get(),
            "ignore_encoder_constraints": self.v_ignore_encoder_constraints.get(),
            "no_audio_playback": self.v_no_audio_playback.get(),
            "no_playback": self.v_no_playback.get(),
            "audio_output_buf": self.v_audio_output_buf.get(),
            "legacy_paste": self.v_legacy_paste.get(),
            "force_adb_forward": self.v_force_adb_forward.get(),
            "camera_high_speed": self.v_camera_high_speed.get(),
            "kill_adb_on_close": self.v_kill_adb_on_close.get(),
        }

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
        self._log("📋 Comando copiado.")

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
            while not self.log_queue.empty():
                batch.append(self.log_queue.get_nowait())
                if len(batch) > 50:
                    break
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
    #  LAUNCH / STOP
    # ─────────────────────────────────────────────
    def _launch(self):
        scrcpy_path = mgr.get_scrcpy_path()
        if not scrcpy_path:
            self._log("❌ scrcpy.exe no encontrado.")
            return
        with self._process_lock:
            if self.process and self.process.poll() is None:
                self._log("⚠️ scrcpy ya está en ejecución.")
                return
        
        args = [scrcpy_path] + self._build_args()
        self._log(f"▶ Ejecutando: {' '.join(args)}")
        
        # UI state change
        self.btn_launch.pack_forget()
        self.btn_stop.configure(state="normal", text="⏹ Detener")
        self.btn_stop.pack(side="right", pady=9)
        
        # Start the log updater for real-time output
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
                with self._process_lock:
                    self.process = proc
                
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        self._log(line.rstrip())
                
                proc.wait()
                self._log(f"⏹ scrcpy terminó (código {proc.returncode})")
            except Exception as e:
                self._log(f"❌ Error: {e}")
            finally:
                self.after(0, self._on_process_end)
                
        threading.Thread(target=run, daemon=True).start()

    def _on_process_end(self):
        with self._process_lock:
            self.process = None
        self._stop_log_updater()
        self.btn_stop.pack_forget()
        self.btn_launch.configure(fg_color=COLORS["green"], text="✅ Terminado")
        self.btn_launch.pack(side="right", pady=9)
        self.btn_stop.configure(state="normal", text="⏹ Detener")
        def reset_btn():
            with self._process_lock:
                if self.process is None and hasattr(self, "btn_launch"):
                    self.btn_launch.configure(fg_color=COLORS["accent"], text="▶ Iniciar Scrcpy")
        self.after(3000, reset_btn)

    def _stop(self):
        with self._process_lock:
            proc = self.process
        if proc and proc.poll() is None:
            self.btn_stop.configure(state="disabled", text="⌛ Deteniendo...")
            self._log("⏹ Deteniendo scrcpy...")
            
            def force_kill():
                if not proc:
                    return
                try:
                    proc.terminate()
                    for _ in range(20):
                        if proc.poll() is not None:
                            return
                        time.sleep(0.1)
                    
                    if proc.poll() is None:
                        self._log("⚠️ No responde, forzando cierre...")
                        proc.kill()
                except Exception as e:
                    self._log(f"⚠️ Error al detener: {e}")

            threading.Thread(target=force_kill, daemon=True).start()

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
            self._log("⚠️ Conecta el teléfono por USB primero"); return
        self._log(f"⚡ Automatizando paso a Wi-Fi para {dev}...")
        def run():
            res = mgr.enable_tcpip(dev)
            def done():
                self._log(f"ℹ️ {res}")
                if "Conectado" in res:
                    ip_part = res.split(" ")[2]
                    self.v_wifi_ip.set(f"{ip_part}:5555")
                    self._log("✅ Ya puedes desconectar el cable USB.")
                self._refresh_devices()
            self.after(0, done)
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    ScrcpyGUI().mainloop()
