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

    def extract(self, product: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(self.install), str(self.firmware), product],
            capture_output=True, text=True,
        )

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
            "nested/TCDA.bin": b"CircuitSetup pack",
            "__MACOSX/._TCDA.bin": b"metadata",
        })
        self.write_zip("sound-pack-999.zip", {"TCDA.bin": b"upstream pack"})

        result = self.extract("Time Circuits Display")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.firmware / "TCDA.bin").read_bytes(), b"CircuitSetup pack")

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
