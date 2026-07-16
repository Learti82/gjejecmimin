import { TRUST_TIERS_ORDERED } from "@/lib/trust";
import { getDict } from "@/lib/i18n";
import { TrustBadge } from "./TrustBadge";

// Explains what each badge means. Shown on the product page so the trust tiers
// are self-documenting rather than requiring a mental model up front.

export function TrustLegend() {
  const dict = getDict();
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">
        {dict.legend.title}
      </h3>
      <ul className="space-y-2.5">
        {TRUST_TIERS_ORDERED.map((meta) => (
          <li key={meta.tier} className="flex items-start gap-3">
            <TrustBadge tier={meta.tier} size="sm" />
            <span className="text-sm leading-snug text-slate-600">
              {dict.trust[meta.tier].description}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
