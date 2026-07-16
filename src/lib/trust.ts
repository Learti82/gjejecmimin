import type { TrustTier } from "./types";

// Single source of truth for how each trust tier is labelled, described, and
// coloured across the UI. Keeping this here means the badge, legend, and any
// future weighting logic all agree on tier semantics.

export interface TrustTierMeta {
  tier: TrustTier;
  label: string;
  short: string;
  description: string;
  /** Higher = more authoritative. Used for ordering/grouping in the UI. */
  weight: number;
  /** Tailwind class fragments for the badge (bg / text / ring). */
  classes: string;
  dotClass: string;
}

export const TRUST_TIERS: Record<TrustTier, TrustTierMeta> = {
  official: {
    tier: "official",
    label: "Official source",
    short: "Official",
    description:
      "From an official statistics body (ASK, INSTAT, BQK). Authoritative reference price.",
    weight: 3,
    classes: "bg-official-bg text-official-fg ring-1 ring-official-ring",
    dotClass: "bg-official-fg",
  },
  verified_retailer: {
    tier: "verified_retailer",
    label: "Verified retailer",
    short: "Verified",
    description:
      "Collected from a known, registered retailer. Reliable but a single shop's shelf price.",
    weight: 2,
    classes: "bg-verified-bg text-verified-fg ring-1 ring-verified-ring",
    dotClass: "bg-verified-fg",
  },
  crowdsourced: {
    tier: "crowdsourced",
    label: "Crowdsourced",
    short: "Crowd",
    description:
      "Submitted by users and not yet corroborated. Treat as an indicative price.",
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
