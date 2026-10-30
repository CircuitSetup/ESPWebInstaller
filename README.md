# CircuitSetup ESPHome Web Installer & Firmware Builder

[Please see here](https://circuitsetup.github.io/ESPWebInstaller/)

The **Build ESPHome Firmware** workflow checks GDO versions hourly (at minute 17,
subject to GitHub's scheduling delays). It rebuilds Security+ when `project_version`
in `circuitsetup-secplus-garage-door-opener.yaml` or `version` in
`CircuitSetup/gdolib`'s `library.json` changes. It rebuilds dry-contact firmware when
`project_version` in `circuitsetup-gdo-dry-contact.yaml` changes. YAML edits without
a version change do not trigger a release. The existing twice-weekly check for all
firmware and new ESPHome versions remains enabled.

Stable GDO builds pin the upstream configuration, packages, and components to a
source commit. Security+ builds use the gdolib tag matching `library.json` (for
example, `v1.4.0`); if that tag is not yet available, the build fails and retries on
the next scheduled check. Security+ release tags include the gdolib version so a
library-only update can produce its own release. The installer continues to use
ESPHome versions for firmware filenames and manifests.
Newer Security+ components manage the gdolib pin themselves. Their pinned version
must match the detected gdolib version before publication; the workflow waits for
upstream compatibility rather than publishing a release with the wrong version.

Publishing requires the existing `RELEASE_TOKEN` repository secret with permission
to create releases in `CircuitSetup/circuitsetup-esphome`. A failed release does
not advance `manifests/source_versions.json`; the next check retries it. ESPHome
development builds do not publish stable GDO releases. For a manual rebuild, run
the workflow with **firmware_family: gdo** and **force_build: true**.

The installer shows **View firmware release** for the selected GDO variant and
ESPHome version. Each manifest records its exact `release_url`; publication adds
the link only after the release and binary are available. Existing retained GDO
manifests were matched to their release assets by SHA-256, including releases
that share the same ESPHome version. If release metadata is unavailable, the
installer keeps installation available and hides the release link.
An existing release is linked only when its asset checksum matches the installer
binary; same-version rebuilds with different bytes keep their release link hidden.
