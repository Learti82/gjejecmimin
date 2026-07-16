import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight text-slate-900">
            gjeje<span className="text-emerald-600">çmimin</span>
          </span>
          <span className="hidden text-xs text-slate-400 sm:inline">
            find the price
          </span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link
            href="/search"
            className="text-slate-600 transition hover:text-slate-900"
          >
            Search
          </Link>
        </nav>
      </div>
    </header>
  );
}
