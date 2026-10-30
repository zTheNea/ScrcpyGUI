"""Unit tests for command_builder.py using unittest."""
import unittest
from datetime import datetime
from command_builder import build_scrcpy_args, _safe_int, format_record_filename, parse_version


class TestSafeInt(unittest.TestCase):
    def test_valid_int(self):
        self.assertEqual(_safe_int(42), 42)
        self.assertEqual(_safe_int(-10), -10)

    def test_string_int(self):
        self.assertEqual(_safe_int("42"), 42)
        self.assertEqual(_safe_int("0"), 0)

    def test_decimal_values(self):
        self.assertEqual(_safe_int("12.34"), 12)
        self.assertEqual(_safe_int("59.9"), 59)
        self.assertEqual(_safe_int(3.7), 3)

    def test_invalid_values(self):
        self.assertEqual(_safe_int("abc"), 0)
        self.assertEqual(_safe_int(None), 0)
        self.assertEqual(_safe_int(None, default=5), 5)
        self.assertEqual(_safe_int("invalid", default=99), 99)


class TestBuildScrcpyArgs(unittest.TestCase):
    def test_audio_disabled_generates_no_audio(self):
        args = build_scrcpy_args({"audio": False})
        self.assertIn("--no-audio", args)

    def test_device_selection(self):
        args = build_scrcpy_args({"device": "RFC12345 (Galaxy S24)"})
        self.assertIn("-s", args)
        idx = args.index("-s")
        self.assertEqual(args[idx + 1], "RFC12345")

    def test_device_placeholder_ignored(self):
        self.assertNotIn("-s", build_scrcpy_args({"device": "Buscando..."}))
        self.assertNotIn("-s", build_scrcpy_args({"device": "Sin dispositivos"}))

    def test_otg_mode_shortcircuits(self):
        args = build_scrcpy_args({"device": "RFC123", "otg_mode": True, "audio": False, "fps": 120, "bitrate": 16})
        self.assertIn("--otg", args)
        self.assertNotIn("--max-fps=120", args)

    def test_otg_mode_with_audio(self):
        cfg = {
            "device": "RFC123",
            "otg_mode": True,
            "audio": True,
            "audio_codec": "opus",
            "audio_bitrate": 128,
            "stay_awake": True,
        }
        args = build_scrcpy_args(cfg)
        self.assertNotIn("--otg", args)
        self.assertIn("--no-video", args)
        self.assertIn("--keyboard=uhid", args)
        self.assertIn("--mouse=uhid", args)
        self.assertIn("--stay-awake", args)
        self.assertNotIn("--no-audio", args)

    def test_no_video_flag(self):
        args = build_scrcpy_args({"no_video": True})
        self.assertIn("--no-video", args)

    def test_camera_mode_flags(self):
        cfg = {
            "video_source": "camera",
            "camera_torch": True,
            "camera_zoom": "2.5",
            "camera_id": "1",
            "camera_fps": 60,
            "camera_high_speed": True,
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--video-source=camera", args)
        self.assertIn("--camera-torch", args)
        self.assertIn("--camera-zoom=2.5", args)
        self.assertIn("--camera-id=1", args)
        self.assertIn("--camera-fps=60", args)
        self.assertIn("--camera-high-speed", args)

    def test_camera_facing_fallback_when_id_is_zero(self):
        cfg = {
            "video_source": "camera",
            "camera_id": "0",
            "camera_facing": "front",
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--camera-facing=front", args)
        self.assertNotIn("--camera-id=0", args)

    def test_window_title_added(self):
        args = build_scrcpy_args({"window_title": "Custom Mirror Window"})
        self.assertIn("--window-title=Custom Mirror Window", args)

    def test_virtual_display_args(self):
        cfg = {
            "virtual_display": True,
            "virtual_display_res": "1920x1080",
            "virtual_dpi": "320",
            "flex_display": True,
            "virtual_display_app": "com.android.chrome",
            "no_vd_decorations": True,
            "no_vd_destroy": True,
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--new-display=1920x1080/320", args)
        self.assertIn("--flex-display", args)
        self.assertIn("--start-app=com.android.chrome", args)
        self.assertIn("--no-vd-system-decorations", args)
        self.assertIn("--no-vd-destroy-content", args)

    def test_v4l2_platform_handling(self):
        args_win = build_scrcpy_args({"v4l2_device": "/dev/video0"}, is_windows=True)
        self.assertTrue(all("v4l2" not in a for a in args_win))

        args_linux = build_scrcpy_args({"v4l2_device": "/dev/video0"}, is_windows=False)
        self.assertIn("--v4l2-sink=/dev/video0", args_linux)

    def test_audio_options(self):
        cfg = {
            "audio": True,
            "audio_source": "mic",
            "audio_codec": "aac",
            "audio_buf": 100,
            "audio_bitrate": 192,
            "audio_dup": True,
            "no_audio_playback": True,
            "audio_output_buf": 80,
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--audio-source=mic", args)
        self.assertIn("--audio-codec=aac", args)
        self.assertIn("--audio-buffer=100", args)
        self.assertIn("--audio-bit-rate=192K", args)
        self.assertIn("--audio-dup", args)
        self.assertIn("--no-audio-playback", args)
        self.assertIn("--audio-output-buffer=80", args)

    def test_scrcpy_v41_codecs_and_flags(self):
        cfg = {
            "codec": "vp9",
            "ignore_encoder_constraints": True,
            "no_playback": True,
            "legacy_paste": True,
            "force_adb_forward": True,
            "kill_adb_on_close": True,
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--video-codec=vp9", args)
        self.assertIn("--ignore-video-encoder-constraints", args)
        self.assertIn("--no-playback", args)
        self.assertIn("--legacy-paste", args)
        self.assertIn("--force-adb-forward", args)
        self.assertIn("--kill-adb-on-close", args)

    def test_vp8_codec(self):
        args = build_scrcpy_args({"codec": "vp8"})
        self.assertIn("--video-codec=vp8", args)

    def test_desktop_dex_preset_args(self):
        from presets import PRESETS
        cfg = PRESETS["desktop"]
        args = build_scrcpy_args(cfg)
        self.assertIn("--new-display=1920x1080/220", args)
        self.assertIn("--keyboard=uhid", args)
        self.assertIn("--mouse=uhid", args)
        self.assertIn("--audio-codec=aac", args)
        self.assertIn("--audio-buffer=30", args)


    def test_phase1_video_display_options(self):
        cfg = {
            "render_fit": "unscaled",
            "render_driver": "opengl",
            "video_encoder": "c2.android.avc.encoder",
            "no_video_playback": True,
            "capture_orientation": "90",
            "display_orientation": "180",
            "angle": 45,
            "window_x": "100",
            "window_y": "200",
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--render-fit=unscaled", args)
        self.assertIn("--render-driver=opengl", args)
        self.assertIn("--video-encoder=c2.android.avc.encoder", args)
        self.assertIn("--no-video-playback", args)
        self.assertIn("--capture-orientation=90", args)
        self.assertIn("--display-orientation=180", args)
        self.assertIn("--angle=45", args)
        self.assertIn("--window-x=100", args)
        self.assertIn("--window-y=200", args)

    def test_phase1_audio_and_control_options(self):
        cfg = {
            "record_format": "mkv",
            "require_audio": True,
            "audio_encoder": "c2.android.opus.encoder",
            "power_off_on_close": True,
            "no_power_on": True,
            "shortcut_mod": "rctrl",
            "push_target": "/sdcard/Download",
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--record-format=mkv", args)
        self.assertIn("--require-audio", args)
        self.assertIn("--audio-encoder=c2.android.opus.encoder", args)
        self.assertIn("--power-off-on-close", args)
        self.assertIn("--no-power-on", args)
        self.assertIn("--shortcut-mod=rctrl", args)
        self.assertIn("--push-target=/sdcard/Download", args)

    def test_phase2_advanced_options(self):
        cfg = {
            "window_width": "800",
            "window_height": "600",
            "no_window": True,
            "display_ime_policy": "hide",
            "verbosity": "debug",
            "pause_on_exit": "if-error",
            "no_cleanup": True,
            "no_downsize_on_error": True,
            "screen_off_timeout": 60,
            "no_key_repeat": True,
            "prefer_text": True,
            "raw_key_events": True,
            "no_mouse_hover": True,
            "port": "27183:27185",
            "tunnel_host": "192.168.1.10",
            "tunnel_port": "5555",
            "no_terminal_title": True,
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--window-width=800", args)
        self.assertIn("--window-height=600", args)
        self.assertIn("--no-window", args)
        self.assertIn("--display-ime-policy=hide", args)
        self.assertIn("--verbosity=debug", args)
        self.assertIn("--pause-on-exit=if-error", args)
        self.assertIn("--no-cleanup", args)
        self.assertIn("--no-downsize-on-error", args)
        self.assertIn("--screen-off-timeout=60", args)
        self.assertIn("--no-key-repeat", args)
        self.assertIn("--prefer-text", args)
        self.assertIn("--raw-key-events", args)
        self.assertIn("--no-mouse-hover", args)
        self.assertIn("--port=27183:27185", args)
        self.assertIn("--tunnel-host=192.168.1.10", args)
        self.assertIn("--tunnel-port=5555", args)
        self.assertIn("--no-terminal-title", args)

    def test_phase2_camera_extras(self):
        cfg = {
            "video_source": "camera",
            "camera_ar": "16:9",
            "camera_size": "1920x1080",
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--video-source=camera", args)
        self.assertIn("--camera-ar=16:9", args)
        self.assertIn("--camera-size=1920x1080", args)

    def test_phase3_presets(self):
        from presets import PRESETS

        # 1. Headless Record
        cfg_rec = PRESETS["headless_record"]
        args_rec = build_scrcpy_args(cfg_rec)
        self.assertIn("--no-video-playback", args_rec)
        self.assertIn("--no-audio-playback", args_rec)
        self.assertTrue(any(a.startswith("--record=") for a in args_rec))

        # 2. Camera Document
        cfg_cam = PRESETS["camera_doc"]
        args_cam = build_scrcpy_args(cfg_cam)
        self.assertIn("--video-source=camera", args_cam)
        self.assertIn("--camera-facing=back", args_cam)
        self.assertIn("--render-fit=unscaled", args_cam)
        self.assertIn("--no-control", args_cam)

        # 3. Multi-monitor
        cfg_mm = PRESETS["multimonitor"]
        args_mm = build_scrcpy_args(cfg_mm)
        self.assertIn("--window-x=1920", args_mm)
        self.assertIn("--window-y=0", args_mm)
        self.assertIn("--fullscreen", args_mm)

        # 4. Gaming Competitive
        cfg_gc = PRESETS["gaming_competitive"]
        args_gc = build_scrcpy_args(cfg_gc)
        self.assertIn("--shortcut-mod=rctrl", args_gc)
        self.assertIn("--keyboard=uhid", args_gc)
        self.assertIn("--mouse=uhid", args_gc)

        # 5. Mirror Readonly
        cfg_ro = PRESETS["mirror_readonly"]
        args_ro = build_scrcpy_args(cfg_ro)
        self.assertIn("--no-control", args_ro)
        self.assertIn("--render-fit=letterbox", args_ro)
        self.assertNotIn("--keep-active", args_ro)
        self.assertNotIn("--stay-awake", args_ro)
        self.assertNotIn("--show-touches", args_ro)

    def test_no_control_suppresses_screen_power_options(self):
        cfg = {
            "no_control": True,
            "stay_awake": True,
            "screen_off": True,
            "power_off_on_close": True,
            "show_touches": True,
            "keep_active": True,
            "virtual_display": True,
            "virtual_display_app": "com.test.app",
        }
        args = build_scrcpy_args(cfg)
        self.assertIn("--no-control", args)
        self.assertNotIn("--stay-awake", args)
        self.assertNotIn("--turn-screen-off", args)
        self.assertNotIn("--power-off-on-close", args)
        self.assertNotIn("--show-touches", args)
        self.assertNotIn("--keep-active", args)
        self.assertNotIn("--start-app=com.test.app", args)

    def test_format_record_filename(self):
        fixed_time = datetime(2026, 9, 9, 15, 30, 45)
        cfg = {"device": "RFC12345 (Galaxy)", "active_mode": "gaming"}
        
        # Test {device}, {preset}, {date}, {time}
        template = "rec_{device}_{preset}_{date}_{time}.mp4"
        res = format_record_filename(template, cfg, dt=fixed_time)
        self.assertEqual(res, "rec_RFC12345_gaming_20260909_153045.mp4")

        # Test standard strftime
        template2 = "rec_%Y%m%d_%H%M%S.mkv"
        res2 = format_record_filename(template2, cfg, dt=fixed_time)
        self.assertEqual(res2, "rec_20260909_153045.mkv")
    def test_virtual_mouse_toggle(self):
        # 1. UHID mouse with virtual_mouse=True
        cfg_on = {
            "virtual_display": True,
            "mouse": "uhid",
            "virtual_mouse": True,
        }
        args_on = build_scrcpy_args(cfg_on)
        self.assertIn("--mouse=uhid", args_on)

        # 2. UHID mouse toggled off (virtual_mouse=False)
        cfg_off = {
            "virtual_display": True,
            "mouse": "uhid",
            "virtual_mouse": False,
        }
        args_off = build_scrcpy_args(cfg_off)
        self.assertNotIn("--mouse=uhid", args_off)

        # 3. Implicit virtual_mouse=True activates UHID
        cfg_auto = {
            "virtual_display": True,
            "virtual_mouse": True,
        }
        args_auto = build_scrcpy_args(cfg_auto)
        self.assertIn("--mouse=uhid", args_auto)

        # 4. Preset virtual_app with virtual_mouse=False suppresses --mouse=uhid
        from presets import PRESETS
        preset_cfg = dict(PRESETS["virtual_app"])
        args_default = build_scrcpy_args(preset_cfg)
        self.assertIn("--mouse=uhid", args_default)

        preset_cfg["virtual_mouse"] = False
        args_disabled = build_scrcpy_args(preset_cfg)
        self.assertNotIn("--mouse=uhid", args_disabled)

    def test_scrcpy_5_hwdec_flags(self):
        # 1. hwdec=d3d11va
        args_d3d = build_scrcpy_args({"hwdec": "d3d11va"})
        self.assertIn("--hwdec=d3d11va", args_d3d)

        # 2. hwdec=disabled
        args_dis = build_scrcpy_args({"hwdec": "disabled"})
        self.assertIn("--hwdec=disabled", args_dis)

        # 3. hwdec empty
        args_empty = build_scrcpy_args({"hwdec": ""})
        self.assertFalse(any(a.startswith("--hwdec") for a in args_empty))

    def test_scrcpy_5_start_app_force_stop(self):
        # 1. Without force-stop
        args1 = build_scrcpy_args({
            "virtual_display": True,
            "virtual_display_app": "com.whatsapp",
            "start_app_force_stop": False,
        })
        self.assertIn("--start-app=com.whatsapp", args1)

        # 2. With force-stop
        args2 = build_scrcpy_args({
            "virtual_display": True,
            "virtual_display_app": "com.whatsapp",
            "start_app_force_stop": True,
        })
        self.assertIn("--start-app=+com.whatsapp", args2)

        # 3. Already prefixed with + should not be duplicated
        args3 = build_scrcpy_args({
            "virtual_display": True,
            "virtual_display_app": "+com.whatsapp",
            "start_app_force_stop": True,
        })
        self.assertIn("--start-app=+com.whatsapp", args3)

    def test_scrcpy_5_record_orientation(self):
        args = build_scrcpy_args({"record_orientation": "90"})
        self.assertIn("--record-orientation=90", args)

    def test_scrcpy_5_min_size_alignment_and_mipmaps(self):
        args = build_scrcpy_args({
            "min_size_alignment": "16",
            "no_mipmaps": True,
        })
        self.assertIn("--min-size-alignment=16", args)
        self.assertIn("--no-mipmaps", args)


class TestVersionAwareCommandBuilder(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("v5.0"), (5, 0))
        self.assertEqual(parse_version("5.1.2"), (5, 1))
        self.assertEqual(parse_version("3.0"), (3, 0))
        self.assertEqual(parse_version((4, 1)), (4, 1))
        self.assertEqual(parse_version((2,)), (2, 0))
        self.assertEqual(parse_version(None), (99, 99))
        self.assertEqual(parse_version(""), (99, 99))

    def test_legacy_version_filters_scrcpy5_flags(self):
        cfg = {
            "hwdec": "d3d11va",
            "min_size_alignment": "16",
            "no_mipmaps": True,
            "virtual_display": True,
            "virtual_display_app": "com.example.app",
            "start_app_force_stop": True,
            "ignore_encoder_constraints": True,
            "no_terminal_title": True,
        }
        # Under scrcpy 2.7:
        args_v2 = build_scrcpy_args(cfg, scrcpy_version="2.7")
        self.assertFalse(any(a.startswith("--hwdec") for a in args_v2))
        self.assertFalse(any(a.startswith("--min-size-alignment") for a in args_v2))
        self.assertNotIn("--no-mipmaps", args_v2)
        self.assertNotIn("--ignore-video-encoder-constraints", args_v2)
        self.assertNotIn("--no-terminal-title", args_v2)
        # virtual display only in 3.0+
        self.assertFalse(any(a.startswith("--new-display") for a in args_v2))

    def test_scrcpy4_supports_encoder_constraints_and_terminal_title(self):
        cfg = {
            "ignore_encoder_constraints": True,
            "no_terminal_title": True,
            "hwdec": "d3d11va",
        }
        args_v4 = build_scrcpy_args(cfg, scrcpy_version="4.1")
        self.assertIn("--ignore-video-encoder-constraints", args_v4)
        self.assertIn("--no-terminal-title", args_v4)
        # hwdec is only 5.0+
        self.assertFalse(any(a.startswith("--hwdec") for a in args_v4))

    def test_scrcpy5_force_stop_syntax(self):
        cfg = {
            "virtual_display": True,
            "virtual_display_app": "com.example.app",
            "start_app_force_stop": True,
        }
        args_v3 = build_scrcpy_args(cfg, scrcpy_version="3.0")
        self.assertIn("--start-app=com.example.app", args_v3)
        self.assertNotIn("--start-app=+com.example.app", args_v3)

        args_v5 = build_scrcpy_args(cfg, scrcpy_version="5.0")
        self.assertIn("--start-app=+com.example.app", args_v5)


if __name__ == "__main__":
    unittest.main()

