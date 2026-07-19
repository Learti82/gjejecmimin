import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "vivafresh_sample.html")
CONFIG = os.path.join(
    os.path.dirname(HERE), "configs", "groceries", "vivafresh.yaml"
)


def _records():
    cfg = load_config(CONFIG)
    with open(FIXTURE, encoding="utf-8") as fh:
        return dedup(list(records_from_html(cfg, fh.read())))


def test_parses_cards():
    r = _records()
    assert len(r) == 2
    assert all(x.category == "groceries" for x in r)


def test_external_id_from_data_attribute_not_url():
    ids = {x.external_id for x in _records()}
    assert ids == {"1219887", "1232595"}


def test_uses_bigprice_not_smallprice():
    by_id = {x.external_id: x for x in _records()}
    pantene = by_id["1219887"]
    assert pantene.price == 1.99
    assert pantene.price != 2.99  # smallprice must not be picked up instead


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
