import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.plausibility import is_implausible_price, price_floor


def test_real_estate_sale_low_prices_are_implausible():
    for p in [2, 3, 11, 37, 999]:
        assert is_implausible_price("real_estate", p, {"price_kind": "asking_price"})


def test_real_estate_sale_real_prices_are_kept():
    for p in [1000, 45000, 250000]:
        assert not is_implausible_price("real_estate", p, {"price_kind": "asking_price"})


def test_real_estate_rent_keeps_normal_rents_blocks_placeholders():
    rent = {"price_kind": "asking_price", "price_period": "muaj"}
    assert is_implausible_price("real_estate", 2, rent)      # €2/month = fake
    assert not is_implausible_price("real_estate", 300, rent)  # €300/month = real
    assert not is_implausible_price("real_estate", 150, rent)


def test_cars_block_placeholder_prices():
    assert is_implausible_price("cars", 37, {})
    assert not is_implausible_price("cars", 3500, {})


def test_other_categories_have_no_floor():
    # Groceries / parts can be genuinely cheap — only the exact-1 filter
    # (in engine/price.py) applies to them, not this floor.
    assert not is_implausible_price("groceries", 0.45, {})
    assert not is_implausible_price("car_parts", 3.0, {})
    assert price_floor("groceries", {}) is None


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
