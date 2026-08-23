"""Contract for the Energy Meter manifests consumed by the inline installer."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "manifests"
FIRMWARE = ROOT / "firmware"


def product_ids(addon_count: int, connection: str) -> tuple[str, ...]:
    base = (
        "6chan_energy_meter_main"
        if addon_count == 0
        else "6chan_energy_meter_1-addon"
        if addon_count == 1
        else f"6chan_energy_meter_{addon_count}-addons"
    )
    if connection == "wifi":
        return (f"{base}_board" if addon_count == 0 else base,)
    if connection == "ethernet_lilygo":
        return (f"{base}_ethernet",)
    return (
        (f"{base}_ethernet_waveshare", f"{base}_ethernet_ws")
        if addon_count == 0
        else (f"{base}_ethernet_waveshare",)
    )


class EnergyMeterInstallerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads((MANIFESTS / "firmware_index.json").read_text())
        cls.products = {entry["productId"]: entry for entry in cls.index}

    def test_standard_selections_have_installable_esphome_manifests(self) -> None:
        self.assertIsInstance(self.index, list)
        for entry in self.index:
            self.assertEqual(set(entry), {"productId", "name", "versions"})
            self.assertTrue(entry["versions"])
            for version in entry["versions"]:
                self.assertEqual(set(version), {"version"})

        selections = [(addon_count, connection) for addon_count in range(7) for connection in
                      ("wifi", "ethernet_lilygo", "ethernet_waveshare")]
        self.assertEqual(len(selections), 21)
        for addon_count, connection in selections:
            candidates = product_ids(addon_count, connection)
            self.assertNotIn("6chan_energy_meter_3-addons_2-voltages", candidates)
            options: dict[str, str] = {}
            for product_id in candidates:
                for version in self.products.get(product_id, {}).get("versions", []):
                    options.setdefault(version["version"], product_id)
            self.assertTrue(options, f"missing current firmware for {addon_count=} {connection=}")

            expected_chip = "ESP32" if connection == "wifi" else "ESP32-S3"
            for version, product_id in options.items():
                manifest_path = MANIFESTS / f"manifest_{product_id}-{version}.json"
                self.assertTrue(manifest_path.is_file(), manifest_path)
                manifest = json.loads(manifest_path.read_text())
                self.assertEqual(manifest["version"], version)
                self.assertEqual(manifest.get("home_assistant_domain"), "esphome")

                self.assertEqual(len(manifest["builds"]), 1, manifest_path)
                build = manifest["builds"][0]
                self.assertEqual(build["chipFamily"], expected_chip, manifest_path)
                parts = build["parts"]
                self.assertEqual(len(parts), 1, manifest_path)
                part = parts[0]
                self.assertEqual(part["offset"], 0, manifest_path)
                binary = f"{product_id}-{version}.bin"
                self.assertEqual(
                    part["path"],
                    f"https://circuitsetup.github.io/ESPWebInstaller/firmware/{binary}",
                    manifest_path,
                )
                self.assertTrue((FIRMWARE / binary).is_file(), binary)


if __name__ == "__main__":
    unittest.main()
