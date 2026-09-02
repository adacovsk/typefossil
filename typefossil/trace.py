"""Turn an averaged glyph bitmap into font outlines.

The pipeline is: sub-pixel contour -> corner detection -> per-span cubic Bezier
least-squares fit -> quadratic conversion for TrueType.

Fitting curves rather than emitting the contour polygon directly is what
separates a usable typeface from a lumpy one. A traced polygon carries every
scan artefact as a vertex; a fitted curve carries the *shape* and drops the
noise, which is the whole reason the instances were averaged first.
"""

from __future__ import annotations

import numpy as np
from fontTools.cu2qu import curve_to_quadratic


def contours(mask: np.ndarray, level: float = 0.5) -> list[np.ndarray]:
    """Sub-pixel contours of ``mask`` at ``level``, as (N, 2) arrays of (x, y).

    Uses matplotlib's contour generator, which interpolates between cells
    rather than snapping to them -- the ink boundary of an averaged glyph sits
    between pixels, so a hard threshold would quantise away exactly the
    precision that averaging bought.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure()
    try:
        cs = fig.add_subplot(111).contour(mask, levels=[level])
        segs = [np.asarray(s, dtype=float) for s in cs.allsegs[0]]
    finally:
        plt.close(fig)
    return [s for s in segs if len(s) >= 12]


def _resample(poly: np.ndarray, step: float = 1.0) -> np.ndarray:
    """Arc-length resampling, so curvature is measured over equal distances."""
    d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(poly, axis=0).T))]
    if d[-1] < step * 4:
        return poly
    t = np.arange(0.0, d[-1], step)
    return np.column_stack([np.interp(t, d, poly[:, 0]), np.interp(t, d, poly[:, 1])])


def _corners(poly: np.ndarray, span: int = 6, thresh_deg: float = 52.0) -> list[int]:
    """Indices where the contour turns sharply enough to be a real corner.

    Blackletter is full of genuine corners -- the flat pen entry and exit
    strokes -- and smoothing through them is what makes a naive revival look
    melted. They have to survive as on-curve points with no tangent continuity.
    """
    n = len(poly)
    if n < span * 3:
        return []
    idx = np.arange(n)
    back = poly[(idx - span) % n] - poly[idx]
    fwd = poly[(idx + span) % n] - poly[idx]
    bn = np.hypot(*back.T)
    fn = np.hypot(*fwd.T)
    ok = (bn > 1e-9) & (fn > 1e-9)
    cosang = np.ones(n)
    cosang[ok] = np.clip(
        (back[ok] * fwd[ok]).sum(1) / (bn[ok] * fn[ok]), -1.0, 1.0
    )
    interior = np.degrees(np.arccos(cosang))
    sharp = np.where(interior < 180.0 - thresh_deg)[0]

    # Collapse runs of adjacent sharp samples to their sharpest member.
    out: list[int] = []
    for i in sharp:
        if out and (i - out[-1]) <= span:
            if interior[i] < interior[out[-1]]:
                out[-1] = int(i)
        else:
            out.append(int(i))
    return out


def _fit_cubic(pts: np.ndarray) -> tuple:
    """Least-squares cubic Bezier through ``pts`` with endpoints pinned.

    Chord-length parameterisation; the two interior control points fall out of
    a 4-unknown linear system. Good enough at this scale, and far cheaper than
    an iterative reparameterising fit.
    """
    p0, p3 = pts[0], pts[-1]
    d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    if d[-1] <= 0:
        return tuple(p0), tuple(p0), tuple(p3), tuple(p3)
    t = (d / d[-1])[:, None]
    b0 = (1 - t) ** 3
    b1 = 3 * t * (1 - t) ** 2
    b2 = 3 * t ** 2 * (1 - t)
    b3 = t ** 3
    rhs = pts - b0 * p0 - b3 * p3
    A = np.hstack([b1, b2])
    sol, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    return tuple(p0), tuple(sol[0]), tuple(sol[1]), tuple(p3)


def _split_fit(pts: np.ndarray, tol: float, depth: int = 0) -> list[tuple]:
    """Fit one cubic; if it strays past ``tol``, split at the worst point."""
    if len(pts) < 4:
        return []
    cur = _fit_cubic(pts)
    ts = np.linspace(0, 1, max(len(pts), 12))[:, None]
    p0, p1, p2, p3 = (np.asarray(c) for c in cur)
    curve = ((1 - ts) ** 3 * p0 + 3 * ts * (1 - ts) ** 2 * p1
             + 3 * ts ** 2 * (1 - ts) * p2 + ts ** 3 * p3)
    # Distance from each sample to its nearest point on the fitted curve.
    err = np.min(np.linalg.norm(pts[:, None, :] - curve[None, :, :], axis=2), axis=1)
    if depth >= 6 or err.max() <= tol or len(pts) < 10:
        return [cur]
    k = int(np.argmax(err))
    k = min(max(k, 4), len(pts) - 5)
    return _split_fit(pts[: k + 1], tol, depth + 1) + _split_fit(pts[k:], tol, depth + 1)


def outline(mask: np.ndarray, transform, tol: float = 0.9,
            simplify: float = 1.0, level: float = 0.5) -> list[list[tuple]]:
    """Fitted contours of ``mask`` in font units.

    ``transform`` maps a source-pixel (x, y) to font units. Returns a list of
    closed paths, each a list of ``("line", pt)`` / ``("curve", c1, c2, pt)``
    segments following an initial ``("move", pt)``.
    """
    paths = []
    for poly in contours(mask, level):
        if np.allclose(poly[0], poly[-1]):
            poly = poly[:-1]
        poly = _resample(poly, simplify)
        if len(poly) < 8:
            continue
        cs = _corners(poly)
        n = len(poly)
        # Split the closed contour into spans between corners; with no corners
        # at all it is one span wrapped back onto its own start.
        if cs:
            spans = [(cs[i], cs[(i + 1) % len(cs)]) for i in range(len(cs))]
        else:
            spans = [(0, 0)]
        segs: list[tuple] = []
        start = None
        for a, b in spans:
            idx = np.arange(a, b + n if b <= a else b + 1) % n
            pts = poly[idx]
            if len(pts) < 4:
                continue
            for c in _split_fit(pts, tol):
                fp = [transform(*p) for p in c]
                if start is None:
                    start = fp[0]
                    segs.append(("move", fp[0]))
                segs.append(("curve", fp[1], fp[2], fp[3]))
        if start is not None and len(segs) > 2:
            paths.append(segs)
    return paths


def draw(pen, paths, quadratic: bool = True, max_err: float = 1.2) -> None:
    """Replay ``paths`` into a fontTools pen, converting to quadratics for TTF."""
    for segs in paths:
        started = False
        cur = None
        for seg in segs:
            if seg[0] == "move":
                pen.moveTo(seg[1])
                cur = seg[1]
                started = True
            elif seg[0] == "line":
                pen.lineTo(seg[1])
                cur = seg[1]
            else:
                _, c1, c2, pt = seg
                if quadratic:
                    quads = curve_to_quadratic((cur, c1, c2, pt), max_err)
                    pen.qCurveTo(*quads[1:])
                else:
                    pen.curveTo(c1, c2, pt)
                cur = pt
        if started:
            pen.closePath()
