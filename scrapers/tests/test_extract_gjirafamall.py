import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "gjirafamall_fragrances_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "fragrances_cosmetics", "gjirafamall_fragrances.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_parses_cards():
    r = _records()
    assert len(r) == 2
    assert all(x.category == "fragrances_cosmetics" for x in r)


def test_current_price_not_strikethrough():
    by_id = {x.external_id: x for x in _records()}
    # 21,99 current must win over the 27,99 old-price strikethrough.
    assert by_id["eau-de-parfum-lattafa-layaan-100ml"].price == 21.99
    assert by_id["dior-sauvage-edt-100ml"].price == 129.00
    assert all(x.currency == "EUR" for x in by_id.values())


def test_id_from_url_slug_and_title():
    by_id = {x.external_id: x for x in _records()}
    r = by_id["dior-sauvage-edt-100ml"]
    assert r.title == "Dior Sauvage EDT, 100ml"
    assert r.url == "https://gjirafamall.com/dior-sauvage-edt-100ml"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
