#!/usr/bin/env python3
"""Package only the finished calculator files and verify the resulting ZIP."""

from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
archive = root / "SenbonZakura-fx-CG50.zip"
files = ("SenbonZakura.g3a", "senb.bin", "README.txt", "LICENSE.txt")
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for name in files:
        path = dist / name
        if not path.is_file():
            raise FileNotFoundError(path)
        output.write(path, arcname=name)
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
    assert tuple(check.namelist()) == files
print(f"ZIP OK: {archive}, {archive.stat().st_size:,} bytes")
for name in files:
    print(f"  {name}: {(dist / name).stat().st_size:,} bytes")
