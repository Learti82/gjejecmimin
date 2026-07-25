-- =============================================================================
-- real_estate_city_stats — per-municipality averages for the map choropleth
-- =============================================================================
-- The clickable Kosovo map colours each municipality by its average real-estate
-- price. Sale and rent prices are on completely different scales, so this is
-- always computed for a single `p_kind` (defaults to 'sale'). Optional property
-- type filter so the map can show e.g. "average apartment sale price by city".
-- =============================================================================

create or replace function real_estate_city_stats(
  p_kind          text default 'sale',
  p_property_type text default null
)
returns table (
  city         text,
  listings     bigint,
  avg_price    numeric,
  median_price numeric
)
language sql
stable
as $$
  select
    geo_city,
    count(*),
    round(avg(price), 2),
    round(percentile_cont(0.5) within group (order by price)::numeric, 2)
  from price_observations
  where property_type is not null
    and geo_city is not null
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
  group by geo_city;
$$;
