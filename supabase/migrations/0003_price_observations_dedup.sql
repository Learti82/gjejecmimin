-- =============================================================================
-- price_observations dedup — supports promote.py's idempotent inserts
-- =============================================================================
-- The scraper -> promote.py pipeline writes one price_observations row per
-- (source config, external listing id) per scrape run. Re-running promote.py
-- on the SAME output file (e.g. re-processing after a crash) must not create
-- duplicate rows; a genuinely NEW scrape (different observed_at) must still
-- insert a fresh observation — prices change over time and that's the point of
-- this being a fact/observation table, not a snapshot.
--
-- source_id encodes "<config id>:<external id>" (e.g.
-- "merrjep_ks_real_estate:998877"), so (source_id, observed_at) uniquely
-- identifies one observation from one scrape run. Partial index (source_id is
-- not null) so hand-seeded rows with a null source_id are never constrained by
-- this — seed.sql's rows already carry distinct source_id values regardless.
-- =============================================================================

create unique index if not exists price_observations_source_observed_uniq
  on price_observations (source_id, observed_at)
  where source_id is not null;
