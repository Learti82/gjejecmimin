// Shown when the database isn't reachable/configured yet, so the app degrades
// to clear setup instructions instead of a stack trace.

export function SetupNotice({ detail }: { detail?: string }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
      <h2 className="mb-1 font-semibold">Database not connected yet</h2>
      <p className="mb-3 text-amber-800">
        The UI is ready, but it needs a Supabase database with the migrations and
        seed data applied. To get running locally:
      </p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          <code className="rounded bg-amber-100 px-1">supabase start</code>
        </li>
        <li>
          <code className="rounded bg-amber-100 px-1">supabase db reset</code>{" "}
          (applies migrations + seed)
        </li>
        <li>
          Copy <code className="rounded bg-amber-100 px-1">.env.example</code> to{" "}
          <code className="rounded bg-amber-100 px-1">.env.local</code> and fill
          in the printed URL + anon key
        </li>
        <li>
          <code className="rounded bg-amber-100 px-1">npm run dev</code>
        </li>
      </ol>
      {detail && (
        <p className="mt-3 rounded bg-amber-100 px-2 py-1 font-mono text-xs text-amber-700">
          {detail}
        </p>
      )}
    </div>
  );
}
