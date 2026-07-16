// Client-safe locale constants and types. Kept free of any server-only imports
// (no next/headers) so both client and server components can import them.

export type Locale = "sq" | "en";
export const DEFAULT_LOCALE: Locale = "sq";
export const LOCALES: Locale[] = ["sq", "en"];
export const LOCALE_COOKIE = "locale";

export const LOCALE_LABELS: Record<Locale, string> = {
  sq: "SQ",
  en: "EN",
};
