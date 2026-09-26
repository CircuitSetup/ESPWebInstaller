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


if __name__ == "__main__":
    unittest.main()
