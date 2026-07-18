"""Config-driven pagination URL generation. Always bounded by max_pages — the
engine never follows pagination unboundedly."""

from __future__ import annotations

from typing import Iterator
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from .config import ScraperConfig


def page_urls(cfg: ScraperConfig, start_path: str, max_pages: int | None = None) -> Iterator[str]:
    pg = cfg.pagination
    limit = pg.max_pages if max_pages is None else min(max_pages, pg.max_pages)
    base = cfg.base_url + start_path if start_path.startswith("/") else start_path

    if pg.mode == "none":
        yield base
        return

    for i in range(limit):
        page_no = pg.start + i * pg.step
        if page_no == pg.start and i == 0:
            # First page: many sites serve it without the param.
            yield base
            continue
        if pg.mode == "query_param":
            parts = urlparse(base)
            q = dict(parse_qsl(parts.query))
            q[pg.param] = str(page_no)
            yield urlunparse(parts._replace(query=urlencode(q)))
        elif pg.mode == "path":
            sep = "" if base.endswith("/") else "/"
            yield f"{base}{sep}{pg.param}/{page_no}"
        else:
            yield base
            return
