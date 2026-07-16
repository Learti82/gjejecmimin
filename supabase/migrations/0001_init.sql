-- =============================================================================
-- gjejecmimin — core schema
-- =============================================================================
-- Price-comparison platform for Kosovo & Albania.
--
-- The tables below are the single landing zone for price data regardless of
-- provenance: an official statistics index, a scraper hitting a verified
-- retailer, or a photo a user snapped in a shop all become rows in the SAME
-- tables. Provenance is captured by `trust_tier` + `source_id` + a confidence
-- score, never by which table the row lives in. The MVP seeds these tables with
-- mock rows; a later ingestion pipeline inserts real rows with no schema change.
-- =============================================================================

create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "pg_trgm";     -- trigram fuzzy product search

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

-- How much we trust a given price point. Ordered from most to least
-- authoritative; the UI renders a distinct badge per tier.
create type trust_tier as enum (
  'official',            -- from an official statistics body / index
  'verified_retailer',   -- scraped/fed from a known, registered retailer
  'crowdsourced'         -- submitted by users, not yet corroborated
);

-- Official statistics sources relevant to the region.
create type official_source as enum (
  'ASK',    -- Agjencia e Statistikave të Kosovës (Kosovo Agency of Statistics)
  'INSTAT', -- Instituti i Statistikave (Albania)
  'BQK'     -- Banka Qendrore e Republikës së Kosovës (Central Bank of Kosovo)
);

-- Lifecycle of a user-submitted price.
create type submission_status as enum (
  'pending',
  'verified',
  'rejected'
);

-- ---------------------------------------------------------------------------
-- stores
-- ---------------------------------------------------------------------------
-- A physical or online retailer. `arbk_registration_id` is the Kosovo business
-- registration number (Agjencia e Regjistrimit të Bizneseve në Kosovë); nullable
-- because crowdsourced / informal sellers may not be registered.
create table stores (
  id                   uuid primary key default gen_random_uuid(),
  name                 text        not null,
  arbk_registration_id text,                       -- nullable, see above
  category             text,                        -- e.g. 'supermarket', 'electronics'
  city                 text,
  verified             boolean     not null default false,
  created_at           timestamptz not null default now()
);

create index stores_name_trgm_idx on stores using gin (name gin_trgm_ops);
create index stores_city_idx on stores (city);

-- ---------------------------------------------------------------------------
-- canonical_products
-- ---------------------------------------------------------------------------
-- The deduplicated "one product" that many raw listings map to. `name` is the
-- human display name; `canonical_name` is a normalized key used to collapse
-- scraper variants ("Coca Cola 1.5L", "coca-cola 1,5 l") onto one product.
create table canonical_products (
  id             uuid primary key default gen_random_uuid(),
  name           text        not null,
  canonical_name text        not null,
  category       text        not null,
  brand          text,
  unit           text,                              -- e.g. '1.5L', '500g', 'each'
  created_at     timestamptz not null default now()
);

create unique index canonical_products_canonical_name_key
  on canonical_products (canonical_name);
create index canonical_products_category_idx on canonical_products (category);
create index canonical_products_name_trgm_idx
  on canonical_products using gin (name gin_trgm_ops);
create index canonical_products_canonical_trgm_idx
  on canonical_products using gin (canonical_name gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- price_observations
-- ---------------------------------------------------------------------------
-- One observed price for one product at one store at one point in time. This is
-- the fact table the whole product/compare UI reads from. Every ingestion path
-- (official index, retailer scrape, crowdsource) writes here.
create table price_observations (
  id               uuid primary key default gen_random_uuid(),
  product_id       uuid        not null references canonical_products (id) on delete cascade,
  store_id         uuid        references stores (id) on delete set null,
  price            numeric(12, 2) not null check (price >= 0),
  currency         text        not null default 'EUR',
  observed_at      timestamptz not null default now(),
  trust_tier       trust_tier  not null,
  source_id        text,                            -- opaque id from the upstream source/scraper
  geo_city         text,
  geo_region       text,
  raw_source_text  text,                            -- original unparsed listing text, for audit
  confidence_score numeric(4, 3) check (confidence_score is null
                                        or (confidence_score >= 0 and confidence_score <= 1)),
  created_at       timestamptz not null default now()
);

create index price_observations_product_idx on price_observations (product_id);
create index price_observations_store_idx on price_observations (store_id);
create index price_observations_trust_tier_idx on price_observations (trust_tier);
create index price_observations_observed_at_idx on price_observations (observed_at desc);
-- Fast "latest price per product/store" lookups.
create index price_observations_product_observed_idx
  on price_observations (product_id, observed_at desc);

-- ---------------------------------------------------------------------------
-- official_indices
-- ---------------------------------------------------------------------------
-- Official statistical index values (CPI-style) per category and period. Used
-- as an authoritative reference point alongside observed retail prices.
create table official_indices (
  id         uuid primary key default gen_random_uuid(),
  source     official_source not null,
  category   text            not null,
  period     text            not null,             -- e.g. '2026-Q2' or '2026-06'
  value      numeric(12, 3)  not null,
  unit       text,                                  -- e.g. 'index', 'EUR', '%'
  created_at timestamptz     not null default now()
);

create unique index official_indices_source_cat_period_key
  on official_indices (source, category, period);

-- ---------------------------------------------------------------------------
-- user_submissions
-- ---------------------------------------------------------------------------
-- A raw crowdsourced price before it becomes a corroborated observation. A
-- moderation/verification step promotes 'verified' submissions into
-- price_observations (that promotion is a later pipeline concern, not the MVP).
create table user_submissions (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid        not null,
  product_id   uuid        references canonical_products (id) on delete set null,
  store_id     uuid        references stores (id) on delete set null,
  price        numeric(12, 2) not null check (price >= 0),
  photo_url    text,
  status       submission_status not null default 'pending',
  submitted_at timestamptz not null default now()
);

create index user_submissions_status_idx on user_submissions (status);
create index user_submissions_user_idx on user_submissions (user_id);
create index user_submissions_product_idx on user_submissions (product_id);

-- ---------------------------------------------------------------------------
-- user_reputation
-- ---------------------------------------------------------------------------
-- Aggregate trust for a submitting user, used to weight crowdsourced prices.
create table user_reputation (
  user_id         uuid primary key,
  confirmed_count integer     not null default 0,
  rejected_count  integer     not null default 0,
  trust_score     numeric(4, 3) not null default 0
                    check (trust_score >= 0 and trust_score <= 1),
  updated_at      timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Search helper
-- ---------------------------------------------------------------------------
-- Fuzzy product search used by the search page. Ranks by trigram similarity and
-- falls back to substring (ILIKE) matches so short queries still return results.
-- Returns a lightweight row plus a live count/min of current observations so the
-- results list can show "from €X across N prices" without a second round-trip.
create or replace function search_products(
  q text,
  category_filter text default null,
  max_results int default 30
)
returns table (
  id             uuid,
  name           text,
  canonical_name text,
  category       text,
  brand          text,
  unit           text,
  observation_count bigint,
  min_price      numeric,
  currency       text,
  rank           real
)
language sql
stable
as $$
  select
    p.id,
    p.name,
    p.canonical_name,
    p.category,
    p.brand,
    p.unit,
    count(o.id)                                   as observation_count,
    min(o.price)                                  as min_price,
    max(o.currency)                               as currency,
    case
      when q = '' then 0::real
      else greatest(similarity(p.name, q), similarity(p.canonical_name, q))
    end                                           as rank
  from canonical_products p
  left join price_observations o on o.product_id = p.id
  where
    (category_filter is null or p.category = category_filter)
    and (
      q = ''
      or p.name ilike '%' || q || '%'
      or p.canonical_name ilike '%' || q || '%'
      or p.brand ilike '%' || q || '%'
      or p.name % q
      or p.canonical_name % q
    )
  group by p.id
  order by rank desc, observation_count desc, p.name asc
  limit max_results;
$$;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
-- The public catalog is world-readable (anon key). Writes are reserved for
-- privileged roles (service role / authenticated flows added later), so the
-- MVP web app reads freely while ingestion happens out-of-band.
alter table stores               enable row level security;
alter table canonical_products   enable row level security;
alter table price_observations   enable row level security;
alter table official_indices     enable row level security;
alter table user_submissions     enable row level security;
alter table user_reputation      enable row level security;

create policy "public read stores"
  on stores for select using (true);
create policy "public read canonical_products"
  on canonical_products for select using (true);
create policy "public read price_observations"
  on price_observations for select using (true);
create policy "public read official_indices"
  on official_indices for select using (true);

-- Submissions & reputation are not publicly readable in the MVP; add
-- per-user policies when auth is wired up. (No select policy => deny by default
-- for anon, service role bypasses RLS.)
