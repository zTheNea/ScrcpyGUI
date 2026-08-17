"""Unit tests for hardware capability preset filtering logic."""
import unittest
from presets import PRESETS


def filter_presets_logic(caps, presets_dict=PRESETS):
    """Pure logic test mimicking ScrcpyGUI._filter_presets."""
    v_codecs = set(caps.get("video_codecs", ["h264", "h265", "av1", "vp9", "vp8"]))
    a_codecs = set(caps.get("audio_codecs", ["opus", "aac", "flac", "raw"]))
    supports_vd = caps.get("supports_virtual_display", True)

    visible = []
    hidden = []

    for key, p in presets_dict.items():
        req_v = p.get("codec", "h264")
        req_a = p.get("audio_codec", "opus")
        req_vd = p.get("virtual_display", False)

        is_compat = True
        if req_v and req_v not in v_codecs:
            is_compat = False
        elif req_vd and not supports_vd:
            is_compat = False
        elif p.get("audio") and req_a and req_a not in a_codecs:
            is_compat = False

        if is_compat:
            visible.append(key)
        else:
            hidden.append(key)

    return visible, hidden


class TestPresetFiltering(unittest.TestCase):
    def test_vp9_hidden_when_not_supported(self):
        # Device supports only H.264 and H.265
        caps = {
            "video_codecs": ["h264", "h265"],
            "audio_codecs": ["opus", "aac"],
            "supports_virtual_display": True,
        }
        visible, hidden = filter_presets_logic(caps)
        self.assertNotIn("vp9", visible)
        self.assertIn("vp9", hidden)
        self.assertIn("desktop", visible)
        self.assertIn("video", visible)

    def test_vp8_hidden_when_not_supported(self):
        # Device supports only H.264 and H.265 (no VP8 encoder)
        caps = {
            "video_codecs": ["h264", "h265"],
            "audio_codecs": ["opus", "aac"],
            "supports_virtual_display": True,
        }
        visible, hidden = filter_presets_logic(caps)
        self.assertNotIn("vp8", visible)
        self.assertIn("vp8", hidden)

    def test_virtual_display_hidden_on_android9_and_below(self):
        # Android 9 (no virtual display support)
        caps = {
            "video_codecs": ["h264", "h265", "vp9"],
            "audio_codecs": ["opus", "aac"],
            "supports_virtual_display": False,
        }
        visible, hidden = filter_presets_logic(caps)
        self.assertNotIn("desktop", visible)
        self.assertNotIn("virtual_app", visible)
        self.assertIn("desktop", hidden)
        self.assertIn("gaming", visible)
        self.assertIn("vp9", visible)

    def test_all_visible_on_flagship(self):
        # Flagship Android 14+ with full codec support
        caps = {
            "video_codecs": ["h264", "h265", "av1", "vp9", "vp8"],
            "audio_codecs": ["opus", "aac", "flac", "raw"],
            "supports_virtual_display": True,
        }
        visible, hidden = filter_presets_logic(caps)
        self.assertEqual(len(hidden), 0)
        self.assertIn("vp9", visible)
        self.assertIn("desktop", visible)
        self.assertIn("video", visible)


if __name__ == "__main__":
    unittest.main()
