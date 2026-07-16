import type { Metadata } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";

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
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 py-10 text-center text-xs text-slate-400">
          gjejeçmimin · MVP with seed data · prices are illustrative
        </footer>
      </body>
    </html>
  );
}
