"""HTML extraction driven entirely by config FieldSelectors.

Supports the cases the real configs need:
  * plain text or attribute reads
  * direct-children-only selection (breadcrumb: immediate <a> only)
  * positional index (breadcrumb link #0=category, #1=brand, ...)
  * existence checks (dealer / trusted-seller badges -> bool)
  * optional regex post-processing (group 1)
"""

from __future__ import annotations

import re
from typing import Any, Optional

from bs4 import BeautifulSoup, Tag

from .config import FieldSelector, ScraperConfig


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def select_listings(soup: BeautifulSoup, cfg: ScraperConfig) -> list[Tag]:
    return soup.select(cfg.listing_selector)


def _matches(element: Tag, fs: FieldSelector) -> list[Tag]:
    if not fs.selector:
        return [element]
    found = element.select(fs.selector)
    if fs.direct_children_only:
        # Keep only nodes that are DIRECT children of `element` matching the
        # selector's final simple selector — approximated by checking parent.
        found = [n for n in found if n.parent is element]
    return found


def extract_field(element: Tag, fs: FieldSelector) -> Any:
    if fs.const is not None:
        return fs.const
    if fs.exists:
        return bool(element.select_one(fs.selector)) if fs.selector else False

    nodes = _matches(element, fs)
    if not nodes:
        return None

    if fs.index is not None:
        if fs.index >= len(nodes):
            return None
        nodes = [nodes[fs.index]]

    node = nodes[0]
    if fs.attr:
        value = node.get(fs.attr)
        if isinstance(value, list):
            value = " ".join(value)
    else:
        value = node.get_text(" ", strip=True)

    if value is None:
        return None
    value = str(value).strip()

    if fs.regex:
        m = re.search(fs.regex, value)
        value = m.group(1) if (m and m.groups()) else (m.group(0) if m else None)

    return value


def extract_all(element: Tag, cfg: ScraperConfig) -> dict[str, Any]:
    out: dict[str, Any] = {"external_id": extract_field(element, cfg.external_id)}
    for name, fs in cfg.fields.items():
        out[name] = extract_field(element, fs)
    return out
