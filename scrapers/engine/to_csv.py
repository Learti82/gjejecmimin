"""Convert a scraped JSONL file into a CSV — the most universally "downloadable
and openable" format (Excel, Google Sheets, etc.), on top of the raw JSONL that
`run` always writes.

Nested fields (attributes, review_flags) are flattened: `attributes` becomes
one CSV column per key seen across the file (e.g. attributes.brand,
attributes.property_type), and review_flags is joined into one string column.
"""

from __future__ import annotations

import argparse
import csv
import json
import os


def jsonl_to_csv(jsonl_path: str, csv_path: str | None = None) -> str:
    if csv_path is None:
        csv_path = os.path.splitext(jsonl_path)[0] + ".csv"

    rows: list[dict] = []
    attr_keys: list[str] = []
    seen_attr_keys: set[str] = set()

    with open(jsonl_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.append(row)
            for k in (row.get("attributes") or {}).keys():
                if k not in seen_attr_keys:
                    seen_attr_keys.add(k)
                    attr_keys.append(k)

    base_cols = [
        "source", "category", "country", "external_id", "url", "title",
        "price", "currency", "city", "region", "is_dealer", "is_trusted_seller",
        "trust_tier", "scraped_at",
    ]
    attr_cols = [f"attributes.{k}" for k in attr_keys]
    fieldnames = base_cols + attr_cols + ["review_flags"]

    os.makedirs(os.path.dirname(os.path.abspath(csv_path)) or ".", exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = {c: row.get(c) for c in base_cols}
            attrs = row.get("attributes") or {}
            for k in attr_keys:
                out[f"attributes.{k}"] = attrs.get(k)
            out["review_flags"] = "; ".join(row.get("review_flags") or [])
            writer.writerow(out)

    return csv_path


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Convert a scraped .jsonl file to .csv")
    p.add_argument("jsonl_path")
    p.add_argument("--out", help="output .csv path (default: same name, .csv)")
    args = p.parse_args(argv)

    out = jsonl_to_csv(args.jsonl_path, args.out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
