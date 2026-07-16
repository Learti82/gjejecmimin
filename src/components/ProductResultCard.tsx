import Link from "next/link";
import { formatPrice } from "@/lib/format";
import { getDict, localizedCategory, plural } from "@/lib/i18n";
import type { ProductSearchResult } from "@/lib/types";

// A single row in the search results list.

export function ProductResultCard({ product }: { product: ProductSearchResult }) {
  const dict = getDict();
  return (
    <Link
      href={`/product/${product.id}`}
      className="group flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-slate-300 hover:shadow-sm"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="truncate font-semibold text-slate-900 group-hover:underline">
            {product.name}
          </h3>
          {product.unit && (
            <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
              {product.unit}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-slate-500">
          {product.brand ? `${product.brand} · ` : ""}
          {localizedCategory(product.category, dict)}
        </p>
      </div>

      <div className="shrink-0 text-right">
        {product.min_price !== null ? (
          <>
            <div className="text-xs text-slate-400">{dict.common.from}</div>
            <div className="text-lg font-semibold text-slate-900">
              {formatPrice(product.min_price, product.currency ?? "EUR")}
            </div>
          </>
        ) : (
          <div className="text-sm text-slate-400">
            {dict.common.noPricesYet}
          </div>
        )}
        <div className="mt-0.5 text-xs text-slate-400">
          {product.observation_count}{" "}
          {plural(
            product.observation_count,
            dict.common.priceOne,
            dict.common.priceMany,
          )}
        </div>
      </div>
    </Link>
  );
}
