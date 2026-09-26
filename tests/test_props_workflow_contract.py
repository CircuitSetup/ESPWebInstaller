from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build_props-and-release.yml"


class PropsWorkflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_same_version_refresh_is_opt_in_and_tcd_only(self) -> None:
        self.assertIn("refresh_tcd_release:", self.workflow)
        self.assertIn(
            'if [ "${{ inputs.refresh_tcd_release }}" == "true" ] && '
            '[ "${{ matrix.name }}" == "Time Circuits Display" ]; then',
            self.workflow,
        )

    def test_tcd_release_checks_out_private_buildac(self) -> None:
        self.assertIn("repository: realA10001986/buildac", self.workflow)
        self.assertIn("token: ${{ secrets.RELEASE_TOKEN }}", self.workflow)
        self.assertIn("path: buildac", self.workflow)

    def test_tcd_release_uses_latest_circuitsetup_sound_pack(self) -> None:
        self.assertIn('install_dir="buildac"', self.workflow)
        self.assertIn("-name 'sound-pack-cs*.zip'", self.workflow)


if __name__ == "__main__":
    unittest.main()
