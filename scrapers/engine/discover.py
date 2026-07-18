"""Selector discovery helper.

Bootstraps a config for a new site: given a page's HTML, it suggests the
`listing_selector` (repeated product-card container), the price node, AND the
anatomy of one card (its links/headings/ids) so you can read off the
title/url/external_id selectors without hunting through DevTools.

It's a heuristic — you still confirm with `inspect` — but it turns "write CSS
selectors" into "confirm the guess".

Note on Tailwind: utility classes with a ':' (e.g. `md:text-lg`) are invalid in
a CSS selector unless escaped, so signatures DROP colon-classes. The remaining
classes are almost always enough to select the element.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from bs4 import BeautifulSoup, Tag

_CURRENCY_DIGIT = re.compile(r"(€|\beur\b|\blek[ëe]?\b).*?\d|\d.*?(€|\beur\b|\blek[ëe]?\b)", re.I)


def _classes(tag: Tag) -> list[str]:
    # Keep only CSS-safe classes (drop Tailwind variant classes like md:text-lg).
    return [c for c in (tag.get("class") or []) if ":" not in c]


def _signature(tag: Tag) -> Optional[str]:
    classes = _classes(tag)
    if not classes:
        return None
    return tag.name + "".join("." + c for c in classes)


def _minimal(tag: Tag) -> Optional[str]:
    classes = _classes(tag)
    if not classes:
        return None
    return tag.name + "." + classes[0]


def _is_price_node(tag: Tag) -> bool:
    text = tag.get_text(" ", strip=True)
    if not _CURRENCY_DIGIT.search(text):
        return False
    for child in tag.find_all(True, recursive=False):
        if _CURRENCY_DIGIT.search(child.get_text(" ", strip=True)):
            return False
    return True


def suggest(html: str, top: int = 3) -> dict:
    soup = BeautifulSoup(html, "lxml")
    price_nodes = [t for t in soup.find_all(True) if _is_price_node(t)]
    price_sig_counts = Counter(s for s in (_signature(p) for p in price_nodes) if s)

    container_counts: Counter[str] = Counter()
    container_first: dict[str, Tag] = {}
    for p in price_nodes:
        for anc in p.parents:
            if not isinstance(anc, Tag):
                continue
            sig = _signature(anc)
            if not sig:
                continue
            if anc.find("a"):
                container_counts[sig] += 1
                container_first.setdefault(sig, anc)
                break

    return {
        "price_nodes_found": len(price_nodes),
        "listing_selector_suggestions": container_counts.most_common(top),
        "price_selector_suggestions": price_sig_counts.most_common(top),
        "container_first": container_first,
    }


def _card_anatomy(container: Tag) -> list[str]:
    lines: list[str] = []

    # id / data-* attributes on the card or its parent (external_id candidates)
    for label, el in (("card", container), ("card parent", container.parent)):
        if not isinstance(el, Tag):
            continue
        ids = {k: v for k, v in el.attrs.items() if k == "id" or k.startswith("data-")}
        if ids:
            lines.append(f"  {label} id/data attrs: {ids}")

    # links (title/url candidates)
    anchors = container.select("a[href]")[:4]
    if anchors:
        lines.append("  links inside the card (title/url candidates):")
        for a in anchors:
            sig = _minimal(a) or "a"
            text = a.get_text(" ", strip=True)[:50]
            href = a.get("href", "")
            lines.append(f"    {sig}   href={href[:50]}   text=\"{text}\"")

    # headings / title-ish nodes
    titles = container.select("h1,h2,h3,h4,[class*=title],[class*=name]")[:4]
    if titles:
        lines.append("  heading/title-ish nodes:")
        for t in titles:
            sig = _minimal(t) or t.name
            text = t.get_text(" ", strip=True)[:50]
            lines.append(f"    {sig}   text=\"{text}\"")
    return lines


def format_report(html: str) -> str:
    s = suggest(html)
    lines = [
        f"price nodes found: {s['price_nodes_found']}",
        "",
        "likely listing_selector (container that repeats per product):",
    ]
    top_container = None
    for sig, count in s["listing_selector_suggestions"] or [("(none found)", 0)]:
        if top_container is None:
            top_container = sig
        lines.append(f"    {sig}    (x{count})")
    lines.append("")
    lines.append("likely price selector (relative to the container):")
    for sig, count in s["price_selector_suggestions"] or [("(none found)", 0)]:
        lines.append(f"    {sig}    (x{count})")
    lines.append("    tip: if there is an 'old-price' strikethrough, use")
    lines.append("         span.price:not(.old-price) for the current price.")

    if top_container and top_container in s["container_first"]:
        lines.append("")
        lines.append(f"anatomy of one card ({top_container}):")
        lines.extend(_card_anatomy(s["container_first"][top_container]))

    lines.append("")
    lines.append("Fill the config with these, then run")
    lines.append("`inspect <config> --pages 1` to confirm.")
    return "\n".join(lines)
