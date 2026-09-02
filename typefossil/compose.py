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


def scale(mask: np.ndarray, factor: float, baseline: int, order: int = 3) -> np.ndarray:
    """Scale about the baseline, keeping the frame size.

    Used to bring a master from a smaller cut of the same design onto the
    primary size. Cubic by default: an averaged master is a smooth greyscale
    field, and resampling it linearly leaves stair-stepping along every
    diagonal that the outline fitter then faithfully reproduces as a jagged
    edge. The cost of the higher order is nothing at this size.

    It remains a starting point rather than a finished answer: a smaller cut of
    a face is optically heavier, so a purely geometric scale still comes out
    slightly too bold.
    """
    if abs(factor - 1.0) < 1e-6:
        return mask.copy()
    h, w = mask.shape
    zoomed = np.clip(ndimage.zoom(mask, factor, order=order), 0.0, 1.0)
    out = np.zeros_like(mask)
    zh, zw = zoomed.shape
    src_base = int(round(baseline * factor))
    top = baseline - src_base
    src_r0, dst_r0 = (0, top) if top >= 0 else (-top, 0)
    n_r = min(zh - src_r0, h - dst_r0)
    n_c = min(zw, w)
    if n_r <= 0 or n_c <= 0:
        return out
    out[dst_r0:dst_r0 + n_r, :n_c] = zoomed[src_r0:src_r0 + n_r, :n_c]
    return out


def soften(mask: np.ndarray, sigma: float = 0.8) -> np.ndarray:
    """Light Gaussian blur, to take the stair-steps off a resampled master.

    The outline fitter works on the 0.5 contour of a greyscale field, so it
    reproduces whatever roughness that field has. A master built from few
    instances -- capitals, which are far rarer than lowercase -- has not had
    that roughness averaged away, and it surfaces as visible aliasing along the
    edges of the finished glyph. A sub-pixel blur removes it without moving the
    contour, since blurring is symmetric about the 0.5 level.
    """
    return ndimage.gaussian_filter(mask, sigma)


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


#: Latin lowercase letters whose design descends below the baseline. Which
#: letters descend is a fact about the alphabet, not something to infer from
#: the bitmap -- see `seat_masters` for why inferring it does not work.
DESCENDERS = set("gjpqy")


def foot_row(mask: np.ndarray, level: float = 0.5) -> int | None:
    """The lowest row carrying ink. For a non-descender this is the baseline."""
    rows = np.where((mask > level).any(axis=1))[0]
    return int(rows[-1]) if len(rows) else None


def _profile(mask: np.ndarray, level: float = 0.5) -> np.ndarray:
    return (mask > level).sum(axis=1).astype(float)


def _best_shift(mask: np.ndarray, reference: np.ndarray, lo: int, hi: int,
                limit: int = 40) -> int:
    """Vertical shift aligning ``mask`` to ``reference`` over rows ``lo:hi``."""
    a = _profile(mask)
    r = _profile(reference)[lo:hi]
    r = r - r.mean()
    best, best_score = 0, -np.inf
    for s in range(-limit, limit + 1):
        seg = a[lo - s:hi - s]
        if len(seg) != len(r):
            continue
        seg = seg - seg.mean()
        denom = np.linalg.norm(seg) * np.linalg.norm(r)
        score = 0.0 if denom == 0 else float((seg @ r) / denom)
        if score > best_score:
            best, best_score = s, score
    return best


def seat_masters(masters: dict, baseline: int, x_height: int,
                 descenders: set | None = None) -> dict:
    """Seat every master on a common baseline.

    Per-line baseline estimates drift, and clustering preserves the drift
    rather than averaging it out -- vertical offset is exactly what k-means
    keys on, so one letter ends up split into a high group and a low group and
    then rides high or low in the finished font.

    Seating is done two ways because one rule does not cover both cases, and
    three attempts at a single rule all failed on some letter. Lowest ink is
    wrong for descenders. Lowest *wide* row is wrong for 'y', which tapers into
    its tail with no step. Sharpest width drop is wrong for descenders too,
    since their steepest fall is where the tail ends. Lowest row wider than the
    tail is wrong for round letters, whose curved foot reads as a tail.

    So: a letter that does not descend is seated on its foot, which is exactly
    the baseline and needs no inference. A letter that does descend is aligned
    by correlating its ink profile against the letters already seated, over the
    x-height band only -- its bowl has to line up with everyone else's body,
    and the tail below is simply not consulted.
    """
    descenders = DESCENDERS if descenders is None else descenders
    seated = {}
    for ch, m in masters.items():
        if ch in descenders:
            continue
        foot = foot_row(m)
        seated[ch] = m.copy() if foot is None else shift(m, baseline - foot, 0)

    if not seated:
        return {**masters}
    reference = sum(seated.values()) / len(seated)
    lo, hi = max(0, baseline - x_height), baseline + 1
    for ch, m in masters.items():
        if ch not in descenders:
            continue
        seated[ch] = shift(m, _best_shift(m, reference, lo, hi), 0)
    return seated
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


def tittle_of(donor: np.ndarray, x_height_top: int, level: float = 0.5) -> np.ndarray:
    """The dot of an 'i', isolated: everything above the x-height."""
    out = np.zeros_like(donor)
    out[:x_height_top] = donor[:x_height_top]
    return out


def add_tittle(base: np.ndarray, donor: np.ndarray, x_height_top: int,
               level: float = 0.5) -> np.ndarray:
    """Give a glyph the dot from another, centred over its own stem.

    'j' is the case this exists for. Its dot is small, and it is the part of the
    letter most often broken, filled or lost to a neighbouring line in a scan,
    so a 'j' cluster can average out to a clean stem with no dot at all even
    when the printed letter plainly has one. Lifting the tittle from 'i' -- the
    same sort's dot, from the same fount -- restores it without drawing
    anything new.

    Alignment is over the stem rather than the bounding box: 'j' curves left
    below the baseline, so its box centre sits left of the stem the dot belongs
    over.
    """
    dot = tittle_of(donor, x_height_top, level)
    if not (dot > level).any():
        return base.copy()
    # Centre both on their x-height stem, not on the whole glyph.
    band = slice(x_height_top, x_height_top + max(8, (base.shape[0] - x_height_top) // 6))
    b_cols = np.where((base[band] > level).any(axis=0))[0]
    d_cols = np.where((donor[band] > level).any(axis=0))[0]
    dx = 0.0
    if len(b_cols) and len(d_cols):
        dx = float(b_cols.mean() - d_cols.mean())
    return union(base, shift(dot, 0, dx))


def cap_height(mask: np.ndarray, baseline: int, level: float = 0.5) -> int | None:
    """Height from the baseline to the top of the ink.

    Measured from the baseline rather than as total ink height, so a capital
    that descends below the line -- 'J' and 'Q' in many cuts -- is not counted
    as taller than its neighbours.
    """
    rows = np.where((mask > level).any(axis=1))[0]
    return None if len(rows) == 0 else int(baseline - rows[0])


def normalise_height(masters: dict, baseline: int, chars, target: int | None = None,
                     tolerance: float = 0.06) -> dict:
    """Bring a group of glyphs that should share a height to one height.

    Three groups need this and all fail the same way. A book prints the same
    capital at two sizes -- a line opening and a larger section head -- and
    clustering cannot separate them because they are the same shape, so a
    letter picked from the larger sort towers over its neighbours. Digits drawn
    from different contexts land at different sizes for the same reason. And an
    x-height letter whose master came from a slightly heavier or larger
    impression sits proud of the line, which reads as the letter being badly
    positioned even though its foot is exactly on the baseline.

    Rescaling is the correction rather than a fudge: these are one design at
    more than one size, the same relationship this module already handles
    between cuts of a face. Glyphs already within ``tolerance`` are left
    untouched rather than resampled for nothing.
    """
    keys = [c for c in masters if c in chars]
    heights = {c: cap_height(masters[c], baseline) for c in keys}
    heights = {c: h for c, h in heights.items() if h}
    if not heights:
        return dict(masters)
    goal = target or int(np.median(list(heights.values())))
    out = dict(masters)
    for c, h in heights.items():
        if abs(h - goal) <= goal * tolerance:
            continue
        out[c] = soften(scale(masters[c], goal / float(h), baseline, order=3), 0.6)
    return out


#: Lowercase letters with neither ascender nor descender: they all share the
#: x-height, so a master that does not is wrong rather than merely different.
X_HEIGHT_LETTERS = set("acemnorsuvwxz")


def normalise_cap_height(masters: dict, baseline: int, target: int | None = None,
                         chars: str | None = None, tolerance: float = 0.06) -> dict:
    """Bring capitals to a single cap height.

    A book prints the same capital at more than one size: an ordinary
    line-opening capital, and a larger one at a section head. Clustering does
    not distinguish them -- they are the same shape -- so whichever the label
    happens to point at is the one that reaches the font, and a letter picked
    from the larger sort towers over its neighbours.

    Rescaling is the right correction rather than a fudge, because the two are
    the same design at different sizes, which is exactly the relationship this
    module already handles between cuts. Letters already within ``tolerance``
    of the target are left untouched, so a normal capital is never resampled
    for nothing.
    """
    keys = chars if chars else [c for c in masters if c.isupper()]
    return normalise_height(masters, baseline, keys, target, tolerance)


def add_dot_below(base: np.ndarray, period: np.ndarray, baseline: int,
                  gap: float = 0.10, level: float = 0.5) -> np.ndarray:
    """Put a baseline dot under a mark that lost one, and lift the mark clear.

    The mirror of `add_tittle`, and it exists because segmentation loses these
    dots systematically: mark re-attachment joins a small component to the
    letter *below* it, which is right for an 'i' and wrong for a '?' or a ';',
    whose dot sits underneath. Those come out of clustering as the hook alone.

    The dot is the fount's own period, so nothing is drawn. The hook is raised
    to make room for it -- without that it would sit on top of the dot, since a
    hook that lost its dot still occupies the full height down to the baseline.
    """
    bb = ink_bbox(period, level)
    if bb is None:
        return base.copy()
    dot_h = bb[1] - bb[0]
    foot = foot_row(base, level)
    if foot is None:
        return base.copy()
    lift = foot - (baseline - dot_h - int(gap * dot_h * 6))
    hook = shift(base, -max(lift, 0), 0)

    # Centre the dot under the hook's own lower stem.
    h_cols = np.where((hook > level).any(axis=0))[0]
    p_cols = np.where((period > level).any(axis=0))[0]
    dx = 0.0
    if len(h_cols) and len(p_cols):
        dx = float(h_cols.mean() - p_cols.mean())
    return union(hook, shift(period, 0, dx))
