import Link from "next/link";
import { getDict, localizedCategory } from "@/lib/i18n";

export function CategoryChips({ categories }: { categories: string[] }) {
  const dict = getDict();
  if (categories.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {categories.map((c) => (
        <Link
          key={c}
          href={`/search?category=${encodeURIComponent(c)}`}
          className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
        >
          {localizedCategory(c, dict)}
        </Link>
      ))}
    </div>
  );
}
