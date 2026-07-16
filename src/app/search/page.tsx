import type { Metadata } from "next";
import { SearchBar } from "@/components/SearchBar";
import { CategoryChips } from "@/components/CategoryChips";
import { ProductResultCard } from "@/components/ProductResultCard";
import { SetupNotice } from "@/components/SetupNotice";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import { getCategories, searchProducts } from "@/lib/data/products";
import { categoryLabel } from "@/lib/format";
import type { ProductSearchResult } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Search" };

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string; category?: string };
}) {
  const q = (searchParams.q ?? "").trim();
  const category = (searchParams.category ?? "").trim() || null;

  if (!isSupabaseConfigured()) {
    return (
      <div className="space-y-6">
        <SearchBar initialQuery={q} autoFocus />
        <SetupNotice />
      </div>
    );
  }

  let results: ProductSearchResult[] = [];
  let categories: string[] = [];
  let error: string | null = null;

  try {
    [results, categories] = await Promise.all([
      searchProducts(q, { category, limit: 50 }),
      getCategories(),
    ]);
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  const hasFilter = q !== "" || category !== null;

  return (
    <div className="space-y-6">
      <SearchBar initialQuery={q} autoFocus={!hasFilter} />

      {categories.length > 0 && (
        <CategoryChips categories={categories} />
      )}

      {error ? (
        <SetupNotice detail={error} />
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {results.length} {results.length === 1 ? "result" : "results"}
            {q && (
              <>
                {" "}
                for <span className="font-medium text-slate-700">“{q}”</span>
              </>
            )}
            {category && (
              <>
                {" "}
                in{" "}
                <span className="font-medium text-slate-700">
                  {categoryLabel(category)}
                </span>
              </>
            )}
          </p>

          {results.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
              No products matched. Try a different term.
            </div>
          ) : (
            <div className="grid gap-3">
              {results.map((p) => (
                <ProductResultCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
