import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "merrjep_car_parts_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "car_parts", "merrjep_ks_car_parts.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_two_link_breadcrumb_city_not_mistaken_for_part_type():
    # Regression: an earlier config version read index 1 as "part_type" but it
    # was actually the city (breadcrumb here is only 2 links, not 4 like cars).
    by_id = {r.external_id: r for r in _records()}
    assert by_id["10603378"].city == "Prishtinë"
    assert by_id["15664075"].city == "Ferizaj"
    assert by_id["10603378"].attributes.get("part_category") == "Pjesë Këmbimi"


def test_contact_only_and_placeholder_prices_both_absent():
    by_id = {r.external_id: r for r in _records()}
    assert by_id["10603378"].price is None  # empty — contact-only listing
    assert by_id["10603999"].price is None  # "1 EUR" placeholder


def test_real_price_still_parses():
    by_id = {r.external_id: r for r in _records()}
    assert by_id["15664075"].price == 220.0
    assert by_id["15664075"].currency == "EUR"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
