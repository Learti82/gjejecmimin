import type { Metadata } from "next";
import { SearchBar } from "@/components/SearchBar";
import { CategoryChips } from "@/components/CategoryChips";
import { ProductResultCard } from "@/components/ProductResultCard";
import { SetupNotice } from "@/components/SetupNotice";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import { getCategories, searchProducts } from "@/lib/data/products";
import { getDict, localizedCategory, plural } from "@/lib/i18n";
import type { ProductSearchResult } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Search" };

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string; category?: string };
}) {
  const dict = getDict();
  const q = (searchParams.q ?? "").trim();
  const category = (searchParams.category ?? "").trim() || null;

  const searchBar = (autoFocus: boolean) => (
    <SearchBar
      initialQuery={q}
      autoFocus={autoFocus}
      placeholder={dict.search.placeholder}
      buttonLabel={dict.search.button}
    />
  );

  if (!isSupabaseConfigured()) {
    return (
      <div className="space-y-6">
        {searchBar(true)}
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
      {searchBar(!hasFilter)}

      {categories.length > 0 && <CategoryChips categories={categories} />}

      {error ? (
        <SetupNotice detail={error} />
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {results.length}{" "}
            {plural(
              results.length,
              dict.common.resultOne,
              dict.common.resultMany,
            )}
            {q && (
              <>
                {" "}
                {dict.common.forQuery}{" "}
                <span className="font-medium text-slate-700">“{q}”</span>
              </>
            )}
            {category && (
              <>
                {" "}
                {dict.common.inCategory}{" "}
                <span className="font-medium text-slate-700">
                  {localizedCategory(category, dict)}
                </span>
              </>
            )}
          </p>

          {results.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
              {dict.search.none}
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
