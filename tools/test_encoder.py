#!/usr/bin/env python3
"""Smoke-test the native RLE encoder and official FastLZ compressor."""

from pathlib import Path
import subprocess

from convert_native import HEADER, encode_rle
from validate_outputs import validate_video

root = Path(__file__).resolve().parents[1]
build = root / "build-test"
build.mkdir(exist_ok=True)
raw = build / "data.bin"
compressed = build / "data.c.bin"
width, height, fps, scale = 96, 54, 10, 4
frames = [
    [False] * (width * height),
    [True] * (width * height),
    [(x + y) % 2 == 0 for y in range(height) for x in range(width)],
]
with raw.open("wb") as output:
    output.write(HEADER.pack(len(frames), width, height, fps, scale))
    for frame in frames:
        output.write(encode_rle(frame))
compressed.unlink(missing_ok=True)
subprocess.run([str(root / "tools" / "compress.exe"), str(raw.resolve())], cwd=build, check=True)
validate_video(compressed)
print("Encoder/compressor smoke test passed.")
