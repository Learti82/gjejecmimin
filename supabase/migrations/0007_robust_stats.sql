-- =============================================================================
-- Robust, comparable price statistics — median €/m², outlier-resistant
-- =============================================================================
-- The mean is wrecked by a single absurd listing (a whole building, a typo),
-- and total price isn't comparable across property sizes/types. So:
--   * the MAP now colours by MEDIAN €/m² (median ignores outliers; €/m²
--     normalizes for size) — which correctly ranks Prishtinë highest.
--   * every €/m² figure is sanity-bounded to [100, 10000] €/m², outside which
--     it's a data error (wrong size or wrong price), not a real price.
-- No data reload needed — this only redefines functions.
-- =============================================================================

-- city stats gains median_ppm2 (the map's colouring metric) -> signature
-- changes, so drop + recreate.
drop function if exists real_estate_city_stats(text, text);

create function real_estate_city_stats(
  p_kind          text default 'sale',
  p_property_type text default null
)
returns table (
  city         text,
  listings     bigint,
  avg_price    numeric,
  median_price numeric,
  median_ppm2  numeric   -- median €/m² — the robust, comparable metric
)
language sql
stable
as $$
  select
    geo_city,
    count(*),
    round(avg(price), 2),
    round(percentile_cont(0.5) within group (order by price)::numeric, 2),
    round(
      percentile_cont(0.5) within group (order by price / area_m2)
        filter (where area_m2 is not null and price / area_m2 between 100 and 10000)
      ::numeric, 2)
  from price_observations
  where property_type is not null
    and geo_city is not null
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
  group by geo_city;
$$;

-- groups: keep the same columns (avg_price_per_m2), just make the €/m² robust
-- (median + sanity bound) instead of a raw mean.
create or replace function real_estate_groups(
  p_city          text    default null,
  p_kind          text    default null,
  p_property_type text    default null,
  p_min_price     numeric default null,
  p_max_price     numeric default null,
  p_min_listings  int     default 1
)
returns table (
  property_type    text,
  city             text,
  listing_kind     text,
  rooms            integer,
  listings         bigint,
  min_price        numeric,
  avg_price        numeric,
  median_price     numeric,
  max_price        numeric,
  avg_price_per_m2 numeric,
  currency         text
)
language sql
stable
as $$
  select
    property_type, geo_city, listing_kind, rooms,
    count(*), min(price), round(avg(price), 2),
    round(percentile_cont(0.5) within group (order by price)::numeric, 2),
    max(price),
    round(
      percentile_cont(0.5) within group (order by price / area_m2)
        filter (where area_m2 is not null and price / area_m2 between 100 and 10000)
      ::numeric, 2),
    max(currency)
  from price_observations
  where property_type is not null
    and (p_city is null          or geo_city = p_city)
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
    and (p_min_price is null     or price >= p_min_price)
    and (p_max_price is null     or price <= p_max_price)
  group by property_type, geo_city, listing_kind, rooms
  having count(*) >= p_min_listings
  order by count(*) desc;
$$;

-- neighborhoods: same robustness for the per-area €/m².
create or replace function real_estate_neighborhoods(
  p_city          text,
  p_kind          text default 'sale',
  p_property_type text default null
)
returns table (
  neighborhood     text,
  listings         bigint,
  avg_price        numeric,
  median_price     numeric,
  avg_price_per_m2 numeric
)
language sql
stable
as $$
  select
    neighborhood,
    count(*),
    round(avg(price), 2),
    round(percentile_cont(0.5) within group (order by price)::numeric, 2),
    round(
      percentile_cont(0.5) within group (order by price / area_m2)
        filter (where area_m2 is not null and price / area_m2 between 100 and 10000)
      ::numeric, 2)
  from price_observations
  where property_type is not null
    and geo_city = p_city
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
  group by neighborhood
  order by count(*) desc;
$$;
