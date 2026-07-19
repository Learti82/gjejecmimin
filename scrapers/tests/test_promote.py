import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from promote import is_marketplace_source, normalize_name, store_name_for


def test_marketplace_detection():
    assert is_marketplace_source("merrjep_ks_cars") is True
    assert is_marketplace_source("merrjep_ks_real_estate") is True
    assert is_marketplace_source("gjirafamall_fragrances") is False
    assert is_marketplace_source("vivafresh") is False


def test_store_name_overrides():
    assert store_name_for("vivafresh") == "Viva Fresh Store"
    assert store_name_for("gjirafamall_clothing") == "GjirafaMall"


def test_store_name_fallback_for_unknown_source():
    assert store_name_for("some_new_shop") == "Some New Shop"


def test_normalize_name_strips_diacritics_and_slugifies():
    assert normalize_name("Banesë 2 dhoma, 65m²") == "banese-2-dhoma-65m2"
    assert normalize_name("Eau de Parfum Lattafa Layaan, 75ml") == \
        "eau-de-parfum-lattafa-layaan-75ml"


def test_normalize_name_diacritic_and_ascii_variants_collapse_together():
    # A title typed/rendered with diacritics and an ASCII-only variant of the
    # exact same words should collapse to the same canonical_name key.
    assert normalize_name("Çmimi i Shtëpisë") == normalize_name("Cmimi i Shtepise")


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
