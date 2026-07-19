"""Config schema + loader.

One engine, many configs (build spec section 1). A site/category is described
entirely by a YAML file; the engine has no per-site code. Grouping the YAML by
category folder is how the platform keeps "all cars" separate from "all real
estate" — the folder name is the authoritative category and is stamped onto
every row.

A config is intentionally declarative. `selectors_verified: false` marks a
config whose CSS selectors were written from documentation but NOT yet checked
against the live DOM — the runner refuses to run it at scale until a human has
inspected the site and flipped this to true (see runner.py).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml


@dataclass
class FieldSelector:
    """How to pull one field out of a listing element."""

    selector: Optional[str] = None  # CSS selector, relative to the listing element
    attr: Optional[str] = None  # attribute to read; None => text content
    direct_children_only: bool = False  # e.g. breadcrumb: immediate <a> only
    index: Optional[int] = None  # pick the Nth match (breadcrumb positions)
    regex: Optional[str] = None  # optional post-extract regex (group 1)
    exists: bool = False  # True => field is a boolean "does this node exist"
    const: Any = None  # constant value (no DOM read), e.g. price_kind tag


@dataclass
class Pagination:
    mode: str = "query_param"  # "query_param" | "path" | "none"
    param: str = "page"  # for query_param mode
    start: int = 1
    step: int = 1
    max_pages: int = 5  # hard ceiling; overridable per run, never unbounded


@dataclass
class ScraperConfig:
    id: str
    site: str
    category: str  # MUST match the containing folder; validated on load
    country: str  # "XK" | "AL"
    base_url: str
    start_paths: list[str]

    listing_selector: str  # CSS selector for each listing container
    external_id: FieldSelector  # stable per-listing id (for de-dup)
    fields: dict[str, FieldSelector] = field(default_factory=dict)

    pagination: Pagination = field(default_factory=Pagination)
    js_rendered: bool = False  # requires a headless browser if true
    trust_tier: str = "verified_retailer"
    default_currency: str = "EUR"
    rate_limit_seconds: float = 2.0  # min gap between requests (spec: >= 2s)
    selectors_verified: bool = False  # gate: refuse scale-run until True
    # ToS explicitly prohibits automated access (spec section 4: flag, don't
    # silently proceed, don't assume auto-blocker — the human decides). When
    # true, `run` refuses unless --acknowledge-tos-risk is passed; `inspect`/
    # `discover` still print a loud warning but don't block (testing a couple
    # pages vs. running production scraping are different risk profiles).
    tos_restricted: bool = False
    tos_note: str = ""
    notes: str = ""


def _field_selector(d: Any) -> FieldSelector:
    if d is None:
        return FieldSelector()
    if isinstance(d, str):
        return FieldSelector(selector=d)
    return FieldSelector(
        selector=d.get("selector"),
        attr=d.get("attr"),
        direct_children_only=bool(d.get("direct_children_only", False)),
        index=d.get("index"),
        regex=d.get("regex"),
        exists=bool(d.get("exists", False)),
        const=d.get("const"),
    )


def load_config(path: str) -> ScraperConfig:
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    pg = raw.get("pagination") or {}
    pagination = Pagination(
        mode=pg.get("mode", "query_param"),
        param=pg.get("param", "page"),
        start=int(pg.get("start", 1)),
        step=int(pg.get("step", 1)),
        max_pages=int(pg.get("max_pages", 5)),
    )

    fields = {name: _field_selector(spec) for name, spec in (raw.get("fields") or {}).items()}

    cfg = ScraperConfig(
        id=raw["id"],
        site=raw["site"],
        category=raw["category"],
        country=raw["country"],
        base_url=raw["base_url"].rstrip("/"),
        start_paths=list(raw["start_paths"]),
        listing_selector=raw["listing_selector"],
        external_id=_field_selector(raw["external_id"]),
        fields=fields,
        pagination=pagination,
        js_rendered=bool(raw.get("js_rendered", False)),
        trust_tier=raw.get("trust_tier", "verified_retailer"),
        default_currency=raw.get("default_currency", "EUR"),
        rate_limit_seconds=float(raw.get("rate_limit_seconds", 2.0)),
        selectors_verified=bool(raw.get("selectors_verified", False)),
        tos_restricted=bool(raw.get("tos_restricted", False)),
        tos_note=raw.get("tos_note", ""),
        notes=raw.get("notes", ""),
    )

    # Enforce: config category must match its folder, and rate limit >= 2s.
    folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
    if folder and folder != cfg.category:
        raise ValueError(
            f"{path}: category '{cfg.category}' does not match folder '{folder}'. "
            "Category is derived from the folder and must agree."
        )
    if cfg.rate_limit_seconds < 2.0:
        raise ValueError(f"{path}: rate_limit_seconds must be >= 2.0 (spec section 4).")

    return cfg
