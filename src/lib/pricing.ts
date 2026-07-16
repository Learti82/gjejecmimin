import type {
  PriceObservationWithStore,
  TrustTier,
} from "./types";
import { TRUST_TIERS_ORDERED } from "./trust";

// Pure aggregation helpers over a product's observations. No I/O — these take
// already-fetched rows so they're trivially testable and reusable by both the
// detail and compare views.

export interface TierGroup {
  tier: TrustTier;
  observations: PriceObservationWithStore[];
}

/** Group observations by trust tier, in authority order (official first). */
export function groupByTier(
  observations: PriceObservationWithStore[],
): TierGroup[] {
  return TRUST_TIERS_ORDERED.map((meta) => ({
    tier: meta.tier,
    observations: observations
      .filter((o) => o.trust_tier === meta.tier)
      .sort((a, b) => a.price - b.price),
  })).filter((g) => g.observations.length > 0);
}

export interface PriceStats {
  count: number;
  min: number | null;
  max: number | null;
  currency: string;
  cheapest: PriceObservationWithStore | null;
}

export function priceStats(
  observations: PriceObservationWithStore[],
): PriceStats {
  if (observations.length === 0) {
    return { count: 0, min: null, max: null, currency: "EUR", cheapest: null };
  }
  let cheapest = observations[0];
  for (const o of observations) {
    if (o.price < cheapest.price) cheapest = o;
  }
  const prices = observations.map((o) => o.price);
  return {
    count: observations.length,
    min: Math.min(...prices),
    max: Math.max(...prices),
    currency: observations[0].currency ?? "EUR",
    cheapest,
  };
}

/**
 * One row per store for the compare view: the most recent observation from each
 * store (official-tier rows, which have no store, are grouped under a synthetic
 * "Official reference" bucket keyed by source_id). Sorted cheapest first.
 */
export interface CompareRow {
  key: string;
  storeName: string;
  city: string | null;
  verified: boolean;
  observation: PriceObservationWithStore;
}

export function toCompareRows(
  observations: PriceObservationWithStore[],
): CompareRow[] {
  const latestByKey = new Map<string, PriceObservationWithStore>();

  for (const o of observations) {
    // Group by store when present; otherwise by the official source id so
    // multiple official references don't collapse into one row.
    const key = o.store_id ?? `official:${o.source_id ?? o.id}`;
    const existing = latestByKey.get(key);
    if (
      !existing ||
      new Date(o.observed_at).getTime() >
        new Date(existing.observed_at).getTime()
    ) {
      latestByKey.set(key, o);
    }
  }

  const rows: CompareRow[] = Array.from(latestByKey.entries()).map(
    ([key, observation]) => ({
      key,
      storeName:
        observation.store?.name ??
        (observation.trust_tier === "official"
          ? "Official reference"
          : "Unknown store"),
      city: observation.store?.city ?? observation.geo_city ?? null,
      verified: observation.store?.verified ?? false,
      observation,
    }),
  );

  return rows.sort((a, b) => a.observation.price - b.observation.price);
}
