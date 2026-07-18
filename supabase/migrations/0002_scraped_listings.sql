-- =============================================================================
-- scraped_listings — staging table for the scraping pipeline
-- =============================================================================
-- Raw scraped rows land here first, with `category` as a first-class column
-- (build spec section 1) and full provenance. A separate normalization step
-- promotes clean, non-flagged rows into the serving tables the website reads
-- (canonical_products + price_observations), so real scraped data ends up in
-- exactly the same tables as the seed data.
--
-- De-dup key is (source, external_id) — the site's stable id, never the URL.
-- =============================================================================

create table if not exists scraped_listings (
  id                bigserial primary key,
  source            text not null,          -- config id, e.g. 'merrjep_ks_cars'
  category          text not null,          -- first-class: cars, real_estate, ...
  country           text not null,          -- 'XK' | 'AL'
  external_id       text not null,          -- site's stable id (de-dup)
  url               text,
  title             text,                   -- personal data already stripped
  price             numeric(14, 2),         -- null = no usable price (empty/placeholder)
  currency          text,
  city              text,
  region            text,
  attributes        jsonb not null default '{}'::jsonb,  -- brand/model, rooms/size, price_kind…
  is_dealer         boolean not null default false,
  is_trusted_seller boolean not null default false,
  trust_tier        trust_tier not null default 'verified_retailer',
  raw_source_text   text,
  review_flags      jsonb not null default '[]'::jsonb,  -- benchmark holds; non-empty = do not auto-publish
  scraped_at        timestamptz not null default now(),

  constraint scraped_listings_source_external_uniq unique (source, external_id)
);

create index if not exists scraped_listings_category_idx on scraped_listings (category);
create index if not exists scraped_listings_source_idx on scraped_listings (source);
create index if not exists scraped_listings_city_idx on scraped_listings (city);
create index if not exists scraped_listings_scraped_at_idx on scraped_listings (scraped_at desc);
-- Rows still awaiting manual review (benchmark flagged them).
create index if not exists scraped_listings_review_idx
  on scraped_listings ((jsonb_array_length(review_flags)))
  where jsonb_array_length(review_flags) > 0;

-- Not publicly readable: staging is internal. No RLS select policy => anon
-- cannot read it; the service role (ingestion) bypasses RLS.
alter table scraped_listings enable row level security;

comment on table scraped_listings is
  'Raw scraped rows (category first-class). Promote clean, unflagged rows into '
  'canonical_products + price_observations for serving.';
