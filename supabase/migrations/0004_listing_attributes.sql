-- =============================================================================
-- Listing attributes on price_observations — powers grouping, filtering, €/m²
-- =============================================================================
-- The MVP treated every scraped listing as its own product, so the serving
-- tables had no structured real-estate attributes to group or filter on. These
-- columns carry the facts needed for the comparison features:
--
--   listing_kind   'sale' | 'rent'   (rent = per month; from price_period)
--   property_type  'Banesa' | 'Shtëpi' | 'Truall/Tokë/...' (from the breadcrumb)
--   rooms          bedroom count parsed from the title ("2+1" -> 2), nullable
--   area_m2        size in m² parsed from the title ("65m²" -> 65), nullable
--
-- price_per_m2 is derived (price / area_m2) in queries, not stored, so it stays
-- correct if either value is later corrected. All nullable — non-real-estate
-- rows simply leave them null.
-- =============================================================================

alter table price_observations
  add column if not exists listing_kind  text,
  add column if not exists property_type text,
  add column if not exists rooms         integer,
  add column if not exists area_m2       numeric(10, 2);

-- Grouping/filtering index for the real-estate comparison views: the common
-- query is "rows for a (property_type, city, listing_kind[, rooms])".
create index if not exists price_observations_re_group_idx
  on price_observations (property_type, geo_city, listing_kind, rooms)
  where property_type is not null;

-- ---------------------------------------------------------------------------
-- real_estate_groups — the comparison view
-- ---------------------------------------------------------------------------
-- Collapses individual real-estate listings into comparable groups
-- (property type + city + sale/rent + bedroom count) and returns price
-- statistics per group: how many listings, min / average / median / max, and
-- the average €/m². This is what turns "340 separate apartment listings" into
-- "2-bedroom apartments in Prishtinë — avg €121k across 340 listings".
--
-- All filter params are optional (null = no filter). Groups with fewer than
-- `p_min_listings` listings are excluded so averages are meaningful.
create or replace function real_estate_groups(
  p_city          text    default null,
  p_kind          text    default null,   -- 'sale' | 'rent'
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
    property_type,
    geo_city as city,
    listing_kind,
    rooms,
    count(*)                                                          as listings,
    min(price)                                                       as min_price,
    round(avg(price), 2)                                             as avg_price,
    round(percentile_cont(0.5) within group (order by price)::numeric, 2) as median_price,
    max(price)                                                       as max_price,
    round(avg(price / nullif(area_m2, 0))
          filter (where area_m2 is not null), 2)                     as avg_price_per_m2,
    max(currency)                                                    as currency
  from price_observations
  where property_type is not null
    and (p_city is null          or geo_city = p_city)
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
    and (p_min_price is null     or price >= p_min_price)
    and (p_max_price is null     or price <= p_max_price)
  group by property_type, geo_city, listing_kind, rooms
  having count(*) >= p_min_listings
  order by listings desc;
$$;

-- Distinct cities that actually have real-estate data, for the filter dropdown.
create or replace function real_estate_cities()
returns table (city text, listings bigint)
language sql
stable
as $$
  select geo_city, count(*)
  from price_observations
  where property_type is not null and geo_city is not null
  group by geo_city
  order by count(*) desc;
$$;
