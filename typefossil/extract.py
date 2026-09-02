"""Find individual letters on a scanned page of metal type.

The unit of work is a *glyph instance*: one impression of one sort, cut out of
the page and placed in a fixed frame whose rows are measured from the text
baseline rather than from the letter's own bounding box. Baseline anchoring is
what makes the later averaging meaningful -- an 'h' and an 'o' averaged on
their bounding boxes would both fill the frame and lose the fact that one is
tall and one is not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image
from scipy import ndimage


@dataclass(frozen=True)
class Frame:
    """Geometry of the fixed frame every glyph instance is placed in."""

    height: int = 320
    width: int = 220
    baseline: int = 232      # row index of the baseline within the frame
    left: int = 4            # left inset, so sidebearing ink is not clipped


@dataclass
class Instance:
    bits: np.ndarray         # packbits of the frame, unpack to Frame.height/width
    width_px: int            # ink width of this impression
    height_px: int
    x_height: float          # median glyph height on its text line
    page: str


def _binarise(gray: np.ndarray, window: int, offset: float) -> np.ndarray:
    """Local threshold. A global cut loses the lighter edge of a curled page."""
    return gray < ndimage.uniform_filter(gray, size=window) - offset


def page_instances(
    path: str,
    frame: Frame = Frame(),
    margin: float = 0.06,
    window: int = 121,
    offset: float = 16.0,
    min_h: int = 18,
    max_h: int = 230,
    min_w: int = 12,
    max_w: int = 230,
    min_area: int = 250,
) -> list[Instance]:
    """Extract every glyph instance from one page image.

    The size bounds are the main thing to tune per source: they are what
    separates type from ornament. Kelmscott pages carry heavy woodcut borders
    and large decorated initials, both of which fall outside a band that fits
    ordinary text sorts.
    """
    gray = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    h, w = gray.shape
    gray = gray[int(h * margin):int(h * (1 - margin)),
                int(w * margin):int(w * (1 - margin))]

    ink = _binarise(gray, window, offset)
    lbl, n = ndimage.label(ink)
    if n == 0:
        return []
    sizes = ndimage.sum(ink, lbl, range(1, n + 1))
    objs = ndimage.find_objects(lbl)

    cand = []
    for i, sl in enumerate(objs):
        gh = sl[0].stop - sl[0].start
        gw = sl[1].stop - sl[1].start
        if not (min_h <= gh <= max_h and min_w <= gw <= max_w):
            continue
        if sizes[i] < min_area:
            continue
        if sizes[i] / float(gh * gw) > 0.92:
            continue          # a solid block: a rule, or ornament
        cand.append((i + 1, sl, gh, gw))
    if len(cand) < 40:
        return []

    out: list[Instance] = []
    for members in _lines(cand):
        bottoms = np.array([m[1][0].stop for m in members])
        heights = np.array([m[2] for m in members])
        baseline = float(np.median(bottoms))
        x_height = float(np.median(heights))

        merged, consumed = _reattach_marks(members, baseline, x_height)
        for k, m in enumerate(merged):
            if k in consumed:
                continue
            inst = _place(lbl, m, baseline, x_height, frame, path)
            if inst is not None:
                out.append(inst)
    return out


def _lines(cand: list) -> list[list]:
    """Group components into text lines by their vertical centres."""
    centres = np.array([(c[1][0].start + c[1][0].stop) / 2 for c in cand])
    order = np.argsort(centres)
    cs = centres[order]
    gaps = np.diff(cs)
    med = np.median(gaps[gaps > 0]) if len(gaps) else 1.0

    lines, cur = [], [order[0]]
    for k in range(1, len(cs)):
        if cs[k] - cs[k - 1] > max(28.0, med * 14):
            lines.append(cur)
            cur = []
        cur.append(order[k])
    lines.append(cur)
    return [[cand[j] for j in L] for L in lines if len(L) >= 8]


def _reattach_marks(members: list, baseline: float, x_height: float):
    """Re-join dots and accents to their base letter.

    Connected-component labelling splits 'i' into two blobs. Left alone the dot
    becomes its own cluster and every 'i' in the font loses it -- which is
    exactly what happens if you skip this step.
    """
    marks = [k for k, m in enumerate(members)
             if m[2] < x_height * 0.55 and m[1][0].stop < baseline - x_height * 0.55]
    members = list(members)
    consumed = set()
    for k in marks:
        mk = members[k]
        mx0, mx1 = mk[1][1].start, mk[1][1].stop
        best, best_ov = None, 0
        for j, m in enumerate(members):
            if j == k or j in marks:
                continue
            x0, x1 = m[1][1].start, m[1][1].stop
            ov = min(mx1, x1) - max(mx0, x0)
            if ov > best_ov and m[1][0].start > mk[1][0].stop - 8:
                best, best_ov = j, ov
        if best is not None and best_ov > (mx1 - mx0) * 0.45:
            consumed.add(k)
            members[best] = members[best] + ((mk,),)
    return members, consumed


def _place(lbl, m, baseline: float, x_height: float, frame: Frame, page: str):
    lid, sl = m[0], m[1]
    extra = m[4] if len(m) > 4 else ()
    r0 = min([sl[0].start] + [e[1][0].start for e in extra])
    r1 = max([sl[0].stop] + [e[1][0].stop for e in extra])
    c0 = min([sl[1].start] + [e[1][1].start for e in extra])
    c1 = max([sl[1].stop] + [e[1][1].stop for e in extra])
    if (r1 - r0) > frame.height * 0.8 or (c1 - c0) > frame.width - 8:
        return None
    top = int(round(frame.baseline - (baseline - r0)))
    if top < 0 or top + (r1 - r0) >= frame.height:
        return None

    sub = lbl[r0:r1, c0:c1] == lid
    for e in extra:
        sub = sub | (lbl[r0:r1, c0:c1] == e[0])
    fr = np.zeros((frame.height, frame.width), np.float32)
    fr[top:top + (r1 - r0), frame.left:frame.left + (c1 - c0)] = sub
    return Instance(np.packbits(fr.astype(bool)), c1 - c0, r1 - r0, x_height, page)


def unpack(inst: Instance, frame: Frame = Frame()) -> np.ndarray:
    n = frame.height * frame.width
    return np.unpackbits(inst.bits)[:n].reshape(frame.height, frame.width).astype(np.float32)
