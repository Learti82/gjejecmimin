import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { TrustBadge } from "@/components/TrustBadge";
import { SetupNotice } from "@/components/SetupNotice";
import { SearchBar } from "@/components/SearchBar";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import { getObservationsForProduct, getProduct } from "@/lib/data/products";
import { toCompareRows } from "@/lib/pricing";
import { formatPrice, timeAgo, formatDate } from "@/lib/format";
import { getDict, getLocale, localizedCategory } from "@/lib/i18n";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Compare prices" };

export default async function ComparePage({
  searchParams,
}: {
  searchParams: { product?: string };
}) {
  const dict = getDict();
  const locale = getLocale();
  const productId = (searchParams.product ?? "").trim();

  if (!isSupabaseConfigured()) return <SetupNotice />;

  if (!productId) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">
          {dict.compare.title}
        </h1>
        <p className="text-slate-600">{dict.compare.prompt}</p>
        <SearchBar
          autoFocus
          placeholder={dict.search.placeholder}
          buttonLabel={dict.search.button}
        />
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
          {dict.compare.backTo} {product.name}
        </Link>
        <h1 className="text-2xl font-bold text-slate-900">
          {dict.compare.heading} · {product.name}
        </h1>
        <p className="text-sm text-slate-500">
          {product.brand ? `${product.brand} · ` : ""}
          {localizedCategory(product.category, dict)}
          {product.unit ? ` · ${product.unit}` : ""} —{" "}
          {dict.compare.subtitleSuffix}
        </p>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          {dict.compare.empty}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">{dict.compare.colStore}</th>
                <th className="px-4 py-3 font-medium">{dict.compare.colCity}</th>
                <th className="px-4 py-3 font-medium">{dict.compare.colTrust}</th>
                <th className="px-4 py-3 font-medium">
                  {dict.compare.colLastVerified}
                </th>
                <th className="px-4 py-3 text-right font-medium">
                  {dict.compare.colPrice}
                </th>
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
                            title={dict.common.verifiedStore}
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
                      title={formatDate(row.observation.observed_at, locale)}
                    >
                      {timeAgo(row.observation.observed_at, locale)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {isCheapest && (
                          <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-xs font-semibold text-white">
                            {dict.common.cheapest}
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
