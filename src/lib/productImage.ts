// Name/category-driven product visuals.
//
// We don't AI-generate a unique image per listing (24k+ items — too slow and
// costly). Instead we pick a representative emoji + colour deterministically
// from keywords in the product name, falling back to the category. This gives
// users an instant visual cue for what a listing is (a tire, an apartment, a
// coffee) with zero external calls and zero stored assets.
//
// The result is stable per product (same name -> same visual every render).

import type { Category } from "./types";

export interface ProductVisual {
  emoji: string;
  /** Tailwind background + text classes for the tile. */
  bg: string;
}

// Keyword -> emoji. Albanian + English terms. Longer/more specific keys are
// matched first (see the sort below) so "goma dimri" still hits "gom".
const KEYWORD_EMOJI: Array<[string, string]> = [
  // car parts
  ["gom", "🛞"], ["tire", "🛞"], ["tyre", "🛞"], ["michelin", "🛞"],
  ["disqe", "🛞"], ["bandash", "🛞"], ["goma", "🛞"],
  ["kandel", "🔌"], ["spark", "🔌"],
  ["bateri", "🔋"], ["akumulator", "🔋"], ["battery", "🔋"],
  ["fren", "🛑"], ["brake", "🛑"], ["ferrod", "🛑"],
  ["vaj", "🛢️"], ["oil", "🛢️"], ["castrol", "🛢️"],
  ["filter", "🧯"], ["filtr", "🧯"],
  ["far", "💡"], ["llamb", "💡"], ["dritë", "💡"],
  ["fshir", "🌧️"], ["wiper", "🌧️"], ["xhami", "🪟"],
  ["motor", "⚙️"], ["mbules", "⚙️"], ["pjes", "⚙️"],
  // real estate
  ["banes", "🏢"], ["apartment", "🏢"], ["garsonier", "🏢"],
  ["shtëpi", "🏠"], ["shtepi", "🏠"], ["shpi", "🏠"], ["vil", "🏡"], ["house", "🏠"],
  ["tok", "🏞️"], ["truall", "🏞️"], ["troje", "🏞️"], ["parcel", "🏞️"],
  ["fush", "🌾"], ["farm", "🚜"], ["arë", "🌾"],
  ["lokal", "🏬"], ["zyr", "🏢"], ["dyqan", "🏬"], ["objekt", "🏗️"],
  // cars
  ["golf", "🚗"], ["audi", "🚗"], ["bmw", "🚗"], ["mercedes", "🚗"],
  ["passat", "🚗"], ["veturë", "🚗"], ["vetur", "🚗"], ["makin", "🚗"],
  ["kamion", "🚚"], ["traktor", "🚜"], ["motoçikl", "🏍️"],
  // groceries
  ["qumësht", "🥛"], ["qumesht", "🥛"], ["milk", "🥛"],
  ["bukë", "🍞"], ["buke", "🍞"], ["bread", "🍞"],
  ["kafe", "☕"], ["coffee", "☕"], ["nescafe", "☕"], ["nescafé", "☕"],
  ["vaj luledielli", "🌻"], ["sheqer", "🧂"], ["kripë", "🧂"],
  ["vezë", "🥚"], ["veze", "🥚"], ["egg", "🥚"],
  ["ujë", "💧"], ["uje", "💧"], ["water", "💧"], ["coca", "🥤"], ["cola", "🥤"],
  ["oriz", "🍚"], ["rice", "🍚"], ["makaron", "🍝"], ["spaghetti", "🍝"],
  ["gjalp", "🧈"], ["djath", "🧀"], ["mish", "🥩"],
  // electronics / tech
  ["iphone", "📱"], ["samsung", "📱"], ["telefon", "📱"], ["phone", "📱"],
  ["redmi", "📱"], ["xiaomi", "📱"],
  ["laptop", "💻"], ["macbook", "💻"], ["dell", "💻"], ["kompjuter", "🖥️"],
  ["tv", "📺"], ["televizor", "📺"], ["monitor", "🖥️"],
  ["kufje", "🎧"], ["headphone", "🎧"], ["sony", "🎧"],
  ["playstation", "🎮"], ["ps5", "🎮"], ["konsol", "🎮"],
  ["maus", "🖱️"], ["mouse", "🖱️"], ["tastier", "⌨️"],
  ["powerbank", "🔋"], ["anker", "🔋"],
  // fragrances / cosmetics
  ["parfum", "🧴"], ["perfume", "🧴"], ["aroma", "🌸"], ["eau de", "🧴"],
  ["kozmetik", "💄"], ["cream", "🧴"], ["krem", "🧴"], ["makeup", "💄"],
  // pharmacy
  ["ilaç", "💊"], ["tablet", "💊"], ["vitamin", "💊"], ["nicorette", "💊"],
  // furniture / clothing
  ["mobil", "🛋️"], ["tavolin", "🪑"], ["karrig", "🪑"], ["shtrat", "🛏️"],
  ["veshje", "👕"], ["këpuc", "👟"], ["kepuc", "👟"], ["xhaket", "🧥"],
];

// Category fallback when no keyword matches.
const CATEGORY_EMOJI: Record<string, string> = {
  real_estate: "🏠",
  cars: "🚗",
  car_parts: "⚙️",
  groceries: "🛒",
  electronics_tech: "🔌",
  fragrances_cosmetics: "🧴",
  pharmacy: "💊",
  furniture: "🛋️",
  clothing: "👕",
};

// A small palette of soft tile backgrounds, chosen deterministically per item.
const PALETTES = [
  "bg-sky-100 text-sky-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-violet-100 text-violet-700",
  "bg-rose-100 text-rose-700",
  "bg-teal-100 text-teal-700",
  "bg-indigo-100 text-indigo-700",
  "bg-lime-100 text-lime-700",
];

const KEYWORDS_SORTED = [...KEYWORD_EMOJI].sort((a, b) => b[0].length - a[0].length);

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/** Lowercase + strip diacritics so "Nescafé"/"Bukë" match "nescafe"/"buke". */
function normalize(s: string): string {
  return (s || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "");
}

export function productVisual(
  name: string,
  category: Category,
): ProductVisual {
  const lower = normalize(name);
  let emoji: string | undefined;
  for (const [kw, e] of KEYWORDS_SORTED) {
    if (lower.includes(normalize(kw))) {
      emoji = e;
      break;
    }
  }
  if (!emoji) emoji = CATEGORY_EMOJI[category] ?? "🏷️";
  const bg = PALETTES[hash(name || category) % PALETTES.length];
  return { emoji, bg };
}
