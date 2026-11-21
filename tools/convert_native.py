#!/usr/bin/env python3
"""Convert a video to the native bad-apple-cg50 RLE + FastLZ format."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import struct
import subprocess
import sys

HEADER = struct.Struct(">HHHHB")


def floyd_steinberg_white(gray: bytes, width: int, height: int) -> list[bool]:
    current = [0] + list(gray[:width]) + [0]
    white = [False] * (width * height)
    for y in range(height):
        following = (
            [0] + list(gray[(y + 1) * width : (y + 2) * width]) + [0]
            if y + 1 < height
            else [0] * (width + 2)
        )
        for x in range(width):
            index = x + 1
            old = max(0, min(255, current[index]))
            is_white = old >= 128
            white[y * width + x] = is_white
            error = old - (255 if is_white else 0)
            current[index + 1] += error * 7 // 16
            following[index - 1] += error * 3 // 16
            following[index] += error * 5 // 16
            following[index + 1] += error // 16
        current = following
    return white


def encode_rle(white: list[bool]) -> bytes:
    if not white:
        raise ValueError("empty frame")
    runs: list[int] = []
    previous = white[0]
    count = 0
    for value in white:
        if value == previous:
            count += 1
        else:
            runs.append(count)
            previous = value
            count = 1
    runs.append(count)
    if max(runs) > 65535 or len(runs) > 32767:
        raise ValueError("frame exceeds native RLE limits")
    return struct.pack(">H", len(runs)) + b"".join(
        struct.pack(">H", run) for run in runs
    ) + bytes((int(white[0]),))


def read_exact(stream, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--compressor", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("video.bin"))
    parser.add_argument("--width", type=int, default=96)
    parser.add_argument("--height", type=int, default=54)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--dither", choices=("none", "floyd-steinberg"), default="floyd-steinberg")
    args = parser.parse_args()
    if not (1 <= args.fps <= 60 and 1 <= args.scale <= 99):
        parser.error("fps must be 1..60 and scale must be 1..99")
    if args.width < 1 or args.height < 1 or args.width * args.scale > 384 or args.height * args.scale > 216:
        parser.error("scaled dimensions must fit within 384x216")

    build = args.output.parent / "build-native"
    build.mkdir(parents=True, exist_ok=True)
    raw_path = build / "data.bin"
    frame_size = args.width * args.height
    frame_count = 0
    command = [args.ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(args.input)]
    if args.duration is not None:
        command.extend(("-t", str(args.duration)))
    vf = (
        f"fps={args.fps},scale={args.width}:{args.height}:force_original_aspect_ratio=increase,"
        f"crop={args.width}:{args.height},setsar=1,format=gray"
    )
    command.extend(("-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdout is not None
        with raw_path.open("wb") as output:
            output.write(b"\0" * HEADER.size)
            while True:
                gray = read_exact(process.stdout, frame_size)
                if not gray:
                    break
                if len(gray) != frame_size:
                    raise ValueError("incomplete frame from ffmpeg")
                if args.dither == "none":
                    white = [value >= 128 for value in gray]
                else:
                    white = floyd_steinberg_white(gray, args.width, args.height)
                output.write(encode_rle(white))
                frame_count += 1
                if frame_count % args.fps == 0:
                    print(f"\rConverted {frame_count} frames...", end="", file=sys.stderr)
            if not (1 <= frame_count <= 65535):
                raise ValueError("video must contain 1..65535 output frames")
            output.seek(0)
            output.write(HEADER.pack(frame_count, args.width, args.height, args.fps, args.scale))
        assert process.stderr is not None
        error = process.stderr.read().decode("utf-8", errors="replace").strip()
        status = process.wait()
        if status:
            raise ValueError(f"ffmpeg failed ({status}): {error}")
    except Exception:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise

    compressed = build / "data.c.bin"
    compressed.unlink(missing_ok=True)
    subprocess.run(
        [str(args.compressor.resolve()), str(raw_path.resolve())],
        cwd=build,
        check=True,
    )
    if not compressed.exists():
        raise ValueError("compressor did not create data.c.bin")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(compressed, args.output)
    print(
        f"\rWrote {args.output}: {frame_count} frames, {args.fps} fps, "
        f"{args.width}x{args.height}, {args.output.stat().st_size:,} bytes.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
