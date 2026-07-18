"""robots.txt compliance (build spec section 4).

Before scraping any path we consult the site's robots.txt with OUR user-agent
and honor Disallow rules and any Crawl-delay. Results are cached per host. If
robots.txt can't be fetched, we default to the conservative choice the caller
requests (the runner treats an unreachable robots.txt as "do not scrape at
scale until a human confirms").
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

USER_AGENT = (
    "GjejeCmiminBot/0.1 (+https://gjejecmimin.com/bot; price-comparison; "
    "contact: hello@gjejecmimin.com)"
)


class RobotsCache:
    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser | None] = {}

    def _parser_for(self, url: str, fetch) -> RobotFileParser | None:
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        if host in self._parsers:
            return self._parsers[host]

        robots_url = urljoin(host, "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            text = fetch(robots_url)
            rp.parse(text.splitlines())
        except Exception:
            self._parsers[host] = None  # unknown -> caller decides
            return None
        self._parsers[host] = rp
        return rp

    def can_fetch(self, url: str, fetch) -> bool | None:
        """True/False if robots.txt is known; None if it couldn't be fetched."""
        rp = self._parser_for(url, fetch)
        if rp is None:
            return None
        return rp.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str, fetch) -> float | None:
        rp = self._parser_for(url, fetch)
        if rp is None:
            return None
        try:
            d = rp.crawl_delay(self.user_agent)
            return float(d) if d is not None else None
        except Exception:
            return None
