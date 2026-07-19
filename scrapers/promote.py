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
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

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


@dataclass
class PromoteStats:
    read: int = 0
    skipped_no_price: int = 0
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


def promote(paths: list[str], dsn: str, dry_run: bool = False) -> PromoteStats:
    import psycopg

    stats = PromoteStats()
    rows = _read_rows(paths)

    # Caches so repeated products/stores in one run hit the DB once, not N times.
    product_cache: dict[str, str] = {}   # canonical_name -> product_id
    store_cache: dict[tuple[str, Optional[str]], Optional[str]] = {}  # (name, city) -> store_id

    conn = psycopg.connect(dsn)
    try:
        with conn.cursor() as cur:
            for row in rows:
                stats.read += 1

                if row.get("price") is None:
                    stats.skipped_no_price += 1
                    continue
                if row.get("review_flags"):
                    stats.skipped_review += 1
                    continue

                title = (row.get("title") or "").strip()
                if not title:
                    continue
                canonical_name = normalize_name(title)

                attrs = row.get("attributes") or {}
                category = row["category"]
                brand = attrs.get("brand")
                unit = attrs.get("unit")

                # --- canonical_products (find or create) ---
                product_id = product_cache.get(canonical_name)
                if product_id is None:
                    cur.execute(
                        "select id from canonical_products where canonical_name = %s",
                        (canonical_name,),
                    )
                    hit = cur.fetchone()
                    if hit:
                        product_id = str(hit[0])
                    else:
                        if dry_run:
                            product_id = f"dry-run-product:{canonical_name}"
                        else:
                            cur.execute(
                                """insert into canonical_products
                                   (name, canonical_name, category, brand, unit)
                                   values (%s, %s, %s, %s, %s)
                                   returning id""",
                                (title, canonical_name, category, brand, unit),
                            )
                            product_id = str(cur.fetchone()[0])
                        stats.products_created += 1
                    product_cache[canonical_name] = product_id

                # --- stores (marketplace listings get no fixed store) ---
                source = row["source"]
                store_id: Optional[str] = None
                if not is_marketplace_source(source):
                    store_name = store_name_for(source)
                    store_key = (store_name, None)
                    if store_key not in store_cache:
                        cur.execute(
                            "select id from stores where name = %s and city is null",
                            (store_name,),
                        )
                        hit = cur.fetchone()
                        if hit:
                            store_cache[store_key] = str(hit[0])
                        else:
                            if dry_run:
                                store_cache[store_key] = f"dry-run-store:{store_name}"
                            else:
                                cur.execute(
                                    """insert into stores (name, category, verified)
                                       values (%s, %s, true) returning id""",
                                    (store_name, category),
                                )
                                store_cache[store_key] = str(cur.fetchone()[0])
                            stats.stores_created += 1
                    store_id = store_cache[store_key]

                # --- price_observations (the fact row the UI reads) ---
                source_id = f"{source}:{row['external_id']}"
                params = (
                    product_id,
                    store_id,
                    row["price"],
                    row.get("currency") or "EUR",
                    row["scraped_at"],
                    row["trust_tier"],
                    source_id,
                    row.get("city"),
                    row.get("region"),
                    row.get("raw_source_text"),
                )
                if dry_run:
                    cur.execute(
                        "select 1 from price_observations "
                        "where source_id = %s and observed_at = %s",
                        (source_id, row["scraped_at"]),
                    )
                    if cur.fetchone() is not None:
                        stats.observations_deduped += 1
                    else:
                        stats.observations_inserted += 1
                    continue

                cur.execute(
                    """insert into price_observations
                         (product_id, store_id, price, currency, observed_at,
                          trust_tier, source_id, geo_city, geo_region, raw_source_text)
                       values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       on conflict (source_id, observed_at) where source_id is not null
                       do nothing
                       returning id""",
                    params,
                )
                if cur.fetchone() is not None:
                    stats.observations_inserted += 1
                else:
                    stats.observations_deduped += 1

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
    print(f"skipped (held review): {stats.skipped_review}")
    print(f"products created:      {stats.products_created}")
    print(f"stores created:        {stats.stores_created}")
    print(f"observations inserted: {stats.observations_inserted}")
    print(f"observations deduped:  {stats.observations_deduped} (already promoted)")
    if args.dry_run:
        print("\n(dry run — nothing was written)")


if __name__ == "__main__":
    main()
