import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.record import Listing
from validation.benchmark_check import flag_outliers, index_divergence, run_benchmark


def _car(id_, price, city="Prishtinë", model="Golf"):
    return Listing(
        source="t", category="cars", country="XK", external_id=id_,
        price=price, currency="EUR", city=city, attributes={"model": model},
    )


def test_outlier_flagged_against_group_median():
    # Five normal ~10k prices + one absurd 90k in the same group.
    records = [_car(str(i), 10000 + i * 100) for i in range(5)]
    records.append(_car("bad", 90000))
    flagged = flag_outliers(records)
    assert flagged == 1
    assert any("price_outlier" in f for r in records for f in r.review_flags)
    good = [r for r in records if r.external_id != "bad"]
    assert all(not r.review_flags for r in good)


def test_small_groups_not_flagged():
    records = [_car("1", 10000), _car("2", 90000)]  # too few for a median
    assert flag_outliers(records) == 0


def test_index_divergence_detected():
    scraped = {"2026-01": 100.0, "2026-06": 200.0}   # +100%
    official = {"2026-01": 100.0, "2026-06": 103.0}  # +3%
    msg = index_divergence(scraped, official)
    assert msg and "divergence" in msg


def test_index_no_divergence_when_aligned():
    scraped = {"2026-01": 100.0, "2026-06": 104.0}
    official = {"2026-01": 100.0, "2026-06": 103.0}
    assert index_divergence(scraped, official) is None


def test_run_benchmark_summary_shape():
    records = [_car(str(i), 10000 + i * 50) for i in range(4)] + [_car("x", 1000000)]
    summary = run_benchmark(records)
    assert summary["total"] == 5
    assert summary["with_price"] == 5
    assert summary["held_for_review"] >= 1


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
