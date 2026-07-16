import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { CategoryChips } from "@/components/CategoryChips";
import { TrustLegend } from "@/components/TrustLegend";
import { ProductResultCard } from "@/components/ProductResultCard";
import { SetupNotice } from "@/components/SetupNotice";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import { getCategories, searchProducts } from "@/lib/data/products";
import type { ProductSearchResult } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const configured = isSupabaseConfigured();

  let categories: string[] = [];
  let featured: ProductSearchResult[] = [];
  let error: string | null = null;

  if (configured) {
    try {
      [categories, featured] = await Promise.all([
        getCategories(),
        searchProducts("", { limit: 6 }),
      ]);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  return (
    <div className="space-y-10">
      <section className="space-y-5 pt-4 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Know the real price before you buy
        </h1>
        <p className="mx-auto max-w-2xl text-slate-600">
          Compare prices across stores in Kosovo &amp; Albania. Every price is
          labelled by how much you can trust it — official statistics, verified
          retailers, or the crowd.
        </p>
        <div className="mx-auto max-w-2xl">
          <SearchBar autoFocus />
        </div>
        {categories.length > 0 && (
          <div className="mx-auto flex max-w-2xl justify-center">
            <CategoryChips categories={categories} />
          </div>
        )}
      </section>

      {!configured && <SetupNotice />}
      {configured && error && <SetupNotice detail={error} />}

      {featured.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">
              Browse the catalog
            </h2>
            <Link
              href="/search"
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              See all →
            </Link>
          </div>
          <div className="grid gap-3">
            {featured.map((p) => (
              <ProductResultCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      <section className="mx-auto max-w-2xl">
        <TrustLegend />
      </section>
    </div>
  );
}
