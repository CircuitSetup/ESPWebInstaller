#!/usr/bin/env python3
"""Add required ESPHome handoff metadata to retained manifests."""

import json
from pathlib import Path


MANIFESTS = Path(__file__).resolve().parents[1] / "manifests"


normalized = 0
for path in sorted(MANIFESTS.glob("manifest_*.json")):
    manifest = json.loads(path.read_text())
    if manifest.get("home_assistant_domain") == "esphome":
        continue
    manifest["home_assistant_domain"] = "esphome"
    path.write_text(json.dumps(manifest, separators=(",", ":")))
    normalized += 1

print(f"Normalized {normalized} manifest(s).")
