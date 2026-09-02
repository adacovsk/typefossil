"""Build Kelmscott Troy from scratch: the worked example.

This is the real recipe for the font in `fonts/`, not a toy. Run it end to end
and it will download roughly 700 MB of page scans and take a few hours, most of
it in clustering; the labelling step in the middle is yours to do by eye.

Read it as a template. The parts that change for a different book are the
`Source` entries and the label maps; everything else is the same pipeline.

The one thing worth internalising before starting your own: a book is a sample
of a fount, not an inventory of it. Kelmscott Troy needed three sources, and
which one supplies what is not arbitrary --

  Godefrey of Boloyne (1893)   lowercase. Set throughout in Troy, and the
                               highest-resolution scan available.
  Kelmscott Chaucer (1896)     capitals. Verse, so every line begins with one;
                               Godefrey opens chapters with woodcut initials
                               rather than type and has few.
  Chaucer's Astrolabe          'z' and the digits. Middle English barely uses
                               'z'; the treatise's zodiak/azimut/zenith do.
                               And Morris sets roman numerals everywhere else,
                               so this is the only arabic figures in the corpus.

Expect to go looking for a third source once you see what your second is
missing.
"""

from pathlib import Path

from typefossil import build, cluster, compose, extract, fetch, project, specimen
from typefossil.extract import Frame

WORK = Path("work")
X_HEIGHT_TROY = 77.0        # measured, in frame pixels
X_HEIGHT_CHAUCER = 60.0     # the smaller cut of the same design


def harvest(identifier: str, pages, out: str, width: int = 5000):
    """Download, segment, cluster and write contact sheets for one source."""
    got = fetch.fetch_pages(identifier, pages, str(WORK / out), width=width)
    instances = []
    for p in got:
        found = extract.page_instances(str(p))
        print(f"{p.name}: {len(found)}")
        instances += found
    print(f"{out}: {len(instances)} instances")

    F = cluster.features(instances)
    lab = cluster.kmeans(cluster.project(F), k=600)
    avgs = cluster.averages(instances, lab)
    sheets = cluster.contact_sheet(avgs, str(WORK / f"{out}-sheet"))
    print("read these and write a label map:", *sheets, sep="\n  ")
    return avgs


def masters_from(avgs, labels, scale_to_troy=1.0, soften=0.0):
    """Merge the clusters assigned to each character into one master."""
    out = {}
    for ch, ids in labels.items():
        ids = [i for i in ids if i in avgs]
        if not ids:
            continue
        m = cluster.merge_masters([(avgs[i][0], avgs[i][1]) for i in ids])
        if scale_to_troy != 1.0:
            m = compose.scale(m, scale_to_troy, Frame().baseline, order=3)
        if soften:
            m = compose.soften(m, soften)
        out[ch] = m
    return out


def main():
    godefrey = harvest(
        "TheHistoryOfGodefreyOfBoloyneAndOfTheConquestOfIherusalem",
        list(range(34, 540, 3)), "godefrey")
    chaucer = harvest("MorrisChaucer", list(range(40, 150)), "chaucer", width=6000)
    astrolabe = harvest("MorrisChaucer", list(range(414, 443)), "astrolabe", width=6000)

    # --- label by eye from the contact sheets, then fill these in -----------
    # Cluster ids are positional: they are only valid for the run above. This
    # is why the finished masters, not the ids, are what the repo commits.
    from labels import GODEFREY, CHAUCER, ASTROLABE       # your own module

    ratio = X_HEIGHT_TROY / X_HEIGHT_CHAUCER
    masters = masters_from(godefrey, GODEFREY)
    for ch, m in masters_from(chaucer, CHAUCER, ratio, soften=2.0).items():
        if ch.isupper() or ch not in masters:
            masters[ch] = m                 # capitals: prefer the verse source
    for ch, m in masters_from(astrolabe, ASTROLABE, ratio, soften=2.0).items():
        masters.setdefault(ch, m)

    # --- corrections that only show up once you look at the whole set ------
    masters = compose.normalise_cap_height(masters, Frame().baseline)
    masters = compose.seat_masters(masters, Frame().baseline, int(X_HEIGHT_TROY))
    if "j" in masters and "i" in masters:
        import numpy as np
        top = int(np.where((masters["n"] > 0.5).any(axis=1))[0][0])
        masters["j"] = compose.add_tittle(masters["j"], masters["i"], top - 4)

    # Check this before trusting the build. Two characters whose masters are
    # nearly identical are one sort labelled twice, and that ships a wrong
    # letter rather than a blurry one.
    for score, a, b in cluster.confusions(masters, threshold=0.95):
        print(f"SUSPICIOUS: {a!r} and {b!r} agree at {score:.3f} -- check at full size")

    design = build.Design(
        family="Kelmscott Troy",
        designer="William Morris (1892); digitised by typefossil",
        copyright="Letterforms by William Morris, 1892, public domain.",
        license_description="Licensed under the SIL Open Font License, Version 1.1.",
    )
    # Capitals average far fewer impressions than lowercase, so their masters
    # keep roughness a tight tolerance would trace faithfully.
    tol = {c: (1.6 if c.isupper() or c.isdigit() else 0.9) for c in masters}
    fb, missing = build.build(masters, design, X_HEIGHT_TROY, tol=tol)
    fb.save("KelmscottTroy-Regular.ttf")
    project.save_masters(masters, "KelmscottTroy-masters.npz")
    print("missing:", "".join(missing) or "(none)")

    specimen.sheet("KelmscottTroy-Regular.ttf", "specimen.png", title="Kelmscott Troy")
    specimen.waterfall("KelmscottTroy-Regular.ttf", "waterfall.png")


if __name__ == "__main__":
    main()
