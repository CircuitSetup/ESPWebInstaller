#!/usr/bin/env bash
set -e

mkdir -p manifests

declare -A name_map=(
  ["circuitsetup-gdo-default"]="CircuitSetup Security+ Garage Door Opener"
  ["circuitsetup-gdo-dry-contact"]="CircuitSetup Garage Door Opener Dry Contact"
  ["6chan_energy_meter_main_board"]="CircuitSetup 6 Channel Energy Meter Main"
  ["6chan_energy_meter_1-addon"]="CircuitSetup 6 Channel Energy Meter Main + 1 Add-on"
  ["6chan_energy_meter_2-addons"]="CircuitSetup 6 Channel Energy Meter Main + 2 Add-ons"
  ["6chan_energy_meter_3-addons"]="CircuitSetup 6 Channel Energy Meter Main + 3 Add-ons"
  ["6chan_energy_meter_main_ethernet"]="CircuitSetup 6 Channel Energy Meter Ethernet"
  ["6chan_energy_meter_1-addon_ethernet"]="CircuitSetup 6 Channel Energy Meter + 1 Add-on Ethernet"
  ["6chan_energy_meter_2-addons_ethernet"]="CircuitSetup 6 Channel Energy Meter + 2 Add-ons Ethernet"
  ["6chan_energy_meter_3-addons_ethernet"]="CircuitSetup 6 Channel Energy Meter + 3 Add-ons Ethernet"
)

for bin_file in firmware/*.bin; do
  fname=$(basename "$bin_file")
  base="${fname%.bin}"
  
  # Match product and version: 2025.8.0 or 2025.8.0-dev
  if [[ "$base" =~ ^(.+)-([0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9]+)?)$ ]]; then
    product="${BASH_REMATCH[1]}"
    version="${BASH_REMATCH[2]}"
  else
    echo "Skipping invalid filename pattern: $fname"
    continue
  fi

  manifest="manifests/manifest_${product}-${version}.json"
  if [[ -f "$manifest" ]]; then
    echo "Manifest exists for $fname → $manifest"
    continue
  fi

  name="${name_map[$product]}"
  if [[ -z "$name" ]]; then
    echo "Skipping unknown product: $product"
    continue
  fi

  # Determine MCU
  if [[ "$product" =~ _ethernet$ || "$product" == circuitsetup-gdo* ]]; then
    MCU="ESP32_S3"
  else
    MCU="ESP32"
  fi

  echo "Generating manifest for $fname → $manifest"

  export MANIFEST_NAME="$name"
  export MANIFEST_FNAME=$(basename "$manifest")
  export MANIFEST_VERSION="$version"

  if [[ "$MCU" == "ESP32_S3" ]]; then
    export ESP32_S3_IMAGE_URI="https://circuitsetup.github.io/ESPWebInstaller/firmware/$fname"
  else
    export ESP32_IMAGE_URI="https://circuitsetup.github.io/ESPWebInstaller/firmware/$fname"
  fi

  ruby ./scripts/update-espwebtools-manifests.rb
done
