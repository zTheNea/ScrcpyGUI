"""Unit tests for Scrcpy Studio UI architecture (state, schema, services, guardian)."""
import unittest

from ui.state import AppState, DEFAULTS
from ui.schema import MAIN_SECTIONS, ADV_SECTIONS
from ui.services import diagnose_exit


class TestUiStudio(unittest.TestCase):

    def setUp(self):
        self.state = AppState()

    def test_schema_keys_exist_in_state(self):
        """Every option in MAIN_SECTIONS and ADV_SECTIONS must exist in AppState."""
        all_specs = []
        for _, specs in MAIN_SECTIONS + ADV_SECTIONS:
            all_specs.extend(specs)

        for spec in all_specs:
            self.assertTrue(
                hasattr(self.state, f"v_{spec.key}"),
                f"Spec key '{spec.key}' missing from AppState defaults"
            )

    def test_state_presets(self):
        """Applying goals/presets should update state variables properly."""
        self.state.apply_preset("gaming")
        self.assertEqual(self.state.get("fps"), 120)
        self.assertEqual(self.state.get("codec"), "h264")

        self.state.apply_preset("desktop")
        self.assertTrue(self.state.get("virtual_display"))
        self.assertEqual(self.state.get("keyboard"), "uhid")
        self.assertTrue(self.state.get("virtual_mouse"))

    def test_guardian_disabled_reason(self):
        """Guardian rules should protect against invalid scrcpy flag combinations."""
        # By default, stay_awake is allowed
        self.assertEqual(self.state.disabled_reason("stay_awake"), "")

        # When no_control is true, stay_awake and show_touches must be blocked
        self.state.set("no_control", True)
        self.assertNotEqual(self.state.disabled_reason("stay_awake"), "")
        self.assertNotEqual(self.state.disabled_reason("show_touches"), "")
        self.assertNotEqual(self.state.disabled_reason("keyboard"), "")

        # When audio is disabled, audio_buf must be blocked
        self.state.set("audio", False)
        self.assertNotEqual(self.state.disabled_reason("audio_buf"), "")

        # When virtual_display is False, virtual_display_app must be blocked
        self.state.set("virtual_display", False)
        self.assertNotEqual(self.state.disabled_reason("virtual_display_app"), "")

    def test_diagnose_exit_actionable_errors(self):
        """Scrcpy error messages should be translated to human actionable diagnoses."""
        d1 = diagnose_exit(["ERROR: Cannot stay awake if control is disabled"])
        self.assertIsNotNone(d1)
        self.assertIn("Solo lectura", d1.message)
        self.assertFalse(d1.fix["stay_awake"])

        d2 = diagnose_exit(["error: device unauthorized. Please check the confirmation dialog on your device."])
        self.assertIsNotNone(d2)
        self.assertIn("autorizado", d2.message)
        self.assertEqual(d2.action, "refresh")

        d3 = diagnose_exit(["ERROR: 'scrcpy-server' does not exist or is not a regular file"])
        self.assertIsNotNone(d3)
        self.assertEqual(d3.action, "download")

    def test_state_batch_notifications(self):
        """Batch updates should only notify once with '*'."""
        events = []
        self.state.subscribe(lambda k: events.append(k))

        with self.state.batch():
            self.state.set("fps", 90)
            self.state.set("bitrate", 16)
            self.state.set("codec", "h265")

        self.assertEqual(events, ["*"])
        self.assertEqual(self.state.get("fps"), 90)
        self.assertEqual(self.state.get("bitrate"), 16)

    def test_auto_wifi_state(self):
        """Auto Wi-Fi flag should be supported and toggleable in AppState."""
        self.assertFalse(self.state.get("auto_wifi"))
        self.state.set("auto_wifi", True)
        self.assertTrue(self.state.get("auto_wifi"))

    def test_enable_tcpip_already_wifi(self):
        """enable_tcpip should detect when device is already on Wi-Fi."""
        import scrcpy_manager as mgr
        res = mgr.enable_tcpip("192.168.1.50:5555")
        self.assertIn("ya está conectado", res.lower())

    def test_wifi_preset_auto_safeguards(self):
        """When device is Wi-Fi, presets should adapt to prevent antenna sleep and input drops."""
        self.state.device = "192.168.1.37:5555"
        self.state.apply_preset("gaming")
        self.assertFalse(self.state.get("screen_off"))
        self.assertEqual(self.state.get("keyboard"), "sdk")
        self.assertEqual(self.state.get("mouse"), "sdk")
        self.assertGreaterEqual(self.state.get("audio_buf"), 60)

    def test_contextual_goal_sections(self):
        """Every goal must return tailored sections with valid Specs."""
        from ui.schema import get_goal_sections
        goals = ["camera", "record", "virtual", "desktop", "gaming", "balanced"]
        for g in goals:
            secs = get_goal_sections(g)
            self.assertGreater(len(secs), 0)
            for title, specs in secs:
                self.assertTrue(len(specs) > 0)
                for s in specs:
                    self.assertTrue(hasattr(self.state, f"v_{s.key}"))


    def test_one_click_goal_presets(self):
        """All 6 home screen goals must configure 100% plug-and-play parameters out of the box."""
        # 1. Balanced (Espejo rápido)
        self.state.apply_preset("balanced")
        self.assertEqual(self.state.get("video_source"), "display")
        self.assertFalse(self.state.get("virtual_display"))
        self.assertFalse(self.state.get("record"))
        self.assertEqual(self.state.get("fps"), 60)
        self.assertEqual(self.state.get("bitrate"), 12)
        self.assertTrue(self.state.get("audio"))

        # 2. Gaming 120 FPS
        self.state.apply_preset("gaming")
        self.assertEqual(self.state.get("fps"), 120)
        self.assertFalse(self.state.get("screen_off"))  # Screen must not blackout
        self.assertEqual(self.state.get("keyboard"), "uhid")
        self.assertEqual(self.state.get("gamepad"), "uhid")

        # 3. Desktop / DeX
        self.state.apply_preset("desktop")
        self.assertTrue(self.state.get("virtual_display"))
        self.assertEqual(self.state.get("virtual_display_res"), "1920x1080")
        self.assertEqual(self.state.get("virtual_dpi"), "220")
        self.assertTrue(self.state.get("virtual_mouse"))

        # 4. Virtual App
        self.state.apply_preset("virtual")
        self.assertTrue(self.state.get("virtual_display"))
        self.assertTrue(self.state.get("flex_display"))
        self.assertTrue(self.state.get("start_app_force_stop"))

        # 5. Screen Record (Grabar Pantalla)
        self.state.apply_preset("record")
        self.assertTrue(self.state.get("record"))
        self.assertIn(".mp4", self.state.get("record_file"))
        self.assertEqual(self.state.get("record_format"), "mp4")
        self.assertEqual(self.state.get("audio_codec"), "aac")
        self.assertFalse(self.state.get("no_video_playback"))

        # 6. Web Camera (Cámara Web)
        self.state.apply_preset("camera")
        self.assertEqual(self.state.get("video_source"), "camera")
        self.assertEqual(self.state.get("camera_facing"), "back")
        self.assertEqual(self.state.get("camera_size"), "1920x1080")
        self.assertEqual(self.state.get("camera_fps"), 30)
        self.assertFalse(self.state.get("audio"))
        self.assertTrue(self.state.get("no_control"))

    def test_one_click_command_generation(self):
        """Commands generated for goals must contain necessary flags with 0 extra tweaks."""
        from command_builder import build_scrcpy_args

        # Camera
        self.state.apply_preset("camera")
        cmd_cam = build_scrcpy_args(self.state.to_config(), is_windows=True)
        self.assertIn("--video-source=camera", cmd_cam)
        self.assertIn("--camera-facing=back", cmd_cam)
        self.assertIn("--camera-size=1920x1080", cmd_cam)
        self.assertIn("--no-audio", cmd_cam)
        self.assertIn("--no-control", cmd_cam)

        # Record
        self.state.apply_preset("record")
        cmd_rec = build_scrcpy_args(self.state.to_config(), is_windows=True)
        rec_args = [arg for arg in cmd_rec if arg.startswith("--record=")]
        self.assertTrue(len(rec_args) > 0)
        self.assertIn("ScrcpyRecordings", rec_args[0])
        self.assertIn("--audio-codec=aac", cmd_rec)

    def test_session_manager_has_recorded_signal(self):
        """SessionManager must provide recorded signal for saved video files."""
        from ui.services import SessionManager
        sm = SessionManager()
        self.assertTrue(hasattr(sm, "recorded"))

    def test_app_state_and_friendly_names(self):
        """State must track available apps and translate package names into human-readable labels."""
        import scrcpy_manager as mgr
        self.state.set_available_apps([("Brave Browser", "com.brave.browser"), ("Calculadora", "com.android.calculator2")])
        self.assertEqual(len(self.state.available_apps), 2)
        self.assertEqual(self.state.available_apps[0], ("Brave Browser", "com.brave.browser"))

        # Friendly names helper
        self.assertEqual(mgr._clean_app_name("com.brave.browser"), "Brave Browser")
        self.assertEqual(mgr._clean_app_name("com.android.settings"), "Ajustes del Sistema")
        self.assertEqual(mgr._clean_app_name("com.whatsapp"), "WhatsApp")
        self.assertEqual(mgr._clean_app_name("flar2.devcheck"), "DevCheck Hardware")

    def test_command_syntax_highlighting(self):
        """format_command_html must syntax-highlight binary, flags, and arguments."""
        from ui.widgets import format_command_html
        cmd = ["scrcpy", "--max-size=1920", "--start-app=+com.brave.browser", "-s", "192.168.1.37:5555"]
        html = format_command_html(cmd)
        self.assertIn("color: #10B981", html)       # Binary
        self.assertIn("--max-size", html)            # Flag
        self.assertIn("1920", html)                  # Number value
        self.assertIn("+com.brave.browser", html)    # Package value
        self.assertIn("192.168.1.37:5555", html)     # Positional argument

    def test_goal_card_active_badge(self):
        """GoalCard must toggle its active badge when selected."""
        import sys
        from PySide6.QtWidgets import QApplication
        from ui.widgets import GoalCard
        _ = QApplication.instance() or QApplication(sys.argv)
        card = GoalCard("🚀", "Espejo Rápido", "1080p a 60 FPS")
        self.assertFalse(card.isChecked())
        self.assertTrue(card._badge.isHidden())

        card.setChecked(True)
        self.assertFalse(card._badge.isHidden())

    def test_device_telemetry_metrics(self):
        """DeviceInfo must support battery dict, latency, and physical screen metrics."""
        from ui.services import DeviceInfo
        dev = DeviceInfo(
            serial="192.168.1.37:5555",
            model="Redmi Note 8 Pro",
            wifi=True,
            battery={"level": 82, "charging": True, "powered": "usb"},
            latency=12.4,
            screen={"res": "1080x2340", "fps": "60"},
        )
        self.assertTrue(dev.wifi)
        self.assertEqual(dev.battery["level"], 82)
        self.assertTrue(dev.battery["charging"])
        self.assertEqual(dev.latency, 12.4)
        self.assertEqual(dev.screen["res"], "1080x2340")

    def test_advanced_dialog_search_and_chips(self):
        """AdvancedDialog must filter rows by search query and category chips."""
        import sys
        from PySide6.QtWidgets import QApplication
        from ui.dialogs import AdvancedDialog
        _ = QApplication.instance() or QApplication(sys.argv)
        dlg = AdvancedDialog(self.state)

        # Initially all rows visible
        self.assertIn("opciones disponibles", dlg.lbl_count.text())

        # Test search query
        dlg.search_input.setText("d3d11va")
        self.assertIn("Mostrando", dlg.lbl_count.text())

        # Test chip category selection
        dlg.search_input.clear()
        chip_btn, chip_key = dlg._chip_buttons[1]  # Vídeo
        dlg._on_chip_selected(chip_key, chip_btn)
        self.assertEqual(dlg._active_category, "vídeo")
        self.assertIn("Mostrando", dlg.lbl_count.text())

    def test_profile_persistence_order_agnostic_and_goal(self):
        """cfg.save_profile and load_profile must work with both (gui, name) and (name, gui) and save goal."""
        import config_manager as cfg
        self.state.set("fps", 144)
        self.state.goal = "gaming"

        # Save with (state, name)
        cfg.save_profile(self.state, "TestProfileOrderAgnostic")
        data = cfg.get_profile_data("TestProfileOrderAgnostic")
        self.assertEqual(data.get("fps"), 144)
        self.assertEqual(data.get("_goal"), "gaming")

        # Reset state
        self.state.reset()
        self.assertEqual(self.state.get("fps"), 60)

        # Load with (name, state)
        ok = cfg.load_profile("TestProfileOrderAgnostic", self.state)
        self.assertTrue(ok)
        self.assertEqual(self.state.get("fps"), 144)
        self.assertEqual(self.state.goal, "gaming")

        # Clean up
        cfg.delete_profile("TestProfileOrderAgnostic")


if __name__ == "__main__":
    unittest.main()


