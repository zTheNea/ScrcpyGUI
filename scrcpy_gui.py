"""
ScrcpyGUI — Native Windows GUI for scrcpy
Allows selecting preconfigured modes (Video, Gaming, Balanced) or custom config.
Launches scrcpy directly from the interface.
Auto-downloads and updates scrcpy from GitHub.
"""
import customtkinter as ctk
from customtkinter import filedialog
import subprocess
import threading
import queue
import time
import os
import shutil
import json
import re
from datetime import datetime
import scrcpy_manager as mgr
import config_manager as cfg
from command_builder import build_scrcpy_args
from presets import (
    PRESETS, VIRTUAL_RES_PRESETS, AUDIO_SOURCES, AUDIO_CODECS,
    KEYBOARD_MODES, MOUSE_MODES, GAMEPAD_MODES, ORIENTATION_VALUES,
    CAMERA_FACING, COLORS, MODE_COLORS,
)

# ── Theme ──
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ScrcpyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScrcpyGUI v1.2.1")
        self.geometry("920x740")
        self.minsize(800, 600)
        self.configure(fg_color=COLORS["bg"])

        self.active_mode = ctk.StringVar(value="")
        self.process = None
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
        
        # scrcpy v4.0 variables
        self.v_flex_display = ctk.BooleanVar(value=False)
        self.v_camera_torch = ctk.BooleanVar(value=False)
        self.v_camera_zoom = ctk.StringVar(value="")
        self.v_keep_active = ctk.BooleanVar(value=False)
        self.v_background_color = ctk.StringVar(value="")
        self.v_no_aspect_ratio_lock = ctk.BooleanVar(value=False)
        self.v_otg_mode = ctk.BooleanVar(value=False)

        # Widget references for enabling/disabling
        self.widgets = {}

        self._build_ui()
        self._add_traces()
        self._schedule_log_updater()
        
        # Load saved config AFTER building UI so widgets exist
        loaded, saved_mode = cfg.load_config(self)
        if loaded:
            if saved_mode and saved_mode in (set(PRESETS) | {"custom"}):
                self._select_mode(saved_mode)
            self._log("💾 Configuración anterior restaurada.")
        
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
            self.v_no_control, self.v_no_video, self.v_camera_id, self.v_otg_mode
        ]
        for v in vars_to_trace:
            v.trace_add("write", lambda *_: self._debounced_update())
        
        # Others that only update command
        other_vars = [self.v_codec, self.v_fps, self.v_bitrate, self.v_audio_source, self.v_audio_codec, 
                      self.v_audio_buf, self.v_display_id, self.v_virtual_display_res, self.v_virtual_display_app,
                      self.v_orientation, self.v_audio_bitrate, self.v_audio_dup, self.v_video_buffer,
                      self.v_time_limit, self.v_camera_facing, self.v_camera_fps, self.v_virtual_dpi,
                      self.v_no_vd_decorations, self.v_no_vd_destroy, self.v_no_clipboard_sync,
                      self.v_disable_screensaver, self.v_flex_display, self.v_camera_torch,
                      self.v_camera_zoom, self.v_keep_active, self.v_background_color,
                      self.v_no_aspect_ratio_lock]
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
    #  UI BUILDING
    # ─────────────────────────────────────────────
    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=16, pady=8)
        self._build_header()
        self._build_updater()
        self._build_status()
        self._build_modes()
        self._build_tabview()
        self._build_command_preview()
        self._build_launch()

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(20, 10))
        
        title_f = ctk.CTkFrame(head, fg_color="transparent")
        title_f.pack(side="left")
        
        ctk.CTkLabel(title_f, text="Scrcpy", font=ctk.CTkFont(size=32, weight="bold"), text_color=COLORS["orange"]).pack(side="left")
        ctk.CTkLabel(title_f, text="GUI", font=ctk.CTkFont(size=32, weight="bold"), text_color=COLORS["text"]).pack(side="left")
        
        os_name = "Windows" if mgr.IS_WINDOWS else "Linux/macOS"
        ctk.CTkLabel(head, text=f"Sistema: {os_name}", font=ctk.CTkFont(size=10, weight="bold"), fg_color=COLORS["border"], text_color=COLORS["text2"], corner_radius=4, padx=6).pack(side="right", pady=10)

    def _build_updater(self):
        f = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        f.pack(fill="x", pady=(8, 8))
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)
        self.scrcpy_status = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=12), text_color=COLORS["text2"])
        self.scrcpy_status.pack(side="left")
        
        self.btn_download = ctk.CTkButton(row, text="⬇️ Descargar scrcpy", width=160, height=30, font=ctk.CTkFont(size=11), fg_color=COLORS["accent"], text_color=COLORS["bg"], hover_color="#06b6d4", command=self._start_download)
        self.btn_check = ctk.CTkButton(row, text="🔍 Buscar actualización", width=160, height=30, font=ctk.CTkFont(size=11), fg_color=COLORS["border"], hover_color=COLORS["card_hover"], command=self._check_update)
        
        if mgr.IS_WINDOWS:
            self.btn_download.pack(side="right", padx=(8, 0))
            self.btn_check.pack(side="right")
        else:
            ctk.CTkLabel(row, text="(Usa tu gestor de paquetes)", font=ctk.CTkFont(size=10), text_color=COLORS["text2"]).pack(side="right")

        self.dl_progress = ctk.CTkProgressBar(f, progress_color=COLORS["accent"], height=6)
        self.dl_progress.set(0)
        self.dl_progress.pack(fill="x", padx=14, pady=(0, 10))
        self.dl_progress.pack_forget()

        self._latest_url, self._latest_tag = "", ""
        path = mgr.get_scrcpy_path()
        ver = mgr.get_installed_version()
        if path:
            self.scrcpy_status.configure(text=f"✅ scrcpy {ver or 'instalado'} — {os.path.dirname(path)}", text_color=COLORS["green"])
            self.btn_download.pack_forget()
        else:
            if mgr.IS_WINDOWS:
                self.scrcpy_status.configure(text="❌ scrcpy no encontrado", text_color=COLORS["danger"])
            else:
                self.scrcpy_status.configure(text="❌ scrcpy no instalado. Instálalo con: sudo apt install scrcpy", text_color=COLORS["danger"])
                self.btn_download.pack_forget()
                self.btn_check.pack_forget()

    def _check_update(self):
        self.scrcpy_status.configure(text="🔍 Buscando actualizaciones...", text_color=COLORS["orange"])
        mgr.check_latest(self._on_check_result)

    def _on_check_result(self, tag, url, err):
        def update():
            if err:
                self.scrcpy_status.configure(text=f"⚠️ Error: {err}", text_color=COLORS["danger"])
                return
            installed = mgr.get_installed_version()
            self._latest_tag, self._latest_url = tag, url
            if installed == tag:
                self.scrcpy_status.configure(text=f"✅ scrcpy {tag} — Ya tienes la última versión", text_color=COLORS["green"])
                self.btn_download.pack_forget()
            else:
                self.scrcpy_status.configure(text=f"🆕 Nueva versión disponible: {tag}" + (f" (actual: {installed})" if installed else ""), text_color=COLORS["accent"])
                self.btn_download.configure(text=f"⬇️ Descargar {tag}")
                try: self.btn_download.pack(side="right", padx=(8, 0))
                except Exception: pass
        self.after(0, update)

    def _start_download(self):
        url, tag = self._latest_url, self._latest_tag
        if not url: self._check_update(); return
        self.btn_download.configure(state="disabled", text="Descargando...")
        self.dl_progress.set(0)
        self.dl_progress.pack(fill="x", padx=14, pady=(0, 10))
        self.scrcpy_status.configure(text="⬇️ Descargando scrcpy...", text_color=COLORS["orange"])
        def on_progress(p):
            if p < 0: self.after(0, lambda: self.scrcpy_status.configure(text="📦 Extrayendo archivos..."))
            else: self.after(0, lambda: self.dl_progress.set(p))
        def on_done(err):
            def finish():
                self.dl_progress.pack_forget()
                if err:
                    self.scrcpy_status.configure(text=f"❌ Error: {err}", text_color=COLORS["danger"])
                    self.btn_download.configure(state="normal", text="⬇️ Reintentar")
                else:
                    mgr._save_version(tag, url)
                    self._scrcpy_path_cache = mgr.get_scrcpy_path()
                    self.scrcpy_status.configure(text=f"✅ scrcpy {tag} instalado en {mgr.SCRCPY_DIR}", text_color=COLORS["green"])
                    self.btn_download.pack_forget()
                    self._log(f"✅ scrcpy {tag} descargado correctamente.")
                    self._update_command()
            self.after(0, finish)
        mgr.download_and_install(url, progress_cb=on_progress, done_cb=on_done)

    def _build_status(self):
        f = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        f.pack(fill="x", pady=(8, 12))
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(inner, text="📱 Dispositivo:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text2"]).pack(side="left", padx=(0, 10))
        self.device_menu = ctk.CTkOptionMenu(inner, variable=self.v_device, values=["Buscando..."], width=300, height=32, fg_color=COLORS["bg"], button_color=COLORS["border"], dynamic_resizing=False, command=lambda _: self._update_command())
        self.device_menu.pack(side="left")
        ctk.CTkButton(inner, text="🔄 Refrescar", width=100, height=32, fg_color="transparent", border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=11), hover_color=COLORS["card_hover"], command=self._refresh_devices).pack(side="right")
        self.after(500, self._refresh_devices)

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
            else:
                vals = [f"{d[0]} ({d[1]})" for d in devs]
                self.device_menu.configure(values=vals)
                if self.v_device.get() not in vals:
                    self.v_device.set(vals[0])
            self._update_command()
        self.after(0, update)

    def _build_modes(self):
        ctk.CTkLabel(self.scroll, text="Selecciona un Modo", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(self.scroll, text="Elige un perfil optimizado o crea tu configuración", font=ctk.CTkFont(size=12), text_color=COLORS["muted"], anchor="w").pack(fill="x", pady=(0, 10))
        
        # Row 1
        grid1 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid1.pack(fill="x", pady=(0, 10))
        grid1.columnconfigure((0, 1, 2, 3), weight=1, uniform="col")
        
        # Row 2
        grid2 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid2.pack(fill="x")
        grid2.columnconfigure((0, 1, 2, 3), weight=1, uniform="col")
        
        items = list(PRESETS.items())
        # First 4 presets in grid1
        for i in range(min(4, len(items))):
            key, p = items[i]
            self._mode_card(grid1, key, p["label"], p["desc"], p["badge"], i)
            
        # Remaining presets + custom in grid2
        for i in range(4, len(items)):
            key, p = items[i]
            self._mode_card(grid2, key, p["label"], p["desc"], p["badge"], i - 4)
            
        custom_idx = len(items) if len(items) < 4 else len(items) - 4
        target_grid = grid1 if len(items) < 4 else grid2
        self._mode_card(target_grid, "custom", "⚙️  Personalizado", "Configura cada parámetro", "Avanzado", custom_idx)

    def _mode_card(self, parent, key, title, desc, badge, col):
        color = MODE_COLORS[key]
        frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=14, border_width=1, border_color=COLORS["border"], cursor="hand2")
        frame.grid(row=0, column=col, sticky="nsew", padx=5, pady=4)
        ctk.CTkLabel(frame, text=badge, font=ctk.CTkFont(size=10), text_color=COLORS["muted"], anchor="e").pack(fill="x", padx=12, pady=(10, 0))
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=15, weight="bold"), text_color=color, anchor="w").pack(fill="x", padx=14, pady=(6, 2))
        ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(size=11), text_color=COLORS["text2"], anchor="w", wraplength=180).pack(fill="x", padx=14, pady=(0, 8))
        if key in PRESETS:
            p = PRESETS[key]
            specs = f"{p['codec'].upper()} · {p['max_size']}px · {p['fps']}fps"
            ctk.CTkLabel(frame, text=specs, font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(padx=14, anchor="w", pady=(0, 10))
        frame.bind("<Button-1>", lambda e, k=key: self._select_mode(k))
        for child in frame.winfo_children(): child.bind("<Button-1>", lambda e, k=key: self._select_mode(k))
        self.mode_buttons[key] = frame

    def _select_mode(self, key):
        self.active_mode.set(key)
        for k, frame in self.mode_buttons.items(): frame.configure(border_color=MODE_COLORS[k] if k == key else COLORS["border"], border_width=2 if k == key else 1)
        if key == "custom":
            self.tabview_frame.pack(fill="x", pady=(8, 12), after=self._modes_anchor)
        else:
            self.tabview_frame.pack_forget()
            self._reset_to_defaults()
            self._apply_preset(PRESETS[key])
        self._debounced_update()

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
        
        # Sync UI components that don't auto-update from trace
        self.res_menu.set("1080p")
        self.v_res_menu.set("1280x720")
        self.app_menu.set("Ninguna")
        self._update_command()

    def _apply_preset(self, p):
        self.v_codec.set(p["codec"]); self.v_max_size.set(str(p["max_size"])); self.v_fps.set(p["fps"])
        self.v_bitrate.set(p["bitrate"]); self.v_audio.set(p["audio"]); self.v_audio_buf.set(p["audio_buffer"])
        self.v_video_buffer.set(p["video_buffer"]); self.v_fullscreen.set(p["fullscreen"])
        self.v_stay_awake.set(p["stay_awake"]); self.v_screen_off.set(p["screen_off"])
        self.v_keyboard.set(p["keyboard"]); self.v_mouse.set(p["mouse"])
        self.v_gamepad.set("uhid" if p.get("gamepad") else "")
        self.v_record.set(p["record"]); self.v_print_fps.set(p["print_fps"]); self.v_show_touches.set(p["show_touches"])
        self.v_crop.set(p["crop"])
        if "otg_mode" in p: self.v_otg_mode.set(p["otg_mode"])
        if "keep_active" in p: self.v_keep_active.set(p["keep_active"])
        if "audio_codec" in p: self.v_audio_codec.set(p["audio_codec"])
        if "audio_bitrate" in p: self.v_audio_bitrate.set(p["audio_bitrate"])

    # ─────────────────────────────────────────────
    #  TABVIEW — replaces old _build_custom_panel + _build_quick_settings + _build_wireless
    # ─────────────────────────────────────────────
    def _build_tabview(self):
        self._modes_anchor = ctk.CTkFrame(self.scroll, fg_color="transparent", height=1); self._modes_anchor.pack(fill="x")
        self.tabview_frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        # Don't pack yet — only shown when "Personalizado" is selected

        self.tabview = ctk.CTkTabview(self.tabview_frame, fg_color="transparent",
                                       segmented_button_fg_color=COLORS["bg"],
                                       segmented_button_selected_color=COLORS["accent"],
                                       segmented_button_selected_hover_color="#06b6d4",
                                       segmented_button_unselected_color=COLORS["card"],
                                       segmented_button_unselected_hover_color=COLORS["card_hover"],
                                       text_color=COLORS["bg"],
                                       text_color_disabled=COLORS["muted"])
        self.tabview.pack(fill="x", padx=8, pady=8)

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
        cols = ctk.CTkFrame(tab, fg_color="transparent"); cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="vid")

        # Left column: Video
        c0 = self._cfg_group(cols, "🎬 Video", 0)
        self._cfg_option_menu(c0, "Fuente Video", self.v_video_source, ["display", "camera"])
        self._cfg_option_menu(c0, "Códec", self.v_codec, ["h264", "h265", "av1"])
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

        # Right column: Camera
        c1 = self._cfg_group(cols, "📷 Cámara", 1)
        self.widgets["camera_id"] = self._cfg_entry(c1, "Cámara ID", self.v_camera_id)
        self.widgets["camera_facing"] = self._cfg_option_menu(c1, "Cámara Cara", self.v_camera_facing, CAMERA_FACING)
        self.widgets["camera_fps"] = self._cfg_slider(c1, "Cámara FPS", self.v_camera_fps, 15, 240)
        self.widgets["camera_torch"] = self._cfg_switch(c1, "🔦 Flash de Cámara", self.v_camera_torch)
        self.widgets["camera_zoom"] = self._cfg_entry(c1, "Zoom de Cámara", self.v_camera_zoom)
        self.widgets["crop_entry"] = self._cfg_entry(c1, "Crop (WxH:X:Y)", self.v_crop)
        self.widgets["no_video"] = self._cfg_switch(c1, "🚫 Sin video", self.v_no_video)

    def _build_tab_audio(self, tab):
        """Audio settings tab."""
        c0 = self._cfg_group_full(tab, "🔊 Configuración de Audio")
        self.widgets["audio_switch"] = self._cfg_switch(c0, "Audio activado", self.v_audio)
        self.widgets["audio_source"] = self._cfg_option_menu(c0, "Fuente Audio", self.v_audio_source, AUDIO_SOURCES)
        self.widgets["audio_codec"] = self._cfg_option_menu(c0, "Codec Audio", self.v_audio_codec, AUDIO_CODECS)
        self.widgets["audio_buf"] = self._cfg_slider(c0, "Buffer audio (ms)", self.v_audio_buf, 0, 500)
        self.widgets["audio_dup"] = self._cfg_switch(c0, "🔊 Duplicar audio", self.v_audio_dup)
        self.widgets["audio_bitrate"] = self._cfg_slider(c0, "Audio Bitrate (K)", self.v_audio_bitrate, 32, 320)

    def _build_tab_display(self, tab):
        """Display, Virtual Display, and Window settings tab."""
        cols = ctk.CTkFrame(tab, fg_color="transparent"); cols.pack(fill="x", padx=4, pady=4)
        cols.columnconfigure((0, 1), weight=1, uniform="dsp")

        # Left: Window
        c0 = self._cfg_group(cols, "🪟 Ventana", 0)
        self._cfg_switch(c0, "Pantalla completa", self.v_fullscreen)
        self._cfg_switch(c0, "Siempre al frente", self.v_always_on_top)
        self._cfg_switch(c0, "Sin bordes", self.v_borderless)
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
        self.v_res_menu = ctk.CTkOptionMenu(v_res_row, variable=self.v_virtual_res_preset, values=VIRTUAL_RES_PRESETS, width=100, fg_color=COLORS["card"], button_color=COLORS["border"], command=self._on_v_res_change)
        self.v_res_menu.pack(side="left", padx=(0, 5))
        self.widgets["v_res_menu"] = self.v_res_menu
        self.e_v_res_custom = ctk.CTkEntry(v_res_row, textvariable=self.v_virtual_display_res, width=70, fg_color=COLORS["card"], border_color=COLORS["border"], state="disabled")
        self.e_v_res_custom.pack(side="left", fill="x", expand=True)
        self.widgets["v_res_entry"] = self.e_v_res_custom

        # App selector
        ctk.CTkLabel(c1, text="🚀 App en Pantalla Virtual", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        app_row = ctk.CTkFrame(c1, fg_color="transparent")
        app_row.pack(fill="x", padx=12, pady=(2, 4))
        self.app_menu = ctk.CTkOptionMenu(app_row, values=["Ninguna", "Manual"], width=100, fg_color=COLORS["card"], button_color=COLORS["border"], command=self._on_v_app_change)
        self.app_menu.pack(side="left", padx=(0, 5))
        self.widgets["v_app_menu"] = self.app_menu
        self.btn_refresh_apps = ctk.CTkButton(app_row, text="🔄", width=32, height=32, fg_color=COLORS["bg"], hover_color=COLORS["border"], command=self._refresh_device_apps)
        self.btn_refresh_apps.pack(side="left", padx=(0, 5))
        self.widgets["v_app_refresh"] = self.btn_refresh_apps
        self.e_v_app = ctk.CTkEntry(app_row, textvariable=self.v_virtual_display_app, width=70, fg_color=COLORS["card"], border_color=COLORS["border"], placeholder_text="com.package.name", state="disabled")
        self.e_v_app.pack(side="left", fill="x", expand=True)
        self.widgets["v_app_entry"] = self.e_v_app

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
        self.widgets["no_clipboard"] = self._cfg_switch(c0, "🚫 Sin clipboard sync", self.v_no_clipboard_sync)
        self.widgets["touches_switch"] = self._cfg_switch(c0, "Mostrar toques", self.v_show_touches)
        self._cfg_switch(c0, "📊 Mostrar FPS", self.v_print_fps)

        c1 = self._cfg_group(cols, "🔴 Grabación", 1)
        self.widgets["record_switch"] = self._cfg_switch(c1, "🔴 Grabar sesión", self.v_record)
        self.widgets["record_entry"] = self._cfg_entry(c1, "Archivo rec", self.v_record_file)
        self.widgets["time_limit"] = self._cfg_slider(c1, "⏱ Tiempo límite (s)", self.v_time_limit, 0, 600)
        self.widgets["video_buffer"] = self._cfg_slider(c1, "Video Buffer (ms)", self.v_video_buffer, 0, 500)

    def _build_tab_wifi(self, tab):
        """Wi-Fi / Wireless connection tab."""
        f = ctk.CTkFrame(tab, fg_color="transparent")
        f.pack(fill="x", padx=4, pady=4)
        
        # Header
        header = ctk.CTkFrame(f, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))
        ctk.CTkLabel(header, text="🔗 Conexión Inalámbrica", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(header, text="(ADB over Network / Wi-Fi)", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(side="left", padx=8)

        # Main row: IP + Connect + Auto-USB
        row_main = ctk.CTkFrame(f, fg_color="transparent")
        row_main.pack(fill="x", padx=14, pady=(0, 12))
        self.e_wifi_ip = ctk.CTkEntry(row_main, placeholder_text="Dirección IP:Puerto (ej: 192.168.1.10:5555)", textvariable=self.v_wifi_ip, height=36, font=ctk.CTkFont(size=12))
        self.e_wifi_ip.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(row_main, text="Conectar", width=110, height=36, fg_color=COLORS["accent"], text_color=COLORS["bg"], font=ctk.CTkFont(size=12, weight="bold"), command=self._wifi_connect).pack(side="left", padx=(0, 6))
        ctk.CTkButton(row_main, text="⚡ Auto-USB", width=110, height=36, fg_color="transparent", border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=11), command=self._wifi_enable_tcpip).pack(side="left")

        # Separator
        ctk.CTkFrame(f, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=0)

        # Pairing row
        row_pair = ctk.CTkFrame(f, fg_color="transparent")
        row_pair.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(row_pair, text="Emparejar (Android 11+):", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left", padx=(0, 12))
        self.e_wifi_code = ctk.CTkEntry(row_pair, placeholder_text="Código de 6 dígitos", textvariable=self.v_wifi_pair_code, width=150, height=30, font=ctk.CTkFont(size=11))
        self.e_wifi_code.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_pair, text="Validar Código", width=120, height=30, fg_color=COLORS["purple"], font=ctk.CTkFont(size=11, weight="bold"), command=self._wifi_pair).pack(side="left")

    def _build_tab_profiles(self, tab):
        """User profiles tab — save, load, and delete configurations."""
        f = ctk.CTkFrame(tab, fg_color="transparent")
        f.pack(fill="x", padx=4, pady=4)

        # Header
        ctk.CTkLabel(f, text="💾 Perfiles de Configuración", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(f, text="Guarda tu configuración actual como un perfil para reutilizarla después.", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=(0, 10))

        # Save row
        save_row = ctk.CTkFrame(f, fg_color="transparent")
        save_row.pack(fill="x", padx=14, pady=(0, 10))
        self.v_profile_name = ctk.StringVar(value="")
        ctk.CTkEntry(save_row, textvariable=self.v_profile_name, placeholder_text="Nombre del perfil (ej. Gaming 60fps)", height=36, font=ctk.CTkFont(size=12), width=300).pack(side="left", padx=(0, 10))
        ctk.CTkButton(save_row, text="💾 Guardar Perfil", width=150, height=36, fg_color=COLORS["green"], text_color=COLORS["bg"], font=ctk.CTkFont(size=12, weight="bold"), command=self._save_profile).pack(side="left")

        # Separator
        ctk.CTkFrame(f, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=6)

        # Profile list
        ctk.CTkLabel(f, text="Perfiles guardados:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text2"]).pack(anchor="w", padx=14, pady=(6, 4))
        self.profiles_list_frame = ctk.CTkFrame(f, fg_color="transparent")
        self.profiles_list_frame.pack(fill="x", padx=14, pady=(0, 10))
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

    # ─────────────────────────────────────────────
    #  COMMAND PREVIEW AND LAUNCH
    # ─────────────────────────────────────────────
    def _build_command_preview(self):
        f = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"]); f.pack(fill="x", pady=(8, 8))
        hdr = ctk.CTkFrame(f, fg_color="transparent"); hdr.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(hdr, text="💻 Comando generado", font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(side="left")
        ctk.CTkButton(hdr, text="📋 Copiar", width=70, height=26, fg_color=COLORS["border"], hover_color=COLORS["card_hover"], font=ctk.CTkFont(size=11), command=self._copy_command).pack(side="right")
        self.cmd_label = ctk.CTkLabel(f, text="scrcpy", font=ctk.CTkFont(family="Consolas", size=12), text_color=COLORS["green"], anchor="w", wraplength=850, justify="left")
        self.cmd_label.pack(fill="x", padx=16, pady=(4, 14))

    def _build_launch(self):
        f = ctk.CTkFrame(self.scroll, fg_color="transparent"); f.pack(fill="x", pady=(4, 16))
        self.btn_launch = ctk.CTkButton(f, text="🚀  Iniciar Scrcpy", height=48, font=ctk.CTkFont(size=16, weight="bold"), fg_color=COLORS["accent"], text_color=COLORS["bg"], hover_color="#06b6d4", corner_radius=12, command=self._launch)
        self.btn_launch.pack(fill="x", pady=(0, 4))
        self.btn_stop = ctk.CTkButton(f, text="⏹  Detener", height=38, font=ctk.CTkFont(size=13), fg_color=COLORS["danger"], hover_color="#dc2626", corner_radius=10, command=self._stop)
        self.btn_stop.pack(fill="x", pady=(0, 4)); self.btn_stop.pack_forget()
        self.log_box = ctk.CTkTextbox(f, height=100, fg_color=COLORS["bg"], font=ctk.CTkFont(family="Consolas", size=11), text_color=COLORS["text2"], border_width=1, border_color=COLORS["border"])
        self.log_box.pack(fill="x", pady=(4, 0)); self.log_box.insert("end", "Listo. Selecciona un modo e inicia.\n"); self.log_box.configure(state="disabled")
        if not mgr.get_scrcpy_path(): self._log("⚠️ scrcpy no encontrado. Usa 'Descargar scrcpy' arriba.")

        self._update_ui_states()
        self._update_command()

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
        for key in ["v_res_menu", "v_res_entry", "v_app_menu", "v_app_refresh", "v_app_entry", "vd_dpi", "vd_no_decorations", "vd_no_destroy", "flex_display"]:
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
    def _on_v_app_change(self, val):
        if val == "Manual":
            self.e_v_app.configure(state="normal", border_color=COLORS["accent"])
        elif val == "Ninguna":
            self.e_v_app.configure(state="disabled", border_color=COLORS["border"])
            self.v_virtual_display_app.set("")
        else:
            self.e_v_app.configure(state="disabled", border_color=COLORS["border"])
            pkg = self.app_list_data.get(val, val)
            self.v_virtual_display_app.set(pkg)
        self._debounced_update()

    def _refresh_device_apps(self):
        dev = self.v_device.get().split(" (")[0]
        if not dev or "Buscando" in dev:
            self._log("⚠️ Conecta un dispositivo primero.")
            return
        
        self.btn_refresh_apps.configure(state="disabled", text="⌛")
        def _task():
            apps = mgr.get_installed_apps(dev)
            self.app_list_data = {name: pkg for name, pkg in apps}
            names = ["Ninguna"] + [name for name, _ in apps] + ["Manual"]
            self.after(0, lambda: self._finish_refresh(names))
        
        threading.Thread(target=_task, daemon=True).start()

    def _finish_refresh(self, names):
        self.app_menu.configure(values=names)
        self.btn_refresh_apps.configure(state="normal", text="🔄")
        self._log(f"✅ {len(names)-2} aplicaciones detectadas.")

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
        }

    def _build_args(self):
        return build_scrcpy_args(self._get_config_dict(), is_windows=mgr.IS_WINDOWS)

    def _update_command(self):
        args = self._build_args()
        exe = self._scrcpy_path_cache or "scrcpy"
        self.cmd_label.configure(text=" ".join([os.path.basename(exe)] + args))

    def _copy_command(self):
        args = self._build_args(); exe = mgr.get_scrcpy_path() or "scrcpy"
        self.clipboard_clear(); self.clipboard_append(" ".join([exe] + args)); self._log("📋 Comando copiado.")

    # ─────────────────────────────────────────────
    #  LOGGING
    # ─────────────────────────────────────────────
    def _schedule_log_updater(self):
        """Start the periodic log updater."""
        self._log_updater_running = True
        self._process_log_queue()

    def _process_log_queue(self):
        """Batch process logs from the queue to the text box."""
        if not self._log_updater_running: return
        
        batch = []
        try:
            while not self.log_queue.empty():
                batch.append(self.log_queue.get_nowait())
                if len(batch) > 50: break
        except queue.Empty:
            pass
        
        if batch:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", "\n".join(batch) + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            
        self.after(100, self._process_log_queue)

    def _log(self, msg):
        """Add a message to the log queue."""
        self.log_queue.put(msg)

    # ─────────────────────────────────────────────
    #  LAUNCH / STOP
    # ─────────────────────────────────────────────
    def _launch(self):
        scrcpy_path = mgr.get_scrcpy_path()
        if not scrcpy_path: self._log("❌ scrcpy.exe no encontrado."); return
        if self.process and self.process.poll() is None: self._log("⚠️ scrcpy ya está en ejecución."); return
        
        args = [scrcpy_path] + self._build_args()
        self._log(f"▶ Ejecutando: {' '.join(args)}")
        
        # UI state change
        self.btn_launch.pack_forget()
        self.btn_stop.configure(state="normal", text="⏹  Detener")
        self.btn_stop.pack(fill="x", pady=(0, 4), before=self.log_box)
        
        def run():
            try:
                kwargs = {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "cwd": os.path.dirname(scrcpy_path),
                    "bufsize": 1
                }
                # Optional: For OTG, sometimes we still get output
                if mgr.IS_WINDOWS:
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                
                self.process = subprocess.Popen(args, **kwargs)
                
                for line in iter(self.process.stdout.readline, ''):
                    if line: self._log(line.rstrip())
                
                self.process.wait()
                self._log(f"⏹ scrcpy terminó (código {self.process.returncode})")
            except Exception as e:
                self._log(f"❌ Error: {e}")
            finally:
                self.after(0, self._on_process_end)
                
        threading.Thread(target=run, daemon=True).start()

    def _on_process_end(self):
        self.process = None
        self.btn_stop.pack_forget()
        self.btn_launch.configure(fg_color=COLORS["green"], text="✅ Terminado — Click para reiniciar")
        self.btn_launch.pack(fill="x", pady=(0, 4), before=self.log_box)
        self.btn_stop.configure(state="normal", text="⏹  Detener")
        self.after(3000, lambda: self.btn_launch.configure(
            fg_color=COLORS["accent"], text="🚀  Iniciar Scrcpy"))

    def _stop(self):
        if self.process and self.process.poll() is None:
            self.btn_stop.configure(state="disabled", text="⌛ Deteniendo...")
            self._log("⏹ Deteniendo scrcpy...")
            
            def force_kill():
                if not self.process: return
                try:
                    self.process.terminate()
                    for _ in range(20):
                        if self.process.poll() is not None: return
                        time.sleep(0.1)
                    
                    if self.process.poll() is None:
                        self._log("⚠️ No responde, forzando cierre...")
                        self.process.kill()
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
