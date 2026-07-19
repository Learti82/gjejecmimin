"""Headless-browser fetcher for JS-rendered sites (e.g. Barnatore, which shows
a loading spinner before content appears — plain `requests` would only ever
see the spinner's empty shell).

Mirrors HttpClient's public interface (`.allowed(url)`, `.get(url)`,
`.robots`, `.limiter`) so the runner can swap one for the other purely based on
a config's `js_rendered` flag, with no other code changes. robots.txt itself is
still fetched with plain `requests` (it's static text — no need to boot a
browser for it); only the actual listing pages go through Playwright.

Playwright is an OPTIONAL dependency (see requirements.txt) — importing this
module never requires it; only calling `.get()` does, so the rest of the
engine works fine without it installed.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

from .rate_limiter import RateLimiter
from .robots import RobotsCache, USER_AGENT


class DisallowedByRobots(Exception):
    pass


class BrowserHttpClient:
    def __init__(
        self,
        rate_limit_seconds: float = 2.0,
        respect_robots: bool = True,
        user_agent: str = USER_AGENT,
        timeout_ms: float = 30_000,
        wait_selector: Optional[str] = None,
        wait_after_load_ms: float = 800,
    ):
        self.limiter = RateLimiter(rate_limit_seconds)
        self.robots = RobotsCache(user_agent)
        self.respect_robots = respect_robots
        self.timeout_ms = timeout_ms
        self.user_agent = user_agent
        # If a config knows a good "content has loaded" selector, wait for it
        # instead of a blind sleep — more reliable than a fixed delay.
        self.wait_selector = wait_selector
        self.wait_after_load_ms = wait_after_load_ms
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._browser = None
        self._playwright = None

    # robots.txt is plain text — fetch it with plain requests, not a browser.
    def _raw_get_text(self, url: str) -> str:
        self.limiter.wait(url)
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def allowed(self, url: str) -> Optional[bool]:
        if not self.respect_robots:
            return True
        return self.robots.can_fetch(url, self._raw_get_text)

    def _ensure_browser(self):
        if self._browser is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "This config has js_rendered: true, which needs Playwright.\n"
                "Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium\n"
            ) from e
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> "BrowserHttpClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def get(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Render `url` in headless Chromium and return the final HTML.

        Waits for `wait_selector` if given, else a fixed settle delay — either
        way the page has had a chance to run its JS before we read the DOM.
        """
        if self.respect_robots:
            verdict = self.robots.can_fetch(url, self._raw_get_text)
            if verdict is False:
                raise DisallowedByRobots(url)

        self._ensure_browser()

        backoff = 2.0
        for attempt in range(1, max_retries + 1):
            self.limiter.wait(url)
            page = None
            try:
                page = self._browser.new_page(user_agent=self.user_agent)
                page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")
                if self.wait_selector:
                    page.wait_for_selector(self.wait_selector, timeout=self.timeout_ms)
                else:
                    page.wait_for_timeout(self.wait_after_load_ms)
                html = page.content()
                return html
            except Exception:
                if attempt == max_retries:
                    return None
                time.sleep(backoff)
                backoff *= 2
            finally:
                if page is not None:
                    page.close()
        return None
