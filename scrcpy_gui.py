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
import os
import shutil
import json
import scrcpy_manager as mgr

# ── Presets ──
PRESETS = {
    "video": {
        "label": "💎 Cinema 4K (2026 AV1)", "desc": "Máxima fidelidad Next-Gen (AV1)",
        "badge": "Ultra/AV1",
        "codec": "av1", "max_size": 3840, "fps": 60, "bitrate": 32,
        "audio": True, "audio_buffer": 60, "video_buffer": 10,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
    },
    "gaming": {
        "label": "🎮 Gaming Pro (144Hz/HID)", "desc": "Latencia cero para eSports",
        "badge": "Low Latency",
        "codec": "h265", "max_size": 1920, "fps": 144, "bitrate": 16,
        "audio": True, "audio_buffer": 20, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": True,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": True,
        "record": False, "record_file": "", "print_fps": True,
        "show_touches": False, "crop": "",
    },
    "balanced": {
        "label": "⚖️ Inalámbrico (Wi-Fi 7/6E)", "desc": "Optimizado para redes modernas",
        "badge": "Wi-Fi 2K",
        "codec": "h265", "max_size": 2560, "fps": 60, "bitrate": 14,
        "audio": True, "audio_buffer": 80, "video_buffer": 15,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
    },
    "ultra": {
        "label": "🚀 Studio Creator", "desc": "Grabación RAW y edición",
        "badge": "Master",
        "codec": "h264", "max_size": 0, "fps": 60, "bitrate": 48,
        "audio": True, "audio_buffer": 40, "video_buffer": 5,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": False,
        "record": True, "record_file": "studio_rec_%Y%m%d_%H%M%S.mp4", "print_fps": True,
        "show_touches": True, "crop": "",
    },
}

# ── Theme ──
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#0f1219", "card": "#1a1f2e", "card_hover": "#232a3d", "border": "#2a3146",
    "accent": "#22d3ee", "purple": "#a78bfa", "green": "#34d399", "orange": "#fb923c",
    "text": "#f1f5f9", "text2": "#94a3b8", "muted": "#64748b", "danger": "#ef4444",
}

MODE_COLORS = {
    "video": "#22d3ee", "gaming": "#a78bfa", "balanced": "#34d399", "ultra": "#f472b6", "custom": "#fb923c",
}

class ScrcpyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScrcpyGUI")
        self.geometry("920x740")
        self.minsize(800, 600)
        self.configure(fg_color=COLORS["bg"])

        self.active_mode = ctk.StringVar(value="")
        self.process = None
        self.mode_buttons = {}

        # ── Config variables ──
        self.v_codec = ctk.StringVar(value="h264")
        self.v_max_size = ctk.StringVar(value="1920")
        self.v_fps = ctk.IntVar(value=60)
        self.v_bitrate = ctk.IntVar(value=8)
        self.v_audio = ctk.BooleanVar(value=True)
        self.v_audio_buf = ctk.IntVar(value=50)
        self.v_video_buf = ctk.IntVar(value=0)
        self.v_fullscreen = ctk.BooleanVar(value=False)
        self.v_stay_awake = ctk.BooleanVar(value=True)
        self.v_screen_off = ctk.BooleanVar(value=False)
        self.v_keyboard = ctk.StringVar(value="")
        self.v_mouse = ctk.StringVar(value="")
        self.v_gamepad = ctk.BooleanVar(value=False)
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
        self.v_virtual_display_res = ctk.StringVar(value="1920x1080")
        self.v_video_source = ctk.StringVar(value="display")
        self.v_camera_id = ctk.StringVar(value="0")
        self.v_camera_size = ctk.StringVar(value="")
        self.v_v4l2_device = ctk.StringVar(value="")
        self.v_wifi_ip = ctk.StringVar(value="")
        self.v_wifi_pair_code = ctk.StringVar(value="")
        self.v_display_id = ctk.StringVar(value="0")

        self._build_ui()
        self._update_command()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=16, pady=8)
        self._build_header()
        self._build_updater()
        self._build_status()
        self._build_wireless()
        self._build_modes()
        self._build_custom_panel()
        self._build_quick_settings()
        self._build_command_preview()
        self._build_launch()

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title and OS Badge
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
            # On Linux, only show check (manual install instruction)
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
                except: pass
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
                    self.scrcpy_status.configure(text=f"✅ scrcpy {tag} instalado en {mgr.SCRCPY_DIR}", text_color=COLORS["green"])
                    self.btn_download.pack_forget()
                    self._log(f"✅ scrcpy {tag} descargado correctamente.")
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
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="col")
        for i, (key, p) in enumerate(PRESETS.items()): self._mode_card(grid, key, p["label"], p["desc"], p["badge"], i)
        self._mode_card(grid, "custom", "⚙️  Personalizado", "Configura cada parámetro", "Avanzado", len(PRESETS))

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
        if key == "custom": self.custom_frame.pack(fill="x", pady=(8, 12), after=self._modes_anchor)
        else:
            self.custom_frame.pack_forget()
            self._apply_preset(PRESETS[key])
        self._update_command()

    def _apply_preset(self, p):
        self.v_codec.set(p["codec"]); self.v_max_size.set(str(p["max_size"])); self.v_fps.set(p["fps"])
        self.v_bitrate.set(p["bitrate"]); self.v_audio.set(p["audio"]); self.v_audio_buf.set(p["audio_buffer"])
        self.v_video_buf.set(p["video_buffer"]); self.v_fullscreen.set(p["fullscreen"])
        self.v_stay_awake.set(p["stay_awake"]); self.v_screen_off.set(p["screen_off"])
        self.v_keyboard.set(p["keyboard"]); self.v_mouse.set(p["mouse"]); self.v_gamepad.set(p["gamepad"])
        self.v_record.set(p["record"]); self.v_print_fps.set(p["print_fps"]); self.v_show_touches.set(p["show_touches"])
        self.v_crop.set(p["crop"])

    def _build_custom_panel(self):
        self._modes_anchor = ctk.CTkFrame(self.scroll, fg_color="transparent", height=1); self._modes_anchor.pack(fill="x")
        self.custom_frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        ctk.CTkLabel(self.custom_frame, text="🔧 Configuración Personalizada", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["orange"]).pack(fill="x", padx=16, pady=(14, 10))
        cols = ctk.CTkFrame(self.custom_frame, fg_color="transparent"); cols.pack(fill="x", padx=12, pady=(0, 14))
        cols.columnconfigure((0, 1, 2), weight=1, uniform="cfg")
        c0 = self._cfg_group(cols, "🎥 Video y Cámara", 0)
        self._cfg_option_menu(c0, "Fuente Video", self.v_video_source, ["display", "camera"])
        self._cfg_option_menu(c0, "Códec", self.v_codec, ["h264", "h265", "av1"])
        self._cfg_entry(c0, "Cámara ID / Res", self.v_camera_id) # Dual use for simple UI
        self._cfg_slider(c0, "FPS", self.v_fps, 15, 120)
        self._cfg_slider(c0, "Bitrate (Mbps)", self.v_bitrate, 1, 32)
        c1 = self._cfg_group(cols, "🔊 Audio y Pantalla", 1)
        self._cfg_switch(c1, "Audio activado", self.v_audio)
        self._cfg_option_menu(c1, "Fuente Audio", self.v_audio_source, ["output", "mic"])
        self._cfg_option_menu(c1, "Codec Audio", self.v_audio_codec, ["opus", "aac", "raw"])
        self._cfg_slider(c1, "Buffer audio (ms)", self.v_audio_buf, 0, 500)
        self._cfg_entry(c1, "Display ID (0=Principal)", self.v_display_id)
        self._cfg_switch(c1, "🖥️ Nueva Pantalla Virtual", self.v_virtual_display)
        self._cfg_entry(c1, "Res. Virtual (Sugerido 1280x720)", self.v_virtual_display_res)
        self.v_virtual_display_res.set("1280x720")
        self._cfg_switch(c1, "Pantalla completa", self.v_fullscreen); self._cfg_switch(c1, "Siempre al frente", self.v_always_on_top); self._cfg_switch(c1, "Sin bordes", self.v_borderless)
        if not mgr.IS_WINDOWS:
            # Linux Only Features
            l_frame = ctk.CTkFrame(c1, fg_color=COLORS["border"], corner_radius=6)
            l_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(l_frame, text="🐧 Sólo Linux", font=ctk.CTkFont(size=9, weight="bold"), text_color=COLORS["accent"]).pack(pady=(2,0))
            self._cfg_entry(l_frame, "V4L2 Sink", self.v_v4l2_device)
        c2 = self._cfg_group(cols, "🎛️ Controles y Graba", 2)
        self._cfg_option_menu(c2, "Teclado", self.v_keyboard, ["", "uhid", "aoa", "disabled"])
        self._cfg_option_menu(c2, "Ratón", self.v_mouse, ["", "uhid", "aoa", "disabled"])
        self._cfg_switch(c2, "Gamepad (UHID)", self.v_gamepad)
        self._cfg_switch(c2, "🔴 Grabar sesión", self.v_record)
        self._cfg_entry(c2, "Archivo rec", self.v_record_file)
        self._cfg_switch(c2, "Mostrar toques", self.v_show_touches)
        self._cfg_entry(c2, "Crop (WxH:X:Y)", self.v_crop)

    def _cfg_group(self, parent, title, col):
        f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10); f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(fill="x", padx=10, pady=(10, 6))
        return f

    def _cfg_option_menu(self, parent, label, var, values):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        m = ctk.CTkOptionMenu(parent, variable=var, values=values, width=180, fg_color=COLORS["card"], button_color=COLORS["border"], command=lambda _: self._update_command())
        m.pack(padx=12, pady=(2, 4), anchor="w")

    def _cfg_entry(self, parent, label, var):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(anchor="w", padx=12, pady=(6, 0))
        e = ctk.CTkEntry(parent, textvariable=var, width=180, fg_color=COLORS["card"], border_color=COLORS["border"])
        e.pack(padx=12, pady=(2, 4), anchor="w"); var.trace_add("write", lambda *_: self._update_command())

    def _cfg_slider(self, parent, label, var, from_, to):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=12, pady=(6, 4))
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
        val_label = ctk.CTkLabel(row, text=str(var.get()), font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"], width=40); val_label.pack(side="right")
        def on_slide(v): var.set(int(float(v))); val_label.configure(text=str(int(float(v)))); self._update_command()
        ctk.CTkSlider(parent, from_=from_, to=to, variable=var, width=180, command=on_slide, progress_color=COLORS["accent"], button_color=COLORS["accent"]).pack(padx=12, anchor="w")

    def _cfg_switch(self, parent, label, var):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
        ctk.CTkSwitch(row, text="", variable=var, width=40, progress_color=COLORS["accent"], command=self._update_command).pack(side="right")

    def _build_quick_settings(self):
        f = ctk.CTkFrame(self.scroll, fg_color="transparent")
        f.pack(fill="x", pady=(0, 8))
        row = ctk.CTkFrame(f, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        row.pack(fill="x")
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(padx=16, pady=10)
        ctk.CTkLabel(inner, text="📱 Apagar pantalla al iniciar:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(side="left", padx=(0, 10))
        ctk.CTkSwitch(inner, text="", variable=self.v_screen_off, width=40, progress_color=COLORS["accent"], command=self._update_command).pack(side="left", padx=(0, 40))
        ctk.CTkLabel(inner, text="💡 Mantener dispositivo despierto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"]).pack(side="left", padx=(0, 10))
        ctk.CTkSwitch(inner, text="", variable=self.v_stay_awake, width=40, progress_color=COLORS["accent"], command=self._update_command).pack(side="left")

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

    def _build_args(self):
        args = []
        # Device
        dev = self.v_device.get().split(" (")[0]
        if dev and "Buscando" not in dev and "Sin dispositivos" not in dev:
            args.extend(["-s", dev])

        # Video Source
        src = self.v_video_source.get()
        if src == "camera":
            args.append("--video-source=camera")
            cid = self.v_camera_id.get().strip()
            if cid: args.append(f"--camera-id={cid}")
        else:
            ms = self.v_max_size.get().strip()
            if ms and ms != "0": args.append(f"--max-size={ms}")
            did = self.v_display_id.get().strip()
            if did and did != "0": args.append(f"--display-id={did}")

        codec = self.v_codec.get(); 
        if codec and codec != "h264": args.append(f"--video-codec={codec}")
        fps = self.v_fps.get()
        if fps: args.append(f"--max-fps={fps}")
        br = self.v_bitrate.get()
        if br and br != 8: args.append(f"--video-bit-rate={br}M")
        
        if not self.v_audio.get(): args.append("--no-audio")
        else:
            src = self.v_audio_source.get()
            if src != "output": args.append(f"--audio-source={src}")
            ac = self.v_audio_codec.get()
            if ac != "opus": args.append(f"--audio-codec={ac}")
            ab = self.v_audio_buf.get()
            if ab > 0: args.append(f"--audio-buffer={ab}")
        
        vb = self.v_video_buf.get()
        if vb > 0: args.append(f"--video-buffer={vb}")
        if self.v_fullscreen.get(): args.append("--fullscreen")
        if self.v_always_on_top.get(): args.append("--always-on-top")
        if self.v_borderless.get(): args.append("--window-borderless")
        if self.v_stay_awake.get(): args.append("--stay-awake")
        if self.v_screen_off.get(): args.append("--turn-screen-off")
        
        if self.v_virtual_display.get():
            res = self.v_virtual_display_res.get().strip() or "1920x1080"
            args.append(f"--new-display={res}")
        
        if not mgr.IS_WINDOWS and self.v_v4l2_device.get().strip():
            args.append(f"--v4l2-sink={self.v_v4l2_device.get().strip()}")
        
        kb = self.v_keyboard.get()
        if kb: args.append(f"--keyboard={kb}")
        ms2 = self.v_mouse.get()
        if ms2: args.append(f"--mouse={ms2}")
        if self.v_gamepad.get(): args.append("--gamepad=uhid")
        
        if self.v_record.get():
            rf = self.v_record_file.get().strip() or "recording.mp4"
            args.append(f"--record={rf}")
        
        if self.v_print_fps.get(): args.append("--print-fps")
        if self.v_show_touches.get(): args.append("--show-touches")
        crop = self.v_crop.get().strip()
        if crop: args.append(f"--crop={crop}")
        return args

    def _update_command(self):
        args = self._build_args(); exe = mgr.get_scrcpy_path() or "scrcpy"
        self.cmd_label.configure(text=" ".join([os.path.basename(exe)] + args))

    def _copy_command(self):
        args = self._build_args(); exe = mgr.get_scrcpy_path() or "scrcpy"
        self.clipboard_clear(); self.clipboard_append(" ".join([exe] + args)); self._log("📋 Comando copiado.")

    def _log(self, msg):
        self.log_box.configure(state="normal"); self.log_box.insert("end", msg + "\n"); self.log_box.see("end"); self.log_box.configure(state="disabled")

    def _launch(self):
        scrcpy_path = mgr.get_scrcpy_path()
        if not scrcpy_path: self._log("❌ scrcpy.exe no encontrado."); return
        if self.process and self.process.poll() is None: self._log("⚠️ scrcpy ya está en ejecución."); return
        args = [scrcpy_path] + self._build_args()
        self._log(f"▶ Ejecutando: {' '.join(args)}")
        self.btn_launch.pack_forget(); self.btn_stop.pack(fill="x", pady=(0, 4), before=self.log_box)
        def run():
            try:
                kwargs = {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "cwd": os.path.dirname(scrcpy_path)
                }
                if mgr.IS_WINDOWS:
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                
                self.process = subprocess.Popen(args, **kwargs)
                for line in self.process.stdout: self.after(0, self._log, line.rstrip())
                self.process.wait()
                self.after(0, self._log, f"⏹ scrcpy terminó (código {self.process.returncode})")
            except Exception as e: self.after(0, self._log, f"❌ Error: {e}")
            finally: self.after(0, self._on_process_end)
        threading.Thread(target=run, daemon=True).start()

    def _on_process_end(self):
        self.process = None; self.btn_stop.pack_forget(); self.btn_launch.pack(fill="x", pady=(0, 4), before=self.log_box)

    def _stop(self):
        if self.process and self.process.poll() is None: self.process.terminate(); self._log("⏹ Deteniendo scrcpy...")


    def _build_wireless(self):
        f = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        f.pack(fill="x", pady=(0, 12))
        
        title_f = ctk.CTkFrame(f, fg_color="transparent")
        title_f.pack(fill="x", padx=14, pady=(10, 5))
        ctk.CTkLabel(title_f, text="🔗 Conexión Inalámbrica (ADB Wi-Fi)", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(side="left")
        
        row1 = ctk.CTkFrame(f, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=5)
        
        self.e_wifi_ip = ctk.CTkEntry(row1, placeholder_text="IP:Puerto (ej: 192.168.1.10:5555)", textvariable=self.v_wifi_ip, width=280, height=32)
        self.e_wifi_ip.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(row1, text="Conectar", width=120, height=32, fg_color=COLORS["accent"], text_color=COLORS["bg"], font=ctk.CTkFont(size=11, weight="bold"), command=self._wifi_connect).pack(side="left", padx=(0, 5))
        ctk.CTkButton(row1, text="Pasar a Wi-Fi (USB)", width=140, height=32, fg_color="transparent", border_width=1, border_color=COLORS["border"], font=ctk.CTkFont(size=11), command=self._wifi_enable_tcpip).pack(side="left")

        # Pairing Section (Hidden by default or smaller)
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(5, 10))
        
        ctk.CTkLabel(row2, text="Emparejar (Android 11+):", font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left", padx=(0, 10))
        self.e_wifi_code = ctk.CTkEntry(row2, placeholder_text="Código", textvariable=self.v_wifi_pair_code, width=100, height=28)
        self.e_wifi_code.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row2, text="Emparejar", width=100, height=28, fg_color=COLORS["purple"], font=ctk.CTkFont(size=11), command=self._wifi_pair).pack(side="left")

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
