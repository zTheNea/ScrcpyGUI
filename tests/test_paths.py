"""Unit tests for paths.py module."""
import os
import platform
import unittest
import paths


class TestPaths(unittest.TestCase):
    def test_app_dir_structure(self):
        self.assertIn("ScrcpyGUI", paths.APP_DIR)
        self.assertTrue(paths.SCRCPY_DIR.startswith(paths.APP_DIR))
        self.assertTrue(paths.VERSION_FILE.startswith(paths.APP_DIR))
        self.assertTrue(paths.CONFIG_FILE.startswith(paths.APP_DIR))
        self.assertTrue(paths.PROFILES_FILE.startswith(paths.APP_DIR))

    def test_platform_flag_matches_os(self):
        self.assertEqual(paths.IS_WINDOWS, platform.system() == "Windows")

    def test_legacy_paths_exist(self):
        self.assertTrue(paths.LEGACY_CONFIG.endswith("config.json"))
        self.assertTrue(paths.LEGACY_PROFILES.endswith("profiles.json"))

    def test_atomic_write_and_safe_read(self):
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            target_file = os.path.join(temp_dir, "test_atomic.json")
            data = {"app": "ScrcpyStudio", "version": 2026, "features": ["audio", "camera"]}

            # 1. Atomic write creates the file
            paths.atomic_write_json(target_file, data, backup=True)
            self.assertTrue(os.path.isfile(target_file))

            # 2. Safe read returns exact dictionary
            read_data = paths.safe_read_json(target_file)
            self.assertEqual(read_data, data)

            # 3. Second atomic write creates a .bak
            data["version"] = 2027
            paths.atomic_write_json(target_file, data, backup=True)
            self.assertTrue(os.path.isfile(target_file + ".bak"))

            # 4. Safe read with corrupt file falls back to .bak or default
            with open(target_file, "w", encoding="utf-8") as f:
                f.write("corrupted json {")
            recovered = paths.safe_read_json(target_file)
            self.assertIsNotNone(recovered)
            self.assertEqual(recovered.get("app"), "ScrcpyStudio")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

