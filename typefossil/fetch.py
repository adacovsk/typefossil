"""Fetch page images for a scanned book from the Internet Archive.

Only the page-image endpoint is used, never the multi-gigabyte JP2 tarball: a
typeface needs a few dozen well-printed text pages, not a whole book.

On provenance -- the reason this tool can exist at all: a faithful photographic
reproduction of a flat public-domain work acquires no new copyright of its own,
so scans of a pre-1900 book are usable as source material rather than merely as
reference. Check the source volume's own status before pointing this at it;
this module cannot do that for you.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE = "https://archive.org"


def metadata(identifier: str) -> dict:
    with urllib.request.urlopen(f"{BASE}/metadata/{identifier}", timeout=60) as r:
        return json.load(r)


def page_url(identifier: str, index: int, width: int = 5000) -> str:
    return f"{BASE}/download/{identifier}/page/n{index}_w{width}.jpg"


def fetch_pages(identifier: str, indices, out_dir: str, width: int = 5000,
                min_bytes: int = 20_000, log=print) -> list[Path]:
    """Download the given page indices, skipping any already present.

    Requests are serial on purpose. The endpoint renders each page on demand
    and a wide fan-out gets throttled, which costs more wall-clock than it
    saves and is rude to a free archive.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    got = []
    for i in indices:
        dest = out / f"n{i}.jpg"
        if dest.exists() and dest.stat().st_size >= min_bytes:
            got.append(dest)
            continue
        try:
            with urllib.request.urlopen(page_url(identifier, i, width), timeout=200) as r:
                data = r.read()
        except Exception as exc:                      # noqa: BLE001
            log(f"n{i}: {exc}")
            continue
        if len(data) < min_bytes:
            log(f"n{i}: too small ({len(data)} bytes), skipped")
            continue
        dest.write_bytes(data)
        got.append(dest)
        log(f"n{i}: {len(data) // 1024} KiB")
    return got
