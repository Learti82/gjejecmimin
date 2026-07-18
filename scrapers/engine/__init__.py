"""GjejeÇmimin scraping engine: one config-driven engine, many site configs.

Public surface used by the runner, importers, and tests.
"""

from .config import ScraperConfig, load_config
from .http_client import HttpClient, DisallowedByRobots
from .pipeline import records_from_html, dedup
from .price import parse_price, detect_currency
from .privacy import scrub_personal_data
from .record import Listing
from .robots import USER_AGENT

__all__ = [
    "ScraperConfig",
    "load_config",
    "HttpClient",
    "DisallowedByRobots",
    "records_from_html",
    "dedup",
    "parse_price",
    "detect_currency",
    "scrub_personal_data",
    "Listing",
    "USER_AGENT",
]
