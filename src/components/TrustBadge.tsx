import { trustMeta } from "@/lib/trust";
import { getDict } from "@/lib/i18n";
import type { TrustTier } from "@/lib/types";

// The core visual primitive that distinguishes data provenance everywhere in
// the app. Colors come from tier metadata; the label comes from the dictionary.

export function TrustBadge({
  tier,
  size = "md",
  withDot = true,
}: {
  tier: TrustTier;
  size?: "sm" | "md";
  withDot?: boolean;
}) {
  const meta = trustMeta(tier);
  const dict = getDict();
  const text = dict.trust[tier];
  const pad = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${pad} ${meta.classes}`}
      title={text.description}
    >
      {withDot && (
        <span
          className={`h-1.5 w-1.5 rounded-full ${meta.dotClass}`}
          aria-hidden
        />
      )}
      {text.short}
    </span>
  );
}
