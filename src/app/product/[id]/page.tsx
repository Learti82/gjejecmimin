import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ObservationRow } from "@/components/ObservationRow";
import { TrustBadge } from "@/components/TrustBadge";
import { TrustLegend } from "@/components/TrustLegend";
import { SetupNotice } from "@/components/SetupNotice";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import {
  getObservationsForProduct,
  getOfficialIndicesForCategory,
  getProduct,
} from "@/lib/data/products";
import { groupByTier, priceStats } from "@/lib/pricing";
import { trustMeta } from "@/lib/trust";
import { formatPrice, categoryLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  if (!isSupabaseConfigured()) return { title: "Product" };
  try {
    const product = await getProduct(params.id);
    return { title: product?.name ?? "Product" };
  } catch {
    return { title: "Product" };
  }
}

export default async function ProductPage({
  params,
}: {
  params: { id: string };
}) {
  if (!isSupabaseConfigured()) return <SetupNotice />;

  const product = await getProduct(params.id);
  if (!product) notFound();

  const [observations, indices] = await Promise.all([
    getObservationsForProduct(product.id),
    getOfficialIndicesForCategory(product.category),
  ]);

  const stats = priceStats(observations);
  const groups = groupByTier(observations);
  const cheapestId = stats.cheapest?.id ?? null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-3">
        <Link
          href="/search"
          className="text-sm text-slate-500 hover:text-slate-800"
        >
          ← Back to search
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">
                {product.name}
              </h1>
              {product.unit && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-sm text-slate-500">
                  {product.unit}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {product.brand ? `${product.brand} · ` : ""}
              {categoryLabel(product.category)}
            </p>
          </div>

          {stats.count > 0 && (
            <div className="flex items-center gap-6">
              <div>
                <div className="text-xs text-slate-400">Lowest price</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {formatPrice(stats.min, stats.currency)}
                </div>
              </div>
              <Link
                href={`/compare?product=${product.id}`}
                className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700"
              >
                Compare stores
              </Link>
            </div>
          )}
        </div>
      </div>

      {stats.count === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          No prices recorded for this product yet.
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
          {/* Observations grouped by trust tier */}
          <div className="space-y-6">
            {groups.map((group) => {
              const meta = trustMeta(group.tier);
              return (
                <section key={group.tier} className="space-y-3">
                  <div className="flex items-center gap-3">
                    <TrustBadge tier={group.tier} />
                    <span className="text-sm text-slate-500">
                      {group.observations.length}{" "}
                      {group.observations.length === 1 ? "price" : "prices"}
                    </span>
                    <span className="hidden text-xs text-slate-400 sm:inline">
                      {meta.description}
                    </span>
                  </div>
                  <div className="space-y-2.5">
                    {group.observations.map((o) => (
                      <ObservationRow
                        key={o.id}
                        observation={o}
                        isCheapest={o.id === cheapestId}
                      />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>

          {/* Sidebar: legend + official index context */}
          <aside className="space-y-6">
            <TrustLegend />
            {indices.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <h3 className="mb-3 text-sm font-semibold text-slate-700">
                  Official indices · {categoryLabel(product.category)}
                </h3>
                <ul className="space-y-2 text-sm">
                  {indices.map((idx) => (
                    <li
                      key={idx.id}
                      className="flex items-center justify-between gap-2"
                    >
                      <span className="text-slate-500">
                        {idx.source} · {idx.period}
                      </span>
                      <span className="font-medium text-slate-800">
                        {idx.value}
                        {idx.unit && idx.unit !== "index"
                          ? ` ${idx.unit}`
                          : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
