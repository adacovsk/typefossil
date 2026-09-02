# typefossil

Recover a working digital typeface from photographs of a printed book.

Metal type is a physical object, and every page printed from it is a
measurement of that object. A page carries hundreds of impressions of the same
sorts, each one blurred slightly differently by ink spread, paper texture and
the scanner. Average enough impressions of the same letter and those errors
cancel, leaving something much closer to the punch than any single impression
is. `typefossil` mechanises that: it segments scanned pages into individual
letters, groups them by which sort they are, averages each group, fits outlines
to the result, and assembles a font.

It is aimed at type that exists only in print — books whose faces were never
digitised, or were digitised badly — and whose copyright has expired.

## What it does, in order

| Stage | Module | What it produces |
|---|---|---|
| Fetch | `fetch.py` | Page images from an Internet Archive identifier |
| Extract | `extract.py` | Every letter on the page, cut out and baseline-anchored |
| Cluster | `cluster.py` | Groups of instances of the same sort, averaged |
| Label | *(you)* | A character assigned to each cluster, from a contact sheet |
| Trace | `trace.py` | Fitted Bézier outlines |
| Build | `build.py` | A `.ttf` with metrics and naming |
| Specimen | `specimen.py` | Proof sheets |

Labelling is the one manual step, and it is manual on purpose. OCR of a
blackletter incunable is unreliable, and a mislabelled cluster is not a blurry
letter — it is the *wrong* letter, silently, in every word that uses it. Reading
a contact sheet of sixty averaged glyphs takes a couple of minutes.

## Four details that carry most of the quality

Each of these was found by building a real font and looking at it. None of them
shows up in the build output, and three of them produce a font that looks
plausible while being wrong.

**Baseline anchoring.** Every instance is placed in a fixed frame whose rows are
measured from its text line's baseline, not from the letter's own bounding box.
Without this, `p` and `b` are the same shape and cluster together, and averaging
mixes them. The frame *is* the feature vector.

**Averaging before tracing, not smoothing after.** Detail thrown away at the
averaging stage cannot be recovered downstream, and noise cancelled there never
has to be smoothed out later — smoothing that would take the genuine corners of
a blackletter pen stroke with it.

**More instances is not a better master.** k-means splits one sort across
several clusters, and it splits by whatever varies most — ink weight, a slight
skew — not by identity. Averaging all of them together folds a crisp master into
a smeared one. `merge_masters` anchors on the sharpest and admits only clusters
that agree with it.

**Seating beats inferring.** Per-line baselines drift, and clustering preserves
the drift rather than averaging it out, so a letter ends up riding high or low.
Which letters descend is a fact about the alphabet, so `seat_masters` puts
non-descenders on their foot and aligns descenders by their bowls — rather than
trying to read the baseline off the bitmap, which fails on some letter no matter
which heuristic you pick.

## The failure mode to watch for

A mislabelled cluster is **not** a blurry glyph — it is the *wrong letter*,
silently, everywhere it appears. In this face `b` and `h` differ only in whether
the bowl closes on the stem, and at contact-sheet size they are
indistinguishable; the first Troy build had no `b` at all, every one of them an
`h`, and it built and rendered and read as perfectly plausible. Run
`cluster.confusions()` over your labelled masters before you trust a build, and
check any flagged pair at full size.

## Usage

```python
from typefossil import fetch, extract, cluster, build, specimen

pages = fetch.fetch_pages("SomeArchiveIdentifier", range(30, 200, 2), "pages/")
instances = [i for p in pages for i in extract.page_instances(str(p))]

F = cluster.features(instances)
lab = cluster.kmeans(cluster.project(F), k=600)
avgs = cluster.averages(instances, lab)
cluster.contact_sheet(avgs, "sheets/labels")      # read these, write the map

masters = {ch: avgs[cid][0] for ch, cid in my_label_map.items()}
fb, missing = build.build(masters, build.Design(family="My Revival"), x_height_px=90)
fb.save("MyRevival.ttf")
specimen.sheet("MyRevival.ttf", "specimen.png")
```

`build.build` returns the characters it could not find, rather than quietly
shipping a font with holes. A source that never prints arabic numerals will
tell you so.

## Provenance and licensing

Two separate questions, and they have different answers.

**The source scans.** A faithful photographic reproduction of a flat
public-domain work acquires no new copyright, so scans of a pre-1900 book are
usable as *source material*, not merely as reference. This is what makes the
whole approach viable. It is on you to confirm the volume you point this at is
actually out of copyright — the tool cannot check.

**Typeface designs vs. font software.** In the United States a typeface *design*
is not copyrightable; the *font software* that renders it is. Redrawing a
typeface from printed specimens has always been lawful, which is why so many
legitimate revivals of historical faces exist. Note that this says nothing about
the licence on an existing digital font of the same face: if you have one, its
EULA is a contract you accepted, and terms forbidding you from modifying or
building upon it bind you regardless of what copyright says. Work from the
printed source, not from someone else's outlines.

**This repository.** The pipeline is licensed **AGPL-3.0-or-later** (`LICENSE`).
Fonts produced and distributed here are licensed **SIL OFL 1.1**
(`LICENSES/OFL-1.1.txt`), which is the appropriate copyleft for a typeface: it is
reciprocal like the GPL, but its embedding provision means putting the font in a
document or an application does not reach the containing work. A GPL'd font
without a font exception creates exactly that problem. No Reserved Font Name is
asserted — see the header of the OFL file for why.

The AGPL covers the tool, not its output. A font you build with `typefossil` from
your own sources is yours to license as you see fit.
