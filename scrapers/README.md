# GjejeÇmimin — scraping system

One config-driven engine, many site configs, organized by **category**. Every
scraped row is tagged with its category folder at the point of storage, so the
platform can group "all cars" separately from "all real estate".

Real scraped rows land in the **same tables** the seed data uses: raw scrapes go
to a `scraped_listings` staging table (category first-class + provenance), then a
normalization step promotes clean rows into `canonical_products` +
`price_observations` (the serving tables the website reads).

## Layout

```
scrapers/
  engine/                     # shared, no per-site code
    http_client.py            # honest UA + >=2s rate limit + robots.txt gate
    rate_limiter.py           # per-host minimum interval
    robots.py                 # robots.txt fetch + can_fetch / crawl-delay
    pagination.py             # bounded, config-driven page URLs
    extract.py                # CSS-selector extraction (breadcrumb, badges…)
    price.py                  # EUR/LEK parsing + exact-1 placeholder filter
    privacy.py                # strips phone numbers / "call <Name>" from text
    config.py                 # YAML schema + loader (category==folder enforced)
    pipeline.py               # extract -> clean -> filter -> tag category -> dedup
    record.py                 # Listing (category is first-class)
    storage.py                # JSONL (default) or Postgres staging
    runner.py                 # CLI: list / robots / inspect / run
  configs/<category>/*.yaml   # one file per site, grouped by category
  official_data_importers/    # ASK / INSTAT / fuel — public data, not scraping
  validation/benchmark_check.py  # outlier + official-index divergence checks
  tests/                      # offline tests + a MerrJep fixture
```

## Install

```bash
pip install -r scrapers/requirements.txt
```

## Workflow (per site/category) — the required order

```bash
cd scrapers

# 1. See all configs and which are verified
python engine/runner.py list

# 2. Check robots.txt FIRST (respects Disallow + Crawl-delay)
python engine/runner.py robots merrjep_ks_cars

# 2b. New site? Let `discover` suggest the listing/price selectors for you.
python engine/runner.py discover gjirafamall_fragrances
#     (offline: analyze a page you saved from your browser)
python engine/runner.py discover --fixture saved_page.html

# 3. Test small: fetch 1-2 pages and eyeball 5-10 parsed rows. Stores nothing.
python engine/runner.py inspect merrjep_ks_cars --pages 1
#    (offline: parse a saved page instead of the network)
python engine/runner.py inspect merrjep_ks_cars --fixture tests/fixtures/merrjep_cars_sample.html

# 4. Only after the sample looks right, set `selectors_verified: true` in the
#    config, then run at scale. The benchmark check runs automatically.
python engine/runner.py run merrjep_ks_cars --pages 5
#    write to Supabase/Postgres staging instead of JSONL:
python engine/runner.py run merrjep_ks_cars --dsn "postgresql://…"
```

**Gates that protect you**
- `run` refuses any config with `selectors_verified: false` (override:
  `--allow-unverified`, discouraged).
- `run` skips URLs disallowed by robots.txt, and skips URLs whose robots.txt
  can't be fetched unless you pass `--allow-unknown-robots`.
- Rate limit is clamped to **≥ 2s per host**; an advertised Crawl-delay that is
  longer wins.

## Data-quality rules baked in

- **Placeholder prices:** a parsed value of **exactly 1** (EUR/LEK) is dropped as
  the "message me" placeholder. Values like `1.200` / `15,000` are kept — the
  filter is on the numeric value, never the leading digit. Empty price = no price.
- **Personal data:** phone numbers and inline `call/kontakt <Name>` directives
  are stripped from any free text kept. Business/store names are preserved.
  Structured personal fields are never selected by any config.
- **Benchmark (auto after each run):** within each (category, city, product)
  group, a price > 3× or < ⅓ of the median is **held for manual review**
  (`review_flags` set), not shown automatically. Optionally compares the scraped
  price trend against the ASK/INSTAT official index and flags wild divergence.

## Official data (not scraping)

ASK (Kosovo), INSTAT (Albania), and official fuel bulletins publish reusable
open data. The importers read a downloaded CSV (or a fed URL) into
`official_indices`, tagged by source — the platform's "official" trust tier and
the benchmark reference.

```bash
python official_data_importers/ask_importer.py path/to/ask_release.csv
python official_data_importers/instat_importer.py path/to/instat_release.csv
python official_data_importers/fuel_bulletin_importer.py path/to/fuel_bulletin.csv
```

## Config status

| Config | Category | Verified | Notes |
|---|---|---|---|
| `merrjep_ks_cars` | cars | ✅ | selectors from the build brief; confirm slug |
| `merrjep_ks_car_parts` | car_parts | ❌ | breadcrumb differs — inspect first |
| `merrjep_ks_real_estate` | real_estate | ❌ | asking-price only; inspect breadcrumb |
| `gjirafa50` | electronics_tech | ❌ | template — inspect from scratch |
| `neptun_ks` | electronics_tech | ❌ | confirm it has an online catalog w/ prices |
| `vivafresh` | groceries | ❌ | template — inspect from scratch |
| `indomio_al` | real_estate | ❌ | likely JS-rendered; asking-price only |
| `gjirafamall_fragrances` | fragrances_cosmetics | ❌ | real paths /parfum, /aroma-kozmetike; fill selectors via `discover` |
| `gjirafamall_clothing` | clothing | ❌ | real path /veshje; card markup likely shared with fragrances |
| `gjirafamall_furniture` | furniture | ❌ | confirm furniture listing slug; fill via `discover` |
| `foleja_fragrances` | fragrances_cosmetics | ❌ | real path /Kozmetike-Kujdesi-Personal/Parfum/ |

Every ❌ config ships with real URLs/category paths but placeholder selectors
(`REPLACE_ME`) — run `discover` on an open network to fill them, then `inspect`
to confirm and flip `selectors_verified: true`.

## Notes / limitations

- **JS-rendered sites** (`js_rendered: true`, e.g. Indomio) need a headless
  fetcher (Playwright). The default engine uses `requests` + BeautifulSoup; the
  runner warns when a config is marked JS-rendered.
- **Legal:** always check robots.txt (built in) and each site's ToS for
  anti-scraping language before enabling a config; flag concerns rather than
  proceeding silently.
- Selectors marked "verified" were verified against markup provided in the build
  brief / live inspection. Templates marked ❌ contain `REPLACE_ME` placeholders
  and must be filled from a real `inspect` run.
```
