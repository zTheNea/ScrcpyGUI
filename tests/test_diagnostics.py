"""Unit tests for diagnostics.py."""
import unittest

from diagnostics import DiagnosticIssue, run_diagnostics


class TestDiagnostics(unittest.TestCase):
    def test_blackout_issue(self):
        cfg = {"no_video": True, "audio": False, "otg_mode": False}
        issues = run_diagnostics(cfg)
        levels = [i.level for i in issues]
        self.assertIn("error", levels)
        self.assertTrue(any("Sin Transmisión" in i.title for i in issues))

    def test_otg_over_network_warning(self):
        cfg = {"otg_mode": True, "device": "192.168.1.50:5555"}
        issues = run_diagnostics(cfg)
        self.assertTrue(any("OTG sobre Wi-Fi" in i.title for i in issues))

    def test_uhid_over_network_warning(self):
        cfg = {"keyboard": "uhid", "device": "192.168.1.100:5555"}
        issues = run_diagnostics(cfg)
        self.assertTrue(any("UHID sobre Red" in i.title for i in issues))

    def test_android_version_camera_warning(self):
        cfg = {"video_source": "camera"}
        dev = {"sdk": 29}  # Android 10
        issues = run_diagnostics(cfg, dev)
        self.assertTrue(any("Cámara requiere Android 12+" in i.title for i in issues))

    def test_android_version_virtual_display(self):
        cfg = {"virtual_display": True}
        dev = {"sdk": 28}  # Android 9
        issues = run_diagnostics(cfg, dev)
        self.assertTrue(any("Pantalla Virtual requiere Android 10+" in i.title for i in issues))

    def test_android_version_flex_display(self):
        cfg = {"flex_display": True}
        dev = {"sdk": 33}  # Android 13
        issues = run_diagnostics(cfg, dev)
        self.assertTrue(any("Pantalla Flex requiere Android 14+" in i.title for i in issues))

    def test_empty_record_file_warning(self):
        cfg = {"record": True, "record_file": "   "}
        issues = run_diagnostics(cfg)
        self.assertTrue(any("Nombre de grabación vacío" in i.title for i in issues))

    def test_clean_config_has_no_errors(self):
        cfg = {
            "device": "RFC12345 (USB)",
            "video_source": "display",
            "codec": "h264",
            "fps": 60,
            "bitrate": 8,
            "audio": True,
            "audio_source": "output",
        }
        dev = {"sdk": 34}
        issues = run_diagnostics(cfg, dev)
        self.assertEqual([i for i in issues if i.level == "error"], [])

    def test_hwdec_os_compatibility_warning(self):
        from paths import IS_WINDOWS
        if IS_WINDOWS:
            # VA-API warning on Windows
            issues = run_diagnostics({"hwdec": "vaapi"})
            self.assertTrue(any("VA-API no soportado en Windows" in i.title for i in issues))
        else:
            # D3D11VA warning on Linux
            issues = run_diagnostics({"hwdec": "d3d11va"})
            self.assertTrue(any("D3D11VA solo para Windows" in i.title for i in issues))


if __name__ == "__main__":
    unittest.main()
