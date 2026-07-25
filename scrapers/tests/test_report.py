import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.neighborhoods import tag_neighborhood
from report import build_groups, group_key


def _re_row(external_id, price, city, ptype, title="", rent=False, review_flags=None):
    return {
        "source": "merrjep_ks_real_estate", "category": "real_estate", "country": "XK",
        "external_id": external_id, "url": None, "title": title,
        "price": price, "currency": "EUR" if price is not None else None,
        "city": city, "region": None,
        "attributes": {
            "price_kind": "asking_price",
            "property_type": ptype,
            **({"price_period": "muaj"} if rent else {}),
        },
        "is_dealer": False, "is_trusted_seller": False, "trust_tier": "verified_retailer",
        "raw_source_text": None, "scraped_at": "2026-07-25T00:00:00+00:00",
        "review_flags": review_flags or [],
    }


def test_neighborhood_tagging_matches_known_names():
    assert tag_neighborhood("Banesë me qera Arbëria (Dragodan)") == "Arbëria (Dragodan)"
    assert tag_neighborhood("Shtëpi ne Mati 1") == "Mati 1"


def test_neighborhood_tagging_no_match_returns_none():
    assert tag_neighborhood("Banesë 2 dhoma") is None
    assert tag_neighborhood("") is None


def test_group_key_splits_sale_vs_rent_and_neighborhood():
    sale = _re_row("1", 65000, "Prishtinë", "Banesa", title="Banesë e re")
    rent = _re_row("2", 300, "Prishtinë", "Banesa", title="Banesë me qera ne Dardania", rent=True)
    assert group_key(sale)[2] == "Sale"
    assert group_key(rent)[2] == "Rent/month"
    assert group_key(rent)[4] == "Dardania"
    assert group_key(sale)[4] == "(area not specified)"


def test_build_groups_computes_correct_stats():
    rows = [
        _re_row("1", 100000, "Prishtinë", "Banesa"),
        _re_row("2", 120000, "Prishtinë", "Banesa"),
        _re_row("3", 110000, "Prishtinë", "Banesa"),
    ]
    groups = build_groups(rows)
    assert len(groups) == 1
    g = next(iter(groups.values()))
    s = g.summary()
    assert s["count"] == 3
    assert s["min"] == 100000
    assert s["max"] == 120000
    assert s["avg"] == 110000.0
    assert g.low_confidence is False  # n=3 meets the threshold


def test_build_groups_skips_no_price_and_held_for_review():
    rows = [
        _re_row("1", None, "Prishtinë", "Banesa"),
        _re_row("2", 999999, "Prishtinë", "Banesa", review_flags=["price_outlier(...)"]),
        _re_row("3", 100000, "Prishtinë", "Banesa"),
    ]
    groups = build_groups(rows)
    g = next(iter(groups.values()))
    assert g.count == 1
    assert g.prices == [100000.0]


def test_low_confidence_flag_below_threshold():
    rows = [_re_row("1", 100000, "Prishtinë", "Banesa")]
    g = next(iter(build_groups(rows).values()))
    assert g.low_confidence is True


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
