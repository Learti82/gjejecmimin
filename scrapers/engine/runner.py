"""Command-line runner for the scraping engine.

Subcommands:
  list                       list all configs and their verification status
  robots   <config>          fetch robots.txt and report allow/deny + crawl-delay
  inspect  <config>          fetch 1-2 pages (or a saved fixture) and print a
                             sample of parsed rows — the section-8 "test small,
                             show me, wait" step. Stores nothing.
  run      <config>          full scrape. GATES: robots must allow, and the
                             config's selectors must be marked verified (unless
                             --allow-unverified). Runs the benchmark check
                             automatically before writing output.

Design intent: the gates make it impossible to accidentally scrape at scale
against an unverified config or a disallowed path.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Optional

# Allow running as `python -m engine.runner` or `python engine/runner.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.config import ScraperConfig, load_config  # noqa: E402
from engine.http_client import HttpClient, DisallowedByRobots  # noqa: E402
from engine.pagination import page_urls  # noqa: E402
from engine.pipeline import dedup, records_from_html  # noqa: E402
from engine.record import Listing  # noqa: E402
from engine import storage  # noqa: E402
from validation.benchmark_check import run_benchmark  # noqa: E402

CONFIG_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")


def _find_config(name: str) -> str:
    if os.path.isfile(name):
        return name
    hits = glob.glob(os.path.join(CONFIG_ROOT, "**", f"{name}.yaml"), recursive=True)
    if not hits:
        hits = glob.glob(os.path.join(CONFIG_ROOT, "**", f"*{name}*.yaml"), recursive=True)
    if not hits:
        raise SystemExit(f"No config matching '{name}' under {CONFIG_ROOT}")
    if len(hits) > 1:
        raise SystemExit("Ambiguous config name; matches:\n  " + "\n  ".join(hits))
    return hits[0]


def cmd_list(_: argparse.Namespace) -> None:
    paths = sorted(glob.glob(os.path.join(CONFIG_ROOT, "**", "*.yaml"), recursive=True))
    if not paths:
        print("No configs found.")
        return
    print(f"{'CATEGORY':<20} {'CONFIG':<32} {'VERIFIED':<9} JS")
    for p in paths:
        cfg = load_config(p)
        print(f"{cfg.category:<20} {cfg.id:<32} {str(cfg.selectors_verified):<9} {cfg.js_rendered}")


def _print_sample(records: list[Listing], limit: int) -> None:
    print(f"\nParsed {len(records)} record(s). Showing up to {limit}:\n")
    for r in records[:limit]:
        price = f"{r.price:.2f} {r.currency}" if r.price is not None else "(no price)"
        badges = []
        if r.is_dealer:
            badges.append("dealer")
        if r.is_trusted_seller:
            badges.append("trusted")
        print(f"  [{r.category}] id={r.external_id}  {price}")
        print(f"      title: {r.title}")
        loc = " / ".join(x for x in (r.city, r.region) if x)
        if loc:
            print(f"      loc:   {loc}")
        if r.attributes:
            print(f"      attrs: {r.attributes}")
        if badges:
            print(f"      badge: {', '.join(badges)}")
        print()


def cmd_robots(args: argparse.Namespace) -> None:
    cfg = load_config(_find_config(args.config))
    client = HttpClient(rate_limit_seconds=cfg.rate_limit_seconds)
    print(f"robots.txt check for {cfg.site} ({cfg.id})")
    for path in cfg.start_paths:
        url = cfg.base_url + path
        try:
            verdict = client.allowed(url)
        except Exception as e:  # network/egress failure
            print(f"  {url}\n    could not fetch robots.txt: {e}")
            continue
        label = {True: "ALLOWED", False: "DISALLOWED", None: "UNKNOWN (robots unreachable)"}[verdict]
        print(f"  {url}\n    -> {label}")
    delay = client.robots.crawl_delay(cfg.base_url + cfg.start_paths[0], client._raw_get_text)
    if delay:
        print(f"  crawl-delay advertised: {delay}s")


def _warn_if_tos_restricted(cfg: ScraperConfig) -> None:
    if not cfg.tos_restricted:
        return
    print("=" * 70)
    print(f"WARNING: '{cfg.id}' ({cfg.site}) has a flagged ToS restriction:")
    print(f"  {cfg.tos_note or 'Terms of Service prohibit automated access.'}")
    print("  This command still runs, but `run` will refuse without")
    print("  --acknowledge-tos-risk. Make your own call before scraping at scale.")
    print("=" * 70)


def cmd_inspect(args: argparse.Namespace) -> None:
    cfg = load_config(_find_config(args.config))
    _warn_if_tos_restricted(cfg)

    if args.fixture:
        with open(args.fixture, "r", encoding="utf-8") as fh:
            html = fh.read()
        records = dedup(list(records_from_html(cfg, html)))
        _print_sample(records, args.limit)
        print("(inspected from local fixture — no network used)")
        return

    client = HttpClient(rate_limit_seconds=cfg.rate_limit_seconds)
    all_records: list[Listing] = []
    pages = max(1, min(args.pages, 2))  # inspect touches at most 2 pages
    for path in cfg.start_paths[:1]:
        for url in page_urls(cfg, path, max_pages=pages):
            try:
                html = client.get(url)
            except DisallowedByRobots:
                print(f"  robots.txt disallows {url} — skipping")
                continue
            if not html:
                print(f"  failed to fetch {url}")
                continue
            all_records.extend(records_from_html(cfg, html))
    _print_sample(dedup(all_records), args.limit)


def cmd_discover(args: argparse.Namespace) -> None:
    from engine.discover import format_report

    if args.fixture:
        with open(args.fixture, "r", encoding="utf-8") as fh:
            html = fh.read()
        print(format_report(html))
        print("\n(analyzed local fixture — no network used)")
        return

    cfg = load_config(_find_config(args.config)) if args.config else None
    if cfg:
        _warn_if_tos_restricted(cfg)
    if not args.url and not cfg:
        raise SystemExit("Provide --url, or a config name, or --fixture.")
    url = args.url or (cfg.base_url + cfg.start_paths[0])
    rate = cfg.rate_limit_seconds if cfg else 2.0
    client = HttpClient(rate_limit_seconds=rate)
    html = client.get(url)
    if not html:
        raise SystemExit(f"Could not fetch {url}")
    print(f"# {url}\n")
    print(format_report(html))


def cmd_run(args: argparse.Namespace) -> None:
    cfg = load_config(_find_config(args.config))

    if not cfg.selectors_verified and not args.allow_unverified:
        raise SystemExit(
            f"Refusing to run '{cfg.id}': selectors_verified is false.\n"
            f"Inspect the live site first (`inspect {cfg.id}`), confirm the sample "
            f"output, set selectors_verified: true in the config, then re-run."
        )
    if cfg.tos_restricted and not args.acknowledge_tos_risk:
        raise SystemExit(
            f"Refusing to run '{cfg.id}': tos_restricted is true.\n"
            f"  {cfg.tos_note or 'Terms of Service prohibit automated access.'}\n"
            f"This is flagged for your decision, not an automatic block. If you have "
            f"decided to proceed anyway, re-run with --acknowledge-tos-risk."
        )
    if cfg.js_rendered:
        print("WARNING: config marks the site JS-rendered; the requests-based "
              "engine may see an empty DOM. Use a headless-browser fetcher.")

    client = HttpClient(rate_limit_seconds=cfg.rate_limit_seconds)
    all_records: list[Listing] = []
    for path in cfg.start_paths:
        for url in page_urls(cfg, path, max_pages=args.pages):
            verdict = client.allowed(url)
            if verdict is False:
                print(f"  robots disallows {url} — skipping")
                continue
            if verdict is None and not args.allow_unknown_robots:
                print(f"  robots.txt unreachable for {url} — skipping (use "
                      f"--allow-unknown-robots to override)")
                continue
            try:
                html = client.get(url)
            except DisallowedByRobots:
                continue
            if html:
                all_records.extend(records_from_html(cfg, html))

    records = dedup(all_records)

    # REQUIRED post-job benchmark step (spec section 6).
    summary = run_benchmark(records)
    print(f"benchmark: {summary}")

    out = args.out or os.path.join("scrapers", "output", f"{cfg.id}.jsonl")
    if args.dsn:
        n = storage.write_postgres(records, args.dsn)
        print(f"wrote {n} rows to Postgres staging (scraped_listings)")
    else:
        n = storage.write_jsonl(records, out)
        print(f"wrote {n} rows to {out}")
    if summary["held_for_review"]:
        print(f"NOTE: {summary['held_for_review']} row(s) held for manual review "
              f"(review_flags set) — do not publish these automatically.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gjejescrape", description="GjejeÇmimin scraping engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list configs").set_defaults(func=cmd_list)

    pr = sub.add_parser("robots", help="check robots.txt for a config")
    pr.add_argument("config")
    pr.set_defaults(func=cmd_robots)

    pd = sub.add_parser("discover", help="suggest listing/price selectors for a new site")
    pd.add_argument("config", nargs="?", help="optional config (uses its first start URL)")
    pd.add_argument("--url", help="page URL to analyze")
    pd.add_argument("--fixture", help="analyze a saved HTML file instead of the network")
    pd.set_defaults(func=cmd_discover)

    pi = sub.add_parser("inspect", help="fetch 1-2 pages (or --fixture) and show a sample")
    pi.add_argument("config")
    pi.add_argument("--pages", type=int, default=1)
    pi.add_argument("--limit", type=int, default=10)
    pi.add_argument("--fixture", help="parse a local HTML file instead of the network")
    pi.set_defaults(func=cmd_inspect)

    prun = sub.add_parser("run", help="full scrape (gated) + benchmark + store")
    prun.add_argument("config")
    prun.add_argument("--pages", type=int, default=5)
    prun.add_argument("--out", help="JSONL output path")
    prun.add_argument("--dsn", help="Postgres DSN to write staging table instead of JSONL")
    prun.add_argument("--allow-unverified", action="store_true",
                      help="run even if selectors_verified is false (dangerous)")
    prun.add_argument("--acknowledge-tos-risk", action="store_true",
                      help="run even if tos_restricted is true — only after you've "
                           "made your own legal call on that site")
    prun.add_argument("--allow-unknown-robots", action="store_true",
                      help="proceed when robots.txt cannot be fetched")
    prun.set_defaults(func=cmd_run)
    return p


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
