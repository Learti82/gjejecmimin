# gjejeçmimin — price comparison platform (MVP)

Search products, compare prices across stores in **Kosovo & Albania**, and see
every price labelled by **how much you can trust it**. This is the MVP: the
database is populated with realistic **seed/mock data**, structured so that a
later scraping/ingestion pipeline can drop **real** rows into the exact same
tables with zero code changes.

- **Stack:** Next.js (App Router) + TypeScript, Tailwind CSS, Supabase (Postgres)
- **No AI/LLM component** — this stage is purely database + search + trust-tier UI.

## Trust tiers

Every price is a row in `price_observations` tagged with a `trust_tier`:

| Tier                | Meaning                                                        | Badge   |
| ------------------- | ------------------------------------------------------------- | ------- |
| `official`          | Official statistics body (ASK, INSTAT, BQK). Reference price. | blue    |
| `verified_retailer` | Known, registered retailer. Reliable single-shop price.       | green   |
| `crowdsourced`      | User-submitted, not yet corroborated. Indicative.             | amber   |

Provenance is captured by data (`trust_tier` + `source_id` + `confidence_score`),
never by which table a row lives in. Mock and real data are indistinguishable to
the app.

## Data model

`supabase/migrations/0001_init.sql` creates:

- **`canonical_products`** — the deduplicated "one product" many listings map to.
- **`price_observations`** — the fact table: one price, one product, one store,
  one point in time. Every ingestion path (official / scraped / crowdsourced)
  writes here. This is what the UI reads.
- **`stores`** — retailers; `arbk_registration_id` (Kosovo business registry) is
  nullable, `verified` drives the verified-retailer tier.
- **`official_indices`** — CPI-style index values per source/category/period.
- **`user_submissions`** — raw crowdsourced prices before verification.
- **`user_reputation`** — per-user trust used to weight crowdsourced prices.

Plus a `search_products(q, category_filter, max_results)` SQL function using
`pg_trgm` fuzzy matching with an ILIKE fallback, and public-read RLS policies.

## Pages

- **`/`** — landing + search box + category chips + trust legend.
- **`/search?q=…&category=…`** — matching `canonical_products`, cheapest-from price.
- **`/product/[id]`** — all observations for a product, **grouped and badged by
  trust tier**, each with store, city, price, and "last verified" timestamp;
  cheapest highlighted; official indices shown as context.
- **`/compare?product=[id]`** — side-by-side latest price per store, **cheapest
  highlighted**.

## Getting started (local)

Requires [Node 18+](https://nodejs.org) and the
[Supabase CLI](https://supabase.com/docs/guides/cli).

```bash
# 1. Install deps
npm install

# 2. Boot local Supabase (Postgres + API + Studio)
supabase start

# 3. Apply migrations + seed data
supabase db reset      # runs migrations/, then seed.sql

# 4. Configure env
cp .env.example .env.local
#    fill NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY
#    with the values `supabase start` printed

# 5. Run the app
npm run dev            # http://localhost:3000
```

If the env vars aren't set, the app renders a friendly setup notice instead of
crashing.

### Scripts

| Command             | What it does                                  |
| ------------------- | --------------------------------------------- |
| `npm run dev`       | Next dev server                               |
| `npm run build`     | Production build                              |
| `npm run typecheck` | `tsc --noEmit`                                |
| `npm run db:seed`   | `supabase db reset` (migrations + seed)       |
| `npm run db:push`   | Push migrations to a linked hosted project    |

## Swapping in real data later

The scraping pipeline should:

1. Upsert retailers into **`stores`** (set `verified` appropriately).
2. Map raw listings to a **`canonical_products`** row (by `canonical_name`).
3. Insert one **`price_observations`** row per observed price, setting
   `trust_tier`, `source_id`, `confidence_score`, `raw_source_text`, and geo.

No schema or UI change is required — real rows render through the same tiered UI
as the seed data. The seed's `truncate … cascade` at the top of `seed.sql` means
it only affects local/dev resets; production ingestion just inserts.
