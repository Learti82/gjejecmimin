import type { TrustTier } from "./types";

// Visual + ordering metadata for each trust tier. Language-neutral: the labels
// and descriptions live in the i18n dictionary (lib/i18n) keyed by tier, so the
// badge, legend, and grouping all stay consistent across languages.

export interface TrustTierMeta {
  tier: TrustTier;
  /** Higher = more authoritative. Used for ordering/grouping in the UI. */
  weight: number;
  /** Tailwind class fragments for the badge (bg / text / ring). */
  classes: string;
  dotClass: string;
}

export const TRUST_TIERS: Record<TrustTier, TrustTierMeta> = {
  official: {
    tier: "official",
    weight: 3,
    classes: "bg-official-bg text-official-fg ring-1 ring-official-ring",
    dotClass: "bg-official-fg",
  },
  verified_retailer: {
    tier: "verified_retailer",
    weight: 2,
    classes: "bg-verified-bg text-verified-fg ring-1 ring-verified-ring",
    dotClass: "bg-verified-fg",
  },
  crowdsourced: {
    tier: "crowdsourced",
    weight: 1,
    classes: "bg-crowd-bg text-crowd-fg ring-1 ring-crowd-ring",
    dotClass: "bg-crowd-fg",
  },
};

/** Tiers from most to least authoritative — handy for grouping sections. */
export const TRUST_TIERS_ORDERED: TrustTierMeta[] = Object.values(
  TRUST_TIERS,
).sort((a, b) => b.weight - a.weight);

export function trustMeta(tier: TrustTier): TrustTierMeta {
  return TRUST_TIERS[tier];
}
