#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SOURCE_REPO_SUBDIR = "timecircuits-A10001986"
TARGET_SRC_SUBDIR = Path("Software") / "src"
ROOT_COPY_FILES = ("AddOns.md", "CheatSheet.pdf")
HEADER_PHOTO_LINES = (
    "![My TCD](img/mytcd_n.jpg)",
    "![My TCD](img/mytcd3_n.jpg)",
    "![My TCD](img/mytcd2_n.jpg)",
)
README_WIKI_URL = "https://github.com/CircuitSetup/Time-Circuits-Display/wiki"
README_WIKI_PATTERN = re.compile(r"^\[View the instructions for assembling your CircuitSetup TCD Kit\]\([^)]*\)$", re.MULTILINE)
TCD_FRONT_PATTERN = re.compile(r"^\| !\[TCD Front\]\([^)]+\) \|$", re.MULTILINE)
README_UPSTREAM_NOTICE = (
    '>[This repository](https://tcd.out-a-ti.me) is the upstream source for CircuitSetup\'s releases. '
    'The differences are that both code and documentation [here](https://tcd.out-a-ti.me) might be ahead '
    'in development, and in the sound-packs.'
)


EXACT_URL_REPLACEMENTS = {
    "https://tcd.out-a-ti.me/AddOns.md#timing": "https://github.com/CircuitSetup/Time-Circuits-Display/blob/master/AddOns.md#timing",
    "https://github.com/realA10001986/Time-Circuits-Display/releases": "https://github.com/CircuitSetup/Time-Circuits-Display/releases",
    "https://github.com/realA10001986/Time-Circuits-Display/blob/main/CheatSheet.pdf": "https://github.com/CircuitSetup/Time-Circuits-Display/blob/master/CheatSheet.pdf",
    "https://github.com/realA10001986/Time-Circuits-Display/blob/main/timecircuits-A10001986/timecircuits-A10001986.ino": "https://github.com/CircuitSetup/Time-Circuits-Display/blob/master/Software/src/timecircuits.ino",
    "https://fc.out-a-ti.me": "https://github.com/CircuitSetup/Flux-Capacitor",
    "https://sid.out-a-ti.me": "https://github.com/CircuitSetup/SID",
    "https://dg.out-a-ti.me": "https://github.com/CircuitSetup/Dash-Gauges",
    "https://remote.out-a-ti.me": "https://github.com/CircuitSetup/Remote",
    "https://github.com/realA10001986/Flux-Capacitor/tree/main?tab=readme-ov-file#connecting-a-tcd-by-wire": "https://github.com/CircuitSetup/Flux-Capacitor#connecting-a-tcd-by-wire",
    "https://github.com/realA10001986/SID/tree/main?tab=readme-ov-file#connecting-a-tcd-by-wire": "https://github.com/CircuitSetup/SID#connecting-a-tcd-by-wire",
    "https://github.com/realA10001986/Dash-Gauges/blob/main/hardware/README.md#connecting-a-tcd-to-the-dash-gauges-by-wire": "https://github.com/CircuitSetup/Dash-Gauges/blob/main/hardware/README.md#connecting-a-tcd-to-the-dash-gauges-by-wire",
    "https://github.com/realA10001986/Remote": "https://github.com/CircuitSetup/Remote",
}

REGEX_URL_REPLACEMENTS = (
    (
        re.compile(r"https://tcd\.out-a-ti\.me(?=(?:[)\]\s]|$))"),
        "https://github.com/CircuitSetup/Time-Circuits-Display",
    ),
    (
        re.compile(r"https://github\.com/realA10001986/Time-Circuits-Display(?=(?:[)\]\s]|$))"),
        "https://github.com/CircuitSetup/Time-Circuits-Display",
    ),
)

FORBIDDEN_README_URLS = (
    "https://tcd.out-a-ti.me",
    "https://fc.out-a-ti.me",
    "https://sid.out-a-ti.me",
    "https://dg.out-a-ti.me",
    "https://remote.out-a-ti.me",
    "https://github.com/realA10001986/Flux-Capacitor/tree/main?tab=readme-ov-file#connecting-a-tcd-by-wire",
    "https://github.com/realA10001986/SID/tree/main?tab=readme-ov-file#connecting-a-tcd-by-wire",
    "https://github.com/realA10001986/Dash-Gauges/blob/main/hardware/README.md#connecting-a-tcd-to-the-dash-gauges-by-wire",
)


@dataclass
class SyncSummary:
    dry_run: bool
    updated_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    validations: list[str] = field(default_factory=list)

    def note_result(self, relpath: str, changed: bool) -> None:
        target_list = self.updated_files if changed else self.unchanged_files
        if relpath not in target_list:
            target_list.append(relpath)

    def render_markdown(self) -> str:
        lines = [
            "## Time Circuits Display Sync",
            f"- Dry run: `{'true' if self.dry_run else 'false'}`",
            f"- Planned file updates: `{len(self.updated_files)}`",
        ]

        if self.validations:
            lines.append("- Validation checks:")
            lines.extend(f"  - {item}" for item in self.validations)

        if self.updated_files:
            lines.append("")
            lines.append("### Files To Update")
            lines.extend(f"- `{path}`" for path in sorted(self.updated_files))
        else:
            lines.append("")
            lines.append("### Files To Update")
            lines.append("- No changes required.")

        return "\n".join(lines) + "\n"


class SyncError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Time Circuits Display content between repos.")
    parser.add_argument("--source-dir", required=True, type=Path, help="Path to the cloned Time-Circuits-Display-A10001986 repo.")
    parser.add_argument("--target-dir", required=True, type=Path, help="Path to the cloned Time-Circuits-Display repo.")
    parser.add_argument("--dry-run", action="store_true", help="Report planned changes without modifying the target repo.")
    parser.add_argument("--summary-file", type=Path, help="Optional markdown file to write a run summary to.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise SyncError(f"Missing {description}: {path}")


def write_text_if_changed(path: Path, content: str, dry_run: bool) -> bool:
    existing = read_text(path) if path.exists() else None
    normalized = content.replace("\r\n", "\n")
    if existing == normalized:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def copy_file_if_changed(src: Path, dst: Path, dry_run: bool) -> bool:
    src_bytes = read_bytes(src)
    dst_bytes = read_bytes(dst) if dst.exists() else None
    if dst_bytes == src_bytes:
        return False
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src_bytes)
    return True


def apply_exact_url_replacements(text: str) -> str:
    updated = text
    for old, new in sorted(EXACT_URL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        updated = updated.replace(old, new)
    for pattern, replacement in REGEX_URL_REPLACEMENTS:
        updated = pattern.sub(replacement, updated)
    return updated


def extract_target_header_line(target_readme: str) -> str:
    match = TCD_FRONT_PATTERN.search(target_readme)
    if not match:
        raise SyncError("Could not extract the existing TCD Front header image from target README.")
    return match.group(0)


def extract_target_wiki_line(target_readme: str) -> str:
    match = README_WIKI_PATTERN.search(target_readme)
    if not match:
        raise SyncError("Could not extract the CircuitSetup wiki link from target README.")
    return match.group(0)


def remove_upstream_header_photos(readme: str) -> str:
    updated = readme
    for line in HEADER_PHOTO_LINES:
        updated = updated.replace(f"{line}\n", "")
        updated = updated.replace(line, "")
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated


def inject_header_line(readme: str, header_line: str) -> str:
    match = re.match(r"^(# .+?)\n\n", readme)
    if not match:
        raise SyncError("Could not find the README title while inserting the target header image.")
    title = match.group(1)
    remainder = readme[match.end():]
    return f"{title}\n\n{header_line}\n\n{remainder}"


def inject_wiki_line(readme: str, wiki_line: str) -> str:
    if wiki_line in readme:
        return readme

    marker = "And don't be fooled by the looks, it got brains, too!"
    if marker not in readme:
        raise SyncError("Could not find the intro marker while inserting the CircuitSetup wiki link.")

    return readme.replace(marker, f"{wiki_line}\n\n{marker}", 1)


def transform_readme(source_readme: str, target_readme: str) -> str:
    header_line = extract_target_header_line(target_readme)
    wiki_line = extract_target_wiki_line(target_readme)

    updated = source_readme
    updated = remove_upstream_header_photos(updated)
    updated = updated.replace(README_UPSTREAM_NOTICE, "")
    updated = apply_exact_url_replacements(updated)
    updated = inject_header_line(updated, header_line)
    updated = inject_wiki_line(updated, wiki_line)
    updated = re.sub(r"\n{3,}", "\n\n", updated).strip() + "\n"
    validate_readme(updated, header_line, wiki_line)
    return updated


def parse_platformio_build_macros(platformio_text: str) -> set[str]:
    macros: set[str] = set()
    for match in re.finditer(r"(?m)^\s*-D([A-Za-z_][A-Za-z0-9_]*)(?:=.*?)?(?:\s*[;#].*)?\s*$", platformio_text):
        macros.add(match.group(1))
    return macros


def comment_out_define(text: str, macro: str) -> str:
    pattern = re.compile(rf"(?m)^([ \t]*)#define[ \t]+{re.escape(macro)}(\b.*)$")
    return pattern.sub(rf"\1//#define {macro}\2", text)


def normalize_tc_global(tc_global_text: str, platformio_text: str) -> str:
    macros = parse_platformio_build_macros(platformio_text)
    macros.add("V_A10001986")

    updated = tc_global_text
    for macro in sorted(macros):
        updated = comment_out_define(updated, macro)

    validate_tc_global(updated, macros)
    return updated


def validate_tc_global(tc_global_text: str, macros: Iterable[str]) -> None:
    for macro in macros:
        if re.search(rf"(?m)^[ \t]*#define[ \t]+{re.escape(macro)}\b", tc_global_text):
            raise SyncError(f"Active define `{macro}` is still present in tc_global.h after normalization.")


def validate_readme(readme: str, header_line: str, wiki_line: str) -> None:
    if readme.count(header_line) != 1:
        raise SyncError("README does not contain exactly one preserved target header image line.")

    expected_prefix = f"# Time Circuits Display\n\n{header_line}\n\n"
    if not readme.startswith(expected_prefix):
        raise SyncError("README does not start with the preserved target header image directly below the title.")

    if wiki_line not in readme:
        raise SyncError("README is missing the preserved CircuitSetup wiki link.")

    for line in HEADER_PHOTO_LINES:
        if line in readme:
            raise SyncError(f"README still contains an upstream header photo line: {line}")

    for url in FORBIDDEN_README_URLS:
        if url in readme:
            raise SyncError(f"README still contains a URL that should have been rewritten: {url}")


def sync_directory(source_dir: Path, target_dir: Path, dry_run: bool, summary: SyncSummary, summary_root: Path) -> None:
    ensure_exists(source_dir, f"source directory {source_dir.name}")

    for src in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        rel = src.relative_to(source_dir)
        dst = target_dir / rel
        changed = copy_file_if_changed(src, dst, dry_run)
        summary.note_result(dst.relative_to(summary_root).as_posix(), changed)


def sync_docs_and_assets(source_root: Path, target_root: Path, dry_run: bool, summary: SyncSummary) -> None:
    for filename in ROOT_COPY_FILES:
        src = source_root / filename
        dst = target_root / filename
        ensure_exists(src, filename)
        if filename.endswith(".md"):
            content = apply_exact_url_replacements(read_text(src)).strip() + "\n"
            changed = write_text_if_changed(dst, content, dry_run)
        else:
            changed = copy_file_if_changed(src, dst, dry_run)
        summary.note_result(filename, changed)

    sync_directory(source_root / "img", target_root / "img", dry_run, summary, target_root)


def sync_readme(source_root: Path, target_root: Path, dry_run: bool, summary: SyncSummary) -> None:
    src = source_root / "README.md"
    dst = target_root / "README.md"
    ensure_exists(src, "source README.md")
    ensure_exists(dst, "target README.md")
    merged = transform_readme(read_text(src), read_text(dst))
    changed = write_text_if_changed(dst, merged, dry_run)
    summary.note_result("README.md", changed)
    summary.validations.append("README header, wiki link, and link rewrites verified")


def sync_source_tree(source_root: Path, target_root: Path, dry_run: bool, summary: SyncSummary) -> None:
    src_dir = source_root / SOURCE_REPO_SUBDIR
    target_src_dir = target_root / TARGET_SRC_SUBDIR
    ensure_exists(src_dir, f"source firmware directory `{SOURCE_REPO_SUBDIR}`")
    ensure_exists(target_src_dir, f"target firmware directory `{TARGET_SRC_SUBDIR.as_posix()}`")

    for src in sorted(path for path in src_dir.rglob("*") if path.is_file()):
        rel = src.relative_to(src_dir)
        if rel.name == "timecircuits-A10001986.ino":
            rel = rel.with_name("timecircuits.ino")
        dst = target_src_dir / rel
        changed = copy_file_if_changed(src, dst, dry_run)
        summary.note_result((TARGET_SRC_SUBDIR / rel).as_posix(), changed)

    tc_global_path = target_src_dir / "tc_global.h"
    platformio_path = target_root / "Software" / "platformio.ini"
    normalized = normalize_tc_global(read_text(tc_global_path), read_text(platformio_path))
    changed = write_text_if_changed(tc_global_path, normalized, dry_run)
    summary.note_result((TARGET_SRC_SUBDIR / "tc_global.h").as_posix(), changed)
    summary.validations.append("tc_global.h build-flag defines normalized and V_A10001986 commented out")


def write_summary(path: Path, summary: SyncSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary.render_markdown(), encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    summary = SyncSummary(dry_run=args.dry_run)

    source_root = args.source_dir.resolve()
    target_root = args.target_dir.resolve()

    try:
        ensure_exists(source_root, "source repo")
        ensure_exists(target_root, "target repo")

        sync_source_tree(source_root, target_root, args.dry_run, summary)
        sync_docs_and_assets(source_root, target_root, args.dry_run, summary)
        sync_readme(source_root, target_root, args.dry_run, summary)
    except SyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary_file:
            failure_summary = SyncSummary(dry_run=args.dry_run)
            failure_summary.validations.append(str(exc))
            write_summary(args.summary_file, failure_summary)
        return 1

    if args.summary_file:
        write_summary(args.summary_file, summary)

    print(summary.render_markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
