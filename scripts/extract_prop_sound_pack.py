import argparse
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile


def version_key(path: Path) -> tuple[tuple[int, ...], str]:
    return tuple(int(number) for number in re.findall(r"\d+", path.name)), path.name


def copy_sound_pack(install_dir: Path, firmware_dir: Path, product: str, tcd_settings: Path | None = None) -> Path:
    if not install_dir.is_dir():
        raise FileNotFoundError(f"Install directory not found: {install_dir}")

    required_version = None
    required_format = None
    if product == "Time Circuits Display":
        if tcd_settings is None:
            raise ValueError("TCD firmware settings are required to verify the CircuitSetup sound pack")
        settings = tcd_settings.read_text(encoding="utf-8")
        versions = re.findall(r'^\s*#define\s+SND_REQ_VERSION\s+"(CS[0-9]{2})"', settings, re.MULTILINE)
        formats = re.findall(r'^\s*#define\s+AC_FMTV\s+([0-9]+)\b', settings, re.MULTILINE)
        if len(versions) != 1 or len(formats) != 1 or int(formats[0]) not in (2, 3):
            raise ValueError(f"Unable to read the CircuitSetup sound-pack requirement from {tcd_settings}")
        required_version, required_format = versions[0], int(formats[0])

    prefix = {"Time Circuits Display": "TCDA", "Flux Capacitor": "FCA", "Dash-Gauges": "DGA"}.get(product)
    direct_pattern = f"{prefix}-{required_version}.bin" if required_version else f"{prefix}-*.bin"
    direct = sorted(
        (path for path in install_dir.glob(direct_pattern) if path.is_file()),
        key=version_key,
    ) if prefix else []
    if direct:
        content = direct[-1].read_bytes()
        filename = f"{prefix}.bin"
    else:
        pattern = f"sound-pack-{required_version.lower()}.zip" if required_version else "sound-pack-*.zip"
        archives = sorted((path for path in install_dir.glob(pattern) if path.is_file()), key=version_key)
        if not archives:
            raise ValueError(f"No {required_version or product} sound pack found in {install_dir}")
        with ZipFile(archives[-1]) as archive:
            binaries = [
                member for member in archive.infolist()
                if not member.is_dir() and member.filename.endswith(".bin")
                and "__MACOSX" not in Path(member.filename).parts
            ]
            if len(binaries) != 1:
                raise ValueError(f"Expected exactly one .bin inside {archives[-1]}, found {len(binaries)}")
            filename = f"{prefix}.bin" if prefix else Path(binaries[0].filename).name
            content = archive.read(binaries[0])

    if required_version:
        # Container v3 moved the version field from byte 5 to byte 13.
        offset = 13 if required_format == 3 else 5
        if (len(content) < 19 or content[:4] != b"TCDA" or content[4] & 0x7f != required_format
                or content[offset:offset + 4] != required_version.encode("ascii")):
            raise ValueError(f"Invalid TCD sound pack: firmware requires {required_version} (container format {required_format})")

    firmware_dir.mkdir(parents=True, exist_ok=True)
    destination = firmware_dir / filename
    destination.write_bytes(content)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy the latest prop sound pack into a firmware release.")
    parser.add_argument("install_dir", type=Path)
    parser.add_argument("firmware_dir", type=Path)
    parser.add_argument("product")
    parser.add_argument("--tcd-settings", type=Path, help="TCD firmware's tc_settings.cpp, required for TCD packs")
    args = parser.parse_args()
    try:
        print(f"Added sound pack: {copy_sound_pack(args.install_dir, args.firmware_dir, args.product, args.tcd_settings)}")
    except (OSError, ValueError, BadZipFile) as error:
        parser.exit(1, f"{error}\n")
