// Small display helpers. Kept pure and framework-free (locale passed in).

import type { Locale } from "./locale";

export function formatPrice(
  amount: number | null | undefined,
  currency = "EUR",
): string {
  if (amount === null || amount === undefined) return "—";
  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Unknown currency code — fall back to a plain number + code.
    return `${amount.toFixed(2)} ${currency}`;
  }
}

// Relative-time phrasing per locale. Albanian day/month/hour nouns don't inflect
// for these counts, so a single form per unit is correct.
const TIME_STRINGS: Record<
  Locale,
  {
    unknown: string;
    justNow: string;
    min: (n: number) => string;
    hr: (n: number) => string;
    day: (n: number) => string;
    month: (n: number) => string;
    year: (n: number) => string;
  }
> = {
  en: {
    unknown: "unknown",
    justNow: "just now",
    min: (n) => `${n} min ago`,
    hr: (n) => `${n} hr${n === 1 ? "" : "s"} ago`,
    day: (n) => `${n} day${n === 1 ? "" : "s"} ago`,
    month: (n) => `${n} month${n === 1 ? "" : "s"} ago`,
    year: (n) => `${n} year${n === 1 ? "" : "s"} ago`,
  },
  sq: {
    unknown: "e panjohur",
    justNow: "tani",
    min: (n) => `${n} min më parë`,
    hr: (n) => `${n} orë më parë`,
    day: (n) => `${n} ditë më parë`,
    month: (n) => `${n} muaj më parë`,
    year: (n) => `${n} vit${n === 1 ? "" : "e"} më parë`,
  },
};

/** "last verified" style relative timestamp, e.g. "3 days ago" / "3 ditë më parë". */
export function timeAgo(
  iso: string | null | undefined,
  locale: Locale = "sq",
): string {
  const s = TIME_STRINGS[locale];
  if (!iso) return s.unknown;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return s.unknown;
  const sec = Math.round((Date.now() - then) / 1000);
  const min = Math.round(sec / 60);
  const hr = Math.round(min / 60);
  const day = Math.round(hr / 24);
  const month = Math.round(day / 30);

  if (sec < 60) return s.justNow;
  if (min < 60) return s.min(min);
  if (hr < 24) return s.hr(hr);
  if (day < 30) return s.day(day);
  if (month < 12) return s.month(month);
  return s.year(Math.round(month / 12));
}

/** Absolute timestamp for tooltips / title attributes. */
export function formatDate(
  iso: string | null | undefined,
  locale: Locale = "sq",
): string {
  if (!iso) return TIME_STRINGS[locale].unknown;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return TIME_STRINGS[locale].unknown;
  return d.toLocaleString(locale === "sq" ? "sq-AL" : "en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
