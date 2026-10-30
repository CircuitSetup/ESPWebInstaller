"""Exercise GDO version detection and publication without network or builds."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
BASH = (shutil.which("bash") if os.name != "nt" else
        str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"))
SECPLUS = "circuitsetup-gdo-default.yaml"
DRY = "circuitsetup-gdo-dry-contact.yaml"
SOURCE_REF = "a" * 40
SOURCE = '''substitutions:
  project_version: "1.6.0"
external_components:
  - source: github://CircuitSetup/circuitsetup-esphome@master
packages:
  remote_package:
    ref: master
dashboard_import:
  package_import_url: github://CircuitSetup/circuitsetup-esphome/circuitsetup-secplus-garage-door-opener.yaml@master
esphome:
  platformio_options:
    lib_deps:
      - "gdolib=https://github.com/CircuitSetup/gdolib#v1.3.2"
'''


class GdoReleasesTest(unittest.TestCase):
    def shell(self, command, *, cwd=ROOT, **env):
        return subprocess.run(
            [BASH, "-c", 'set -euo pipefail; source "$REPO/scripts/configs.sh"; ' + command],
            cwd=cwd, text=True, capture_output=True,
            env={**os.environ, "REPO": ROOT.as_posix(), **env},
        )

    def state(self, config=SECPLUS, source=SOURCE, library="1.4.0", ref=SOURCE_REF):
        result = self.shell(
            'curl() { printf \'{"version":"%s"}\\n\' "$LIBRARY"; }; '
            'printf "%s" "$SOURCE" | config_source_state "$CONFIG" "$SOURCE_REF"',
            CONFIG=config, SOURCE=source, LIBRARY=library, SOURCE_REF=ref,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def fingerprint(self, config, state):
        result = self.shell('source_state_version "$CONFIG" "$STATE"',
                            CONFIG=config, STATE=json.dumps(state))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_yaml_edits_and_unrelated_commits_do_not_change_versions(self):
        old = self.state()
        new = self.state(source=SOURCE + "# edited without version bump\n", ref="b" * 40)
        self.assertEqual(self.fingerprint(SECPLUS, old), self.fingerprint(SECPLUS, new))

    def test_project_version_bump_changes_each_variant(self):
        for config in (SECPLUS, DRY):
            with self.subTest(config=config):
                old = self.state(config)
                new = self.state(config, source=SOURCE.replace('"1.6.0"', '"1.6.1"'))
                self.assertNotEqual(self.fingerprint(config, old), self.fingerprint(config, new))

    def test_gdolib_version_bump_changes_only_security_plus(self):
        for config, changed in ((SECPLUS, True), (DRY, False)):
            with self.subTest(config=config):
                old = self.state(config, library="1.4.0")
                new = self.state(config, library="1.4.1")
                self.assertEqual(self.fingerprint(config, old) != self.fingerprint(config, new), changed)

    def test_legacy_dry_contact_snapshot_does_not_force_a_release(self):
        self.assertEqual(self.fingerprint(DRY, "1.6.0"), self.fingerprint(DRY, self.state(DRY)))

    def test_energy_meter_snapshot_format_is_preserved(self):
        result = self.shell(
            'printf \'substitutions:\\n  version: "1.8"\\n\' | '
            'config_source_state 6chan_energy_meter_main_board.yaml master'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), "1.8")

    def test_missing_or_invalid_versions_fail(self):
        for source, library in (("substitutions:\n", "1.4.0"), (SOURCE, ""), (SOURCE, "garbage")):
            with self.subTest(source=source, library=library):
                result = self.shell(
                    'curl() { printf \'{"version":"%s"}\\n\' "$LIBRARY"; }; '
                    'printf "%s" "$SOURCE" | config_source_state "$CONFIG" "$SOURCE_REF"',
                    CONFIG=SECPLUS, SOURCE=source, LIBRARY=library, SOURCE_REF=SOURCE_REF,
                )
                self.assertNotEqual(result.returncode, 0)

    def test_upstream_failure_does_not_return_successful_state(self):
        result = self.shell('curl() { return 22; }; fetch_config_source_state "$CONFIG" master', CONFIG=SECPLUS)
        self.assertNotEqual(result.returncode, 0)

    def test_build_pins_source_commit_and_detected_library_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gdo.yaml"
            path.write_text(SOURCE, encoding="utf-8")
            result = self.shell('curl() { return 0; }; prepare_gdo_config "$CONFIG_PATH" "$STATE"',
                                CONFIG_PATH=path.as_posix(), STATE=json.dumps(self.state()))
            self.assertEqual(result.returncode, 0, result.stderr)
            config = path.read_text(encoding="utf-8")
            self.assertIn(f"circuitsetup-esphome@{SOURCE_REF}", config)
            self.assertIn(f"ref: {SOURCE_REF}", config)
            self.assertIn("gdolib#v1.4.0", config)
            self.assertNotIn("gdolib#v1.3.2", config)
            self.assertIn("circuitsetup-secplus-garage-door-opener.yaml@master", config)

    def test_build_accepts_component_managed_gdolib(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gdo.yaml"
            path.write_text(SOURCE.split("esphome:")[0], encoding="utf-8")
            result = self.shell(
                'curl() { printf \'GDOLIB_REPOSITORY = "https://github.com/CircuitSetup/gdolib#v1.4.0"\\n\'; }; '
                'prepare_gdo_config "$CONFIG_PATH" "$STATE"',
                CONFIG_PATH=path.as_posix(), STATE=json.dumps(self.state()),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = path.read_text(encoding="utf-8")
            self.assertIn(f"circuitsetup-esphome@{SOURCE_REF}", config)
            self.assertNotIn("lib_deps", config)
            self.assertIn("circuitsetup-secplus-garage-door-opener.yaml@master", config)

    def test_component_pin_must_match_detected_gdolib_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gdo.yaml"
            path.write_text(SOURCE, encoding="utf-8")
            result = self.shell(
                'curl() { printf \'GDOLIB_REPOSITORY = "https://github.com/CircuitSetup/gdolib#v1.3.2"\\n\'; }; '
                'prepare_gdo_config "$CONFIG_PATH" "$STATE"',
                CONFIG_PATH=path.as_posix(), STATE=json.dumps(self.state()),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("v1.3.2", result.stderr)
            self.assertIn("v1.4.0", result.stderr)

    def test_library_only_bump_gets_a_distinct_release_tag(self):
        tags = []
        for library in ("1.4.0", "1.4.1"):
            result = self.shell('gdo_release_tag "$CONFIG" 2026.10.1 "$STATE"',
                                CONFIG=SECPLUS, STATE=json.dumps(self.state(library=library)))
            self.assertEqual(result.returncode, 0, result.stderr)
            tags.append(result.stdout.strip())
        self.assertEqual(tags, [
            "circuitsetup-secplus-garage-door-opener-v1.6.0-esphome-v2026.10.1-gdolib-v1.4.0",
            "circuitsetup-secplus-garage-door-opener-v1.6.0-esphome-v2026.10.1-gdolib-v1.4.1",
        ])

    def test_workflow_selects_only_variants_with_version_changes(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/build_esphome_firmware.yml").read_text())
        script = next(step["run"] for step in workflow["jobs"]["determine-build"]["steps"]
                      if step.get("id") == "set-files")
        for expression, value in {
            "${{ steps.esphome_version.outputs.version }}": "2026.10.1",
            "${{ github.event.inputs.force_build }}": "false",
            "${{ github.event.inputs.esphome_dev }}": "false",
        }.items():
            script = script.replace(expression, value)
        self.assertNotIn("${{", script)
        cases = [
            ("1.6.0", "1.4.0", "1.2", []),
            ("1.6.1", "1.4.0", "1.2", [SECPLUS]),
            ("1.6.0", "1.4.1", "1.2", [SECPLUS]),
            ("1.6.0", "1.4.0", "1.3", [DRY]),
        ]
        for project, library, dry, expected in cases:
            with self.subTest(project=project, library=library, dry=dry), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "scripts").mkdir()
                shutil.copy(ROOT / "scripts/configs.sh", root / "scripts/configs.sh")
                (root / "firmware").mkdir()
                for config in (SECPLUS, DRY):
                    (root / "firmware" / f"{config[:-5]}-2026.10.1.bin").write_bytes(b"existing")
                (root / "manifests").mkdir()
                (root / "manifests/source_versions.json").write_text(json.dumps({
                    SECPLUS: {"project_version": "1.6.0", "gdolib_version": "1.4.0", "source_ref": SOURCE_REF},
                    DRY: "1.2",
                }))
                output = root / "output.txt"
                result = self.shell('''curl() {
  case "${@: -1}" in
    *gdolib*) printf '{"version":"%s"}' "$LIBRARY" ;;
    *dry-contact*) printf 'substitutions:\\n  project_version: "%s"\\n' "$DRY_VERSION" ;;
    *) printf '%s\\n# edited without version bump\\n' "$SOURCE" ;;
  esac
}
''' + script, cwd=root, FIRMWARE_FAMILY="gdo", LIBRARY=library, DRY_VERSION=dry,
                    SOURCE=SOURCE.replace('"1.6.0"', f'"{project}"'), GITHUB_OUTPUT=output.as_posix())
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
                self.assertEqual(json.loads(outputs["files"]), expected)

    def release(self, *, exists="false", assets=None, create_status="0", expected_link=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "firmware").mkdir()
            binary = "circuitsetup-gdo-default-2026.10.1.bin"
            (root / "firmware" / binary).write_bytes(b"firmware")
            (root / "manifests").mkdir()
            snapshot = root / "manifests/source_versions.json"
            snapshot.write_text(json.dumps({SECPLUS: self.state()}), encoding="utf-8")
            manifest = root / "manifests/manifest_circuitsetup-gdo-default-2026.10.1.json"
            metadata = {"version": "2026.10.1", "builds": []}
            if not expected_link:
                metadata["release_url"] = "https://github.com/CircuitSetup/circuitsetup-esphome/releases/tag/stale"
            manifest.write_text(json.dumps(metadata), encoding="utf-8")
            before = snapshot.read_bytes()
            result = self.shell('''
gh() {
  case "$1 $2" in
    'api repos/CircuitSetup/circuitsetup-esphome/releases/tags/'*) [[ "$EXISTS" == true ]] || return 1; printf '%s' "$RELEASE_JSON" ;;
    'release list') printf '[]' ;;
    'release create') printf 'created %s\n' "$3"; return "$CREATE_STATUS" ;;
    'release upload') printf 'uploaded %s\n' "$4" ;;
    *) return 99 ;;
  esac
}
source "$REPO/scripts/release-gdo.sh"
''', cwd=root, FILES_JSON=json.dumps([SECPLUS]), ESPHOME_VERSION="2026.10.1",
                ESPHOME_DEV="false", EXISTS=exists, RELEASE_JSON=json.dumps({"assets": assets or []}), CREATE_STATUS=create_status)
            self.assertEqual(snapshot.read_bytes(), before)
            linked_release = json.loads(manifest.read_text()).get("release_url")
            if result.returncode == 0 and expected_link:
                self.assertEqual(linked_release,
                    "https://github.com/CircuitSetup/circuitsetup-esphome/releases/tag/"
                    "circuitsetup-secplus-garage-door-opener-v1.6.0-esphome-v2026.10.1-gdolib-v1.4.0")
            else:
                self.assertIsNone(linked_release)
            return result

    def test_release_creation_uses_captured_version(self):
        result = self.release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("created circuitsetup-secplus-garage-door-opener-v1.6.0-esphome-v2026.10.1-gdolib-v1.4.0", result.stdout)

    def test_partial_release_can_receive_its_missing_binary(self):
        result = self.release(exists="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uploaded firmware/circuitsetup-gdo-default-2026.10.1.bin", result.stdout)

    def test_complete_release_is_not_republished(self):
        import hashlib
        result = self.release(exists="true", assets=[{
            "name": "circuitsetup-gdo-default-2026.10.1.bin",
            "digest": "sha256:" + hashlib.sha256(b"firmware").hexdigest(),
        }])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("uploaded", result.stdout)
        self.assertNotIn("created", result.stdout)

    def test_different_or_unverifiable_release_binary_is_not_linked(self):
        for digest in ("sha256:" + "0" * 64, None):
            with self.subTest(digest=digest):
                result = self.release(exists="true", expected_link=False, assets=[{
                    "name": "circuitsetup-gdo-default-2026.10.1.bin", "digest": digest,
                }])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("uploaded", result.stdout)
                self.assertNotIn("created", result.stdout)

    def test_publication_failure_is_not_swallowed(self):
        result = self.release(create_status="1")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
