import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.listing_attrs import parse_rooms, parse_area_m2


def test_rooms_plus_one_convention():
    assert parse_rooms("Banesë 2+1, 65m² në Prishtinë") == 2
    assert parse_rooms("Banese 3 + 1 me qira") == 3


def test_rooms_dhoma_form():
    assert parse_rooms("Banese 3 dhoma") == 3
    assert parse_rooms("Banesë me 1 dhomë") == 1


def test_rooms_absent():
    assert parse_rooms("Tokë 1000m² afër autostradës") is None
    assert parse_rooms("Shtëpi në shitje") is None


def test_area_forms():
    assert parse_area_m2("Banesë 2+1, 65m²") == 65.0
    assert parse_area_m2("Shtëpi 264m2 me qira") == 264.0
    assert parse_area_m2("Truall 1200 m² në Fushë Kosovë") == 1200.0
    assert parse_area_m2("Banese 88.5m2") == 88.5


def test_area_absent_or_absurd():
    assert parse_area_m2("Banese pa madhesi") is None
    assert parse_area_m2("Banese 2m2") is None       # too small -> parsing noise
    assert parse_area_m2("Truall 999999m2") is None  # absurd


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
