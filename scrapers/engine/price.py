"""Currency + price parsing and placeholder detection.

Rules (build spec section 7):
  * A blank/empty price field means "no price" -> return (None, None).
  * A parsed numeric price of EXACTLY 1 (EUR or LEK) is the known "message me"
    placeholder and is dropped. We match on the parsed VALUE == 1, never on the
    string starting with '1' — so 1,200 and 15,000 are kept.
  * Anything else parses to a float in a detected currency.

European formatting is handled: "1.234,56" (dot thousands, comma decimal),
"1,234.56" (comma thousands, dot decimal), "1 234", "1234.5", "1.5" all parse.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# The single, evidence-based placeholder value. Do NOT add speculative values
# here — the spec says flag suspected placeholders to a human first.
PLACEHOLDER_VALUES = {1.0}

_CURRENCY_PATTERNS = [
    ("EUR", re.compile(r"€|\beur\b|\beuro\b", re.I)),
    ("LEK", re.compile(r"\blek[ëe]?\b|\ball\b|\blekë\b", re.I)),
]

# Grab the numeric chunk (digits with , . and spaces as separators).
_NUM_RE = re.compile(r"\d[\d\.\,\s]*\d|\d")


def detect_currency(text: str, default: str = "EUR") -> str:
    for code, pat in _CURRENCY_PATTERNS:
        if pat.search(text or ""):
            return code
    return default


def _to_float(num: str) -> Optional[float]:
    """Normalize a European/US formatted number string to a float."""
    s = num.strip().replace(" ", "")
    if not s:
        return None

    has_dot = "." in s
    has_comma = "," in s
    if has_dot and has_comma:
        # The rightmost symbol is the decimal separator.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")  # 1.234,56 -> 1234.56
        else:
            s = s.replace(",", "")  # 1,234.56 -> 1234.56
    elif has_comma:
        # Comma is decimal if it looks like ",dd" at the end, else thousands.
        if re.search(r",\d{1,2}$", s):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_dot:
        # Dot-only is ambiguous. In this locale (Kosovo/Albania) the dot is the
        # THOUSANDS separator, so "12.500" = 12500 and "1.200" = 1200. Treat a
        # single dot followed by exactly 3 digits (with a non-zero integer part)
        # or multiple dots as thousands; otherwise it's a decimal ("1.99").
        parts = s.split(".")
        if len(parts) > 2:
            s = s.replace(".", "")  # 1.234.567 -> 1234567
        else:
            head, tail = parts[0], parts[1]
            if len(tail) == 3 and head.isdigit() and head != "0" and len(head) <= 3:
                s = head + tail  # 12.500 -> 12500 ; 1.200 -> 1200
            # else keep decimal (1.99, 0.50, 12.5)
    try:
        return float(s)
    except ValueError:
        return None


def parse_price(
    text: Optional[str], default_currency: str = "EUR"
) -> Tuple[Optional[float], Optional[str]]:
    """Return (price, currency). (None, None) means 'no usable price'.

    Empty input and the exact-1 placeholder both yield (None, None).
    """
    if text is None:
        return (None, None)
    text = text.strip()
    if not text:
        return (None, None)

    m = _NUM_RE.search(text)
    if not m:
        return (None, None)

    value = _to_float(m.group(0))
    if value is None:
        return (None, None)

    currency = detect_currency(text, default_currency)

    if value in PLACEHOLDER_VALUES:
        return (None, None)  # "1 EUR / 1 LEK" placeholder -> treated as no price

    if value < 0:
        return (None, None)

    return (round(value, 2), currency)
