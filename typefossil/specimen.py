"""Render specimen sheets for a built font."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

PANGRAM = "The quick brown fox jumped over the lazy dog"

LINES = [
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 64),
    ("abcdefghijklmnopqrstuvwxyz", 64),
    ("0123456789 .,;:!?'\"()-&", 56),
    (PANGRAM, 72),
    (PANGRAM.lower(), 56),
    ("Hamburgefonstiv", 96),
]


def sheet(ttf_path: str, out_path: str, title: str = "", width: int = 1500,
          margin: int = 48, bg: int = 255, fg: int = 20) -> str:
    """Write a specimen PNG exercising the character set at several sizes."""
    rows = []
    for text, size in LINES:
        font = ImageFont.truetype(ttf_path, size)
        rows.append((text, font, size))

    height = margin * 2 + sum(int(s * 1.65) for _, _, s in rows) + (40 if title else 0)
    img = Image.new("L", (width, height), bg)
    d = ImageDraw.Draw(img)

    y = margin
    if title:
        d.text((margin, y), title, fill=140, font=ImageFont.load_default())
        y += 40
    for text, font, size in rows:
        d.text((margin, y), text, fill=fg, font=font)
        y += int(size * 1.65)
    img.save(out_path)
    return out_path


def waterfall(ttf_path: str, out_path: str, text: str = PANGRAM,
              sizes=(18, 24, 32, 44, 60, 80), width: int = 1500) -> str:
    """Sizes stacked smallest-first -- where a display face shows its limits."""
    fonts = [(s, ImageFont.truetype(ttf_path, s)) for s in sizes]
    height = 96 + sum(int(s * 1.6) for s, _ in fonts)
    img = Image.new("L", (width, height), 255)
    d = ImageDraw.Draw(img)
    y = 48
    for s, f in fonts:
        d.text((48, y), text, fill=20, font=f)
        y += int(s * 1.6)
    img.save(out_path)
    return out_path
