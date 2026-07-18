"""Fuel prices — from OFFICIAL bulletins, not station scraping (spec section 5).

Fuel prices are taken from official BQK / ministry bulletins (the regulated /
published reference), imported into `official_indices` under category 'fuel'.
Point this at a downloaded bulletin CSV. Typical fuel types: diesel, petrol,
lpg — each becomes a row with unit 'EUR' (price per litre).

Expected CSV columns (override with flags):
    period, fuel_type, price[, unit]
"""

from __future__ import annotations

import argparse
from typing import Optional

from base import OfficialIndexRow, parse_csv, read_source, write_jsonl

SOURCE = "BQK"  # official reference source for fuel


def import_csv(
    path_or_url: str,
    period_col: str = "period",
    type_col: str = "fuel_type",
    price_col: str = "price",
    unit: str = "EUR",
    fetch=None,
) -> list[OfficialIndexRow]:
    text = read_source(path_or_url, fetch=fetch)
    out: list[OfficialIndexRow] = []
    for rec in parse_csv(text):
        try:
            value = float(str(rec[price_col]).replace(",", "."))
        except (KeyError, ValueError):
            continue
        fuel_type = (rec.get(type_col) or "fuel").strip().lower()
        out.append(
            OfficialIndexRow(
                source=SOURCE,
                category=f"fuel:{fuel_type}",
                period=str(rec[period_col]).strip(),
                value=value,
                unit=unit,
            )
        )
    return out


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Import official fuel-price bulletin")
    p.add_argument("source", help="local CSV path or URL of an official fuel bulletin")
    p.add_argument("--out", default="scrapers/output/fuel_indices.jsonl")
    p.add_argument("--period-col", default="period")
    p.add_argument("--type-col", default="fuel_type")
    p.add_argument("--price-col", default="price")
    args = p.parse_args(argv)

    rows = import_csv(
        args.source,
        period_col=args.period_col,
        type_col=args.type_col,
        price_col=args.price_col,
    )
    n = write_jsonl(rows, args.out)
    print(f"Fuel bulletin: imported {n} rows -> {args.out}")


if __name__ == "__main__":
    main()
