import type { Metadata } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";
import { getDict, getLocale } from "@/lib/i18n";

export const metadata: Metadata = {
  title: {
    default: "gjejeçmimin — find the price",
    template: "%s · gjejeçmimin",
  },
  description:
    "Compare product prices across stores in Kosovo & Albania, with every price labelled by how much you can trust it.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = getLocale();
  const dict = getDict();
  return (
    <html lang={locale}>
      <body>
        <SiteHeader />
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 py-10 text-center text-xs text-slate-400">
          {dict.footer}
        </footer>
      </body>
    </html>
  );
}
