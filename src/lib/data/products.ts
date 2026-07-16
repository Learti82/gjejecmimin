import "server-only";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import type {
  CanonicalProduct,
  OfficialIndex,
  PriceObservationWithStore,
  ProductSearchResult,
  Store,
} from "@/lib/types";

// -----------------------------------------------------------------------------
// Data-access layer.
//
// Every query in the app goes through these functions. They read from the exact
// tables an ingestion pipeline writes to — there is no mock branch here, so
// swapping seed data for real scraped data requires zero code changes. The only
// thing that differs between "MVP with seed data" and "production" is the rows
// in Postgres.
// -----------------------------------------------------------------------------

/**
 * Fuzzy product search backed by the `search_products` SQL function
 * (trigram similarity + ILIKE fallback). Empty query returns the catalog.
 */
export async function searchProducts(
  query: string,
  options: { category?: string | null; limit?: number } = {},
): Promise<ProductSearchResult[]> {
  const { category = null, limit = 30 } = options;
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.rpc("search_products", {
    q: query.trim(),
    category_filter: category,
    max_results: limit,
  });

  if (error) {
    throw new Error(`searchProducts failed: ${error.message}`);
  }

  return (data ?? []).map((row: ProductSearchResult) => ({
    ...row,
    // Postgres numerics arrive as strings over the wire; normalize to numbers.
    observation_count: Number(row.observation_count ?? 0),
    min_price: row.min_price === null ? null : Number(row.min_price),
    rank: Number(row.rank ?? 0),
  }));
}

/** A single canonical product by id, or null if not found. */
export async function getProduct(
  id: string,
): Promise<CanonicalProduct | null> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("canonical_products")
    .select("*")
    .eq("id", id)
    .maybeSingle();

  if (error) throw new Error(`getProduct failed: ${error.message}`);
  return data as CanonicalProduct | null;
}

/**
 * All price observations for a product, newest first, with the store joined in.
 * Used by the product detail and compare views. Numerics are normalized to JS
 * numbers so callers never deal with string coercion.
 */
export async function getObservationsForProduct(
  productId: string,
): Promise<PriceObservationWithStore[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("price_observations")
    .select("*, store:stores(*)")
    .eq("product_id", productId)
    .order("observed_at", { ascending: false });

  if (error) {
    throw new Error(`getObservationsForProduct failed: ${error.message}`);
  }

  return (data ?? []).map((row: PriceObservationWithStore) => ({
    ...row,
    price: Number(row.price),
    confidence_score:
      row.confidence_score === null ? null : Number(row.confidence_score),
    store: (row.store as Store | null) ?? null,
  }));
}

/** Official index rows for a category (authoritative reference context). */
export async function getOfficialIndicesForCategory(
  category: string,
): Promise<OfficialIndex[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("official_indices")
    .select("*")
    .eq("category", category)
    .order("period", { ascending: false });

  if (error) {
    throw new Error(`getOfficialIndicesForCategory failed: ${error.message}`);
  }

  return (data ?? []).map((row: OfficialIndex) => ({
    ...row,
    value: Number(row.value),
  }));
}

/** Distinct category slugs present in the catalog, for the browse chips. */
export async function getCategories(): Promise<string[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("canonical_products")
    .select("category");

  if (error) throw new Error(`getCategories failed: ${error.message}`);

  const set = new Set<string>();
  for (const row of data ?? []) {
    if (row.category) set.add(row.category as string);
  }
  return Array.from(set).sort();
}
