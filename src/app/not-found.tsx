import Link from "next/link";
import { getDict } from "@/lib/i18n";

export default function NotFound() {
  const dict = getDict();
  return (
    <div className="py-16 text-center">
      <h1 className="text-2xl font-bold text-slate-900">
        {dict.notFound.title}
      </h1>
      <p className="mt-2 text-slate-500">{dict.notFound.desc}</p>
      <Link
        href="/"
        className="mt-6 inline-block rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
      >
        {dict.notFound.home}
      </Link>
    </div>
  );
}
