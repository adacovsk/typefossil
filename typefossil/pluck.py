"""Pull a named glyph straight off a page by pointing at it.

Clustering is the right tool for a letter printed thousands of times and the
wrong one for a letter printed three times: it needs a population to average,
and a rare capital is absorbed into a larger lookalike long before it forms a
cluster of its own. Worse, a filter tuned on the letters you *have* can exclude
the one you are hunting -- Troy's 'Q' descends, so a width/height test
calibrated on non-descending capitals rejects it.

Reading the page and naming the coordinates avoids both. The transcription says
which page; the eye says where; this takes it from there.
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def pluck(path, seed_xy, frame_h=320, frame_w=220, baseline_row=232,
          window=340, min_area=400, x_height=60, greyscale=True):
    """Return a baseline-anchored frame holding the glyph nearest ``seed_xy``.

    With ``greyscale`` (the default) the frame keeps the scan's own ink values
    inside the component rather than a hard 0/1 mask. This matters more than it
    sounds: a binarised impression has staircase edges, so it has to be blurred
    back into smoothness before tracing, and that blur spreads ink across the
    fine gaps a letter depends on -- it closed the gap between the two
    horizontals of 'F'. The scan already holds a smooth ink boundary; throwing
    it away and reconstructing it with a Gaussian is strictly worse.
    """
    sx, sy = seed_xy
    im = Image.open(path).convert("L")
    x0, y0 = max(0, sx - window // 2), max(0, sy - window // 2)
    a = np.asarray(im.crop((x0, y0, x0 + window, y0 + window)), np.float32)
    ink = a < ndimage.uniform_filter(a, size=81) - 16
    lbl, n = ndimage.label(ink)
    if n == 0:
        return None
    sizes = ndimage.sum(ink, lbl, range(1, n + 1))
    best, best_d = None, 1e9
    cx, cy = sx - x0, sy - y0
    for i, sl in enumerate(ndimage.find_objects(lbl)):
        if sizes[i] < min_area:
            continue
        h = sl[0].stop - sl[0].start
        if h < x_height * 1.1:              # must be at least capital height
            continue
        mx = (sl[1].start + sl[1].stop) / 2
        my = (sl[0].start + sl[0].stop) / 2
        d = (mx - cx) ** 2 + (my - cy) ** 2
        if d < best_d:
            best, best_d = (i + 1, sl), d
    if best is None:
        return None
    lid, sl = best
    r0, r1, c0, c1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    sel = (lbl[r0:r1, c0:c1] == lid)
    if greyscale:
        # Ink intensity, normalised so paper is 0 and the darkest ink is 1,
        # then restricted to this component so a neighbour cannot bleed in.
        patch = a[r0:r1, c0:c1]
        lo, hi = float(patch.min()), float(np.median(a))
        ink_val = np.clip((hi - patch) / max(hi - lo, 1e-6), 0.0, 1.0)
        grown = ndimage.binary_dilation(sel, iterations=2)
        sub = np.where(grown, ink_val, 0.0).astype(np.float32)
    else:
        sub = sel.astype(np.float32)
    fr = np.zeros((frame_h, frame_w), np.float32)
    # Seat by the glyph's own cap height: these are plucked one at a time, so
    # there is no line of neighbours to take a baseline from.
    top = baseline_row - int((r1 - r0) * 0.82)
    if top < 0 or top + (r1 - r0) >= frame_h or (c1 - c0) > frame_w - 8:
        return None
    fr[top:top + (r1 - r0), 4:4 + (c1 - c0)] = sub
    return fr


def align_and_average(frames, level: float = 0.5, limit: int = 12):
    """Average plucked impressions after aligning them to the first.

    Plucked frames are seated by their own cap height, not by a shared text
    line, so two impressions of the same letter can sit a few pixels apart.
    Averaging them unaligned produces a half-value ghost along every edge,
    which the outline fitter then renders as a thin or broken stroke -- it made
    the leg of 'K' fade where it meets the stem.
    """
    import numpy as np
    from scipy import ndimage

    frames = [f for f in frames if f is not None]
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0].copy()
    ref = frames[0]
    out = [ref]
    for f in frames[1:]:
        best, best_score = (0, 0), -1.0
        for dy in range(-limit, limit + 1):
            for dx in range(-limit, limit + 1):
                s = float((ndimage.shift(f, (dy, dx), order=0, cval=0.0) * ref).sum())
                if s > best_score:
                    best, best_score = (dy, dx), s
        out.append(ndimage.shift(f, best, order=1, cval=0.0))
    return np.mean(out, axis=0)
