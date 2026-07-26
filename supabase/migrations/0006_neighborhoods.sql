-- =============================================================================
-- Neighborhood-level aggregation — one average per area, not a listing dump
-- =============================================================================
-- The product direction: show clean averages per area (neighborhood/street),
-- e.g. "apartments in Dragodan, Prishtinë — €2,100/m²", instead of thousands
-- of individual listings. MerrJep cards only carry the city, but the title
-- often names the neighborhood ("Banesë në Arbëri (Dragodan)"), so promote.py
-- parses it (analysis/neighborhoods.py) into this column.
-- =============================================================================

alter table price_observations
  add column if not exists neighborhood text;

create index if not exists price_observations_neighborhood_idx
  on price_observations (geo_city, neighborhood)
  where neighborhood is not null;

-- Per-neighborhood averages for one city: the "one row per area" view.
-- Land has no m², so avg_price_per_m2 is null there — the UI shows total price
-- for land and €/m² for apartments/houses.
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
    round(avg(price / nullif(area_m2, 0)) filter (where area_m2 is not null), 2)
  from price_observations
  where property_type is not null
    and geo_city = p_city
    and (p_kind is null          or listing_kind = p_kind)
    and (p_property_type is null or property_type = p_property_type)
  group by neighborhood
  order by count(*) desc;
$$;
