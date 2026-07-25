"""Parse structured real-estate attributes out of free-text listing titles.

MerrJep listing cards don't expose bedroom count or size as fields — they live
in the title ("Banesë 2+1, 65m² në Prishtinë"). These heuristics pull them out
so the site can group/filter by rooms and compute €/m². Best-effort: a title
that doesn't mention a number returns None for that field (no guessing).
"""

from __future__ import annotations

import re
from typing import Optional

# "2+1" / "3 + 1" -> 2 bedrooms ("+1" is the living room, Kosovo convention).
# Also plain "2 dhoma" / "3 dhomë" -> 2 / 3.
_ROOMS_PLUS = re.compile(r"\b([1-9])\s*\+\s*1\b")
_ROOMS_DHOMA = re.compile(r"\b([1-9])\s*dhom", re.IGNORECASE)

# "65m2" / "65 m²" / "120 m2" / "1.5 ari"? keep to m². Capture the number.
_AREA = re.compile(r"(\d{1,6}(?:[.,]\d{1,2})?)\s*(?:m2|m²|metra katror)", re.IGNORECASE)


def parse_rooms(title: str) -> Optional[int]:
    if not title:
        return None
    m = _ROOMS_PLUS.search(title)
    if m:
        return int(m.group(1))
    m = _ROOMS_DHOMA.search(title)
    if m:
        return int(m.group(1))
    return None


def parse_area_m2(title: str) -> Optional[float]:
    if not title:
        return None
    m = _AREA.search(title)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    # Sanity: ignore absurd sizes (parsing noise). 5–100000 m² is plausible
    # (small studio up to large land parcels).
    if val < 5 or val > 100_000:
        return None
    return round(val, 2)
