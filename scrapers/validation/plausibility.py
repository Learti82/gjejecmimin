"""Category-aware price plausibility floors.

The exact-1 placeholder filter (engine/price.py) catches "1 EUR", but sellers
also use other trivially-low prices (€2, €3, €37, ...) as "contact me for the
real price" placeholders — very common on real-estate listings. Those are not
real prices and must not reach users.

A blanket low-price filter would be wrong: a €0.40 grocery item or a €3 wiper
blade is genuine, and a €300/month apartment RENTAL is genuine. So floors are
per (category, sale-vs-rent):

  real_estate, sale  -> €1,000  (no property in Kosovo sells for less)
  real_estate, rent  -> €30     (a real monthly rent; blocks €1-2 placeholders)
  cars               -> €150    (a real car; blocks €1-37 "call me" listings)
  everything else    -> no extra floor (groceries/parts can be genuinely cheap;
                        they still get the exact-1 filter + the 10^10 ceiling)

Rent vs sale is read from attributes.price_period ("muaj" => monthly rent).
"""

from __future__ import annotations

from typing import Optional

# (category, kind) -> minimum plausible price in EUR. kind is "rent" or "sale".
PRICE_FLOORS: dict[tuple[str, str], float] = {
    ("real_estate", "sale"): 1000.0,
    ("real_estate", "rent"): 30.0,
    ("cars", "sale"): 150.0,
    ("cars", "rent"): 30.0,
}


def _kind(attributes: Optional[dict]) -> str:
    attrs = attributes or {}
    return "rent" if attrs.get("price_period") == "muaj" else "sale"


def price_floor(category: str, attributes: Optional[dict]) -> Optional[float]:
    """Minimum plausible price for this category+kind, or None if unfloored."""
    return PRICE_FLOORS.get((category, _kind(attributes)))


def is_implausible_price(
    category: str, price: float, attributes: Optional[dict]
) -> bool:
    """True if this price is too low to be real for its category (a placeholder
    / 'contact me' price), and should be dropped rather than shown to users."""
    floor = price_floor(category, attributes)
    return floor is not None and price < floor
