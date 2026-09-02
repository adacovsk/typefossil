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


def compose_j(i_mask: np.ndarray, donor: np.ndarray, baseline: int,
              dx: int = 0, dy: int = 0) -> np.ndarray:
    """Build 'j' from 'i' plus a descender.

    Not an invention: 'j' *is* a descending 'i'. It entered the alphabet as a
    swash variant of 'i' and only became a separate letter later, which is
    exactly why a Middle English fount has no separate sort for it. Grafting
    the tail of an existing descender onto the 'i' stem reconstructs the letter
    the punchcutter would have cut, in the hand he actually cut.
    """
    tail = shift(below(donor, baseline), dy, dx)
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
