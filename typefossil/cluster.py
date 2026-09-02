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


def kmeans(P: np.ndarray, k: int, iters: int = 45, seed: int = 0,
           block: int = 2000) -> np.ndarray:
    """Plain Lloyd's algorithm, blocked so the distance matrix stays small."""
    rng = np.random.default_rng(seed)
    C = P[rng.choice(len(P), k, replace=False)].copy()
    lab = np.zeros(len(P), np.int32)
    for _ in range(iters):
        for s in range(0, len(P), block):
            blk = P[s:s + block]
            lab[s:s + block] = ((blk[:, None, :] - C[None, :, :]) ** 2).sum(-1).argmin(1)
        new = C.copy()
        for j in range(k):
            m = lab == j
            if m.any():
                new[j] = P[m].mean(0)
        if np.allclose(new, C, atol=1e-4):
            return lab
        C = new
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
