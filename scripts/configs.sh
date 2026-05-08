#!/bin/bash

# Metadata for each YAML config: "Display Name|MCU Type"
declare -A CONFIG_META

CONFIG_META["circuitsetup-gdo-default.yaml"]="CircuitSetup Security+ Garage Door Opener|ESP32_S3"
CONFIG_META["circuitsetup-gdo-dry-contact.yaml"]="CircuitSetup Garage Door Opener Dry Contact|ESP32_S3"

CONFIG_META["6chan_energy_meter_main_board.yaml"]="CircuitSetup 6 Channel Energy Meter Main|ESP32"
CONFIG_META["6chan_energy_meter_1-addon.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 1 Add-on|ESP32"
CONFIG_META["6chan_energy_meter_2-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 2 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_3-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 3 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_3-addons_2-voltages.yaml"]="CircuitSetup 6 Channel Energy Meter 3 Add-ons 2 Voltages|ESP32"
CONFIG_META["6chan_energy_meter_4-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 4 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_5-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 5 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_6-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 6 Add-ons|ESP32"

CONFIG_META["6chan_energy_meter_main_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_main_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_1-addon_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 1 Add-on Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_1-addon_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 1 Add-on Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_2-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 2 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_2-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 2 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_3-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 3 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_3-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 3 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_4-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 4 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_4-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 4 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_5-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 5 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_5-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 5 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_6-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 6 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_6-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 6 Add-ons Ethernet Waveshare|ESP32_S3"

# Source metadata for each YAML config. The download path is the config built by
# ESPHome; the version path is the YAML whose firmware version should trigger a
# rebuild when it changes upstream.
declare -A CONFIG_REPO
declare -A CONFIG_DOWNLOAD_PATH
declare -A CONFIG_VERSION_PATH
declare -A CONFIG_VERSION_KEY

for config in "${!CONFIG_META[@]}"; do
  if [[ "$config" == circuitsetup-gdo-default.yaml ]]; then
    CONFIG_REPO["$config"]="CircuitSetup/circuitsetup-esphome"
    CONFIG_DOWNLOAD_PATH["$config"]="$config"
    CONFIG_VERSION_PATH["$config"]="circuitsetup-secplus-garage-door-opener.yaml"
    CONFIG_VERSION_KEY["$config"]="project_version"
  elif [[ "$config" == circuitsetup-gdo-dry-contact.yaml ]]; then
    CONFIG_REPO["$config"]="CircuitSetup/circuitsetup-esphome"
    CONFIG_DOWNLOAD_PATH["$config"]="$config"
    CONFIG_VERSION_PATH["$config"]="$config"
    CONFIG_VERSION_KEY["$config"]="project_version"
  else
    CONFIG_REPO["$config"]="CircuitSetup/Expandable-6-Channel-ESP32-Energy-Meter"
    CONFIG_DOWNLOAD_PATH["$config"]="Software/ESPHome/$config"
    CONFIG_VERSION_PATH["$config"]="Software/ESPHome/$config"
    CONFIG_VERSION_KEY["$config"]="version"
  fi
done

config_raw_url() {
  local config="$1"
  local branch="$2"
  local path_kind="${3:-download}"
  local path="${CONFIG_DOWNLOAD_PATH[$config]}"

  if [[ "$path_kind" == "version" ]]; then
    path="${CONFIG_VERSION_PATH[$config]}"
  fi

  printf 'https://raw.githubusercontent.com/%s/%s/%s\n' "${CONFIG_REPO[$config]}" "$branch" "$path"
}

extract_yaml_scalar() {
  local key="$1"
  sed -nE "s/.*(^|[[:space:]])${key}:[[:space:]]*[\"']?([^\"'[:space:]#]+).*/\2/p" | head -n 1
}

fetch_config_source_version() {
  local config="$1"
  local branch="$2"
  local url

  url=$(config_raw_url "$config" "$branch" version)
  curl -fsSL "$url" | extract_yaml_scalar "${CONFIG_VERSION_KEY[$config]}"
}

# Flat list of config file names
CONFIG_LIST=("${!CONFIG_META[@]}")
