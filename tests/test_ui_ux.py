"""Tests for UI/UX improvements: design tokens, categories, error diagnostics."""
import unittest
from presets import PRESETS, PRESET_CATEGORIES, COLORS
from scrcpy_gui import ScrcpyGUI


class TestUIUXImprovements(unittest.TestCase):
    def test_preset_categories_completeness(self):
        """Every preset key in PRESETS should belong to a category."""
        all_cat_keys = set()
        for cat_info in PRESET_CATEGORIES.values():
            self.assertIn("title", cat_info)
            self.assertIn("keys", cat_info)
            for k in cat_info["keys"]:
                all_cat_keys.add(k)
                self.assertIn(k, PRESETS, f"Category key {k} must exist in PRESETS")

        # Every preset in PRESETS must be categorised
        for preset_key in PRESETS:
            self.assertIn(
                preset_key,
                all_cat_keys,
                f"Preset '{preset_key}' is not classified in any PRESET_CATEGORIES",
            )

    def test_wcag_color_tokens(self):
        """Ensure all required color tokens exist and are valid hex strings."""
        required = ["bg", "card", "card_hover", "border", "accent", "text", "text2", "muted", "danger"]
        for r in required:
            self.assertIn(r, COLORS)
            self.assertTrue(COLORS[r].startswith("#"), f"{r} must be a hex color")

    def test_diagnose_exit_reason(self):
        """Verify human-friendly UX error diagnosis."""
        # Create a dummy instance without rendering Tk window if possible, or instantiate method unbound
        diagnose = ScrcpyGUI._diagnose_exit_reason

        # 1. Stay awake error
        lines1 = ["scrcpy 5.0", "ERROR: Cannot request to stay awake if control is disabled"]
        hint1 = diagnose(None, lines1)
        self.assertIsNotNone(hint1)
        self.assertIn("despierto", hint1.lower())

        # 2. Show touches error
        lines2 = ["ERROR: Cannot request to show touches if control is disabled"]
        hint2 = diagnose(None, lines2)
        self.assertIsNotNone(hint2)
        self.assertIn("toques", hint2.lower())

        # 3. Server missing error
        lines3 = ["ERROR: 'scrcpy-server' does not exist"]
        hint3 = diagnose(None, lines3)
        self.assertIsNotNone(hint3)
        self.assertIn("scrcpy-server", hint3.lower())

        # 4. Unauthorized
        lines4 = ["adb: device unauthorized. Please check the confirmation dialog."]
        hint4 = diagnose(None, lines4)
        self.assertIsNotNone(hint4)
        self.assertIn("autorizado", hint4.lower())

        # 5. Normal output with no recognized error
        lines5 = ["scrcpy finished normally"]
        self.assertIsNone(diagnose(None, lines5))


if __name__ == "__main__":
    unittest.main()
