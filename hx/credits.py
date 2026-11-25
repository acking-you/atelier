"""Title and credits, read from the materials at render time (none of it is typed here)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "reference" / "haoxiangaizhegeshijie"


@lru_cache(maxsize=1)
def _meta() -> dict:
    return json.loads((REF / "meta.json").read_text(encoding="utf-8"))


def title() -> str:
    return _meta()["title"]


def artist() -> str:
    return _meta()["artist"]


@lru_cache(maxsize=1)
def roles() -> tuple:
    """((role, name), ...) from the LRC header lines of the form `role : name` (lyricist, composer, ...)."""
    out = []
    for raw in (REF / "haoxiangaizhegeshijie.lrc").read_text(encoding="utf-8").splitlines()[:4]:
        m = re.match(r"\[[\d:.]+\]\s*(\S+)\s*[:：]\s*(.+?)\s*$", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return tuple(out)
