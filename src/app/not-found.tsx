import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-2xl font-bold text-slate-900">Not found</h1>
      <p className="mt-2 text-slate-500">
        We couldn’t find that page or product.
      </p>
      <Link
        href="/"
        className="mt-6 inline-block rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
      >
        Back home
      </Link>
    </div>
  );
}
