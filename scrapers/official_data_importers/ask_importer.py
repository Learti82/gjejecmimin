"""ASK — Agjencia e Statistikave të Kosovës (Kosovo Agency of Statistics).

Imports published price-index data (e.g. CPI / IÇK by category) into
`official_indices`. ASK publishes open data via the ASKdata PxWeb portal
(https://askdata.rks-gov.net) and downloadable CSV/Excel releases. Point this
importer at a downloaded CSV (or a PxWeb JSON-stat export) — no scraping.

Expected CSV columns (map with --col flags if the release differs):
    period, category, value[, unit]
"""

from __future__ import annotations

import argparse
from typing import Optional

from base import OfficialIndexRow, parse_csv, read_source, write_jsonl

SOURCE = "ASK"


def import_csv(
    path_or_url: str,
    period_col: str = "period",
    category_col: str = "category",
    value_col: str = "value",
    unit_col: Optional[str] = "unit",
    default_category: Optional[str] = None,
    default_unit: str = "index",
    fetch=None,
) -> list[OfficialIndexRow]:
    text = read_source(path_or_url, fetch=fetch)
    rows: list[OfficialIndexRow] = []
    for rec in parse_csv(text):
        try:
            value = float(str(rec[value_col]).replace(",", "."))
        except (KeyError, ValueError):
            continue
        rows.append(
            OfficialIndexRow(
                source=SOURCE,
                category=(rec.get(category_col) or default_category or "cpi").strip(),
                period=str(rec[period_col]).strip(),
                value=value,
                unit=(rec.get(unit_col) if unit_col else None) or default_unit,
            )
        )
    return rows


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Import ASK (Kosovo) official index data")
    p.add_argument("source", help="local CSV path or URL of an ASK data release")
    p.add_argument("--out", default="scrapers/output/ask_indices.jsonl")
    p.add_argument("--period-col", default="period")
    p.add_argument("--category-col", default="category")
    p.add_argument("--value-col", default="value")
    p.add_argument("--unit-col", default="unit")
    p.add_argument("--default-category", default=None)
    args = p.parse_args(argv)

    rows = import_csv(
        args.source,
        period_col=args.period_col,
        category_col=args.category_col,
        value_col=args.value_col,
        unit_col=args.unit_col,
        default_category=args.default_category,
    )
    n = write_jsonl(rows, args.out)
    print(f"ASK: imported {n} index rows -> {args.out}")


if __name__ == "__main__":
    main()
