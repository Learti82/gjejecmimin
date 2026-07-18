"""HTTP client: honest identification, rate limiting, and robots.txt gating in
one place. Every network read in the system goes through here.

- Identifies with a truthful User-Agent (never a disguised browser string).
- Enforces the per-host >=2s rate limit before each request.
- Consults robots.txt (with the same UA) and refuses disallowed URLs.
- Retries transient failures with backoff; respects Crawl-delay when present.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

from .rate_limiter import RateLimiter
from .robots import RobotsCache, USER_AGENT


class DisallowedByRobots(Exception):
    pass


class HttpClient:
    def __init__(
        self,
        rate_limit_seconds: float = 2.0,
        respect_robots: bool = True,
        user_agent: str = USER_AGENT,
        timeout: float = 30.0,
    ):
        self.limiter = RateLimiter(rate_limit_seconds)
        self.robots = RobotsCache(user_agent)
        self.respect_robots = respect_robots
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "sq,en;q=0.8",
            }
        )

    # Raw fetch used by the robots parser itself (no robots check, but still
    # rate-limited so we never hammer /robots.txt either).
    def _raw_get_text(self, url: str) -> str:
        self.limiter.wait(url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def allowed(self, url: str) -> Optional[bool]:
        if not self.respect_robots:
            return True
        return self.robots.can_fetch(url, self._raw_get_text)

    def get(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch a page's HTML, honoring robots.txt and rate limits.

        Returns None on a hard failure after retries. Raises DisallowedByRobots
        if robots.txt explicitly forbids the URL.
        """
        if self.respect_robots:
            verdict = self.robots.can_fetch(url, self._raw_get_text)
            if verdict is False:
                raise DisallowedByRobots(url)
            # verdict None => robots unreachable; the runner decides policy.
            delay = self.robots.crawl_delay(url, self._raw_get_text)
            if delay and delay > self.limiter.min_interval:
                self.limiter.min_interval = delay

        backoff = 2.0
        for attempt in range(1, max_retries + 1):
            self.limiter.wait(url)
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in (429, 503):
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
            except requests.RequestException:
                if attempt == max_retries:
                    return None
                time.sleep(backoff)
                backoff *= 2
        return None
