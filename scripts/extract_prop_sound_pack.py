import argparse
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile


def version_key(path: Path) -> tuple[tuple[int, ...], str]:
    return tuple(int(number) for number in re.findall(r"\d+", path.name)), path.name


def copy_sound_pack(install_dir: Path, firmware_dir: Path, product: str) -> Path:
    if not install_dir.is_dir():
        raise FileNotFoundError(f"Install directory not found: {install_dir}")

    prefix = {"Flux Capacitor": "FCA", "Dash-Gauges": "DGA"}.get(product)
    direct = sorted(
        (path for path in install_dir.glob(f"{prefix}-*.bin") if path.is_file()),
        key=version_key,
    ) if prefix else []
    if direct:
        content = direct[-1].read_bytes()
        filename = f"{prefix}.bin"
    else:
        pattern = "sound-pack-cs*.zip" if product == "Time Circuits Display" else "sound-pack-*.zip"
        archives = sorted((path for path in install_dir.glob(pattern) if path.is_file()), key=version_key)
        if not archives:
            raise ValueError(f"No sound pack found in {install_dir}")
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

    firmware_dir.mkdir(parents=True, exist_ok=True)
    destination = firmware_dir / filename
    destination.write_bytes(content)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy the latest prop sound pack into a firmware release.")
    parser.add_argument("install_dir", type=Path)
    parser.add_argument("firmware_dir", type=Path)
    parser.add_argument("product")
    args = parser.parse_args()
    try:
        print(f"Added sound pack: {copy_sound_pack(args.install_dir, args.firmware_dir, args.product)}")
    except (OSError, ValueError, BadZipFile) as error:
        parser.exit(1, f"{error}\n")
