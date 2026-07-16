import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { TrustBadge } from "@/components/TrustBadge";
import { SetupNotice } from "@/components/SetupNotice";
import { SearchBar } from "@/components/SearchBar";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import {
  getObservationsForProduct,
  getProduct,
} from "@/lib/data/products";
import { toCompareRows } from "@/lib/pricing";
import { formatPrice, timeAgo, formatDate, categoryLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Compare prices" };

export default async function ComparePage({
  searchParams,
}: {
  searchParams: { product?: string };
}) {
  const productId = (searchParams.product ?? "").trim();

  if (!isSupabaseConfigured()) return <SetupNotice />;

  if (!productId) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Compare prices</h1>
        <p className="text-slate-600">
          Search for a product, then open it and hit “Compare stores”.
        </p>
        <SearchBar autoFocus />
      </div>
    );
  }

  const product = await getProduct(productId);
  if (!product) notFound();

  const observations = await getObservationsForProduct(product.id);
  const rows = toCompareRows(observations);
  const cheapestPrice = rows.length > 0 ? rows[0].observation.price : null;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href={`/product/${product.id}`}
          className="text-sm text-slate-500 hover:text-slate-800"
        >
          ← Back to {product.name}
        </Link>
        <h1 className="text-2xl font-bold text-slate-900">
          Compare · {product.name}
        </h1>
        <p className="text-sm text-slate-500">
          {product.brand ? `${product.brand} · ` : ""}
          {categoryLabel(product.category)}
          {product.unit ? ` · ${product.unit}` : ""} — latest price per store,
          cheapest first.
        </p>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          No prices to compare yet.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Store</th>
                <th className="px-4 py-3 font-medium">City</th>
                <th className="px-4 py-3 font-medium">Trust</th>
                <th className="px-4 py-3 font-medium">Last verified</th>
                <th className="px-4 py-3 text-right font-medium">Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row) => {
                const isCheapest = row.observation.price === cheapestPrice;
                return (
                  <tr
                    key={row.key}
                    className={isCheapest ? "bg-emerald-50/70" : undefined}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 font-medium text-slate-900">
                        {row.storeName}
                        {row.verified && (
                          <span
                            className="text-xs text-verified-fg"
                            title="Registered / verified store"
                          >
                            ✓
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {row.city ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <TrustBadge tier={row.observation.trust_tier} size="sm" />
                    </td>
                    <td
                      className="px-4 py-3 text-slate-500"
                      title={formatDate(row.observation.observed_at)}
                    >
                      {timeAgo(row.observation.observed_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {isCheapest && (
                          <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-xs font-semibold text-white">
                            Cheapest
                          </span>
                        )}
                        <span className="font-semibold text-slate-900">
                          {formatPrice(
                            row.observation.price,
                            row.observation.currency,
                          )}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
