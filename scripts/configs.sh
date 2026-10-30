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
    CONFIG_DOWNLOAD_PATH["$config"]="circuitsetup-secplus-garage-door-opener.yaml"
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

# Capture versions before compiling; source_ref records provenance, not a trigger.
config_source_state() {
  local config="$1" source_ref="$2" project_version gdolib_version
  project_version=$(extract_yaml_scalar "${CONFIG_VERSION_KEY[$config]}")
  [[ "$project_version" =~ ^[0-9]+(\.[0-9]+)+([a-zA-Z0-9.+-]*)$ ]] || {
    echo "Missing or invalid source version for $config" >&2
    return 1
  }

  if [[ "$config" == circuitsetup-gdo-* ]]; then
    if [[ "$config" == circuitsetup-gdo-default.yaml ]]; then
      gdolib_version=$(curl -fsSL https://raw.githubusercontent.com/CircuitSetup/gdolib/master/library.json \
        | jq -er '.version | select(type == "string" and test("^[0-9]+\\.[0-9]+\\.[0-9]+([a-zA-Z0-9.+-]*)$"))') || return 1
      jq -cnS --arg project_version "$project_version" --arg source_ref "$source_ref" \
        --arg gdolib_version "$gdolib_version" \
        '{project_version: $project_version, source_ref: $source_ref, gdolib_version: $gdolib_version}'
    else
      jq -cnS --arg project_version "$project_version" --arg source_ref "$source_ref" \
        '{project_version: $project_version, source_ref: $source_ref}'
    fi
  else
    jq -cn --arg version "$project_version" '$version'
  fi
}

fetch_config_source_state() {
  curl -fsSL "$(config_raw_url "$1" "$2" version)" | config_source_state "$1" "$2"
}

source_state_version() {
  local config="$1" state="$2"
  if [[ "$config" == circuitsetup-gdo-* ]]; then
    jq -cS 'if type == "string" then {project_version: .} elif type == "object" then del(.source_ref) else . end' <<< "$state"
  else
    jq -cS . <<< "$state"
  fi
}

prepare_gdo_config() {
  local path="$1" state="$2" source_ref gdolib_version component_gdolib
  source_ref=$(jq -er '.source_ref | select(test("^[0-9a-f]{40}$"))' <<< "$state") || return 1
  sed -i -E "/package_import_url:/!s/@master/@${source_ref}/g; s/ref: master/ref: ${source_ref}/g" "$path"
  gdolib_version=$(jq -r '.gdolib_version // empty' <<< "$state")
  if [[ -n "$gdolib_version" ]]; then
    component_gdolib=$(curl -fsSL "https://raw.githubusercontent.com/CircuitSetup/circuitsetup-esphome/${source_ref}/components/secplus_gdo/__init__.py" \
      | sed -nE '/^GDOLIB_REPOSITORY[[:space:]]*=/p' \
      | bash "$(dirname "${BASH_SOURCE[0]}")/gdolib-release-notes.sh" --extract) || return 1
    if [[ -n "$component_gdolib" && "$component_gdolib" != "v${gdolib_version}" ]]; then
      echo "GDO component pins $component_gdolib; waiting for it to support detected gdolib v${gdolib_version}." >&2
      return 1
    fi
    if grep -Fq 'gdolib=https://github.com/CircuitSetup/gdolib#' "$path"; then
      sed -i -E "s|(gdolib=https://github.com/CircuitSetup/gdolib#)[^\"'[:space:]]+|\\1v${gdolib_version}|g" "$path"
    elif [[ -z "$component_gdolib" ]]; then
      echo "Could not determine the GDO component's gdolib dependency." >&2
      return 1
    fi
  fi
}

gdo_release_tag() {
  local config="$1" esphome_version="$2" state="$3" base project_version gdolib_version
  base="${config%.yaml}"
  [[ "$config" != circuitsetup-gdo-default.yaml ]] || base="circuitsetup-secplus-garage-door-opener"
  project_version=$(jq -er '.project_version' <<< "$state") || return 1
  gdolib_version=$(jq -r '.gdolib_version // empty' <<< "$state")
  printf '%s-v%s-esphome-v%s' "$base" "$project_version" "$esphome_version"
  [[ -z "$gdolib_version" ]] || printf -- '-gdolib-v%s' "$gdolib_version"
  printf '\n'
}

# Flat list of config file names
CONFIG_LIST=("${!CONFIG_META[@]}")
