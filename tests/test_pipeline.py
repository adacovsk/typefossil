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


def test_compose_j_adds_a_descender_below_the_baseline():
    from typefossil import compose
    base = np.zeros((120, 60))
    base[40:70, 25:35] = 1.0          # an 'i'-like stem, sitting on row 70
    donor = np.zeros((120, 60))
    donor[40:95, 20:30] = 1.0         # a descending letter
    j = compose.compose_j(base, donor, baseline=70)
    assert (j[:70] > 0.5).any()       # keeps the stem
    assert (j[70:] > 0.5).any()       # gains a tail
    assert not (base[70:] > 0.5).any()  # and the donor was not mutated


def test_scale_preserves_the_baseline():
    from typefossil import compose
    m = np.zeros((120, 60))
    m[50:70, 20:40] = 1.0             # ink resting on row 70
    s = compose.scale(m, 1.4, baseline=70)
    rows = np.where((s > 0.5).any(axis=1))[0]
    assert abs(rows[-1] + 1 - 70) <= 2


def test_align_left_moves_ink_to_the_requested_column():
    from typefossil import compose
    m = np.zeros((40, 40))
    m[10:20, 25:30] = 1.0
    a = compose.align_left(m, x=4)
    cols = np.where((a > 0.5).any(axis=0))[0]
    assert abs(cols[0] - 4) <= 1


def test_confusions_flags_two_labels_on_one_shape():
    from typefossil import cluster
    shape = disc()
    other = np.zeros((60, 60))
    other[10:50, 10:20] = 1.0
    found = cluster.confusions({"b": shape, "h": shape.copy(), "l": other})
    pairs = {tuple(sorted((a, b))) for _, a, b in found}
    assert ("b", "h") in pairs
    assert ("b", "l") not in pairs


def test_merge_masters_prefers_a_sharp_master_over_a_populous_blurry_one():
    from typefossil import cluster
    sharp = disc()
    blurry = sharp * 0.5 + 0.25
    merged = cluster.merge_masters([(sharp, 10), (blurry, 500)])
    assert cluster.sharpness(merged) > cluster.sharpness(blurry)


def test_masters_round_trip_through_the_archive(tmp_path=None):
    import pathlib, tempfile
    from typefossil import project
    tmp_path = pathlib.Path(tmp_path or tempfile.mkdtemp())
    masters = {"a": disc(), "B": disc(40, 12), ".": disc(20, 5)}
    out = tmp_path / "m.npz"
    project.save_masters(masters, str(out), meta={"source": "test"})
    back, meta = project.load_masters(str(out))
    assert sorted(back) == sorted(masters)
    assert meta["source"] == "test"
    assert np.allclose(back["a"], masters["a"])


def test_seat_masters_puts_non_descenders_on_the_baseline():
    from typefossil import compose
    high = np.zeros((300, 120)); high[60:140, 20:80] = 1.0
    low = np.zeros((300, 120)); low[120:200, 20:80] = 1.0
    seated = compose.seat_masters({"n": high, "o": low}, baseline=232, x_height=77)
    for m in seated.values():
        assert compose.foot_row(m) == 232


def test_seat_masters_keeps_a_descender_below_the_line():
    from typefossil import compose
    body = np.zeros((300, 120)); body[150:232, 20:80] = 1.0
    desc = np.zeros((300, 120))
    desc[150:232, 20:80] = 1.0
    desc[232:280, 40:56] = 1.0
    seated = compose.seat_masters({"n": body, "p": desc}, baseline=232, x_height=82)
    assert compose.foot_row(seated["n"]) == 232
    assert compose.foot_row(seated["p"]) > 232      # tail still hangs
