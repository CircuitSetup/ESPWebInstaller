import os
import re
from pathlib import Path


base_dir = Path(os.environ["BASE_DIR"])
src_dir = base_dir / "src"
if not src_dir.exists():
    raise SystemExit(f"src directory not found at {src_dir}")

changelog_file = None
for path in sorted(src_dir.glob("*.ino")):
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")
    if "changelog" in content.lower():
        changelog_file = path
        changelog_content = content
        break

if changelog_file is None:
    raise SystemExit("No .ino file containing a changelog was found")

current_version = os.environ.get("CURRENT_VERSION", "").lstrip("vV")
last_version = os.environ.get("LAST_VERSION", "").lstrip("vV") or None

version_notes = {}
version_order = []
active_version = None
active_note_index = None
in_changelog = False
pending_notes = []
pending_note_index = None


def ensure_version_entry(version: str, *, prepend: bool = False) -> None:
    if version not in version_notes:
        version_notes[version] = []
    if version not in version_order:
        if prepend:
            version_order.insert(0, version)
        else:
            version_order.append(version)


def append_continuation(notes: list[str], index: int | None, text: str) -> None:
    if index is None or not text:
        return
    separator = "" if notes[index].endswith("-") else " "
    notes[index] += separator + text


def version_key(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError as error:
        raise SystemExit(f"Unsupported changelog version: {version}") from error


for raw_line in changelog_content.splitlines():
    line = raw_line.strip()
    if not in_changelog:
        if "changelog" in line.lower():
            in_changelog = True
        continue
    if line.startswith("*/"):
        break
    if not line or not line.startswith("*"):
        continue

    content = line[1:].lstrip()
    header_match = re.match(
        r"(?P<date>\d{4}/\d{2}/\d{2})\s+\([^)]*\)(?:\s+\[(?P<version>[^\]]+)\])?",
        content,
    )
    if header_match:
        version = header_match.group("version")
        if version:
            version = version.strip()
            if pending_notes:
                target_version = current_version or version
                if not target_version:
                    raise SystemExit("Found changelog notes without any version to assign")
                ensure_version_entry(target_version, prepend=not version_order)
                version_notes[target_version].extend(pending_notes)
                pending_notes.clear()
                pending_note_index = None
            active_version = version
            active_note_index = None
            ensure_version_entry(active_version)
        continue

    if active_version is None:
        if content.startswith("-"):
            text = content[1:].strip()
            if text:
                pending_notes.append(text)
                pending_note_index = len(pending_notes) - 1
        else:
            append_continuation(pending_notes, pending_note_index, content.strip())
        continue

    if content.startswith("-"):
        text = content[1:].strip()
        version_notes[active_version].append(text)
        active_note_index = len(version_notes[active_version]) - 1
    else:
        append_continuation(
            version_notes[active_version], active_note_index, content.strip()
        )

if pending_notes:
    target_version = current_version or (version_order[0] if version_order else None)
    if not target_version:
        raise SystemExit("Found changelog notes without any version to assign")
    ensure_version_entry(target_version, prepend=not version_order)
    version_notes[target_version].extend(pending_notes)

if not version_notes:
    raise SystemExit("No changelog entries with versions were found")

fallback_version = None
if current_version and current_version not in version_notes:
    fallback_version = version_order[0]
    print(
        f"Current version {current_version} not found in changelog; "
        f"using top changelog entry {fallback_version}."
    )

if fallback_version:
    selected_versions = [fallback_version]
else:
    selected_versions = []
    last_version_key = version_key(last_version) if last_version else None
    for version in version_order:
        if last_version_key and version_key(version) <= last_version_key:
            break
        selected_versions.append(version)

if not selected_versions:
    selected_versions = [current_version] if current_version else []

body_lines = []
for version in selected_versions:
    notes = version_notes.get(version, [])
    if not notes:
        continue
    body_lines.append(f"## {version}")
    for note in notes:
        body_lines.append(f"- {note}")
    body_lines.append("")

if not body_lines:
    raise SystemExit("No release notes collected from changelog")

body = "\n".join(body_lines).strip()

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
    output.write("body<<EOF\n")
    output.write(body)
    output.write("\nEOF\n")
