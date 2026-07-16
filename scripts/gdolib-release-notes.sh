#!/bin/bash

set -euo pipefail

repo="CircuitSetup/gdolib"

extract_ref() {
  sed -nE 's|.*github\.com/CircuitSetup/gdolib[^#]*#([^"[:space:]]+).*|\1|p' | head -n 1
}

render_notes() {
  local old_ref="$1"
  local new_ref="$2"

  [[ "$old_ref" == "$new_ref" ]] && return 0

  gh api "repos/$repo/compare/${old_ref}...${new_ref}" | jq -r \
    --arg old "$old_ref" --arg new "$new_ref" '
      "## gdolib changes (\($old) to \($new))\n\n" +
      ([.commits[] |
        "* " + (.commit.message | split("\n")[0]) +
        " ([`" + (.sha[0:7]) + "`](https://github.com/CircuitSetup/gdolib/commit/" + .sha + "))"
      ] | join("\n")) +
      "\n\n**Full gdolib changelog**: https://github.com/CircuitSetup/gdolib/compare/\($old)...\($new)"
    '
}

case "${1:-}" in
  --extract)
    extract_ref
    ;;
  --self-test)
    ref=$(printf '%s\n' '  - "gdolib=https://github.com/CircuitSetup/gdolib#v1.3.0"' | extract_ref)
    [[ "$ref" == "v1.3.0" ]]
    [[ -z "$(render_notes v1.3.0 v1.3.0)" ]]
    notes=$(render_notes v1.2.0 v1.3.0)
    grep -Fq '## gdolib changes (v1.2.0 to v1.3.0)' <<< "$notes"
    grep -Fq 'https://github.com/CircuitSetup/gdolib/compare/v1.2.0...v1.3.0' <<< "$notes"
    echo "gdolib release notes self-test passed."
    ;;
  *)
    render_notes "${1:?Missing previous gdolib ref}" "${2:?Missing current gdolib ref}"
    ;;
esac
