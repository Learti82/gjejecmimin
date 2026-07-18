"""Storage writers.

Default: JSONL to disk (zero-dependency, works offline, easy to inspect).
Optional: a Postgres/Supabase `scraped_listings` staging table (see
supabase/migrations for the DDL). Staging keeps raw provenance + benchmark
flags; a separate normalization step promotes clean rows into the serving
tables (canonical_products / price_observations) that the website reads — so
real scraped data lands in the exact same tables as the seed data.

Category is written on every staged row as a first-class column.
"""

from __future__ import annotations

import json
import os
from typing import Iterable

from .record import Listing


def write_jsonl(records: Iterable[Listing], path: str) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
            n += 1
    return n


def write_postgres(records: Iterable[Listing], dsn: str) -> int:
    """Upsert into the scraped_listings staging table. Requires psycopg.

    De-dup key is (source, external_id). Import is lazy so the JSONL path never
    needs a database driver installed.
    """
    import psycopg  # type: ignore

    rows = list(records)
    if not rows:
        return 0

    sql = """
        insert into scraped_listings
          (source, category, country, external_id, url, title, price, currency,
           city, region, attributes, is_dealer, is_trusted_seller, trust_tier,
           raw_source_text, review_flags, scraped_at)
        values
          (%(source)s, %(category)s, %(country)s, %(external_id)s, %(url)s,
           %(title)s, %(price)s, %(currency)s, %(city)s, %(region)s,
           %(attributes)s, %(is_dealer)s, %(is_trusted_seller)s, %(trust_tier)s,
           %(raw_source_text)s, %(review_flags)s, %(scraped_at)s)
        on conflict (source, external_id) do update set
           price = excluded.price,
           currency = excluded.currency,
           title = excluded.title,
           city = excluded.city,
           region = excluded.region,
           attributes = excluded.attributes,
           is_dealer = excluded.is_dealer,
           is_trusted_seller = excluded.is_trusted_seller,
           review_flags = excluded.review_flags,
           scraped_at = excluded.scraped_at;
    """
    n = 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for r in rows:
                d = r.to_dict()
                d["attributes"] = json.dumps(d["attributes"], ensure_ascii=False)
                d["review_flags"] = json.dumps(d["review_flags"], ensure_ascii=False)
                cur.execute(sql, d)
                n += 1
        conn.commit()
    return n
