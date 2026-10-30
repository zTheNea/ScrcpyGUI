"""Unit tests for the unified engine.adb.ADBGateway."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from engine.adb import (
    ADBGateway,
    BatteryStatus,
    DeviceRecord,
    DisplayMetrics,
    InstalledApp,
    get_adb_gateway,
)


class TestADBGatewayDTOs(unittest.TestCase):
    def test_device_record(self):
        dev = DeviceRecord(serial="192.168.1.100:5555", model="Pixel 7", state="device")
        self.assertTrue(dev.is_online)
        self.assertTrue(dev.is_wireless)
        self.assertEqual(dev.display_name, "192.168.1.100:5555 (Pixel 7)")

        dev_usb = DeviceRecord(serial="RFC12345", model="", state="offline")
        self.assertFalse(dev_usb.is_online)
        self.assertFalse(dev_usb.is_wireless)
        self.assertEqual(dev_usb.display_name, "RFC12345 (offline)")

    def test_battery_status(self):
        batt = BatteryStatus(level=85, temperature=31.5, health="Good", charging=True)
        self.assertEqual(batt.summary, "85% (Cargando) - 31.5°C")

        batt_unplugged = BatteryStatus(level=50, temperature=28.0, health="Good", charging=False)
        self.assertEqual(batt_unplugged.summary, "50% - 28.0°C")

    def test_display_metrics(self):
        metrics = DisplayMetrics(resolution="1080x2400", density=420)
        self.assertEqual(metrics.width, 1080)
        self.assertEqual(metrics.height, 2400)
        self.assertEqual(metrics.summary, "1080x2400 @ 420 DPI")


class TestADBGatewayOperations(unittest.TestCase):
    def setUp(self):
        self.gateway = ADBGateway()
        self.gateway.clear_cache()

    @patch("subprocess.run")
    def test_devices_parsing(self, mock_run):
        mock_output = (
            "List of devices attached\n"
            "RFC12345\tdevice product:cheetah model:Pixel_7 device:cheetah\n"
            "192.168.1.50:5555\tunauthorized\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")

        devices = self.gateway.devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].serial, "RFC12345")
        self.assertEqual(devices[0].model, "Pixel 7")
        self.assertEqual(devices[0].state, "device")
        self.assertEqual(self.gateway.get_unauthorized_count(), 1)

    @patch("subprocess.run")
    def test_get_battery(self, mock_run):
        dumpsys_output = (
            "Current Battery Service state:\n"
            "  AC powered: true\n"
            "  USB powered: false\n"
            "  status: 2\n"
            "  level: 88\n"
            "  scale: 100\n"
            "  temperature: 324\n"
            "  health: 2\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=dumpsys_output, stderr="")

        batt = self.gateway.get_battery("RFC12345")
        self.assertIsNotNone(batt)
        self.assertEqual(batt.level, 88)
        self.assertEqual(batt.temperature, 32.4)
        self.assertEqual(batt.health, "Good")
        self.assertEqual(batt.power_source, "ac")
        self.assertTrue(batt.charging)

    @patch("subprocess.run")
    def test_get_screen_metrics(self, mock_run):
        def side_effect(cmd, **kwargs):
            if "wm size" in " ".join(cmd):
                return MagicMock(returncode=0, stdout="Physical size: 1080x2340\n", stderr="")
            if "wm density" in " ".join(cmd):
                return MagicMock(returncode=0, stdout="Physical density: 440\n", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="error")

        mock_run.side_effect = side_effect
        metrics = self.gateway.get_screen_metrics("RFC12345")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.width, 1080)
        self.assertEqual(metrics.height, 2340)
        self.assertEqual(metrics.density, 440)

    @patch("subprocess.run")
    def test_get_installed_apps_and_caching(self, mock_run):
        pm_output = (
            "package:com.whatsapp\n"
            "package:org.telegram.messenger\n"
            "package:com.spotify.music\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=pm_output, stderr="")

        # First call hits subprocess
        apps1 = self.gateway.get_installed_apps("RFC12345", third_party_only=True)
        self.assertEqual(len(apps1), 3)
        self.assertEqual(mock_run.call_count, 1)

        # Second call should use in-memory cache without calling subprocess again
        apps2 = self.gateway.get_installed_apps("RFC12345", third_party_only=True)
        self.assertEqual(len(apps2), 3)
        self.assertEqual(mock_run.call_count, 1)

        # Clearing cache should force subprocess call on next invocation
        self.gateway.clear_cache("RFC12345")
        apps3 = self.gateway.get_installed_apps("RFC12345", third_party_only=True)
        self.assertEqual(len(apps3), 3)
        self.assertEqual(mock_run.call_count, 2)

    def test_singleton_getter(self):
        gw1 = get_adb_gateway()
        gw2 = get_adb_gateway()
        self.assertIs(gw1, gw2)


if __name__ == "__main__":
    unittest.main()
