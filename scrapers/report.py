"""Group scraped listings and compute count/min/avg/median/max price per group.

Reads whatever `run` wrote (.jsonl) — no network, no external site involved.
Grouping key depends on category, so "similar things" means something sane per
vertical:

  real_estate -> property type + sale/rent + city + best-effort neighborhood
                 (from analysis/neighborhoods.py — see its docstring for why
                 this is approximate, not authoritative: MerrJep's cards don't
                 expose a structured street/neighborhood field, only a title
                 that sometimes mentions one)
  cars        -> brand + model + city
  car_parts   -> city only (there's no reliable "type of part" field — see
                 merrjep_ks_car_parts.yaml's notes)
  anything else -> category + city

Only rows with a price are included. Groups are shown even at n=1, but flagged
low-confidence below a configurable threshold (default 3) since an "average"
of one or two listings isn't meaningful.

Usage:
    python report.py output/merrjep_ks_real_estate.jsonl
    python report.py "output/merrjep_ks_*.jsonl" --out report.csv
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from analysis.neighborhoods import tag_neighborhood
from validation.plausibility import is_implausible_price

LOW_CONFIDENCE_THRESHOLD = 3


import os as _os

SCRAPERS_DIR = _os.path.dirname(_os.path.abspath(__file__))


def _resolve(pattern: str) -> list[str]:
    """Match a glob pattern relative to the CWD, and if that finds nothing, also
    try it relative to the scrapers/ directory — so `report.py "output/x.jsonl"`
    works whether you run it from the repo root or from inside scrapers/."""
    matches = sorted(glob.glob(pattern))
    if not matches and not _os.path.isabs(pattern):
        matches = sorted(glob.glob(_os.path.join(SCRAPERS_DIR, pattern)))
    return matches


def _read_rows(paths: list[str]) -> list[dict]:
    rows: list[dict] = []
    matched_any = False
    for pattern in paths:
        matches = _resolve(pattern)
        if not matches:
            continue
        matched_any = True
        for path in matches:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))

    if not matched_any:
        import os

        wanted = ", ".join(paths)
        available = []
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        if os.path.isdir(out_dir):
            available = [f for f in sorted(os.listdir(out_dir)) if f.endswith(".jsonl")]
        msg = [f"No data files matched: {wanted}"]
        if available:
            msg.append("Available scraped files in output/:")
            msg += [f"  output/{f}" for f in available]
        else:
            msg.append("The output/ folder has no .jsonl files yet.")
        msg.append("")
        msg.append("You need to RUN the scrape before the report can read it, e.g.:")
        msg.append("  python engine/runner.py run merrjep_ks_apartments --pages 100")
        raise SystemExit("\n".join(msg))

    return rows


def group_key(row: dict) -> tuple[str, ...]:
    category = row["category"]
    attrs = row.get("attributes") or {}
    city = row.get("city") or "(unknown city)"

    if category == "real_estate":
        ptype = attrs.get("property_type") or "(unknown type)"
        kind = "Rent/month" if attrs.get("price_period") == "muaj" else "Sale"
        neighborhood = tag_neighborhood(row.get("title") or "") or "(area not specified)"
        return (category, ptype, kind, city, neighborhood)
    if category == "cars":
        brand = attrs.get("brand") or "(unknown brand)"
        model = attrs.get("model") or "(unknown model)"
        return (category, brand, model, city)
    if category == "car_parts":
        return (category, city)
    return (category, city)


@dataclass
class GroupStats:
    key: tuple[str, ...]
    prices: list[float] = field(default_factory=list)
    currency: str = "EUR"

    @property
    def count(self) -> int:
        return len(self.prices)

    @property
    def low_confidence(self) -> bool:
        return self.count < LOW_CONFIDENCE_THRESHOLD

    def summary(self) -> dict:
        return {
            "count": self.count,
            "min": round(min(self.prices), 2),
            "avg": round(statistics.mean(self.prices), 2),
            "median": round(statistics.median(self.prices), 2),
            "max": round(max(self.prices), 2),
            "currency": self.currency,
        }


def build_groups(rows: list[dict]) -> dict[tuple[str, ...], GroupStats]:
    groups: dict[tuple[str, ...], GroupStats] = {}
    for row in rows:
        price = row.get("price")
        if price is None:
            continue
        if row.get("review_flags"):
            continue  # benchmark-held outliers don't count toward averages
        if is_implausible_price(row["category"], price, row.get("attributes")):
            continue  # fake "contact me" low prices must not skew averages
        key = group_key(row)
        g = groups.setdefault(key, GroupStats(key=key, currency=row.get("currency") or "EUR"))
        g.prices.append(float(row["price"]))
    return groups


def format_key(key: tuple[str, ...]) -> str:
    return " / ".join(key[1:])  # drop the leading category, shown as a section header


def print_report(groups: dict[tuple[str, ...], GroupStats]) -> None:
    by_category: dict[str, list[GroupStats]] = defaultdict(list)
    for g in groups.values():
        by_category[g.key[0]].append(g)

    for category, glist in sorted(by_category.items()):
        print(f"\n=== {category} ===")
        glist.sort(key=lambda g: -g.count)
        for g in glist:
            s = g.summary()
            flag = "  (low confidence, n<3)" if g.low_confidence else ""
            print(
                f"  {format_key(g.key):<55} n={s['count']:<4} "
                f"avg={s['avg']:>10,.2f}  median={s['median']:>10,.2f}  "
                f"min={s['min']:>10,.2f}  max={s['max']:>10,.2f} {s['currency']}{flag}"
            )


def write_csv(groups: dict[tuple[str, ...], GroupStats], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "category", "group", "count", "avg", "median", "min", "max",
            "currency", "low_confidence",
        ])
        for g in sorted(groups.values(), key=lambda g: (g.key[0], -g.count)):
            s = g.summary()
            writer.writerow([
                g.key[0], format_key(g.key), s["count"], s["avg"], s["median"],
                s["min"], s["max"], s["currency"], g.low_confidence,
            ])


def main(argv: Optional[list[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Group scraped listings and average prices")
    p.add_argument("paths", nargs="+", help=".jsonl file(s) or glob pattern(s)")
    p.add_argument("--out", help="also write a CSV summary to this path")
    args = p.parse_args(argv)

    rows = _read_rows(args.paths)
    groups = build_groups(rows)

    total_priced = sum(g.count for g in groups.values())
    print(f"read {len(rows)} rows, {total_priced} with a usable price, "
          f"grouped into {len(groups)} groups")
    print_report(groups)

    if args.out:
        write_csv(groups, args.out)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
