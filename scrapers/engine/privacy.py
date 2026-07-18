"""Personal-data stripping (build spec section 4).

We NEVER store seller phone numbers, personal names, or personal contact info.
Business/store names are fine (business identity, not personal data). But people
often embed contact details directly in ad copy ("call Agim 044 123 456"), so
any free-text field we keep (title, raw_source_text) is passed through
`scrub_personal_data` first.

This is deliberately conservative: it removes phone numbers and the common
"call/contact <Name>" patterns in Albanian/English. It does NOT try to identify
every possible name (that's not reliable) — the rule elsewhere is "if unsure,
don't extract it". Structured personal fields are simply never selected by any
config in the first place.
"""

from __future__ import annotations

import re

# Kosovo/Albania mobile formats: 044/045/043/046/048/049 + 6 digits, with
# optional +383 / 0 prefixes and spaces/dashes/dots as separators. Also catches
# generic 9-12 digit runs that look like phone numbers.
_PHONE_RES = [
    re.compile(r"(?:\+?383|0)?\s*0?4[3-9](?:[\s\.\-]?\d){6}"),
    re.compile(r"(?:\+?355|0)?\s*6[6-9](?:[\s\.\-]?\d){7}"),  # AL mobile
    re.compile(r"\b\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{3,4}\b"),
]

# "call/contact/whatsapp/viber <Name>" — strip the directive + following token(s).
_CONTACT_RE = re.compile(
    r"\b(?:call|contact|kontakt|telefon|tel|whatsapp|viber|merrni|thirrni|"
    r"kontaktoni|na kontaktoni)\b[:\s]*"
    r"([A-ZÇËË][\wçëÇË]+(?:\s+[A-ZÇËË][\wçëÇË]+)?)?",
    re.I,
)


def scrub_personal_data(text: str | None) -> str | None:
    """Remove phone numbers and inline 'call <Name>' contact directives.

    Returns the cleaned string (collapsed whitespace), or None if the input was
    None. Store/business names in the remaining text are left intact.
    """
    if text is None:
        return None
    cleaned = text
    for rx in _PHONE_RES:
        cleaned = rx.sub(" ", cleaned)
    cleaned = _CONTACT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" \t\n\r-–—:,.")
    return cleaned or None


def contains_possible_phone(text: str | None) -> bool:
    if not text:
        return False
    return any(rx.search(text) for rx in _PHONE_RES)
