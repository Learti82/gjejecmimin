import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.config import load_config
from engine.pagination import page_urls
from engine.pipeline import records_from_html, dedup

FIXTURE = os.path.join(HERE, "fixtures", "merrjep_real_estate_sample.html")
CONFIG_DIR = os.path.join(os.path.dirname(HERE), "configs", "real_estate")
SPLIT = ["merrjep_ks_apartments", "merrjep_ks_houses", "merrjep_ks_land"]


def test_split_configs_share_verified_selectors_and_parse():
    # The split-by-type configs reuse the combined config's verified selectors,
    # so they must parse the same real-estate fixture identically.
    with open(FIXTURE, encoding="utf-8") as fh:
        html = fh.read()
    for name in SPLIT:
        cfg = load_config(os.path.join(CONFIG_DIR, f"{name}.yaml"))
        records = dedup(list(records_from_html(cfg, html)))
        assert len(records) == 4, name
        assert all(r.category == "real_estate" for r in records), name
        by_id = {r.external_id: r for r in records}
        assert by_id["2002"].attributes.get("price_period") == "muaj", name
        assert by_id["2001"].city == "Prishtinë", name


def test_per_city_pagination_appends_page_param():
    cfg = load_config(os.path.join(CONFIG_DIR, "merrjep_ks_apartments.yaml"))
    urls = list(page_urls(cfg, cfg.start_paths[0], max_pages=3))
    assert urls[0].endswith("/banesa/prishtine")           # page 1: bare path
    assert "page=2" in urls[1]
    assert "page=3" in urls[2]
    # Every start_path is a distinct city under the same property-type slug.
    assert all("/banesa/" in p for p in cfg.start_paths)
    assert len(cfg.start_paths) == len(set(cfg.start_paths))


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
