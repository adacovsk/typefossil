"""Assemble labelled, averaged glyph masters into a font binary."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from . import trace
from .extract import Frame

# Characters that must exist in any usable font but which a given source may
# simply never print. Middle English incunables have no arabic numerals at all,
# and 'j', 'v' and 'w' are unevenly attested. The builder reports these rather
# than silently shipping a font with holes in it.
CORE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?'\"()-")


@dataclass
class Metrics:
    upm: int = 1000
    x_height_ratio: float = 0.47     # x-height as a fraction of the em
    ascent: float = 0.80
    descent: float = -0.22
    side_bearing: float = 0.035      # per side, as a fraction of the em
    space_ratio: float = 0.26


@dataclass
class Design:
    family: str = "Untitled"
    style: str = "Regular"
    version: str = "1.000"
    copyright: str = ""
    license_url: str = "https://openfontlicense.org"
    license_description: str = ""
    designer: str = ""
    description: str = ""
    metrics: Metrics = field(default_factory=Metrics)


def _glyph_name(ch: str) -> str:
    """A PostScript-safe glyph name for a character."""
    special = {
        " ": "space", ".": "period", ",": "comma", ";": "semicolon",
        ":": "colon", "!": "exclam", "?": "question", "'": "quotesingle",
        '"': "quotedbl", "(": "parenleft", ")": "parenright",
        "-": "hyphen", "&": "ampersand", "/": "slash",
    }
    if ch in special:
        return special[ch]
    if ch.isalpha() and ch.isascii():
        return ch
    if ch.isdigit():
        return ["zero", "one", "two", "three", "four",
                "five", "six", "seven", "eight", "nine"][int(ch)]
    return "uni%04X" % ord(ch)


def _ink_columns(mask: np.ndarray, level: float = 0.5) -> tuple[int, int] | None:
    cols = np.where((mask > level).any(axis=0))[0]
    if len(cols) == 0:
        return None
    return int(cols[0]), int(cols[-1]) + 1


def build(masters: dict[str, np.ndarray], design: Design,
          x_height_px: float, frame: Frame = Frame(),
          tol: float = 0.9) -> tuple:
    """Build a TTF from ``{character: averaged mask}``.

    ``x_height_px`` is the measured x-height of the source in frame pixels; it
    sets the single scale factor from scan space to font units, so every glyph
    keeps the proportions it had on the page.
    """
    m = design.metrics
    scale = (m.upm * m.x_height_ratio) / x_height_px
    sb = int(m.side_bearing * m.upm)

    glyphs: dict[str, object] = {}
    widths: dict[str, int] = {}
    for ch, mask in sorted(masters.items()):
        span = _ink_columns(mask)
        if span is None:
            continue
        c0, c1 = span
        # Left-align the ink at a fixed sidebearing rather than keeping the
        # frame's own left inset: the frame position reflects where the letter
        # happened to sit in its source word, which is not a design value.
        def xf(x, y, _c0=c0):
            return ((x - _c0) * scale + sb, (frame.baseline - y) * scale)

        pen = TTGlyphPen(None)
        paths = trace.outline(mask, xf, tol=tol)
        if not paths:
            continue
        trace.draw(pen, paths)
        name = _glyph_name(ch)
        glyphs[name] = pen.glyph()
        widths[name] = int((c1 - c0) * scale + 2 * sb)

    pen = TTGlyphPen(None)
    glyphs["space"] = pen.glyph()
    widths["space"] = int(m.space_ratio * m.upm)
    glyphs[".notdef"] = TTGlyphPen(None).glyph()
    widths[".notdef"] = int(0.4 * m.upm)

    order = [".notdef", "space"] + sorted(n for n in glyphs if n not in (".notdef", "space"))
    cmap = {ord(ch): _glyph_name(ch) for ch in masters if _glyph_name(ch) in glyphs}
    cmap[32] = "space"

    fb = FontBuilder(m.upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf({n: glyphs[n] for n in order})
    fb.setupHorizontalMetrics({n: (widths.get(n, 600), 0) for n in order})
    fb.setupHorizontalHeader(ascent=int(m.ascent * m.upm), descent=int(m.descent * m.upm))
    fb.setupNameTable({
        "familyName": design.family,
        "styleName": design.style,
        "uniqueFontIdentifier": f"{design.family}-{design.style}-{design.version}",
        "fullName": f"{design.family} {design.style}",
        "psName": f"{design.family.replace(' ', '')}-{design.style}",
        "version": f"Version {design.version}",
        "copyright": design.copyright,
        "designer": design.designer,
        "description": design.description,
        "licenseInfoURL": design.license_url,
        "licenseDescription": design.license_description,
    })
    fb.setupOS2(
        sTypoAscender=int(m.ascent * m.upm),
        sTypoDescender=int(m.descent * m.upm),
        sxHeight=int(m.x_height_ratio * m.upm),
        usWinAscent=int(m.ascent * m.upm),
        usWinDescent=int(-m.descent * m.upm),
    )
    fb.setupPost()
    missing = sorted(CORE - set(masters))
    return fb, missing
