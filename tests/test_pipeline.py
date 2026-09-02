"""Tests for the parts of the pipeline that have a checkable right answer.

Segmentation and labelling quality are judged by eye on a contact sheet; these
cover the geometry and the font assembly, where a regression is silent.
"""

import numpy as np

from typefossil import build, cluster, extract, trace


def disc(size=60, r=20):
    yy, xx = np.mgrid[0:size, 0:size]
    return ((xx - size // 2) ** 2 + (yy - size // 2) ** 2 < r * r).astype(float)


def test_trace_closes_a_disc_into_one_path():
    paths = trace.outline(disc(), lambda x, y: (x, y))
    assert len(paths) == 1
    assert paths[0][0][0] == "move"


def test_trace_fits_a_circle_economically():
    """A circle should need about four cubics, not a vertex per pixel."""
    paths = trace.outline(disc(), lambda x, y: (x, y))
    curves = [s for s in paths[0] if s[0] == "curve"]
    assert 3 <= len(curves) <= 10


def test_trace_keeps_corners_of_a_square():
    m = np.zeros((60, 60))
    m[15:45, 15:45] = 1.0
    paths = trace.outline(m, lambda x, y: (x, y))
    pts = [s[-1] for s in paths[0] if s[0] != "move"]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # The fitted outline must still reach the square's extent on both axes.
    assert max(xs) - min(xs) > 25
    assert max(ys) - min(ys) > 25


def test_frame_places_glyphs_on_a_shared_baseline():
    f = extract.Frame()
    assert 0 < f.baseline < f.height


def test_build_reports_missing_core_characters():
    masters = {"a": disc(), "b": disc()}
    fb, missing = build.build(masters, build.Design(family="T"), x_height_px=20.0)
    assert "z" in missing and "0" in missing
    assert "a" not in missing


def test_build_emits_a_loadable_font(tmp_path=None):
    masters = {c: disc() for c in "abc"}
    fb, _ = build.build(masters, build.Design(family="Test"), x_height_px=20.0)
    import pathlib, tempfile
    tmp_path = pathlib.Path(tmp_path or tempfile.mkdtemp())
    out = tmp_path / "Test.ttf"
    fb.save(str(out))

    from fontTools.ttLib import TTFont
    font = TTFont(str(out))
    cmap = font.getBestCmap()
    assert {ord("a"), ord("b"), ord("c")} <= set(cmap)
    assert font["head"].unitsPerEm == 1000
    # A glyph must carry real contours, not an empty shell.
    assert font["glyf"]["a"].numberOfContours >= 1


def test_glyph_names_are_postscript_safe():
    assert build._glyph_name(".") == "period"
    assert build._glyph_name("A") == "A"
    assert build._glyph_name("7") == "seven"


def test_kmeans_separates_two_obvious_groups():
    rng = np.random.default_rng(0)
    P = np.vstack([rng.normal(0, 0.1, (60, 4)), rng.normal(6, 0.1, (60, 4))])
    lab = cluster.kmeans(P, 2, seed=1)
    assert len(set(lab[:60])) == 1
    assert len(set(lab[60:])) == 1
    assert lab[0] != lab[-1]


def test_kmeans_returns_one_label_per_point():
    rng = np.random.default_rng(2)
    P = rng.normal(size=(40, 3))
    for k in (3, 5):
        lab = cluster.kmeans(P, k)
        assert lab.shape == (40,)
        assert lab.min() >= 0 and lab.max() < k
