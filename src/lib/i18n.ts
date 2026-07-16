import { cookies } from "next/headers";
import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  LOCALE_LABELS,
  LOCALES,
  type Locale,
} from "./locale";

// Lightweight, dependency-free i18n. Locale is stored in a cookie so server
// components render the right language on first paint (no client flash), and a
// small client switcher flips the cookie + refreshes. Shqip ("sq") is default.
//
// Client-safe constants (LOCALES, labels, the Locale type) live in ./locale so
// client components can import them without pulling in next/headers.

export {
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  LOCALE_LABELS,
  LOCALES,
  type Locale,
} from "./locale";

/** Read the active locale from the cookie (Shqip by default). */
export function getLocale(): Locale {
  const v = cookies().get(LOCALE_COOKIE)?.value;
  return v === "en" ? "en" : "sq";
}

const sq = {
  nav: { search: "Kërko" },
  tagline: "gjej çmimin",
  common: {
    from: "nga",
    priceOne: "çmim",
    priceMany: "çmime",
    resultOne: "rezultat",
    resultMany: "rezultate",
    forQuery: "për",
    inCategory: "në",
    noPricesYet: "ende pa çmime",
    cheapest: "Më lirë",
    verifiedStore: "dyqan i verifikuar",
    confidence: "besueshmëri",
    lastVerified: "Verifikuar",
    officialReference: "Referencë zyrtare",
    unknownStore: "Dyqan i panjohur",
  },
  home: {
    title: "Njihe çmimin real para se të blesh",
    subtitle:
      "Krahaso çmimet nëpër dyqane në Kosovë e Shqipëri. Çdo çmim etiketohet sipas nivelit të besueshmërisë — statistika zyrtare, tregtarë të verifikuar, ose komuniteti.",
    browse: "Shfleto katalogun",
    seeAll: "Shiko të gjitha →",
  },
  search: {
    placeholder: "Kërko një produkt — p.sh. qumësht, iPhone, pjesë makinash…",
    button: "Kërko",
    none: "Asnjë produkt nuk u gjet. Provo një term tjetër.",
    title: "Kërko",
  },
  legend: { title: "Si t’i lexoni këto çmime" },
  trust: {
    official: {
      short: "Zyrtare",
      label: "Burim zyrtar",
      description:
        "Nga një organ zyrtar statistikash (ASK, INSTAT, BQK). Çmim referues autoritativ.",
    },
    verified_retailer: {
      short: "Verifikuar",
      label: "Tregtar i verifikuar",
      description:
        "Mbledhur nga një tregtar i njohur dhe i regjistruar. I besueshëm, por çmim i një dyqani të vetëm.",
    },
    crowdsourced: {
      short: "Komunitet",
      label: "Nga komuniteti",
      description:
        "Dërguar nga përdoruesit dhe ende i pakonfirmuar. Trajtoje si çmim orientues.",
    },
  },
  product: {
    back: "← Kthehu te kërkimi",
    lowestPrice: "Çmimi më i ulët",
    compareStores: "Krahaso dyqanet",
    noPrices: "Ende nuk ka çmime të regjistruara për këtë produkt.",
    officialIndices: "Indekset zyrtare",
  },
  compare: {
    title: "Krahaso çmimet",
    heading: "Krahaso",
    prompt: "Kërko një produkt, hape dhe kliko “Krahaso dyqanet”.",
    subtitleSuffix: "çmimi më i fundit për dyqan, më i liri i pari.",
    backTo: "← Kthehu te",
    empty: "Ende asnjë çmim për të krahasuar.",
    colStore: "Dyqani",
    colCity: "Qyteti",
    colTrust: "Besimi",
    colLastVerified: "Verifikuar së fundi",
    colPrice: "Çmimi",
  },
  categories: {
    groceries: "Ushqime",
    electronics: "Elektronikë",
    car_parts: "Pjesë Makinash",
    food: "Ushqim",
    market: "Treg",
    supermarket: "Supermarket",
    cpi: "IÇK",
    exchange: "Këmbim",
  },
  footer: "gjejeçmimin · MVP me të dhëna shembull · çmimet janë ilustruese",
  notFound: {
    title: "Nuk u gjet",
    desc: "Nuk e gjetëm atë faqe ose produkt.",
    home: "Kthehu në ballinë",
  },
  setup: {
    title: "Baza e të dhënave ende nuk është lidhur",
    intro:
      "Ndërfaqja është gati, por i duhet një bazë të dhënash Supabase me migrimet dhe të dhënat shembull të aplikuara. Për ta nisur lokalisht:",
    envHint:
      "Kopjo .env.example te .env.local dhe plotëso URL-në + anon key të shtypur",
    seedNote: "(apliko migrimet + të dhënat shembull)",
  },
};

// English mirrors the exact same shape.
const en: typeof sq = {
  nav: { search: "Search" },
  tagline: "find the price",
  common: {
    from: "from",
    priceOne: "price",
    priceMany: "prices",
    resultOne: "result",
    resultMany: "results",
    forQuery: "for",
    inCategory: "in",
    noPricesYet: "no prices yet",
    cheapest: "Cheapest",
    verifiedStore: "verified store",
    confidence: "confidence",
    lastVerified: "Last verified",
    officialReference: "Official reference",
    unknownStore: "Unknown store",
  },
  home: {
    title: "Know the real price before you buy",
    subtitle:
      "Compare prices across stores in Kosovo & Albania. Every price is labelled by how much you can trust it — official statistics, verified retailers, or the crowd.",
    browse: "Browse the catalog",
    seeAll: "See all →",
  },
  search: {
    placeholder: "Search a product — e.g. milk, iPhone, brake pads…",
    button: "Search",
    none: "No products matched. Try a different term.",
    title: "Search",
  },
  legend: { title: "How to read these prices" },
  trust: {
    official: {
      short: "Official",
      label: "Official source",
      description:
        "From an official statistics body (ASK, INSTAT, BQK). Authoritative reference price.",
    },
    verified_retailer: {
      short: "Verified",
      label: "Verified retailer",
      description:
        "Collected from a known, registered retailer. Reliable but a single shop's shelf price.",
    },
    crowdsourced: {
      short: "Crowd",
      label: "Crowdsourced",
      description:
        "Submitted by users and not yet corroborated. Treat as an indicative price.",
    },
  },
  product: {
    back: "← Back to search",
    lowestPrice: "Lowest price",
    compareStores: "Compare stores",
    noPrices: "No prices recorded for this product yet.",
    officialIndices: "Official indices",
  },
  compare: {
    title: "Compare prices",
    heading: "Compare",
    prompt: "Search for a product, then open it and hit “Compare stores”.",
    subtitleSuffix: "latest price per store, cheapest first.",
    backTo: "← Back to",
    empty: "No prices to compare yet.",
    colStore: "Store",
    colCity: "City",
    colTrust: "Trust",
    colLastVerified: "Last verified",
    colPrice: "Price",
  },
  categories: {
    groceries: "Groceries",
    electronics: "Electronics",
    car_parts: "Car Parts",
    food: "Food",
    market: "Market",
    supermarket: "Supermarket",
    cpi: "CPI",
    exchange: "Exchange",
  },
  footer: "gjejeçmimin · MVP with seed data · prices are illustrative",
  notFound: {
    title: "Not found",
    desc: "We couldn’t find that page or product.",
    home: "Back home",
  },
  setup: {
    title: "Database not connected yet",
    intro:
      "The UI is ready, but it needs a Supabase database with the migrations and seed data applied. To get running locally:",
    envHint:
      "Copy .env.example to .env.local and fill in the printed URL + anon key",
    seedNote: "(applies migrations + seed)",
  },
};

export type Dictionary = typeof sq;

const DICTS: Record<Locale, Dictionary> = { sq, en };

/** The dictionary for the active locale (reads the cookie). */
export function getDict(): Dictionary {
  return DICTS[getLocale()];
}

/** Localized category name, falling back to a title-cased slug. */
export function localizedCategory(category: string, dict: Dictionary): string {
  const map = dict.categories as Record<string, string>;
  if (map[category]) return map[category];
  return category
    .split(/[_\s-]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Pick singular/plural word for a count. */
export function plural(n: number, one: string, many: string): string {
  return n === 1 ? one : many;
}
