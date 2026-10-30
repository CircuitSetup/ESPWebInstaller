#!/bin/bash

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/configs.sh"

repo="CircuitSetup/circuitsetup-esphome"

for config in circuitsetup-gdo-default.yaml circuitsetup-gdo-dry-contact.yaml; do
  jq -e --arg config "$config" 'index($config) != null' <<< "$FILES_JSON" >/dev/null || continue
  binary="firmware/${config%.yaml}-${ESPHOME_VERSION}.bin"
  [[ -f "$binary" ]] || { echo "Missing release binary: $binary" >&2; exit 1; }
  state=$(jq -ce --arg config "$config" '.[$config] | select(type == "object")' manifests/source_versions.json)
  project_version=$(jq -er '.project_version' <<< "$state")
  source_ref=$(jq -er '.source_ref' <<< "$state")
  tag=$(gdo_release_tag "$config" "$ESPHOME_VERSION" "$state")
  friendly="${CONFIG_META[$config]%|*}"
  release_url="https://github.com/${repo}/releases/tag/${tag}"

  if release=$(gh api "repos/${repo}/releases/tags/${tag}" 2>/dev/null); then
    asset=$(jq -c --arg name "$(basename "$binary")" '.assets[] | select(.name == $name)' <<< "$release")
    if [[ -z "$asset" ]]; then
      gh release upload "$tag" "$binary" --repo "$repo"
    elif [[ "$(jq -r '.digest // empty' <<< "$asset")" != "sha256:$(sha256sum "$binary" | cut -d' ' -f1)" ]]; then
      echo "Release $tag has a different or unverifiable binary. Omitting its installer link."
      release_url=""
    fi
    echo "Release $tag already exists."
  else
    notes="Built with ESPHome ${ESPHOME_VERSION}"
    notes+=$'\n\n'"Source: https://github.com/${repo}/commit/${source_ref}"
    if [[ "$config" == circuitsetup-gdo-default.yaml ]]; then
      current_gdolib="v$(jq -er '.gdolib_version' <<< "$state")"
      notes+=$'\n\n'"gdolib: ${current_gdolib}"
      previous_tag=$(gh release list --repo "$repo" --limit 100 --json tagName,publishedAt \
        | jq -r '[.[] | select(.tagName | startswith("circuitsetup-secplus-garage-door-opener-v"))] | sort_by(.publishedAt) | last | .tagName // empty')
      if [[ -n "$previous_tag" ]]; then
        if [[ "$previous_tag" == *-gdolib-* ]]; then
          previous_gdolib="${previous_tag##*-gdolib-}"
        else
          previous_gdolib=$(curl -fsSL \
            "https://raw.githubusercontent.com/${repo}/${previous_tag}/${CONFIG_VERSION_PATH[$config]}" \
            | bash "$(dirname "${BASH_SOURCE[0]}")/gdolib-release-notes.sh" --extract)
        fi
        if [[ -n "$previous_gdolib" ]]; then
          gdolib_notes=$(bash "$(dirname "${BASH_SOURCE[0]}")/gdolib-release-notes.sh" "$previous_gdolib" "$current_gdolib")
          [[ -z "$gdolib_notes" ]] || notes+=$'\n\n'"$gdolib_notes"
        fi
      fi
    fi

    gh release create "$tag" "$binary" --repo "$repo" --target "$source_ref" \
      --title "$friendly v${project_version} - ESPHome v${ESPHOME_VERSION}" \
      --notes "$notes" --generate-notes
  fi

  manifest="manifests/manifest_${config%.yaml}-${ESPHOME_VERSION}.json"
  tmp=$(mktemp)
  jq --arg release_url "$release_url" \
    'if $release_url == "" then del(.release_url) else .release_url = $release_url end' "$manifest" > "$tmp"
  mv "$tmp" "$manifest"
done
