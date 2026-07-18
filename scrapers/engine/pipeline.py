"""The scraping pipeline: turn config + HTML into clean, category-tagged
Listing records.

Order of operations per listing element:
  1. extract raw fields via config selectors
  2. require a stable external_id (else skip — can't de-dup safely)
  3. parse price + currency; empty/placeholder(==1) => price stays None
  4. scrub personal data from any free-text we keep (title, raw text)
  5. stamp the first-class `category` (from config folder) + provenance
  6. de-dup by (source, external_id)

This module is transport-agnostic: `records_from_html` works on a raw HTML
string, so it is used identically for live scraping, offline inspection against
a saved fixture, and unit tests.
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Optional
from urllib.parse import urljoin

from .config import ScraperConfig
from .extract import extract_all, parse_html, select_listings
from .price import parse_price
from .privacy import scrub_personal_data
from .record import Listing

# Field names the engine understands specially; everything else in a config's
# `fields` becomes a category-specific attribute (brand/model, rooms/size, ...).
_KNOWN_FIELDS = {
    "title",
    "price",
    "url",
    "city",
    "region",
    "is_dealer",
    "is_trusted_seller",
}


def _build_listing(cfg: ScraperConfig, raw: dict[str, Any]) -> Optional[Listing]:
    external_id = raw.get("external_id")
    if not external_id:
        return None  # cannot de-dup reliably without a stable id

    price_text = raw.get("price")
    price, currency = parse_price(
        price_text if isinstance(price_text, str) else None,
        cfg.default_currency,
    )

    title = scrub_personal_data(raw.get("title") if isinstance(raw.get("title"), str) else None)

    url = raw.get("url")
    if url and cfg.base_url and url.startswith("/"):
        url = urljoin(cfg.base_url + "/", url.lstrip("/"))

    attributes = {
        k: v
        for k, v in raw.items()
        if k not in _KNOWN_FIELDS and k not in ("external_id",) and v not in (None, "")
    }

    return Listing(
        source=cfg.id,
        category=cfg.category,  # first-class, from the config/folder
        country=cfg.country,
        external_id=str(external_id),
        url=url if isinstance(url, str) else None,
        title=title,
        price=price,
        currency=currency if price is not None else None,
        city=(raw.get("city") or None),
        region=(raw.get("region") or None),
        attributes=attributes,
        is_dealer=bool(raw.get("is_dealer")),
        is_trusted_seller=bool(raw.get("is_trusted_seller")),
        trust_tier=cfg.trust_tier,
        raw_source_text=scrub_personal_data(
            price_text if isinstance(price_text, str) else None
        ),
    )


def records_from_html(cfg: ScraperConfig, html: str) -> Iterator[Listing]:
    soup = parse_html(html)
    for element in select_listings(soup, cfg):
        raw = extract_all(element, cfg)
        listing = _build_listing(cfg, raw)
        if listing is not None:
            yield listing


def dedup(records: Iterable[Listing]) -> list[Listing]:
    seen: set[tuple[str, str]] = set()
    out: list[Listing] = []
    for r in records:
        key = (r.source, r.external_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
