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
    browser_client.py         # same, but headless Chromium for JS-rendered sites
    rate_limiter.py           # per-host minimum interval
    robots.py                 # robots.txt fetch + can_fetch / crawl-delay
    pagination.py             # bounded, config-driven page URLs
    extract.py                # CSS-selector extraction (breadcrumb, badges…)
    discover.py                # suggests listing/price selectors + card anatomy
    price.py                  # EUR/LEK parsing + exact-1 placeholder filter
    privacy.py                # strips phone numbers / "call <Name>" from text
    config.py                 # YAML schema + loader (category==folder enforced)
    pipeline.py               # extract -> clean -> filter -> tag category -> dedup
    record.py                 # Listing (category is first-class)
    storage.py                # JSONL (always) + optional Postgres staging
    to_csv.py                  # JSONL -> CSV (Excel/Sheets-friendly)
    runner.py                 # CLI: list / robots / discover / inspect / run
  configs/<category>/*.yaml   # one file per site, grouped by category
  official_data_importers/    # ASK / INSTAT / fuel — public data, not scraping
  validation/benchmark_check.py  # outlier + official-index divergence checks
  promote.py                   # staging/JSONL -> live site tables (no scraping)
  tests/                      # offline tests + fixtures per site
```

## Install

```bash
cd scrapers
pip install -r requirements.txt

# Only if you'll run a JS-rendered config (js_rendered: true, e.g. barnatore):
pip install playwright
playwright install chromium

# Only if you'll use --dsn (push into Postgres/Supabase) or promote.py:
pip install "psycopg[binary]"
```

## Workflow (per site/category) — the required order

```bash
cd scrapers

# 1. See all configs and which are verified
python engine/runner.py list

# 2. Check robots.txt FIRST (respects Disallow + Crawl-delay)
python engine/runner.py robots merrjep_ks_cars

# 2b. New site? Let `discover` suggest the listing/price selectors for you
#     (works through JS-rendered pages too, if the config sets js_rendered: true).
python engine/runner.py discover gjirafamall_fragrances
#     (offline: analyze a page you saved from your browser)
python engine/runner.py discover --fixture saved_page.html

# 3. Test small: fetch 1-2 pages and eyeball 5-10 parsed rows. Stores nothing.
python engine/runner.py inspect merrjep_ks_cars --pages 1
#    (offline: parse a saved page instead of the network)
python engine/runner.py inspect merrjep_ks_cars --fixture tests/fixtures/merrjep_cars_sample.html

# 4. Only after the sample looks right, set `selectors_verified: true` in the
#    config, then run at scale. The benchmark check runs automatically, and a
#    downloadable .jsonl + .csv is ALWAYS written locally (see below), whether
#    or not you also push to a database.
python engine/runner.py run merrjep_ks_cars --pages 5
#    also push into Supabase/Postgres staging (in addition to the local file):
python engine/runner.py run merrjep_ks_cars --pages 5 --dsn "postgresql://…"

# 5. Get the scraped data onto your live website (no scraping involved — this
#    only moves data already on your machine into your own database):
python promote.py output/merrjep_ks_cars.jsonl --dsn "postgresql://…"
#    preview what it would do without writing anything:
python promote.py output/merrjep_ks_cars.jsonl --dsn "postgresql://…" --dry-run
```

### Where your scraped data ends up

Every `run` **always** writes a local, downloadable file — this happens
unconditionally, even if you also use `--dsn`:

```
scrapers/output/<config-id>.jsonl    # one JSON object per line, always written
scrapers/output/<config-id>.csv      # same data, flattened — open in Excel/Sheets
```

Skip the CSV with `--no-csv` if you only want the JSONL. To get the data onto
**gjejecmimin.com itself**, run `promote.py` against your Supabase connection
string afterward (step 5 above) — it reads whatever `.jsonl` file(s) you point
it at and writes into `canonical_products` + `price_observations`, the exact
tables the live site queries. It's safe to re-run on the same file (it won't
create duplicate prices — see "Idempotent" below) and it never talks to any
external website, only your own database.

**Gates that protect you**
- `run` refuses any config with `selectors_verified: false` (override:
  `--allow-unverified`, discouraged).
- `run` refuses any config with `tos_restricted: true` (override:
  `--acknowledge-tos-risk`, only after you've made the legal call yourself).
  `inspect`/`discover` print a loud warning but don't block — testing a couple
  pages and running production scraping are different risk profiles.
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

## Site legal status (live-checked)

| Site | robots.txt | ToS | Verdict |
|---|---|---|---|
| MerrJep (cars, car parts, real estate) | `Allow: /` | no anti-scraping language found | ✅ clear to build |
| online.vivafresh.shop (groceries) | clean, `Crawl-delay: 1` | none found | ✅ clear to build |
| GjirafaMall / Gjirafa50 (marketplace, electronics) | permissive | **explicitly bans bots/automated access + data-extraction tools**, company-wide | ⚠️ flagged — `tos_restricted: true`, `run` blocked without `--acknowledge-tos-risk` |
| Neptun-ks.com (electronics) | **`User-agent: ClaudeBot / Disallow: /`** (also GPTBot, CCBot, etc.) | — | ⛔ skip — direct signal against Claude-based access, honored in spirit regardless of this engine's own UA string |
| Indomio.al (AL real estate) | aggressive bot-blocklist (hundreds of named tools) | — | ⚠️ your call — not yet inspected further pending a decision |
| Barnatore Online (pharmacy) | clean | none found | ✅ clear to build, but **JS-rendered** (needs Playwright) |
| JYSK-ks.com (furniture) | no robots.txt file (ambiguous) | not checked | confirmed selectors available; category pages need drill-down into subcategories; Scandinavian price format (`"20,-"`) needs a parser tweak |

## Config status

| Config | Category | Verified | Notes |
|---|---|---|---|
| `merrjep_ks_cars` | cars | ✅ | live path `/shpallje/makina/vetura`; 4-link breadcrumb |
| `merrjep_ks_real_estate` | real_estate | ❌ (one `inspect` away) | live path `/shpallje/patundshmeri`; 2-link breadcrumb (type, city); rentals detected via `/ muaj` |
| `merrjep_ks_car_parts` | car_parts | ✅ | live path confirmed; 2-link breadcrumb (category, city) — most listings have no price (contact-only), which is expected |
| `vivafresh` | groceries | ❌ | selectors confirmed live; needs a real category start_path |
| `gjirafamall_fragrances` | fragrances_cosmetics | ❌ + ⚠️ ToS | fully wired from live `discover`; blocked by `tos_restricted` |
| `gjirafamall_clothing` | clothing | ❌ + ⚠️ ToS | real path /veshje; blocked by `tos_restricted` |
| `gjirafamall_furniture` | furniture | ❌ + ⚠️ ToS | confirm furniture listing slug; blocked by `tos_restricted` |
| `foleja_fragrances` | fragrances_cosmetics | ❌ | real path /Kozmetike-Kujdesi-Personal/Parfum/ — Foleja is a different company, not flagged |
| `gjirafa50` | electronics_tech | ❌ | selectors confirmed (`.product-item` / `a.product-title-lines` / `span.price.main`) but same Gjirafa ToS applies — flag before building further |
| `neptun_ks` | electronics_tech | ⛔ do not build | robots.txt disallows ClaudeBot specifically |
| `indomio_al` | real_estate | ❌ | aggressive anti-bot robots.txt — awaiting a decision before inspecting further |
| `barnatore` | pharmacy | ❌ | selectors confirmed live; **JS-rendered** (uses `browser_client.py` automatically); confirm `/shop` is the real listing path |

Every ❌ config ships with real URLs/category paths but placeholder selectors
(`REPLACE_ME`) — run `discover` on an open network to fill them, then `inspect`
to confirm and flip `selectors_verified: true`.

## Copy-paste commands per site (run from inside `scrapers/`)

```bash
# --- Cars (MerrJep) — already verified ---
python engine/runner.py run merrjep_ks_cars --pages 10

# --- Real estate (MerrJep) — one crawl gets every city + apartments/houses/land ---
python engine/runner.py inspect merrjep_ks_real_estate --pages 1   # confirm sample first
#   then set selectors_verified: true in the config, and:
python engine/runner.py run merrjep_ks_real_estate --pages 50

# --- Car parts (MerrJep) — already verified ---
python engine/runner.py run merrjep_ks_car_parts --pages 30

# --- Groceries (Viva Fresh) — needs a real category URL first ---
#   open online.vivafresh.shop in a browser, copy a real products/category URL,
#   paste it into configs/groceries/vivafresh.yaml under start_paths, then:
python engine/runner.py discover vivafresh
python engine/runner.py inspect vivafresh --pages 1

# --- Fragrances (Foleja) — different company, not ToS-flagged ---
python engine/runner.py robots foleja_fragrances
python engine/runner.py discover foleja_fragrances
python engine/runner.py inspect foleja_fragrances --pages 1

# --- Pharmacy (Barnatore) — JS-rendered, needs Playwright installed first ---
python engine/runner.py discover barnatore     # renders with headless Chromium
python engine/runner.py inspect barnatore --pages 1

# --- GjirafaMall / Gjirafa50 — ToS-flagged, read the warning before running ---
#   `inspect`/`discover` still work (they print a warning); `run` refuses
#   unless you've made your own call and pass --acknowledge-tos-risk:
python engine/runner.py run gjirafamall_fragrances --pages 5 --acknowledge-tos-risk
```

## Notes / limitations

- **JS-rendered sites** (`js_rendered: true`, e.g. Barnatore, Indomio) are
  handled automatically by `robots`/`discover`/`inspect`/`run` — they detect
  the flag and switch to `browser_client.py` (headless Chromium via
  Playwright) instead of plain `requests`, no extra flags needed. Requires
  `pip install playwright && playwright install chromium` first.
- **Legal:** always check robots.txt (built in) and each site's ToS for
  anti-scraping language before enabling a config; flag concerns rather than
  proceeding silently. Sites with a confirmed prohibition carry
  `tos_restricted: true` and are gated on `run` (see above).
- Selectors marked "verified" were verified against markup provided in the build
  brief / live inspection. Templates marked ❌ contain `REPLACE_ME` placeholders
  and must be filled from a real `inspect`/`discover` run.
- **`promote.py`** uses a simple slugify-based product matcher (title →
  canonical_name, diacritics stripped). Two different products that happen to
  share a title will collapse into one row — fine for MVP, but a smarter
  brand+model+unit-aware matcher is future work if that becomes a problem at
  scale.
```
