#!/bin/bash

set -euo pipefail

select_configs() {
  local family="$1"
  local files_json="$2"

  case "$family" in
    gdo)
      jq -r '.[] | select(startswith("circuitsetup-gdo-"))' <<< "$files_json"
      ;;
    energy_meter)
      jq -r '.[] | select(startswith("6chan_energy_meter_"))' <<< "$files_json"
      ;;
    *)
      echo "Unknown firmware family: $family" >&2
      return 1
      ;;
  esac
}

if [[ "${1:-}" == "--list" ]]; then
  select_configs "${2:?Missing firmware family}" "${3:?Missing files JSON}"
  exit 0
fi

family="${1:?Missing firmware family}"
files_json="${2:?Missing files JSON}"
version="${3:?Missing ESPHome version}"
esphome_dev="${4:-false}"
repo_root="$(pwd)"

mapfile -t configs < <(select_configs "$family" "$files_json")

output_dir="batch-output/$family"
work_dir="batch-work/$family"
mkdir -p "$output_dir/firmware" "$output_dir/manifests" "$work_dir"
echo '{}' > "$output_dir/${family}-source_versions.json"

if [[ ${#configs[@]} -eq 0 ]]; then
  echo "No $family firmware needs to be built."
  exit 0
fi

source scripts/configs.sh

check_branch_exists() {
  local repo="$1"
  local branch="$2"
  [[ "$(curl -s -o /dev/null -w '%{http_code}' "https://api.github.com/repos/${repo}/branches/${branch}")" == "200" ]]
}

gdo_branch="master"
energy_meter_branch="master"
image_version="$version"

if [[ "$esphome_dev" == "true" ]]; then
  image_version="dev"
  check_branch_exists CircuitSetup/circuitsetup-esphome dev && gdo_branch="dev"
  check_branch_exists CircuitSetup/Expandable-6-Channel-ESP32-Energy-Meter dev && energy_meter_branch="dev"
fi

image="ghcr.io/esphome/esphome:$image_version"
cache_dir="$HOME/.cache/esphome"
mkdir -p "$cache_dir"

echo "::group::Pull ESPHome image"
docker pull "$image"
echo "::endgroup::"

docker_args=(
  run --rm
  --workdir /github/workspace
  -v "$(pwd):/github/workspace"
  -v "$cache_dir:/cache"
  -v "$HOME:$HOME"
  --user "$(id -u):$(id -g)"
  -e HOME
  -e PLATFORMIO_GLOBALLIB_DIR=
)

for config_file in "${configs[@]}"; do
  config_base="$(basename "$config_file" .yaml)"
  config_dir="$work_dir/$config_base"
  config_path="$config_dir/$config_file"
  mkdir -p "$config_dir"

  if [[ "$config_file" == circuitsetup-gdo-* ]]; then
    config_branch="$gdo_branch"
  else
    config_branch="$energy_meter_branch"
  fi

  url="$(config_raw_url "$config_file" "$config_branch" download)"
  echo "Downloading $config_file from $url"
  curl -fSL "$url" -o "$config_path"

  echo "::group::Compile $config_file"
  docker "${docker_args[@]}" "$image" compile "$config_path"
  echo "::endgroup::"

  idedata="$(docker "${docker_args[@]}" "$image" idedata "$config_path")"
  prog_path="$(jq -r '.prog_path' <<< "$idedata")"
  if [[ "$prog_path" == /github/workspace/* ]]; then
    source_firmware=".${prog_path#/github/workspace}"
  else
    source_firmware="$prog_path"
  fi
  source_firmware="${source_firmware%/*}/firmware.factory.bin"

  if [[ ! -f "$source_firmware" ]]; then
    echo "Compiled factory binary not found: $source_firmware" >&2
    exit 1
  fi

  filename="${config_base}-${version}.bin"
  cp "$source_firmware" "$output_dir/firmware/$filename"

  matched_entry="${CONFIG_META[$config_file]:-}"
  if [[ -z "$matched_entry" ]]; then
    echo "No manifest mapping found for $config_file." >&2
    exit 1
  fi

  IFS='|' read -r name mcu <<< "$matched_entry"
  export MANIFEST_NAME="$name"
  export MANIFEST_FNAME="manifest_${config_base}-${version}.json"
  export MANIFEST_VERSION="$version"
  unset ESP32_IMAGE_URI ESP32_S3_IMAGE_URI

  if [[ "$mcu" == "ESP32_S3" ]]; then
    export ESP32_S3_IMAGE_URI="https://circuitsetup.github.io/ESPWebInstaller/firmware/$filename"
  else
    export ESP32_IMAGE_URI="https://circuitsetup.github.io/ESPWebInstaller/firmware/$filename"
  fi

  (
    cd "$output_dir"
    ruby "$repo_root/scripts/update-espwebtools-manifests.rb"
  )

  if [[ "$esphome_dev" != "true" ]]; then
    source_version="$(fetch_config_source_version "$config_file" master)"
    if [[ -z "$source_version" ]]; then
      echo "Could not determine source version for $config_file" >&2
      exit 1
    fi

    snapshot="$output_dir/${family}-source_versions.json"
    tmp="$(mktemp)"
    jq --arg config "$config_file" --arg source_version "$source_version" \
      '. + {($config): $source_version}' "$snapshot" > "$tmp"
    mv "$tmp" "$snapshot"
  fi
done
