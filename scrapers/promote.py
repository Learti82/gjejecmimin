"""Promote clean scraped rows into the live serving tables.

This is the piece that connects a scrape to the actual website: it reads
scraped Listing rows (from one or more .jsonl files — whatever `run` wrote)
and writes them into the SAME tables the site's UI reads:
`canonical_products` + `price_observations` (see supabase/migrations/0001_init.sql).

It does NOT touch any external website — it only moves data that is already
sitting on your machine into your own Supabase/Postgres database, so none of
the scraping legal/robots/ToS concerns apply here.

Rules:
  * Rows with a price of null are skipped (nothing to compare).
  * Rows the benchmark held for review (non-empty review_flags) are skipped —
    they need a human look first, never auto-published.
  * MerrJep sources are a marketplace of many individual sellers, not one
    store — store_id is left null and the city goes on geo_city instead
    (price_observations.store_id is nullable for exactly this reason).
  * Single-store catalogs (GjirafaMall, Gjirafa50, Foleja, vivafresh,
    Barnatore, ...) get ONE row in `stores`, created on first use.
  * Idempotent: re-running on the same file does not create duplicate
    price_observations (see migration 0003's partial unique index on
    (source_id, observed_at)) — re-scraping later, with a new scraped_at,
    correctly adds a fresh observation instead.

Usage:
    python promote.py scrapers/output/*.jsonl --dsn "postgresql://..."
    python promote.py scrapers/output/merrjep_ks_real_estate.jsonl --dsn "..." --dry-run
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validation.plausibility import is_implausible_price  # noqa: E402

# Sources that are a marketplace of many individual sellers (no single store
# identity) vs. a single retailer's own catalog. Marketplace listings get
# store_id = null (geo_city carries the location instead); catalog listings
# get upserted into `stores` once and reused for every row from that source.
_MARKETPLACE_SOURCE_PREFIXES = ("merrjep_",)

# source (config id) -> display name for the `stores` row, for single-store
# catalogs. Falls back to a title-cased version of the source id if missing.
_STORE_NAME_OVERRIDES = {
    "gjirafamall_fragrances": "GjirafaMall",
    "gjirafamall_clothing": "GjirafaMall",
    "gjirafamall_furniture": "GjirafaMall",
    "gjirafa50": "Gjirafa50",
    "foleja_fragrances": "Foleja",
    "vivafresh": "Viva Fresh Store",
    "barnatore": "Barnatore Online",
}


def is_marketplace_source(source: str) -> bool:
    return source.startswith(_MARKETPLACE_SOURCE_PREFIXES)


def store_name_for(source: str) -> str:
    if source in _STORE_NAME_OVERRIDES:
        return _STORE_NAME_OVERRIDES[source]
    return source.replace("_", " ").title()


def normalize_name(title: str) -> str:
    """Slugify a title into a canonical_name key.

    Strips diacritics (Ç -> C, ë -> e, ...) so minor accent variance across
    scrapes still collapses to the same product, then lowercases and hyphenates.
    This is a simple heuristic, not real product-matching — two different
    products that happen to share a title will collapse into one row. Good
    enough for MVP; a smarter matcher (brand+model+unit aware) is future work.
    """
    decomposed = unicodedata.normalize("NFKD", title)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug or "item"


# price_observations.price is numeric(12,2): max absolute value < 10^10. Any
# scraped price at/above this is junk (a mistyped/mangled listing, a phone
# number parsed as a price, a troll entry) — no real property or car is worth
# 10 billion EUR — so we skip it rather than let one bad row abort the insert.
MAX_PRICE = 10 ** 10


@dataclass
class PromoteStats:
    read: int = 0
    skipped_no_price: int = 0
    skipped_bad_price: int = 0
    skipped_implausible: int = 0
    skipped_review: int = 0
    products_created: int = 0
    stores_created: int = 0
    observations_inserted: int = 0
    observations_deduped: int = 0


def _read_rows(paths: list[str]) -> list[dict]:
    rows: list[dict] = []
    for pattern in paths:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
    return rows


def _chunks(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _s(value) -> str:
    """Coerce a DB text value to str. Most drivers return str for text columns,
    but some encodings return bytes — normalize so dict keys match reliably."""
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    return value


def promote(paths: list[str], dsn: str, dry_run: bool = False) -> PromoteStats:
    """Batch-promote scraped rows into canonical_products + price_observations.

    Batched on purpose: the whole job runs as a handful of set-based SQL
    statements instead of one round-trip per listing, so tens of thousands of
    rows complete in seconds even over a remote (pooler) connection.
    """
    import psycopg

    stats = PromoteStats()
    rows = _read_rows(paths)
    stats.read = len(rows)

    # ---- filter + normalize once, in Python (no DB) ----
    usable: list[dict] = []
    for row in rows:
        price = row.get("price")
        if price is None:
            stats.skipped_no_price += 1
            continue
        if price < 0 or price >= MAX_PRICE:
            stats.skipped_bad_price += 1  # junk value the DB column can't hold
            continue
        if is_implausible_price(row["category"], price, row.get("attributes")):
            stats.skipped_implausible += 1  # too-low "contact me" placeholder
            continue
        if row.get("review_flags"):
            stats.skipped_review += 1
            continue
        title = (row.get("title") or "").strip()
        if not title:
            continue
        row["_canonical"] = normalize_name(title)
        usable.append(row)

    if not usable:
        return stats

    # First occurrence of each canonical_name defines the product row.
    products: dict[str, tuple] = {}
    for row in usable:
        cn = row["_canonical"]
        if cn not in products:
            attrs = row.get("attributes") or {}
            products[cn] = (row["title"].strip(), cn, row["category"],
                            attrs.get("brand"), attrs.get("unit"))
    canonical_names = list(products.keys())

    conn = psycopg.connect(dsn)
    try:
        with conn.cursor() as cur:
            # ---- canonical_products: which already exist? ----
            existing_products: set[str] = set()
            for chunk in _chunks(canonical_names, 1000):
                cur.execute(
                    "select canonical_name from canonical_products "
                    "where canonical_name = any(%s)",
                    (chunk,),
                )
                existing_products.update(_s(r[0]) for r in cur.fetchall())
            new_products = [products[cn] for cn in canonical_names
                            if cn not in existing_products]
            stats.products_created = len(new_products)

            if not dry_run and new_products:
                cur.executemany(
                    "insert into canonical_products "
                    "(name, canonical_name, category, brand, unit) "
                    "values (%s, %s, %s, %s, %s) "
                    "on conflict (canonical_name) do nothing",
                    new_products,
                )

            # ---- map canonical_name -> product id (for observation FKs) ----
            product_id: dict[str, str] = {}
            if not dry_run:
                for chunk in _chunks(canonical_names, 1000):
                    cur.execute(
                        "select id, canonical_name from canonical_products "
                        "where canonical_name = any(%s)",
                        (chunk,),
                    )
                    for pid, cn in cur.fetchall():
                        product_id[_s(cn)] = str(pid)

            # ---- stores: only single-catalog sources; usually 0 for MerrJep ----
            store_id_by_source: dict[str, Optional[str]] = {}
            catalog_sources = {
                row["source"]: row["category"]
                for row in usable
                if not is_marketplace_source(row["source"])
            }
            for source, category in catalog_sources.items():
                name = store_name_for(source)
                cur.execute("select id from stores where name = %s and city is null", (name,))
                hit = cur.fetchone()
                if hit:
                    store_id_by_source[source] = str(hit[0])
                else:
                    stats.stores_created += 1
                    if dry_run:
                        store_id_by_source[source] = None
                    else:
                        cur.execute(
                            "insert into stores (name, category, verified) "
                            "values (%s, %s, true) returning id",
                            (name, category),
                        )
                        store_id_by_source[source] = str(cur.fetchone()[0])

            # ---- price_observations ----
            all_source_ids = [f"{r['source']}:{r['external_id']}" for r in usable]
            existing_obs: set[str] = set()
            for chunk in _chunks(all_source_ids, 1000):
                cur.execute(
                    "select source_id from price_observations where source_id = any(%s)",
                    (chunk,),
                )
                existing_obs.update(_s(r[0]) for r in cur.fetchall())

            obs_params: list[tuple] = []
            for row in usable:
                source = row["source"]
                source_id = f"{source}:{row['external_id']}"
                if source_id in existing_obs:
                    stats.observations_deduped += 1
                    continue
                stats.observations_inserted += 1
                if dry_run:
                    continue
                store_id = None if is_marketplace_source(source) \
                    else store_id_by_source.get(source)
                obs_params.append((
                    product_id[row["_canonical"]],
                    store_id,
                    row["price"],
                    row.get("currency") or "EUR",
                    row["scraped_at"],
                    row["trust_tier"],
                    source_id,
                    row.get("city"),
                    row.get("region"),
                    row.get("raw_source_text"),
                ))

            if not dry_run and obs_params:
                cur.executemany(
                    "insert into price_observations "
                    "(product_id, store_id, price, currency, observed_at, "
                    " trust_tier, source_id, geo_city, geo_region, raw_source_text) "
                    "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "on conflict (source_id, observed_at) where source_id is not null "
                    "do nothing",
                    obs_params,
                )

        if not dry_run:
            conn.commit()
    finally:
        conn.close()

    return stats


def main(argv=None) -> None:
    p = argparse.ArgumentParser(
        description="Promote clean scraped rows into canonical_products + price_observations"
    )
    p.add_argument("paths", nargs="+", help=".jsonl file(s) or glob pattern(s)")
    p.add_argument("--dsn", required=True, help="Postgres/Supabase connection string")
    p.add_argument("--dry-run", action="store_true",
                   help="report what would happen without writing anything")
    args = p.parse_args(argv)

    stats = promote(args.paths, args.dsn, dry_run=args.dry_run)
    print(f"read:                  {stats.read}")
    print(f"skipped (no price):    {stats.skipped_no_price}")
    print(f"skipped (bad price):   {stats.skipped_bad_price}")
    print(f"skipped (fake low):    {stats.skipped_implausible}")
    print(f"skipped (held review): {stats.skipped_review}")
    print(f"products created:      {stats.products_created}")
    print(f"stores created:        {stats.stores_created}")
    print(f"observations inserted: {stats.observations_inserted}")
    print(f"observations deduped:  {stats.observations_deduped} (already promoted)")
    if args.dry_run:
        print("\n(dry run — nothing was written)")


if __name__ == "__main__":
    main()
