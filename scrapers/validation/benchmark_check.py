"""Benchmark / sanity-check layer (build spec section 6).

Runs automatically after each scraping job (the runner calls `run_benchmark`
before anything is considered publishable). Two independent checks:

1. Intra-dataset outliers: within the same (category, city, product-key) group,
   any price > ~3x or < ~1/3 of the group MEDIAN is held for manual review
   rather than shown to users. Groups smaller than a threshold are skipped
   (a median from 1-2 points isn't meaningful).

2. Official-index divergence: for categories that map to an official index
   (ASK/INSTAT), compare the mean scraped price trend against the official
   index trend across periods; flag wild divergence (scraper may have broken or
   be reading the wrong field).

Flagged records get a `review_flags` entry; they are NOT dropped — a human
reviews them.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Iterable, Optional, Sequence

from engine.record import Listing

OUTLIER_HIGH_MULTIPLIER = 3.0
OUTLIER_LOW_DIVISOR = 3.0
MIN_GROUP_SIZE = 4  # need enough points for a meaningful median
INDEX_DIVERGENCE_TOLERANCE = 0.35  # 35% gap between trend deltas = suspicious


def _group_key(r: Listing) -> tuple[str, str, str]:
    # Product key: prefer a normalized brand+model/title; fall back to title.
    attrs = r.attributes or {}
    product = (
        attrs.get("model")
        or attrs.get("brand")
        or (r.title or "")
    ).strip().lower()
    return (r.category, (r.city or "").strip().lower(), product)


def flag_outliers(records: Sequence[Listing]) -> int:
    """Mutate records in place, adding 'price_outlier' flags. Returns #flagged."""
    groups: dict[tuple[str, str, str], list[Listing]] = defaultdict(list)
    for r in records:
        if r.price is not None:
            groups[_group_key(r)].append(r)

    flagged = 0
    for key, members in groups.items():
        if len(members) < MIN_GROUP_SIZE:
            continue
        prices = [m.price for m in members if m.price is not None]
        median = statistics.median(prices)
        if median <= 0:
            continue
        hi = median * OUTLIER_HIGH_MULTIPLIER
        lo = median / OUTLIER_LOW_DIVISOR
        for m in members:
            if m.price is not None and (m.price > hi or m.price < lo):
                flag = f"price_outlier(median={median:.2f},price={m.price:.2f})"
                if flag not in m.review_flags:
                    m.review_flags.append(flag)
                    flagged += 1
    return flagged


def index_divergence(
    scraped_by_period: dict[str, float],
    official_by_period: dict[str, float],
    tolerance: float = INDEX_DIVERGENCE_TOLERANCE,
) -> Optional[str]:
    """Compare period-over-period % change of scraped means vs official index.

    Returns a human-readable warning string if the two trends diverge beyond
    `tolerance`, else None. Both dicts are {period: value}; periods are sorted.
    """
    periods = sorted(set(scraped_by_period) & set(official_by_period))
    if len(periods) < 2:
        return None

    def pct_change(series: dict[str, float]) -> float:
        first, last = series[periods[0]], series[periods[-1]]
        if first == 0:
            return 0.0
        return (last - first) / first

    scraped_delta = pct_change(scraped_by_period)
    official_delta = pct_change(official_by_period)
    gap = abs(scraped_delta - official_delta)
    if gap > tolerance:
        return (
            f"index_divergence: scraped trend {scraped_delta:+.1%} vs official "
            f"{official_delta:+.1%} over {periods[0]}..{periods[-1]} (gap {gap:.1%})"
        )
    return None


def run_benchmark(
    records: Sequence[Listing],
    scraped_by_period: Optional[dict[str, float]] = None,
    official_by_period: Optional[dict[str, float]] = None,
) -> dict:
    """The required post-job step. Returns a summary; mutates records' flags."""
    n_outliers = flag_outliers(records)
    divergence = None
    if scraped_by_period and official_by_period:
        divergence = index_divergence(scraped_by_period, official_by_period)

    held = [r for r in records if r.held_for_review()]
    return {
        "total": len(records),
        "with_price": sum(1 for r in records if r.price is not None),
        "outliers_flagged": n_outliers,
        "held_for_review": len(held),
        "index_divergence": divergence,
    }
