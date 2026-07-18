import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.price import parse_price, detect_currency


def test_empty_is_no_price():
    assert parse_price("") == (None, None)
    assert parse_price(None) == (None, None)
    assert parse_price("   ") == (None, None)


def test_exact_one_is_placeholder():
    assert parse_price("1 €") == (None, None)
    assert parse_price("1 EUR") == (None, None)
    assert parse_price("1") == (None, None)
    assert parse_price("1 LEK") == (None, None)


def test_one_prefixed_prices_are_kept():
    # Must NOT be filtered just for starting with '1'.
    assert parse_price("1.200 €") == (1200.0, "EUR")
    assert parse_price("15,000 LEK") == (15000.0, "LEK")
    assert parse_price("1,5 €") == (1.5, "EUR")  # 1.5 is a real price, not "1"


def test_european_and_us_formats():
    assert parse_price("12.500 €") == (12500.0, "EUR")
    assert parse_price("8,900 EUR") == (8900.0, "EUR")
    assert parse_price("1.234,56 €") == (1234.56, "EUR")
    assert parse_price("1 234 lekë") == (1234.0, "LEK")


def test_currency_detection_default():
    assert detect_currency("no symbol here", default="EUR") == "EUR"
    assert detect_currency("2500 Lek") == "LEK"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
