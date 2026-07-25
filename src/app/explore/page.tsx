import type { Metadata } from "next";
import { SetupNotice } from "@/components/SetupNotice";
import { isSupabaseConfigured } from "@/lib/supabase/server";
import {
  getRealEstateGroups,
  getRealEstateCities,
  type RealEstateGroup,
} from "@/lib/data/realEstate";
import { getDict } from "@/lib/i18n";
import { formatPrice } from "@/lib/format";
import { KOSOVO_MUNICIPALITIES } from "@/lib/kosovo";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Compare real estate" };

function toNum(v?: string): number | null {
  if (!v) return null;
  const n = Number(v.replace(/[^\d.]/g, ""));
  return Number.isFinite(n) ? n : null;
}

export default async function ExplorePage({
  searchParams,
}: {
  searchParams: {
    city?: string;
    kind?: string;
    type?: string;
    min?: string;
    max?: string;
  };
}) {
  const dict = getDict();
  const t = dict.explore;

  if (!isSupabaseConfigured()) return <SetupNotice />;

  const city = (searchParams.city ?? "").trim() || null;
  const kind = (searchParams.kind ?? "").trim() || null;
  const type = (searchParams.type ?? "").trim() || null;
  const minPrice = toNum(searchParams.min);
  const maxPrice = toNum(searchParams.max);

  let groups: RealEstateGroup[] = [];
  let cities: { city: string; listings: number }[] = [];
  let error: string | null = null;
  try {
    [groups, cities] = await Promise.all([
      getRealEstateGroups({
        city,
        kind,
        propertyType: type,
        minPrice,
        maxPrice,
        minListings: 3, // averages need a few listings to be meaningful
      }),
      getRealEstateCities(),
    ]);
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  // Prefer cities that actually have data; fall back to the full municipality list.
  const cityOptions = cities.length
    ? cities.map((c) => c.city)
    : KOSOVO_MUNICIPALITIES;

  const sel = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t.title}</h1>
        <p className="mt-1 text-sm text-slate-500">{t.subtitle}</p>
      </div>

      {/* Filters — plain GET form, server-rendered, shareable URLs */}
      <form
        method="get"
        className="flex flex-wrap items-end gap-2 rounded-xl border border-slate-200 bg-white p-3"
      >
        <select name="city" defaultValue={city ?? ""} className={sel} aria-label="City">
          <option value="">{t.allCities}</option>
          {cityOptions.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select name="kind" defaultValue={kind ?? ""} className={sel} aria-label="Sale or rent">
          <option value="">{t.sale} + {t.rent}</option>
          <option value="sale">{t.sale}</option>
          <option value="rent">{t.rent}</option>
        </select>

        <select name="type" defaultValue={type ?? ""} className={sel} aria-label="Property type">
          <option value="">{t.allTypes}</option>
          <option value="Banesa">{t.apartments}</option>
          <option value="Shtëpi">{t.houses}</option>
          <option value="Truall/Tokë/Fusha dhe farma">{t.land}</option>
        </select>

        <input
          name="min"
          type="number"
          inputMode="numeric"
          defaultValue={searchParams.min ?? ""}
          placeholder={t.minPrice}
          className={`${sel} w-28`}
        />
        <input
          name="max"
          type="number"
          inputMode="numeric"
          defaultValue={searchParams.max ?? ""}
          placeholder={t.maxPrice}
          className={`${sel} w-28`}
        />

        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          {t.apply}
        </button>
      </form>

      {error ? (
        <SetupNotice detail={error} />
      ) : groups.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          {t.none}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {groups.map((g, i) => (
            <GroupCard key={i} g={g} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function GroupCard({
  g,
  t,
}: {
  g: RealEstateGroup;
  t: ReturnType<typeof getDict>["explore"];
}) {
  const isRent = g.listing_kind === "rent";
  const roomsLabel =
    g.rooms === null
      ? null
      : g.rooms === 1
        ? t.studio
        : `${g.rooms} ${t.rooms}`;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-slate-900">
            {g.property_type}
            {roomsLabel ? ` · ${roomsLabel}` : ""}
          </h3>
          <p className="text-sm text-slate-500">
            {g.city ?? "—"}
            {" · "}
            <span
              className={
                isRent ? "text-amber-600" : "text-emerald-600"
              }
            >
              {isRent ? t.rent : t.sale}
            </span>
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          {g.listings} {t.listingsLabel}
        </span>
      </div>

      <div className="mt-3 flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {t.avg}
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {formatPrice(g.avg_price, g.currency)}
            {isRent && (
              <span className="text-sm font-normal text-slate-400">
                {t.perMonth}
              </span>
            )}
          </div>
        </div>
        {g.avg_price_per_m2 !== null && (
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              €/m²
            </div>
            <div className="text-lg font-semibold text-slate-700">
              {formatPrice(g.avg_price_per_m2, g.currency)}
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-2 text-xs text-slate-500">
        <span>
          {t.median}: {formatPrice(g.median_price, g.currency)}
        </span>
        <span>
          {t.range}: {formatPrice(g.min_price, g.currency)} –{" "}
          {formatPrice(g.max_price, g.currency)}
        </span>
      </div>
    </div>
  );
}
