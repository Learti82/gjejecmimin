"""Shared helpers for official-data importers (build spec section 5).

Official statistics (ASK, INSTAT) and official fuel bulletins (BQK/ministry) are
public data meant for reuse — this is NOT adversarial scraping. Importers pull a
published release (CSV/JSON, or a PxWeb API response) and normalize it into
`official_indices` rows tagged by source. These rows are the platform's
"official" trust tier and the benchmark reference in validation/.

Each importer accepts either a URL or a local file path, so imports are
reproducible and testable offline. Output is a list of OfficialIndexRow, written
to JSONL or Postgres by the caller.
"""

from __future__ import annotations

import csv
import io
import json
import os
from dataclasses import dataclass, asdict
from typing import Iterable, Optional


@dataclass
class OfficialIndexRow:
    source: str          # 'ASK' | 'INSTAT' | 'BQK'
    category: str        # e.g. 'food', 'fuel', 'cpi'
    period: str          # e.g. '2026-06' or '2026-Q2'
    value: float
    unit: Optional[str] = None  # 'index' | 'EUR' | '%'

    def to_dict(self) -> dict:
        return asdict(self)


def read_source(path_or_url: str, fetch=None) -> str:
    """Return the raw text of a local file or a URL.

    For URLs a `fetch(url)->str` callable must be provided (the engine's
    HttpClient, or any function). Local files are read directly so importers run
    with no network.
    """
    if os.path.isfile(path_or_url):
        with open(path_or_url, "r", encoding="utf-8") as fh:
            return fh.read()
    if fetch is None:
        raise ValueError(f"'{path_or_url}' is not a local file and no fetch() was provided")
    return fetch(path_or_url)


def parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def write_jsonl(rows: Iterable[OfficialIndexRow], path: str) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
            n += 1
    return n
