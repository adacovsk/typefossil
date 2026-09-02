"""Construct a glyph that the source never printed, out of ones it did.

Every revival needs this. A book is a sample of a fount, not an inventory of
it, and the gaps are systematic rather than random: a language that does not
distinguish ``i`` from ``j`` prints no ``j``, a printer who sets roman numerals
prints no arabic figures, a page whose chapter opening is a woodcut initial
prints no capital there.

Composing is honest as long as it is *recorded*. These glyphs are the tool's
drawing, not the punchcutter's, and a font that mixes the two without saying so
is misrepresenting its own provenance. Everything built here should be listed
in the project's provenance notes.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def shift(mask: np.ndarray, dy: int = 0, dx: int = 0) -> np.ndarray:
    """Translate a mask within its frame, filling with background."""
    return ndimage.shift(mask, (dy, dx), order=1, mode="constant", cval=0.0)


def scale(mask: np.ndarray, factor: float, baseline: int) -> np.ndarray:
    """Scale about the baseline, keeping the frame size.

    Used to bring a master from a smaller cut of the same design onto the
    primary size. It is a starting point and not a finished answer: a smaller
    cut is optically heavier, so a purely geometric scale comes out too bold.
    """
    if abs(factor - 1.0) < 1e-6:
        return mask.copy()
    h, w = mask.shape
    zoomed = ndimage.zoom(mask, factor, order=1)
    out = np.zeros_like(mask)
    zh, zw = zoomed.shape
    # Align the baseline row of the scaled image with the frame's baseline.
    src_base = int(round(baseline * factor))
    top = baseline - src_base
    src_r0, dst_r0 = (0, top) if top >= 0 else (-top, 0)
    n_r = min(zh - src_r0, h - dst_r0)
    n_c = min(zw, w)
    if n_r <= 0 or n_c <= 0:
        return out
    out[dst_r0:dst_r0 + n_r, :n_c] = zoomed[src_r0:src_r0 + n_r, :n_c]
    return out


def union(*masks: np.ndarray) -> np.ndarray:
    """Combine masks by taking the darkest ink at each pixel."""
    out = masks[0].copy()
    for m in masks[1:]:
        out = np.maximum(out, m)
    return out


def below(mask: np.ndarray, baseline: int) -> np.ndarray:
    """Just the descending part of a glyph."""
    out = mask.copy()
    out[:baseline, :] = 0.0
    return out


def above(mask: np.ndarray, baseline: int) -> np.ndarray:
    out = mask.copy()
    out[baseline:, :] = 0.0
    return out


def mirror(mask: np.ndarray) -> np.ndarray:
    """Horizontal mirror, about the glyph's own ink centre."""
    cols = np.where((mask > 0.5).any(axis=0))[0]
    if len(cols) == 0:
        return mask.copy()
    out = np.zeros_like(mask)
    piece = mask[:, cols[0]:cols[-1] + 1][:, ::-1]
    out[:, cols[0]:cols[0] + piece.shape[1]] = piece
    return out


def descender_from(donor: np.ndarray, baseline: int, dx: int = 0) -> np.ndarray:
    """The tail of a descending letter, ready to graft onto another stem."""
    return shift(below(donor, baseline), 0, dx)


def _ink_centre_at(mask: np.ndarray, row: int, level: float = 0.5,
                   band: int = 6) -> float | None:
    """Horizontal centre of the ink crossing a given row."""
    lo, hi = max(0, row - band), min(mask.shape[0], row + band + 1)
    cols = np.where((mask[lo:hi] > level).any(axis=0))[0]
    return float(cols.mean()) if len(cols) else None


def compose_j(i_mask: np.ndarray, donor: np.ndarray, baseline: int,
              dx: int = 0, dy: int = 0, overlap: int = 8) -> np.ndarray:
    """Build 'j' from 'i' plus a descender lifted from another letter.

    Not an invention: 'j' *is* a descending 'i'. It entered the alphabet as a
    swash variant of 'i' and became a separate letter only later, which is
    exactly why a Middle English fount has no separate sort for it. Grafting
    an existing tail onto the 'i' stem reconstructs the letter in the hand the
    punchcutter actually cut, rather than drawing a new one.

    The tail is aligned automatically: its ink at the baseline is centred under
    the stem's ink at the baseline, and it is lifted by ``overlap`` rows so the
    two actually meet. Without that the tail floats free of the stem, which is
    what a naive union produces.
    """
    stem_c = _ink_centre_at(i_mask, baseline - 4)
    tail = below(donor, baseline - overlap)
    tail_c = _ink_centre_at(tail, baseline)
    auto_dx = 0.0 if (stem_c is None or tail_c is None) else stem_c - tail_c
    tail = shift(tail, dy - overlap, auto_dx + dx)
    return union(i_mask, tail)


def ink_bbox(mask: np.ndarray, level: float = 0.5):
    rows = np.where((mask > level).any(axis=1))[0]
    cols = np.where((mask > level).any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1


def align_left(mask: np.ndarray, x: int = 4) -> np.ndarray:
    """Move a glyph's ink so it starts at column ``x``."""
    bb = ink_bbox(mask)
    if bb is None:
        return mask.copy()
    return shift(mask, 0, x - bb[2])


def weight(mask: np.ndarray, amount: int) -> np.ndarray:
    """Embolden (positive) or lighten (negative) by a morphological step.

    The use for this is matching a master taken from a different size of the
    same design, where a geometric scale alone leaves the weight wrong.
    """
    if amount == 0:
        return mask.copy()
    op = ndimage.grey_dilation if amount > 0 else ndimage.grey_erosion
    return op(mask, size=(abs(amount) * 2 + 1, abs(amount) * 2 + 1))


def baseline_row(mask: np.ndarray, level: float = 0.5,
                 width_frac: float = 0.55) -> int | None:
    """Estimate where a glyph actually sits on the baseline.

    Not simply the lowest ink: that is wrong for every descender. It is the
    lowest row at which the glyph is still *wide* -- the bottom of the bowl or
    the feet -- because a descender's tail is narrow relative to its body. For
    a letter with no descender the two coincide, so one rule covers both.
    """
    ink = mask > level
    widths = ink.sum(axis=1)
    if not widths.any():
        return None
    rows = np.where(widths >= widths.max() * width_frac)[0]
    return int(rows[-1]) if len(rows) else None


def snap_baseline(mask: np.ndarray, baseline: int, **kw) -> np.ndarray:
    """Move a master so it sits on the baseline.

    Per-line baseline estimates come from the median of component bottoms and
    are only as good as the line: a line heavy with descenders, or two lines
    merged by the line finder, pulls the estimate off. The error survives
    clustering -- k-means happily splits one letter into a high group and a low
    group, since vertical offset is exactly the kind of variation it keys on --
    and then the letter rides high or low in the finished font. Re-seating each
    finished master on its own measured baseline removes the whole class.
    """
    row = baseline_row(mask, **kw)
    if row is None:
        return mask.copy()
    return shift(mask, baseline - row, 0)
