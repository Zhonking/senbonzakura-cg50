#!/usr/bin/env python3
"""Validate G3A structure/checksums and the native compressed video container."""

from pathlib import Path
import struct
import sys


def validate_g3a(path: Path) -> None:
    data = path.read_bytes()
    assert data[:14] == bytes.fromhex("aa ac bd af 90 88 9a 8d d3 ff fe ff fe ff")
    code_size = int.from_bytes(data[0x2E:0x32], "big")
    assert len(data) == int.from_bytes(data[0x5C:0x60], "big")
    assert len(data) == code_size + 0x7004
    expected = int.from_bytes(data[0x20:0x24], "big")
    assert data[-4:] == data[0x20:0x24]
    actual = sum(data[:0x20]) + sum(data[0x24:-4])
    assert actual & 0xFFFFFFFF == expected
    assert data[0x40:0x4D] == b"Senbon Zakura"
    assert data[0x60:0x67] == b"@SENBON"
    assert data.count(b"\\\\fls0\\senb.bin") == 1
    assert b"video.bin" not in data
    print(f"G3A OK: {path.name}, {len(data):,} bytes, checksum {expected:08X}")


def validate_video(path: Path) -> None:
    data = path.read_bytes()
    frames, width, height, fps, scale = struct.unpack(">HHHHB", data[:9])
    assert frames and width and height and 1 <= fps <= 60
    assert width * scale <= 384 and height * scale <= 216
    offset = 9
    total_runs = 0
    for frame in range(frames):
        assert offset + 5 <= len(data), f"truncated frame {frame}"
        original_size, compressed_size = struct.unpack(">HH", data[offset : offset + 4])
        offset += 4
        assert original_size >= 2 and original_size % 2 == 0
        assert compressed_size > 0 and offset + compressed_size < len(data)
        offset += compressed_size
        initial_white = data[offset]
        assert initial_white in (0, 1)
        offset += 1
        total_runs += original_size // 2
        if original_size <= 16:
            assert compressed_size == original_size
    assert offset == len(data), f"trailing bytes: {len(data) - offset}"
    print(
        f"VIDEO OK: {frames} frames, {width}x{height} at {fps} fps, "
        f"scale {scale}, {total_runs:,} runs, {len(data):,} bytes"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: validate_outputs.py ADDIN.g3a video.bin")
    validate_g3a(Path(sys.argv[1]))
    validate_video(Path(sys.argv[2]))
