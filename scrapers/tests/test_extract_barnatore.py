import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "barnatore_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "pharmacy", "barnatore.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_parses_cards_correct_container():
    r = _records()
    assert len(r) == 2
    assert all(x.category == "pharmacy" for x in r)


def test_external_id_targets_product_link_not_add_to_cart_button():
    # Regression: the card has two <a> tags; must not pick up href="#" from
    # the "+ Shto në shportë" button.
    ids = {x.external_id for x in _records()}
    assert ids == {"nicorette-fresh-mint-4-mg-", "vichy-normaderm-200ml"}


def test_current_price_not_old_price_strikethrough():
    by_id = {x.external_id: x for x in _records()}
    assert by_id["nicorette-fresh-mint-4-mg-"].price == 4.50
    assert by_id["vichy-normaderm-200ml"].price == 14.99  # not the 18.00 old_price


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
