import { TrustBadge } from "./TrustBadge";
import { formatPrice, timeAgo, formatDate } from "@/lib/format";
import type { PriceObservationWithStore } from "@/lib/types";

// One price observation, as shown on the product detail page. Renders store,
// city, price, trust badge, and a "last verified" timestamp. Highlighted when
// it is the cheapest across all observations.

export function ObservationRow({
  observation,
  isCheapest = false,
}: {
  observation: PriceObservationWithStore;
  isCheapest?: boolean;
}) {
  const o = observation;
  const storeName =
    o.store?.name ??
    (o.trust_tier === "official" ? "Official reference" : "Unknown store");
  const city = o.store?.city ?? o.geo_city;

  return (
    <div
      className={`flex items-center justify-between gap-4 rounded-lg border p-3.5 ${
        isCheapest
          ? "border-emerald-300 bg-emerald-50/60 ring-1 ring-emerald-200"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-slate-900">{storeName}</span>
          {o.store?.verified && (
            <span
              className="text-xs text-verified-fg"
              title="Registered / verified store"
            >
              ✓ verified store
            </span>
          )}
          {isCheapest && (
            <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-xs font-semibold text-white">
              Cheapest
            </span>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
          {city && <span>{city}</span>}
          <span title={formatDate(o.observed_at)}>
            Last verified {timeAgo(o.observed_at)}
          </span>
          {o.confidence_score !== null && (
            <span className="text-slate-400">
              confidence {Math.round(o.confidence_score * 100)}%
            </span>
          )}
        </div>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <span className="text-lg font-semibold text-slate-900">
          {formatPrice(o.price, o.currency)}
        </span>
        <TrustBadge tier={o.trust_tier} size="sm" />
      </div>
    </div>
  );
}
