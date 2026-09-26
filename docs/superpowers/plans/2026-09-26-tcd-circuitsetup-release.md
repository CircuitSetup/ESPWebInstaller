# TCD CircuitSetup Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild v3.27 as a CircuitSetup-edition firmware and automatically attach the newest CircuitSetup BuildAC sound pack.

**Architecture:** Put the edition flag in PlatformIO's shared flags so all TCD environments inherit it. Let the existing props builder privately check out BuildAC only for TCD, extract its newest `sound-pack-cs*.zip`, and opt into refreshing the existing TCD release without rebuilding unchanged sibling props.

**Tech Stack:** PlatformIO, GitHub Actions, Python `unittest`, GitHub Releases

**Spec:** `docs/superpowers/specs/2026-09-26-tcd-circuitsetup-release.md`

## Global Constraints

- Do not increment the firmware version.
- Do not change the other four prop build/release paths.
- Do not publish BuildAC source or private audio files.
- Reuse the existing `RELEASE_TOKEN` secret for the private BuildAC checkout.

## Review Focus

- A normal same-version run must still skip TCD unless the refresh input is selected.
- A TCD refresh must not force same-version releases for the other four props.
- The selected archive must be the highest `sound-pack-cs*.zip` in BuildAC's root.
- An archive with zero or multiple usable `.bin` files must fail the release.
- Existing same-name release assets must be overwritten, not duplicated.

---

### Task 1: Pin the workflow contract

**Files:**
- Create: `tests/test_props_workflow_contract.py`
- Modify: `.github/workflows/build_props-and-release.yml`

**Interfaces:**
- Consumes: the existing matrix job, `RELEASE_TOKEN`, and sound-pack extraction step.
- Produces: `refresh_tcd_release` dispatch input and TCD-only BuildAC checkout/extraction.

- [ ] Write a failing contract test asserting the refresh input, TCD-only same-version condition, private BuildAC checkout, and `sound-pack-cs*.zip` selection.
- [ ] Run `python -m unittest tests.test_props_workflow_contract -v` and confirm it fails for the missing workflow behavior.
- [ ] Make the smallest workflow edit that satisfies the contract.
- [ ] Run the focused test, then `python -m unittest discover -s tests -v` and confirm all tests pass.

### Task 2: Build every TCD environment as CircuitSetup edition

**Files:**
- Modify: `C:/Users/John/Documents/Time-Circuits-Display/Software/platformio.ini`

**Interfaces:**
- Consumes: PlatformIO's existing `${common.build_flags}` inheritance.
- Produces: `CS_EDITION` for `esp32dev`, `GTE`, and `GTE_ACAR`.

- [ ] Add `-DCS_EDITION` once to `[common] build_flags` without changing the version.
- [ ] Build `esp32dev` and `GTE` and verify both binaries contain the CircuitSetup sound-pack marker `CS09`.
- [ ] Commit and push the TCD configuration change.

### Task 3: Publish and verify v3.27 in place

**Files:**
- Modify: no additional source files.

**Interfaces:**
- Consumes: the pushed builder workflow and TCD branch.
- Produces: refreshed v3.27 firmware assets and BuildAC-derived `TCDA.bin`.

- [ ] Commit and push the verified ESPWebInstaller workflow/test changes.
- [ ] Dispatch the props builder with `refresh_tcd_release=true` and wait for the TCD job to finish.
- [ ] Confirm the other four same-version jobs skipped publication.
- [ ] Download v3.27 assets; verify firmware contains `CS09`, `TCDA.bin` matches BuildAC `sound-pack-cs09.zip`, and release tag/version remains v3.27.
