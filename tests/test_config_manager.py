"""Unit tests for config_manager.py persistence using unittest."""
import os
import shutil
import tempfile
import unittest
import config_manager as cfg


class DummyVar:
    def __init__(self, val):
        self._val = val

    def get(self):
        return self._val

    def set(self, val):
        self._val = val


class MockGUI:
    def __init__(self):
        self.active_mode = DummyVar("gaming")
        for k in cfg.CONFIG_KEYS:
            setattr(self, f"v_{k}", DummyVar("default_" + k if "name" in k or "res" in k else 10))


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_config_file = cfg.CONFIG_FILE
        self.old_profiles_file = cfg.PROFILES_FILE
        self.old_app_dir = cfg._APP_DIR

        cfg._APP_DIR = self.test_dir
        cfg.CONFIG_FILE = os.path.join(self.test_dir, "config.json")
        cfg.PROFILES_FILE = os.path.join(self.test_dir, "profiles.json")

    def tearDown(self):
        cfg.CONFIG_FILE = self.old_config_file
        cfg.PROFILES_FILE = self.old_profiles_file
        cfg._APP_DIR = self.old_app_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_roundtrip(self):
        gui = MockGUI()
        gui.v_codec.set("av1")
        gui.v_fps.set(144)
        cfg.save_config(gui)

        self.assertTrue(os.path.exists(cfg.CONFIG_FILE))

        # Load into new gui
        new_gui = MockGUI()
        success, mode = cfg.load_config(new_gui)
        self.assertTrue(success)
        self.assertEqual(mode, "gaming")
        self.assertEqual(new_gui.v_codec.get(), "av1")
        self.assertEqual(new_gui.v_fps.get(), 144)

    def test_profile_crud(self):
        gui = MockGUI()
        gui.v_bitrate.set(32)

        self.assertEqual(cfg.list_profiles(), [])

        # Save
        cfg.save_profile(gui, "MiPerfil4K")
        self.assertEqual(cfg.list_profiles(), ["MiPerfil4K"])

        # Load
        new_gui = MockGUI()
        self.assertTrue(cfg.load_profile(new_gui, "MiPerfil4K"))
        self.assertEqual(new_gui.v_bitrate.get(), 32)

        # Delete
        self.assertTrue(cfg.delete_profile("MiPerfil4K"))
        self.assertEqual(cfg.list_profiles(), [])
        self.assertFalse(cfg.load_profile(new_gui, "MiPerfil4K"))


if __name__ == "__main__":
    unittest.main()
