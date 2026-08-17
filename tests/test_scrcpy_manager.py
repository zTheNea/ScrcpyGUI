"""Unit tests for scrcpy_manager.py helper functions using unittest."""
import unittest
from scrcpy_manager import _extract_ip


class TestExtractIp(unittest.TestCase):
    def test_ip_route_src_format(self):
        text = "1.1.1.1 via 192.168.1.1 dev wlan0 src 192.168.1.45 uid 0\n    cache"
        self.assertEqual(_extract_ip(text), "192.168.1.45")

    def test_inet_addr_ifconfig_format(self):
        text = "wlan0     Link encap:UNSPEC  HWaddr 00-00-00-00\n          inet addr:192.168.0.105  Bcast:192.168.0.255  Mask:255.255.255.0"
        self.assertEqual(_extract_ip(text), "192.168.0.105")

    def test_ip_addr_show_format(self):
        text = "inet 192.168.10.22/24 brd 192.168.10.255 scope global wlan0"
        self.assertEqual(_extract_ip(text), "192.168.10.22")

    def test_ignores_loopback_and_empty(self):
        self.assertIsNone(_extract_ip("inet 127.0.0.1/8 scope host lo"))
        self.assertIsNone(_extract_ip("inet 0.0.0.0"))
        self.assertIsNone(_extract_ip(""))
        self.assertIsNone(_extract_ip(None))

    def test_ignores_link_local(self):
        text = "inet 169.254.120.1/16 scope link"
        self.assertIsNone(_extract_ip(text))


class TestDeviceParsers(unittest.TestCase):
    def test_parse_encoders_real_output(self):
        from scrcpy_manager import parse_encoders
        sample = """
        [server] INFO: List of video encoders:
        --video-codec=h264 --video-encoder='c2.mtk.avc.encoder'
        --video-codec=h265 --video-encoder='c2.mtk.hevc.encoder'
        --video-codec=av1 --video-encoder='c2.android.av1.decoder'
        --video-codec=vp9 --video-encoder='OMX.google.vp9.encoder'
        [server] INFO: List of audio encoders:
        --audio-codec=opus --audio-encoder='c2.android.opus.encoder'
        --audio-codec=aac --audio-encoder='c2.android.aac.encoder'
        --audio-codec=flac --audio-encoder='c2.android.flac.encoder'
        """
        res = parse_encoders(sample)
        self.assertIn("h264", res["video_codecs"])
        self.assertIn("h265", res["video_codecs"])
        self.assertIn("av1", res["video_codecs"])
        self.assertIn("vp9", res["video_codecs"])
        self.assertIn("opus", res["audio_codecs"])
        self.assertIn("aac", res["audio_codecs"])
        self.assertIn("flac", res["audio_codecs"])
        self.assertIn("c2.mtk.hevc.encoder", res["video_encoders"])

    def test_parse_cameras_real_output(self):
        from scrcpy_manager import parse_cameras
        sample = """
        [server] INFO: List of cameras:
        --camera-id=0    (facing: back)
        --camera-id=1    (facing: front)
        --camera-id=2    (facing: back)
        """
        cams = parse_cameras(sample)
        self.assertEqual(len(cams), 3)
        self.assertEqual(cams[0][0], "0")
        self.assertEqual(cams[0][1], "back")
        self.assertIn("Trasera", cams[0][2])
        self.assertEqual(cams[1][0], "1")
        self.assertEqual(cams[1][1], "front")
        self.assertIn("Frontal", cams[1][2])

    def test_parse_displays_real_output(self):
        from scrcpy_manager import parse_displays
        sample = """
        [server] INFO: List of displays:
        --display-id=0 (1080x2400)
        --display-id=2 (1920x1080)
        """
        displays = parse_displays(sample)
        self.assertEqual(len(displays), 2)
        self.assertEqual(displays[0][0], "0")
        self.assertIn("Principal", displays[0][1])
        self.assertEqual(displays[1][0], "2")


if __name__ == "__main__":
    unittest.main()
