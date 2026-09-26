import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_prop_release_notes.py"


class PropReleaseNotesTests(unittest.TestCase):
    def run_parser(self, changelog: str, current: str, previous: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            src_dir = base_dir / "src"
            src_dir.mkdir()
            (src_dir / "firmware.ino").write_text(changelog, encoding="utf-8")
            output_path = base_dir / "github_output.txt"
            env = os.environ.copy()
            env.update(
                BASE_DIR=str(base_dir),
                CURRENT_VERSION=current,
                LAST_VERSION=previous,
                GITHUB_OUTPUT=str(output_path),
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = output_path.read_text(encoding="utf-8")
            return output.removeprefix("body<<EOF\n").removesuffix("\nEOF\n")

    def test_stops_before_patch_release_when_changelog_uses_minor_version(self):
        body = self.run_parser(
            """/* Changelog
 * 2026/09/20 (Author) [1.27]
 * - Current release
 * 2026/06/26 (Author) [1.24]
 * - Intermediate release
 * 2026/04/27 (Author) [1.23]
 * - Already released
 * 2026/04/19 (Author) [1.22]
 * - Older release
 */
""",
            "v1.27",
            "v1.23.1",
        )

        self.assertEqual(
            body,
            "## 1.27\n- Current release\n\n## 1.24\n- Intermediate release",
        )

    def test_preserves_hyphenated_words_across_wrapped_lines(self):
        body = self.run_parser(
            """/* Changelog
 * 2026/09/20 (Author) [2.0]
 * - The filename check is case-
 *   insensitive.
 * 2026/01/01 (Author) [1.0]
 * - Already released
 */
""",
            "v2.0",
            "v1.0",
        )

        self.assertEqual(body, "## 2.0\n- The filename check is case-insensitive.")


if __name__ == "__main__":
    unittest.main()
