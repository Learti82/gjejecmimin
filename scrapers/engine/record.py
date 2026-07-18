"""The canonical shape of one scraped listing.

`category` is a first-class field on every record (section 1 of the build spec):
it is set from the config's category folder at the moment of extraction, never
inferred later. Downstream storage groups/searches by this field, so it must
always be present.

Only factual product/price/location fields live here. No seller phone numbers,
personal names, or other personal data are ever carried on this object — the
pipeline strips them before a record is built (see engine/privacy.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Listing:
    # --- provenance / identity ---
    source: str  # config id, e.g. "merrjep_ks_cars"
    category: str  # first-class category folder, e.g. "cars"
    country: str  # "XK" (Kosovo) or "AL" (Albania)
    external_id: str  # site's stable id (e.g. data-product-id) — used for de-dup
    url: Optional[str] = None

    # --- the facts we compare on ---
    title: Optional[str] = None
    price: Optional[float] = None  # None = "no price" (empty / placeholder filtered)
    currency: Optional[str] = None  # "EUR" or "LEK"
    city: Optional[str] = None
    region: Optional[str] = None

    # --- category-specific attributes (brand/model for cars, rooms/size for
    #     real estate, etc.). Kept as a free-form dict so one record type serves
    #     every category without schema churn. ---
    attributes: dict[str, Any] = field(default_factory=dict)

    # --- trust signals used by the platform's trust-tier model ---
    is_dealer: bool = False  # store/dealer badge present
    is_trusted_seller: bool = False  # trusted-seller badge present
    trust_tier: str = "verified_retailer"  # set per-config; official importers use "official"

    # --- audit trail ---
    raw_source_text: Optional[str] = None  # original title/price text, facts only
    scraped_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # --- benchmark/validation bookkeeping (filled by validation layer) ---
    review_flags: list[str] = field(default_factory=list)

    def held_for_review(self) -> bool:
        return bool(self.review_flags)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
