from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "extract_prop_sound_pack.py"


class PropSoundPackTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.install = Path(temporary.name) / "install"
        self.install.mkdir()
        self.firmware = Path(temporary.name) / "firmware"
        self.settings = Path(temporary.name) / "tc_settings.cpp"
        self.settings.write_text(
            '#ifdef CS_EDITION\n#define SND_REQ_VERSION "CS10"\n'
            '#else\n#define SND_REQ_VERSION "TW10"\n#endif\n#define AC_FMTV 3\n',
            encoding="utf-8",
        )

    def extract(self, product: str) -> subprocess.CompletedProcess:
        arguments = ["--tcd-settings", str(self.settings)] if product == "Time Circuits Display" else []
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(self.install), str(self.firmware), product, *arguments],
            capture_output=True, text=True,
        )

    def tcd_pack(self, version: str = "CS10", container_format: int = 3) -> bytes:
        header = bytearray(19)
        header[:4] = b"TCDA"
        header[4] = container_format | 0x80
        offset = 13 if container_format == 3 else 5
        header[offset:offset + 4] = version.encode("ascii")
        return bytes(header) + b"CircuitSetup audio"

    def write_zip(self, name: str, files: dict[str, bytes]) -> None:
        with ZipFile(self.install / name, "w") as archive:
            for filename, content in files.items():
                archive.writestr(filename, content)

    def test_copies_latest_direct_pack_using_the_release_filename(self) -> None:
        for product, prefix, code in (("Flux Capacitor", "FCA", "FC"), ("Dash-Gauges", "DGA", "DG")):
            with self.subTest(product=product):
                (self.install / f"{prefix}-{code}9.bin").write_bytes(b"old pack")
                (self.install / f"{prefix}-{code}10.bin").write_bytes(b"new pack")
                (self.install / f"{product}-A10001986-V2.00.bin").write_bytes(b"main firmware")

                result = self.extract(product)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((self.firmware / f"{prefix}.bin").read_bytes(), b"new pack")
        self.assertEqual({path.name for path in self.firmware.glob("*")}, {"FCA.bin", "DGA.bin"})

    def test_tcd_uses_the_latest_circuitsetup_zip_and_ignores_macos_files(self) -> None:
        self.write_zip("sound-pack-cs9.zip", {"TCDA.bin": b"old pack"})
        self.write_zip("sound-pack-cs10.zip", {
            "nested/TCDA.bin": self.tcd_pack(),
            "__MACOSX/._TCDA.bin": b"metadata",
        })
        self.write_zip("sound-pack-999.zip", {"TCDA.bin": b"upstream pack"})

        result = self.extract("Time Circuits Display")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.firmware / "TCDA.bin").read_bytes(), self.tcd_pack())

    def test_tcd_uses_the_required_direct_circuitsetup_pack(self) -> None:
        (self.install / "TCDA-CS10.bin").write_bytes(self.tcd_pack())
        (self.install / "TCDA-CS11.bin").write_bytes(self.tcd_pack("CS11"))
        (self.install / "TCDA-TW10.bin").write_bytes(self.tcd_pack("TW10"))
        self.write_zip("sound-pack-cs09.zip", {"TCDA.bin": self.tcd_pack("CS09", 2)})

        result = self.extract("Time Circuits Display")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.firmware / "TCDA.bin").read_bytes(), self.tcd_pack())

    def test_tcd_fails_when_only_an_older_pack_is_available(self) -> None:
        self.write_zip("sound-pack-cs09.zip", {"TCDA.bin": self.tcd_pack("CS09", 2)})

        result = self.extract("Time Circuits Display")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CS10", result.stderr)
        self.assertFalse(self.firmware.exists())

    def test_tcd_requires_firmware_settings(self) -> None:
        self.write_zip("sound-pack-cs09.zip", {"TCDA.bin": self.tcd_pack("CS09", 2)})

        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(self.install), str(self.firmware), "Time Circuits Display"],
            capture_output=True, text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.firmware.exists())

    def test_tcd_rejects_mislabeled_or_invalid_containers(self) -> None:
        for content in (self.tcd_pack("TW10"), self.tcd_pack("CS09"), self.tcd_pack(container_format=2), b"TCDA"):
            with self.subTest(content=content):
                (self.install / "TCDA-CS10.bin").write_bytes(content)

                result = self.extract("Time Circuits Display")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("CS10", result.stderr)
                self.assertFalse(self.firmware.exists())

    def test_tcd_rejects_a_mislabeled_zip_payload(self) -> None:
        self.write_zip("sound-pack-cs10.zip", {"TCDA.bin": self.tcd_pack("CS09", 2)})

        result = self.extract("Time Circuits Display")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CS10", result.stderr)
        self.assertFalse(self.firmware.exists())

    def test_tcd_requires_the_firmware_sound_pack_requirement(self) -> None:
        (self.install / "TCDA-CS10.bin").write_bytes(self.tcd_pack())
        self.settings.write_text('#define SND_REQ_VERSION "TW10"\n#define AC_FMTV 3\n', encoding="utf-8")

        result = self.extract("Time Circuits Display")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CircuitSetup", result.stderr)
        self.assertFalse(self.firmware.exists())

    def test_legacy_zip_preserves_the_remote_sound_pack_filename(self) -> None:
        self.write_zip("sound-pack-9.zip", {"REMA.bin": b"old pack"})
        self.write_zip("sound-pack-10.zip", {"nested/REMA.bin": b"remote pack"})

        result = self.extract("Remote")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.firmware / "REMA.bin").read_bytes(), b"remote pack")

    def test_missing_sound_pack_fails_without_creating_output(self) -> None:
        result = self.extract("Remote")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.firmware.exists())

    def test_zip_requires_exactly_one_sound_pack_binary(self) -> None:
        for files in ({"README.md": b"no binary"}, {"one.bin": b"one", "two.bin": b"two"}):
            with self.subTest(files=files):
                self.write_zip("sound-pack-1.zip", files)

                result = self.extract("Remote")

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.firmware.exists())


if __name__ == "__main__":
    unittest.main()
