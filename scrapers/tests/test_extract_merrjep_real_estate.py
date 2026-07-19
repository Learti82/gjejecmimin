import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "merrjep_real_estate_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "real_estate", "merrjep_ks_real_estate.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_all_tagged_real_estate():
    records = _records()
    assert len(records) == 4
    assert all(r.category == "real_estate" for r in records)


def test_two_link_breadcrumb_maps_type_and_city():
    by_id = {r.external_id: r for r in _records()}
    assert by_id["2001"].attributes.get("property_type") == "Banesë"
    assert by_id["2001"].city == "Prishtinë"
    assert by_id["2003"].attributes.get("property_type") == "Tokë/Truall"
    assert by_id["2003"].city == "Ferizaj"


def test_rental_detected_via_muaj_suffix():
    by_id = {r.external_id: r for r in _records()}
    assert by_id["2002"].attributes.get("price_period") == "muaj"
    assert by_id["2002"].price == 350.0
    assert "price_period" not in by_id["2001"].attributes  # sale, not rental


def test_placeholder_and_empty_prices_still_dropped():
    by_id = {r.external_id: r for r in _records()}
    assert by_id["2003"].price is None  # empty price
    assert by_id["2004"].price is None  # "1 €" placeholder


def test_every_row_tagged_asking_not_confirmed_transaction():
    for r in _records():
        assert r.attributes.get("price_kind") == "asking_price"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
