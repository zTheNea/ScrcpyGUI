"""Unit tests for history_manager.py."""
import os
import shutil
import tempfile
import unittest

import history_manager as hm
import paths


class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_app_dir = paths.APP_DIR
        self.old_history_file = hm.HISTORY_FILE

        paths.APP_DIR = self.test_dir
        hm.HISTORY_FILE = os.path.join(self.test_dir, "history.json")

    def tearDown(self):
        hm.HISTORY_FILE = self.old_history_file
        paths.APP_DIR = self.old_app_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_record_and_get_history(self):
        self.assertEqual(hm.get_history(), [])

        entry = hm.record_session(
            device="TESTDEV1",
            preset="gaming",
            args=["-s", "TESTDEV1", "--max-fps=120"],
            config={"fps": 120},
        )

        self.assertIn("id", entry)
        self.assertEqual(entry["device"], "TESTDEV1")
        self.assertEqual(entry["preset"], "gaming")

        history = hm.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["id"], entry["id"])

    def test_max_history_entries_rotation(self):
        for i in range(hm.MAX_HISTORY_ENTRIES + 10):
            hm.record_session(
                device=f"DEV_{i}",
                preset="desktop",
                args=[f"--id={i}"],
            )

        history = hm.get_history()
        self.assertEqual(len(history), hm.MAX_HISTORY_ENTRIES)
        # Most recent should be at index 0
        self.assertEqual(history[0]["device"], f"DEV_{hm.MAX_HISTORY_ENTRIES + 9}")

    def test_delete_history_item(self):
        e1 = hm.record_session("DEV1", "desktop", [])
        e2 = hm.record_session("DEV2", "video", [])

        self.assertEqual(len(hm.get_history()), 2)
        deleted = hm.delete_history_item(e1["id"])
        self.assertTrue(deleted)

        history = hm.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["id"], e2["id"])

    def test_clear_history(self):
        hm.record_session("DEV1", "desktop", [])
        hm.record_session("DEV2", "video", [])
        self.assertEqual(len(hm.get_history()), 2)

        hm.clear_history()
        self.assertEqual(hm.get_history(), [])


if __name__ == "__main__":
    unittest.main()
