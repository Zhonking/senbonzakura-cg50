#!/usr/bin/env python3
"""Brand the reference Bad Apple player as Senbon Zakura and rebuild checksums."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "BadApple.g3a"
OUTPUT = ROOT / "dist" / "SenbonZakura.g3a"


def put(data: bytearray, offset: int, size: int, value: str) -> None:
    encoded = value.encode("ascii")
    if len(encoded) >= size:
        raise ValueError(f"{value!r} does not fit in {size} bytes")
    data[offset : offset + size] = encoded + b"\0" * (size - len(encoded))


def font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def make_icon(selected: bool) -> bytes:
    background = "black" if selected else "white"
    foreground = "white" if selected else "black"
    accent = "#ff80c0" if selected else "#c02060"
    image = Image.new("RGB", (92, 64), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 90, 62), outline=accent, width=2)
    # A small five-petal sakura mark.
    cx, cy = 46, 13
    for dx, dy in ((0, -6), (6, -2), (4, 5), (-4, 5), (-6, -2)):
        draw.ellipse((cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4), fill=accent)
    draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=foreground)
    draw.text((46, 28), "SENBON", font=font(13), fill=foreground, anchor="mm")
    draw.text((46, 43), "ZAKURA", font=font(13), fill=foreground, anchor="mm")
    draw.text((46, 56), "CG50 VIDEO", font=font(7), fill=accent, anchor="mm")

    result = bytearray()
    for red, green, blue in image.getdata():
        pixel = ((red * 31 // 255) << 11) | ((green * 63 // 255) << 5) | (blue * 31 // 255)
        result.extend(pixel.to_bytes(2, "big"))
    return bytes(result)


def main() -> None:
    data = bytearray(SOURCE.read_bytes())
    if data[:14] != bytes.fromhex("aa ac bd af 90 88 9a 8d d3 ff fe ff fe ff"):
        raise ValueError("not a Prizm G3A add-in")
    code_size = int.from_bytes(data[0x2E:0x32], "big")
    if len(data) != 0x7000 + code_size + 4:
        raise ValueError("unexpected G3A layout")
    old_video_name = b"video.bin"
    new_video_name = b"senb.bin\0"
    if data.count(old_video_name) != 1:
        raise ValueError("expected exactly one video path in the player")
    data = data.replace(old_video_name, new_video_name)

    put(data, 0x40, 0x1C, "Senbon Zakura")
    put(data, 0x60, 0x0B, "@SENBON")
    for index in range(8):
        put(data, 0x6B + index * 0x18, 0x18, "Senbon Zakura")
    put(data, 0x130, 0x0C, "01.00.0000")
    put(data, 0x13C, 0x0F, "2026.1121.1355")
    put(data, 0xEBC, 0x144, "SenbonZakura.g3a")
    data[0x1000:0x3E00] = make_icon(False)
    data[0x4000:0x6E00] = make_icon(True)

    data[0x20:0x24] = b"\0" * 4
    data[-4:] = b"\0" * 4
    checksum = sum(data) & 0xFFFFFFFF
    data[0x20:0x24] = checksum.to_bytes(4, "big")
    data[-4:] = checksum.to_bytes(4, "big")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(data)
    print(f"Wrote {OUTPUT} ({len(data)} bytes), checksum {checksum:08X}")


if __name__ == "__main__":
    main()
