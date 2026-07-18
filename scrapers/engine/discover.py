"""Selector discovery helper.

Bootstraps a config for a new site: given a page's HTML, it suggests the
likely `listing_selector` (the repeated product-card container) and the price
node, so you don't have to hunt through DevTools by hand. It's a heuristic — you
still confirm with `inspect` — but it turns "write CSS selectors" into "confirm
the guess".

Heuristic:
  * A "price node" is the innermost element whose text has a currency marker
    (EUR/€ or LEK) next to digits.
  * The listing container is the most-repeated class-signature of elements that
    each wrap a price node AND a link — that pattern is almost always the card.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from bs4 import BeautifulSoup, Tag

_CURRENCY_DIGIT = re.compile(r"(€|\beur\b|\blek[ëe]?\b).*?\d|\d.*?(€|\beur\b|\blek[ëe]?\b)", re.I)


def _signature(tag: Tag) -> Optional[str]:
    classes = tag.get("class") or []
    if not classes:
        return None
    return tag.name + "".join("." + c for c in classes)


def _is_price_node(tag: Tag) -> bool:
    text = tag.get_text(" ", strip=True)
    if not _CURRENCY_DIGIT.search(text):
        return False
    # innermost: no child carries the same currency+digit signal
    for child in tag.find_all(True, recursive=False):
        if _CURRENCY_DIGIT.search(child.get_text(" ", strip=True)):
            return False
    return True


def suggest(html: str, top: int = 3) -> dict:
    soup = BeautifulSoup(html, "lxml")
    price_nodes = [t for t in soup.find_all(True) if _is_price_node(t)]

    price_sig_counts = Counter(s for s in (_signature(p) for p in price_nodes) if s)

    container_counts: Counter[str] = Counter()
    for p in price_nodes:
        for anc in p.parents:
            if not isinstance(anc, Tag):
                continue
            sig = _signature(anc)
            if not sig:
                continue
            if anc.find("a"):  # a card almost always has a link
                container_counts[sig] += 1
                break  # nearest classful ancestor with a link wins

    return {
        "price_nodes_found": len(price_nodes),
        "listing_selector_suggestions": container_counts.most_common(top),
        "price_selector_suggestions": price_sig_counts.most_common(top),
    }


def format_report(html: str) -> str:
    s = suggest(html)
    lines = [
        f"price nodes found: {s['price_nodes_found']}",
        "",
        "likely listing_selector (container that repeats per product):",
    ]
    for sig, count in s["listing_selector_suggestions"] or [("(none found)", 0)]:
        lines.append(f"    {sig}    (x{count})")
    lines.append("")
    lines.append("likely price selector (relative to the container):")
    for sig, count in s["price_selector_suggestions"] or [("(none found)", 0)]:
        lines.append(f"    {sig}    (x{count})")
    lines.append("")
    lines.append("Next: put the top listing_selector in the config, open one card")
    lines.append("in DevTools to read the title/link/brand selectors, then run")
    lines.append("`inspect <config> --fixture <saved.html>` to confirm.")
    return "\n".join(lines)
