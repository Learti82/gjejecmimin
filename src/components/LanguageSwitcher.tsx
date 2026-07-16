"use client";

import { useRouter } from "next/navigation";
import { LOCALES, LOCALE_LABELS, type Locale } from "@/lib/locale";

// Flips the `locale` cookie and refreshes the server components so the whole
// page re-renders in the chosen language. Shqip is the default; this only needs
// to persist a deviation from it.

export function LanguageSwitcher({ current }: { current: Locale }) {
  const router = useRouter();

  function choose(locale: Locale) {
    if (locale === current) return;
    document.cookie = `locale=${locale};path=/;max-age=31536000;samesite=lax`;
    router.refresh();
  }

  return (
    <div
      className="flex items-center rounded-lg border border-slate-200 p-0.5 text-xs font-medium"
      role="group"
      aria-label="Language"
    >
      {LOCALES.map((l) => (
        <button
          key={l}
          onClick={() => choose(l)}
          aria-pressed={l === current}
          className={`rounded-md px-2 py-1 transition ${
            l === current
              ? "bg-slate-900 text-white"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          {LOCALE_LABELS[l]}
        </button>
      ))}
    </div>
  );
}
