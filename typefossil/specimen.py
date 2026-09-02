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

#: Prose for the setting block. Morris's own words on the book as an object,
#: from "The Ideal Book" (1893) -- contemporary with the type, and it exercises
#: ordinary word shapes rather than a contrived pangram.
SETTING = (
    "I have always been a great admirer of the calligraphy of the Middle Ages, "
    "and of the earlier printing which took its place. As to the fifteenth "
    "century books, I had noticed that they were always beautiful by force of "
    "the mere typography, even without the added ornament, with which many of "
    "them are so lavishly supplied."
)


def _available(path: str) -> set:
    from fontTools.ttLib import TTFont
    return {chr(c) for c in TTFont(path).getBestCmap()}


def _fits(text: str, have: set) -> str:
    """Drop characters the font does not have, so a proof shows no blanks."""
    return "".join(c for c in text if c in have or c == " ")


def _wrap(text: str, font, width: int, draw) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def sheet(ttf_path: str, out_path: str, title: str = "", width: int = 1500,
          margin: int = 48, bg: int = 255, fg: int = 20) -> str:
    """Write a specimen PNG exercising the character set at several sizes."""
    have = _available(ttf_path)
    rows = [(_fits(t, have), ImageFont.truetype(ttf_path, s), s) for t, s in LINES]

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


def full_sheet(ttf_path: str, out_path: str, family: str = "", subtitle: str = "",
               width: int = 1600, margin: int = 64, bg: int = 252, fg: int = 18,
               note: str = "") -> str:
    """A complete specimen: character set, waterfall, and a block of setting.

    A proof of a display face has to answer three different questions, and one
    line of sample text answers none of them well: which characters exist at
    all, how the face holds together as sizes fall, and what it looks like as
    actual text rather than as an alphabet. Hence three sections.

    Characters the font lacks are dropped rather than shown as blanks -- a
    specimen should show what the font *is*, and the gaps belong in its
    provenance notes where they can be explained.
    """
    have = _available(ttf_path)

    # Set the family name in the face itself -- but only if the face can
    # actually set it. Dropping a missing letter would silently mangle the name
    # ("Kelmscott" -> "elmscott" for a font with no capital K), which is worse
    # than admitting the gap: a specimen may omit characters from a proof, never
    # from the name of the thing it is proofing.
    name = family or "Specimen"
    settable = all(c in have or c == " " for c in name)
    blocks = []
    if settable:
        blocks.append(("title", name, ImageFont.truetype(ttf_path, 108), 108))
    else:
        blocks.append(("title-fallback", name,
                       ImageFont.truetype(ttf_path, 108), 108))

    for label, chars, size in (
        ("Capitals", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 76),
        ("Lowercase", "abcdefghijklmnopqrstuvwxyz", 76),
        ("Figures & points", "0123456789 . , ; : ! ? - & ( ) ' \"", 68),
    ):
        blocks.append(("row", label, _fits(chars, have), size))

    for size in (12, 16, 20, 28, 40, 56, 80):
        blocks.append(("water", _fits(PANGRAM, have), size))

    blocks.append(("setting", _fits(SETTING, have), 30))

    # Measure first so the canvas is exactly tall enough.
    probe = ImageDraw.Draw(Image.new("L", (10, 10)))
    height = margin
    for b in blocks:
        if b[0] in ("title", "title-fallback"):
            height += int(b[3] * 1.5) + 30
            if b[0] == "title-fallback":
                height += 26
        elif b[0] == "row":
            height += 26 + int(b[3] * 1.35) + 22
        elif b[0] == "water":
            height += int(b[2] * 1.5)
        else:
            f = ImageFont.truetype(ttf_path, b[2])
            height += 34 + len(_wrap(b[1], f, width - 2 * margin, probe)) * int(b[2] * 1.5)
    height += margin + (40 if note else 0)

    img = Image.new("L", (width, height), bg)
    d = ImageDraw.Draw(img)
    small = ImageFont.load_default()
    y = margin

    for b in blocks:
        if b[0] in ("title", "title-fallback"):
            if b[0] == "title":
                d.text((margin, y), b[1], fill=fg, font=b[2])
                y += int(b[3] * 1.5)
            else:
                d.text((margin, y), b[1], fill=fg, font=ImageFont.load_default())
                y += 26
                missing = sorted({c for c in b[1] if c not in have and c != " "})
                d.text((margin, y), _fits("Hamburgefonstiv", have), fill=fg, font=b[2])
                y += int(b[3] * 1.5)
                d.text((margin, y), "the face cannot set its own name: no "
                       + ", ".join(missing), fill=150, font=ImageFont.load_default())
                y += 26
            if subtitle:
                d.text((margin, y), subtitle, fill=120, font=small)
            y += 30
            d.line([(margin, y), (width - margin, y)], fill=200)
            y += 12
        elif b[0] == "row":
            d.text((margin, y), b[1].upper(), fill=150, font=small)
            y += 26
            d.text((margin, y), b[2], fill=fg, font=ImageFont.truetype(ttf_path, b[3]))
            y += int(b[3] * 1.35) + 22
        elif b[0] == "water":
            f = ImageFont.truetype(ttf_path, b[2])
            d.text((margin, y), b[1], fill=fg, font=f)
            d.text((width - margin - 34, y + b[2] // 3), str(b[2]), fill=185, font=small)
            y += int(b[2] * 1.5)
        else:
            y += 14
            d.line([(margin, y), (width - margin, y)], fill=200)
            y += 20
            f = ImageFont.truetype(ttf_path, b[2])
            for line in _wrap(b[1], f, width - 2 * margin, d):
                d.text((margin, y), line, fill=fg, font=f)
                y += int(b[2] * 1.5)

    if note:
        y += 10
        d.text((margin, y), note, fill=150, font=small)
    img.save(out_path)
    return out_path


def waterfall(ttf_path: str, out_path: str, text: str = PANGRAM,
              sizes=(18, 24, 32, 44, 60, 80), width: int = 1500) -> str:
    """Sizes stacked smallest-first -- where a display face shows its limits."""
    have = _available(ttf_path)
    text = _fits(text, have)
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
