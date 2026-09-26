from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.sync_time_circuits_display import SyncSummary, sync_source_tree


class SyncSourceTreeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.source = root / "source"
        self.target = root / "target"
        (self.source / "timecircuits-A10001986").mkdir(parents=True)
        (self.target / "Software" / "src").mkdir(parents=True)
        (self.target / "Software" / "platformio.ini").write_text("")
        (self.source / "timecircuits-A10001986" / "tc_global.h").write_text("#define V_A10001986\n")
        (self.target / "Software" / "src" / "tc_global.h").write_text("#define V_A10001986\n")

    def test_removes_files_that_no_longer_exist_upstream(self) -> None:
        stale = self.target / "Software" / "src" / "stale.cpp"
        stale.write_text("old")
        summary = SyncSummary(dry_run=False)

        sync_source_tree(self.source, self.target, False, summary)

        self.assertFalse(stale.exists())
        self.assertIn("Software/src/stale.cpp", summary.updated_files)

    def test_dry_run_reports_deleted_upstream_files_without_removing_them(self) -> None:
        stale = self.target / "Software" / "src" / "stale.cpp"
        stale.write_text("old")
        summary = SyncSummary(dry_run=True)

        sync_source_tree(self.source, self.target, True, summary)

        self.assertTrue(stale.exists())
        self.assertIn("Software/src/stale.cpp", summary.updated_files)

    def test_renames_obsolete_platformio_build_flags(self) -> None:
        platformio = self.target / "Software" / "platformio.ini"
        platformio.write_text(
            "\n".join(
                (
                    "-DTC_HAVEGPS",
                    "-DTC_HAVELIGHT",
                    "-DTC_HAVETEMP",
                    "-DTC_HAVE_RE",
                    "-DTC_HAVE_REMOTE",
                    "-DTC_HAVEMQTT",
                    "-DIS_ACAR_DISPLAY",
                )
            )
        )
        tc_global = self.source / "timecircuits-A10001986" / "tc_global.h"
        tc_global.write_text(
            "\n".join(
                (
                    "#define HAVE_GPS",
                    "#define HAVE_LIGHT",
                    "#define HAVE_TEMP",
                    "#define HAVE_RE",
                    "#define HAVE_REMOTE",
                    "#define HAVE_MQTT",
                    "#define ACAR_DISPLAY",
                )
            )
        )
        summary = SyncSummary(dry_run=False)

        sync_source_tree(self.source, self.target, False, summary)

        updated = platformio.read_text()
        for obsolete in (
            "TC_HAVEGPS",
            "TC_HAVELIGHT",
            "TC_HAVETEMP",
            "TC_HAVE_RE",
            "TC_HAVE_REMOTE",
            "TC_HAVEMQTT",
            "IS_ACAR_DISPLAY",
        ):
            self.assertNotIn(obsolete, updated)
        for current in (
            "HAVE_GPS",
            "HAVE_LIGHT",
            "HAVE_TEMP",
            "HAVE_RE",
            "HAVE_REMOTE",
            "HAVE_MQTT",
            "ACAR_DISPLAY",
        ):
            self.assertIn(f"-D{current}", updated)
            self.assertIn(f"//#define {current}", (self.target / "Software" / "src" / "tc_global.h").read_text())
        self.assertIn("Software/platformio.ini", summary.updated_files)

    def test_dry_run_reports_build_flag_renames_without_writing_platformio(self) -> None:
        platformio = self.target / "Software" / "platformio.ini"
        platformio.write_text("-DTC_HAVEGPS\n")
        summary = SyncSummary(dry_run=True)

        sync_source_tree(self.source, self.target, True, summary)

        self.assertEqual(platformio.read_text(), "-DTC_HAVEGPS\n")
        self.assertIn("Software/platformio.ini", summary.updated_files)


if __name__ == "__main__":
    unittest.main()
