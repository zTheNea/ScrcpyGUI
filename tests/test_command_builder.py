"""Unit tests for command_builder.py using unittest."""
import unittest
from command_builder import build_scrcpy_args, _safe_int


class TestSafeInt(unittest.TestCase):
    def test_valid_int(self):
        self.assertEqual(_safe_int(42), 42)
        self.assertEqual(_safe_int(-10), -10)

    def test_string_int(self):
        self.assertEqual(_safe_int("42"), 42)
        self.assertEqual(_safe_int("0"), 0)

    def test_invalid_values(self):
        self.assertEqual(_safe_int("abc"), 0)
        self.assertEqual(_safe_int("12.34"), 0)
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


if __name__ == "__main__":
    unittest.main()
