"""A project file: everything needed to rebuild one font reproducibly.

The labelling step is human judgement, and it is the only part of the pipeline
that cannot be re-derived from the inputs. Recording it here is what makes a
build repeatable -- and it is why re-clustering with different parameters is
not free: cluster ids are positional, so changing ``k`` or the seed invalidates
every label. Settle the clustering, then label, then keep both pinned.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Source:
    """One scanned book contributing glyphs."""

    identifier: str                  # Internet Archive identifier
    pages: list[int]
    width: int = 5000
    title: str = ""
    year: str = ""
    #: Scale applied to this source's masters before they join the font. Sources
    #: printed at different sizes need normalising to the primary source's
    #: x-height -- a smaller cut of the same face is optically heavier, so this
    #: is a starting point for the eye, not a finished answer.
    scale: float = 1.0
    notes: str = ""


@dataclass
class Project:
    name: str
    family: str
    sources: list[Source] = field(default_factory=list)
    #: ``{character: cluster id}``, per source key.
    labels: dict[str, dict[str, int]] = field(default_factory=dict)
    k: int = 600
    seed: int = 0
    x_height_px: float = 90.0
    notes: str = ""

    def save(self, path: str) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: str) -> "Project":
        raw = json.loads(Path(path).read_text())
        raw["sources"] = [Source(**s) for s in raw.get("sources", [])]
        return cls(**raw)


def save_masters(masters: dict, path: str, meta: dict | None = None) -> None:
    """Store labelled glyph masters as a compressed archive.

    Cluster ids are positional: change ``k``, the seed, or the page set and
    every id means something else, so a label map keyed by id is only valid for
    the exact run that produced it. The masters themselves have no such problem.
    Saving them is what makes a font rebuildable -- retracing, remetricking or
    renaming it costs seconds and needs none of the segmentation, clustering or
    labelling to be repeated.
    """
    import json as _json

    import numpy as np

    payload = {f"glyph_{ord(ch):04X}": m.astype(np.float32) for ch, m in masters.items()}
    payload["__chars__"] = np.array(
        [ord(ch) for ch in sorted(masters)], dtype=np.int32
    )
    payload["__meta__"] = np.frombuffer(
        _json.dumps(meta or {}).encode("utf-8"), dtype=np.uint8
    )
    np.savez_compressed(path, **payload)


def load_masters(path: str) -> tuple[dict, dict]:
    """Read back ``save_masters``. Returns ``(masters, meta)``."""
    import json as _json

    import numpy as np

    z = np.load(path)
    chars = [chr(c) for c in z["__chars__"]]
    masters = {ch: z[f"glyph_{ord(ch):04X}"] for ch in chars}
    meta = _json.loads(bytes(z["__meta__"]).decode("utf-8")) if "__meta__" in z else {}
    return masters, meta
