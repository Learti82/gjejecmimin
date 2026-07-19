import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "foleja_fragrances_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "fragrances_cosmetics", "foleja_fragrances.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_parses_cards():
    r = _records()
    assert len(r) == 2
    assert all(x.category == "fragrances_cosmetics" for x in r)


def test_uses_list_price_not_original_price():
    # Current best guess: list-price-price is the actual selling price;
    # whole-original-price (when present) is a higher pre-discount reference
    # and must NOT be picked up instead.
    by_id = {x.external_id: x for x in _records()}
    asad = by_id["YLL-200014020"]
    assert asad.price == 32.99
    assert asad.price != 45.00


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
