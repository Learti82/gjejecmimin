import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.privacy import scrub_personal_data, contains_possible_phone


def test_strips_kosovo_phone():
    out = scrub_personal_data("Audi A4 — call Agim 044 123 456")
    assert "044" not in out
    assert "123" not in out
    assert "Audi A4" in out


def test_strips_various_phone_formats():
    for s in ["thirrni 045-678-901", "tel: 049.11.22.33", "+383 44 123 456"]:
        assert not contains_possible_phone(scrub_personal_data(s) or "")


def test_keeps_business_name():
    out = scrub_personal_data("Auto Sallon Xeni - Golf 7")
    assert "Auto Sallon Xeni" in out
    assert "Golf 7" in out


def test_none_passthrough():
    assert scrub_personal_data(None) is None


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
