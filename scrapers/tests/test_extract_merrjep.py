import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "merrjep_cars_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "cars", "merrjep_ks_cars.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        html = fh.read()
    return cfg, dedup(list(records_from_html(cfg, html)))


def test_all_listings_parsed_and_category_tagged():
    _, records = _records()
    assert len(records) == 4
    assert all(r.category == "cars" for r in records)  # first-class category
    assert all(r.country == "XK" for r in records)


def test_external_id_used_for_identity():
    _, records = _records()
    ids = {r.external_id for r in records}
    assert ids == {"1001", "1002", "1003", "1004"}


def test_price_rules():
    _, records = _records()
    by_id = {r.external_id: r for r in records}
    assert by_id["1001"].price == 12500.0 and by_id["1001"].currency == "EUR"
    assert by_id["1002"].price is None          # empty price
    assert by_id["1003"].price is None          # "1 €" placeholder
    assert by_id["1004"].price == 8900.0


def test_breadcrumb_maps_to_attributes_and_city():
    _, records = _records()
    r = {x.external_id: x for x in records}["1001"]
    assert r.attributes.get("brand") == "Volkswagen"
    assert r.attributes.get("model") == "Golf"
    assert r.city == "Prishtinë"


def test_badges():
    _, records = _records()
    by_id = {r.external_id: r for r in records}
    assert by_id["1001"].is_dealer is True
    assert by_id["1003"].is_trusted_seller is True
    assert by_id["1002"].is_dealer is False


def test_personal_data_scrubbed_from_title():
    _, records = _records()
    r = {x.external_id: x for x in records}["1003"]
    assert "044" not in (r.title or "")
    assert "Audi A4" in (r.title or "")


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
