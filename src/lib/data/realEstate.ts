import "server-only";
import { getSupabaseServerClient } from "@/lib/supabase/server";

// Data access for the real-estate comparison view (grouped stats). Backed by
// the real_estate_groups / real_estate_cities SQL functions (migration 0004).

export interface RealEstateGroup {
  property_type: string;
  city: string | null;
  listing_kind: string | null; // 'sale' | 'rent'
  rooms: number | null;
  listings: number;
  min_price: number;
  avg_price: number;
  median_price: number;
  max_price: number;
  avg_price_per_m2: number | null;
  currency: string;
}

export interface RealEstateFilters {
  city?: string | null;
  kind?: string | null; // 'sale' | 'rent'
  propertyType?: string | null;
  minPrice?: number | null;
  maxPrice?: number | null;
  minListings?: number;
}

function num(v: unknown): number {
  return v === null || v === undefined ? 0 : Number(v);
}

export async function getRealEstateGroups(
  filters: RealEstateFilters = {},
): Promise<RealEstateGroup[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.rpc("real_estate_groups", {
    p_city: filters.city ?? null,
    p_kind: filters.kind ?? null,
    p_property_type: filters.propertyType ?? null,
    p_min_price: filters.minPrice ?? null,
    p_max_price: filters.maxPrice ?? null,
    p_min_listings: filters.minListings ?? 1,
  });
  if (error) throw new Error(`getRealEstateGroups failed: ${error.message}`);
  return (data ?? []).map((r: RealEstateGroup) => ({
    ...r,
    rooms: r.rooms === null ? null : Number(r.rooms),
    listings: num(r.listings),
    min_price: num(r.min_price),
    avg_price: num(r.avg_price),
    median_price: num(r.median_price),
    max_price: num(r.max_price),
    avg_price_per_m2:
      r.avg_price_per_m2 === null ? null : num(r.avg_price_per_m2),
  }));
}

export interface CityCount {
  city: string;
  listings: number;
}

export async function getRealEstateCities(): Promise<CityCount[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.rpc("real_estate_cities");
  if (error) throw new Error(`getRealEstateCities failed: ${error.message}`);
  return (data ?? []).map((r: { city: string; listings: number }) => ({
    city: r.city,
    listings: num(r.listings),
  }));
}

export interface CityStat {
  city: string;
  listings: number;
  avg_price: number;
  median_price: number;
}

export async function getRealEstateCityStats(
  kind: string = "sale",
  propertyType: string | null = null,
): Promise<CityStat[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.rpc("real_estate_city_stats", {
    p_kind: kind,
    p_property_type: propertyType,
  });
  if (error) throw new Error(`getRealEstateCityStats failed: ${error.message}`);
  return (data ?? []).map((r: CityStat) => ({
    city: r.city,
    listings: num(r.listings),
    avg_price: num(r.avg_price),
    median_price: num(r.median_price),
  }));
}

export interface NeighborhoodStat {
  neighborhood: string | null;
  listings: number;
  avg_price: number;
  median_price: number;
  avg_price_per_m2: number | null;
}

export async function getRealEstateNeighborhoods(
  city: string,
  kind: string = "sale",
  propertyType: string | null = null,
): Promise<NeighborhoodStat[]> {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.rpc("real_estate_neighborhoods", {
    p_city: city,
    p_kind: kind,
    p_property_type: propertyType,
  });
  if (error)
    throw new Error(`getRealEstateNeighborhoods failed: ${error.message}`);
  return (data ?? []).map((r: NeighborhoodStat) => ({
    neighborhood: r.neighborhood,
    listings: num(r.listings),
    avg_price: num(r.avg_price),
    median_price: num(r.median_price),
    avg_price_per_m2:
      r.avg_price_per_m2 === null ? null : num(r.avg_price_per_m2),
  }));
}
