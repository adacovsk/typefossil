"""Group glyph instances by which sort they are, and average each group.

Averaging is the step that does the real work. One impression of a letter
carries the ink spread, the paper texture and the scan noise of that one
impression; fifty impressions averaged carry the punch. Nothing downstream can
recover detail that this step throws away, and nothing downstream has to
remove noise that this step has already cancelled.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from .extract import Frame, Instance, unpack


def features(instances: list[Instance], frame: Frame = Frame(),
             fh: int = 40, fw: int = 28) -> np.ndarray:
    """Downscaled baseline-anchored frames, plus aspect, as a feature matrix.

    The frame is kept as the feature (rather than the letter's own bitmap) so
    that vertical position is part of the distance: 'p' and 'b' are the same
    shape and differ only in where they sit relative to the baseline.
    """
    F = np.zeros((len(instances), fh * fw + 2), np.float32)
    for i, inst in enumerate(instances):
        im = Image.fromarray((unpack(inst, frame) * 255).astype(np.uint8))
        F[i, :-2] = np.asarray(im.resize((fw, fh), Image.BILINEAR), np.float32).ravel() / 255.0
        xh = max(inst.x_height, 1.0)
        F[i, -2] = inst.width_px / xh
        F[i, -1] = inst.height_px / xh
    return F


def project(F: np.ndarray, dims: int = 48, sample: int = 4000, seed: int = 0) -> np.ndarray:
    """PCA down to ``dims`` via SVD on a random sample."""
    X = F - F.mean(0)
    rng = np.random.default_rng(seed)
    n = min(sample, len(X))
    _, _, Vt = np.linalg.svd(X[rng.choice(len(X), n, replace=False)], full_matrices=False)
    return np.ascontiguousarray(X @ Vt[:dims].T)


def kmeans(P: np.ndarray, k: int, iters: int = 60, seed: int = 0,
           block: int = 20000) -> np.ndarray:
    """Lloyd's algorithm, blocked and expressed as a matrix product.

    Two things matter at this size and they pull against each other. Written
    naively -- an (n, k, d) difference tensor -- it is memory bound and crawls;
    at 67k instances it took the better part of an hour where this takes a
    minute. Written as one GEMM over all points it is fast but allocates an
    (n, k) matrix per iteration, which for 323k points and 700 clusters is
    1.8 GB of float64 and will fail outright on a machine with anything else
    running.

    So: the |a-b|^2 = |a|^2 - 2a.b + |b|^2 identity for the speed, in row
    blocks for the footprint. Peak allocation is (block, k) regardless of how
    many instances there are.
    """
    rng = np.random.default_rng(seed)
    C = P[rng.choice(len(P), k, replace=False)].copy()
    Pn = (P * P).sum(1)[:, None]
    lab = np.full(len(P), -1, np.int32)
    for _ in range(iters):
        new = np.empty(len(P), np.int32)
        Cn = (C * C).sum(1)[None, :]
        for s in range(0, len(P), block):
            blk = slice(s, s + block)
            d = Pn[blk] - 2.0 * (P[blk] @ C.T) + Cn
            new[blk] = d.argmin(1)
        if (new == lab).all():
            break
        lab = new
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = P[m].mean(0)
    return lab


def averages(instances: list[Instance], lab: np.ndarray, frame: Frame = Frame(),
             cap: int = 250, min_count: int = 4) -> dict[int, tuple]:
    """Average each cluster's frames. Returns ``{cluster: (mask, count, width)}``."""
    out = {}
    for c in np.unique(lab):
        idx = np.where(lab == c)[0]
        if len(idx) < min_count:
            continue
        take = idx[:cap]
        mask = np.mean([unpack(instances[j], frame) for j in take], axis=0)
        width = float(np.median([instances[j].width_px for j in idx]))
        out[int(c)] = (mask, len(idx), width)
    return out


def contact_sheet(avgs: dict[int, tuple], path: str, per_sheet: int = 60,
                  cols: int = 12) -> list[str]:
    """Write contact sheets of averaged clusters, labelled with their ids.

    Assigning characters to clusters is the one genuinely manual step, and this
    is what you read to do it. It is deliberately not automated: OCR of a
    blackletter incunable is unreliable, and a mislabelled cluster is a wrong
    letter in every word that uses it.
    """
    from PIL import ImageDraw, ImageFont

    order = sorted(avgs, key=lambda c: -avgs[c][1])
    font = ImageFont.load_default()
    cw, ch = 108, 150
    written = []
    for b in range((len(order) + per_sheet - 1) // per_sheet):
        chunk = order[b * per_sheet:(b + 1) * per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        canv = Image.new("L", (cols * cw, rows * ch), 255)
        d = ImageDraw.Draw(canv)
        for i, c in enumerate(chunk):
            mask = avgs[c][0]
            im = Image.fromarray(((1 - mask) * 255).astype(np.uint8))
            im = im.crop((0, 40, 155, 300)).resize((98, 120))
            x, y = (i % cols) * cw + 4, (i // cols) * ch + 2
            canv.paste(im, (x, y))
            d.text((x, y + 122), str(c), fill=0, font=font)
        name = f"{path}_{b}.png"
        canv.save(name)
        written.append(name)
    return written


def sharpness(mask: np.ndarray) -> float:
    """How binary a master is, in [0, 1].

    An averaged master is crisp when its pixels are mostly ink or mostly paper
    and blurred when many sit in between. Instances that agree average towards
    0/1; instances that are misaligned -- or are not actually the same sort --
    average towards grey.
    """
    return float(np.abs(2.0 * mask - 1.0).mean())


def agreement(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation between two masters, as a merge test."""
    x, y = a.ravel() - a.mean(), b.ravel() - b.mean()
    d = float(np.linalg.norm(x) * np.linalg.norm(y))
    return 0.0 if d == 0 else float((x @ y) / d)


def merge_masters(masters: list[tuple[np.ndarray, int]],
                  min_agreement: float = 0.93) -> np.ndarray:
    """Combine clusters of the same character, but only those that agree.

    More instances is not automatically a better master. k-means splits one
    sort across several clusters, and it splits it by whatever varies most --
    often ink weight or a slight skew, not identity. Averaging a crisp cluster
    together with a misaligned one produces something blurrier than the crisp
    cluster alone, which is a real quality regression and an easy one to miss.

    So: anchor on the sharpest cluster, and fold in only those that correlate
    with it above ``min_agreement``, weighted by instance count.
    """
    if not masters:
        raise ValueError("no masters to merge")
    anchor = max(masters, key=lambda mc: sharpness(mc[0]))[0]
    keep = [(m, n) for m, n in masters if agreement(m, anchor) >= min_agreement]
    if not keep:
        return anchor
    total = sum(n for _, n in keep)
    return sum(m * n for m, n in keep) / total


def confusions(masters: dict[str, np.ndarray], threshold: float = 0.97) -> list[tuple]:
    """Pairs of characters whose masters are suspiciously alike.

    Labelling is done by eye from a contact sheet, and at thumbnail size some
    letters are genuinely hard to tell apart -- in a blackletter face 'b' and
    'h' differ only in whether the bowl closes on the stem. Mislabelling one as
    the other is silent: the font builds, every glyph looks plausible, and one
    letter of the alphabet is simply wrong everywhere it appears.

    Two *different* characters whose averaged masters correlate this highly are
    almost certainly the same sort labelled twice. Returns the offending pairs,
    worst first, for a human to re-check at full size.
    """
    keys = sorted(masters)
    out = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            score = agreement(masters[a], masters[b])
            if score >= threshold:
                out.append((score, a, b))
    return sorted(out, reverse=True)
