import Link from "next/link";
import Image from "next/image";
import { getDict, getLocale } from "@/lib/i18n";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function SiteHeader() {
  const dict = getDict();
  const locale = getLocale();
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex items-center" aria-label="gjejeçmimin">
          <Image
            src="/logo.svg"
            alt="gjejeçmimin"
            width={240}
            height={64}
            priority
            className="h-9 w-auto"
          />
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link
            href="/search"
            className="text-slate-600 transition hover:text-slate-900"
          >
            {dict.nav.search}
          </Link>
          <Link
            href="/explore"
            className="hidden text-slate-600 transition hover:text-slate-900 sm:inline"
          >
            {dict.explore.nav}
          </Link>
          <LanguageSwitcher current={locale} />
        </nav>
      </div>
    </header>
  );
}
