# GDO Upstream Releases Implementation Plan

**Goal:** Automatically build and publish GDO firmware when gdolib's version or either upstream GDO YAML's `project_version` changes.

**Architecture:** Extend the existing ESPHome build workflow with an hourly GDO check. Retain the twice-weekly full check and manual controls. Save successful build inputs in the existing source-version snapshot and reuse the current installer publication process.

**Tech stack:** GitHub Actions, Bash, curl, jq, Python unittest.

## Design and scope

- Reuse the current workflow instead of adding a second publisher or requiring cross-repository credentials for dispatching events.
- Poll hourly; immediate cross-repository dispatch would require additional upstream changes and is unnecessary for automatic detection.
- Compare only `project_version` in the two named YAML files; compare gdolib's `library.json` version for Security+ only. The user explicitly excluded YAML edits without a version bump.
- Build Security+ against the matching gdolib version tag. Pin GDO YAML, packages, and external components to the captured upstream commit.
- Record each variant's project version, source commit, and applicable gdolib version before compilation. Ignore source commits during version comparison.
- Include gdolib's version in Security+ release tags so library-only version updates produce distinct releases.
- Publish releases before committing successful snapshots. A failed release must remain eligible for retry; an existing release missing its binary must be repairable.
- Keep energy-meter detection and installer naming unchanged. Do not publish firmware from pull requests.

## Review focus

Version-only gdolib changes must affect Security+; content-only YAML changes must skip; unchanged versions must skip; failed upstream reads must fail closed; publication failures must not advance successful build state.

## Tasks

- [x] Add behavioral tests for version fingerprints, pinned build configuration, release identity, and release retry/asset handling. Run them before implementation.
- [x] Extend `scripts/configs.sh` with source-state and GDO configuration helpers; update `scripts/build-firmware-batch.sh` to capture and use the exact build inputs.
- [x] Extract GDO publication into `scripts/release-gdo.sh`, consuming recorded inputs instead of refetching current versions.
- [x] Update `.github/workflows/build_esphome_firmware.yml` with hourly GDO selection, tests, state comparison, and release-before-state-commit ordering.
- [x] Document operation and the existing `RELEASE_TOKEN` requirement in `README.md`.
- [x] Run the full unittest suite, shell syntax checks, workflow validation, and read-only upstream smoke checks; review the diff and commit the intended changes.

## Review record

The independent review found that pinning all `@master` URLs would also pin the
Dashboard adoption URL. Added a failing regression assertion, excluded
`package_import_url` from the rewrite, and reran the suite successfully. Build
inputs remain pinned; adopted Dashboard configurations continue following master.

Validation: 37 unittest tests passed, including execution of the workflow's actual
selection step against unchanged and bumped versions. Actionlint 1.7.12, Bash
syntax checks, and `git diff --check` passed. Both Security+ (project 1.6.0,
gdolib 1.4.0) and dry-contact (project 1.2) compiled with ESPHome 2026.10.1 against
source commit `0b45121305c4c44e52db76c22a9bd3cc8214e0df`. The `idedata` factory-binary
path was verified. No GitHub release was published and no hardware was flashed.
