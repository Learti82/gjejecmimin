"""Best-effort neighborhood/street-area tagging from free-text titles.

MerrJep's search-result cards only expose city (from the breadcrumb) — no
structured street or neighborhood field. Sellers often mention a neighborhood
in the listing TITLE though (e.g. "Banese me qira Arbëria (Dragodan)"), so this
scans title text for known Kosovo neighborhood names as a heuristic.

This is NOT reliable structured data: it only catches listings whose title
happens to mention a recognized name, spelled a recognized way. Titles with no
match, or an unlisted neighborhood, tag as None ("area not specified" in
reports) rather than guessing. Treat results as directional, not authoritative
— a true street-level breakdown would need each listing's detail page, which
this does not fetch.
"""

from __future__ import annotations

import re
from typing import Optional

# canonical name -> alternate spellings/aliases to match in title text.
# Kosovo cities' well-known neighborhoods (Prishtina-heavy, since that's where
# MerrJep listing volume concentrates) — extend this list as needed.
_NEIGHBORHOODS: dict[str, list[str]] = {
    "Arbëria (Dragodan)": ["arberia", "arbëria", "dragodan"],
    "Ulpianë": ["ulpiane", "ulpianë", "ulpiana"],
    "Dardania": ["dardania", "dardani"],
    "Bregu i Diellit": ["bregu i diellit", "breg diellit"],
    "Sunny Hill": ["sunny hill", "sunny-hill"],
    "Kalabria": ["kalabria", "kalabri"],
    "Lakrishte": ["lakrishte"],
    "Mati 1": ["mati 1", "mati1"],
    "Mati 2": ["mati 2", "mati2"],
    "Mati 3": ["mati 3", "mati3"],
    "Qendër": ["qender", "qendër", "qendra"],
    "Velania": ["velania", "velani"],
    "Emshir": ["emshir"],
    "Kodra e Trimave": ["kodra e trimave", "kodër e trimave"],
    "Kolovica": ["kolovica", "kolovice"],
    "Aktash": ["aktash"],
    "Prishtina e Re": ["prishtina e re", "prishtine e re"],
    "Zahir Pajaziti": ["zahir pajaziti"],
    "Bill Klinton": ["bill klinton", "bulevardi bill klinton"],
    "Muhaxheri": ["muhaxheri", "muhaxher"],
    "Sofalia": ["sofali", "sofalia"],
    "Kalabria e Re": ["kalabria e re"],
    "Fushë Kosovë": ["fushe kosove", "fushë kosovë"],
    "Vranjevc": ["vranjevc"],
    "Tophane": ["tophane"],
    "Bregu i Diellit II": ["bregu i diellit 2", "bregu i diellit ii"],
    "Rrezonanca": ["rrezonanca"],
    "Lakrishte e Re": ["lakrishte e re"],
    "Kalabria I": ["kalabria 1", "kalabria i"],
    "Peyton": ["peyton"],
    "Kastriot / Obiliq": ["kastriot", "obiliq", "obiliq/kastriot"],
}

# Longer/more specific aliases first, so "Bregu i Diellit II" doesn't get
# shadowed by a "Bregu i Diellit" partial match.
_ORDERED = sorted(
    ((canon, alias) for canon, aliases in _NEIGHBORHOODS.items() for alias in aliases),
    key=lambda pair: -len(pair[1]),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def tag_neighborhood(title: str) -> Optional[str]:
    """Return the first recognized neighborhood name mentioned in `title`, or
    None if nothing matched. Best-effort only — see module docstring."""
    if not title:
        return None
    norm = _normalize(title)
    for canonical, alias in _ORDERED:
        if alias in norm:
            return canonical
    return None
