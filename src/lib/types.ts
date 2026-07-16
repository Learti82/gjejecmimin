// Domain types shared across the app. These mirror the database schema exactly,
// so the same shapes describe seed rows today and real scraped rows later.

export type TrustTier = "official" | "verified_retailer" | "crowdsourced";

export type OfficialSource = "ASK" | "INSTAT" | "BQK";

export type SubmissionStatus = "pending" | "verified" | "rejected";

export type Category = string; // 'groceries' | 'electronics' | 'car_parts' | ...

export interface Store {
  id: string;
  name: string;
  arbk_registration_id: string | null;
  category: string | null;
  city: string | null;
  verified: boolean;
  created_at: string;
}

export interface CanonicalProduct {
  id: string;
  name: string;
  canonical_name: string;
  category: string;
  brand: string | null;
  unit: string | null;
  created_at: string;
}

export interface PriceObservation {
  id: string;
  product_id: string;
  store_id: string | null;
  price: number;
  currency: string;
  observed_at: string;
  trust_tier: TrustTier;
  source_id: string | null;
  geo_city: string | null;
  geo_region: string | null;
  raw_source_text: string | null;
  confidence_score: number | null;
  created_at: string;
}

/** A price observation with its store joined in (store may be null for official-tier rows). */
export interface PriceObservationWithStore extends PriceObservation {
  store: Store | null;
}

export interface OfficialIndex {
  id: string;
  source: OfficialSource;
  category: string;
  period: string;
  value: number;
  unit: string | null;
  created_at: string;
}

/** Row returned by the `search_products` SQL function. */
export interface ProductSearchResult {
  id: string;
  name: string;
  canonical_name: string;
  category: string;
  brand: string | null;
  unit: string | null;
  observation_count: number;
  min_price: number | null;
  currency: string | null;
  rank: number;
}
