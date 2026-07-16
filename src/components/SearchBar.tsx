"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

// Client search input. Navigates to /search?q=... so results are server-rendered
// and shareable/bookmarkable. Keeping the query in the URL means the search page
// stays a plain server component reading from the database.

export function SearchBar({
  initialQuery = "",
  autoFocus = false,
  placeholder = "Search a product…",
  buttonLabel = "Search",
}: {
  initialQuery?: string;
  autoFocus?: boolean;
  placeholder?: string;
  buttonLabel?: string;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const [value, setValue] = useState(initialQuery);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const next = new URLSearchParams(params.toString());
    const q = value.trim();
    if (q) next.set("q", q);
    else next.delete("q");
    router.push(`/search?${next.toString()}`);
  }

  return (
    <form onSubmit={submit} className="flex w-full gap-2" role="search">
      <input
        type="search"
        name="q"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        autoFocus={autoFocus}
        placeholder={placeholder}
        aria-label="Search products"
        className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
      />
      <button
        type="submit"
        className="shrink-0 rounded-lg bg-slate-900 px-5 py-3 font-medium text-white transition hover:bg-slate-700"
      >
        {buttonLabel}
      </button>
    </form>
  );
}
