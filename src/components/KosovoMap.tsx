"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { CityStat } from "@/lib/data/realEstate";
import { formatPrice } from "@/lib/format";

// Clickable choropleth map of Kosovo's 38 municipalities, rendered as inline
// SVG from public/kosovo.geojson (no external map library — self-contained,
// CSP-safe). Each municipality is shaded by its average real-estate price;
// clicking one filters the Explore page to that city.

interface GeoFeature {
  properties: { name: string };
  geometry: {
    type: "Polygon" | "MultiPolygon";
    coordinates: number[][][] | number[][][][];
  };
}

function stripDiacritics(s: string): string {
  return s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").trim();
}

// Match a municipality name to a scraped city stat, tolerating accent and
// suffix differences ("Mitrovicë" scraped vs "Mitrovicë e Jugut" on the map).
function matchStat(
  name: string,
  byName: Map<string, CityStat>,
): CityStat | undefined {
  const n = stripDiacritics(name);
  if (byName.has(n)) return byName.get(n);
  for (const [key, stat] of byName) {
    if (n.startsWith(key) || key.startsWith(n)) return stat;
  }
  return undefined;
}

function hexLerp(a: string, b: string, t: number): string {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const p = pa.map((v, i) => Math.round(v + (pb[i] - v) * t));
  return `#${p.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

export function KosovoMap({
  stats,
  selectedCity,
  preserve,
  labelColorBy,
}: {
  stats: CityStat[];
  selectedCity: string | null;
  preserve: Record<string, string | undefined>;
  labelColorBy: string;
}) {
  const router = useRouter();
  const [features, setFeatures] = useState<GeoFeature[] | null>(null);
  const [hover, setHover] = useState<{
    name: string;
    stat?: CityStat;
    x: number;
    y: number;
  } | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    fetch("/kosovo.geojson")
      .then((r) => r.json())
      .then((d) => {
        if (alive) setFeatures(d.features as GeoFeature[]);
      })
      .catch(() => setFeatures([]));
    return () => {
      alive = false;
    };
  }, []);

  const byName = useMemo(() => {
    const m = new Map<string, CityStat>();
    for (const s of stats) m.set(stripDiacritics(s.city), s);
    return m;
  }, [stats]);

  const { paths, minV, maxV } = useMemo(() => {
    if (!features) return { paths: [], minV: 0, maxV: 0 };

    // Collect points, project (equirectangular, corrected for latitude).
    let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
    const rings: { name: string; ring: number[][] }[][] = [];
    for (const f of features) {
      const polys =
        f.geometry.type === "Polygon"
          ? [f.geometry.coordinates as number[][][]]
          : (f.geometry.coordinates as number[][][][]);
      const featRings: { name: string; ring: number[][] }[] = [];
      for (const poly of polys) {
        for (const ring of poly) {
          featRings.push({ name: f.properties.name, ring });
          for (const [lng, lat] of ring) {
            if (lng < minLng) minLng = lng;
            if (lng > maxLng) maxLng = lng;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
          }
        }
      }
      rings.push(featRings);
    }

    const midLat = ((minLat + maxLat) / 2) * (Math.PI / 180);
    const kx = Math.cos(midLat);
    const W = 640;
    const spanX = (maxLng - minLng) * kx;
    const spanY = maxLat - minLat;
    const scale = W / spanX;
    const H = spanY * scale;
    const px = (lng: number) => (lng - minLng) * kx * scale;
    const py = (lat: number) => (maxLat - lat) * scale;

    const vals = stats.map((s) => s.avg_price).filter((v) => v > 0);
    const minV = vals.length ? Math.min(...vals) : 0;
    const maxV = vals.length ? Math.max(...vals) : 0;

    const paths = features.map((f, i) => {
      const d = rings[i]
        .map(
          ({ ring }) =>
            "M" +
            ring
              .map(([lng, lat]) => `${px(lng).toFixed(1)},${py(lat).toFixed(1)}`)
              .join("L") +
            "Z",
        )
        .join(" ");
      const stat = matchStat(f.properties.name, byName);
      let fill = "#e5e7eb"; // no data
      if (stat && maxV > minV) {
        const t = Math.sqrt((stat.avg_price - minV) / (maxV - minV));
        fill = hexLerp("#dbeafe", "#1e3a8a", t);
      } else if (stat) {
        fill = "#93c5fd";
      }
      return { name: f.properties.name, d, fill, stat, W, H };
    });

    return { paths, minV, maxV, W, H };
  }, [features, byName, stats]);

  const width = paths[0]?.W ?? 640;
  const height = paths[0]?.H ?? 520;

  function go(city: string) {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(preserve)) if (v) q.set(k, v);
    q.set("city", city);
    router.push(`/explore?${q.toString()}`);
  }

  if (!features) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-400">
        …
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-xs text-slate-500">{labelColorBy}</span>
        {maxV > minV && (
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span>{formatPrice(minV, "EUR")}</span>
            <span
              className="h-2 w-24 rounded"
              style={{
                background: "linear-gradient(90deg,#dbeafe,#1e3a8a)",
              }}
            />
            <span>{formatPrice(maxV, "EUR")}</span>
          </div>
        )}
      </div>
      <div ref={wrapRef} className="relative">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          style={{ maxHeight: 520 }}
          onMouseLeave={() => setHover(null)}
        >
          {paths.map((p) => {
            const isSel =
              selectedCity &&
              stripDiacritics(p.name) === stripDiacritics(selectedCity);
            return (
              <path
                key={p.name}
                d={p.d}
                fill={p.fill}
                stroke={isSel ? "#0f172a" : "#ffffff"}
                strokeWidth={isSel ? 2 : 0.6}
                className="cursor-pointer transition-[stroke] hover:stroke-slate-900"
                onClick={() => go(p.name)}
                onMouseMove={(e) => {
                  const r = wrapRef.current?.getBoundingClientRect();
                  setHover({
                    name: p.name,
                    stat: p.stat,
                    x: e.clientX - (r?.left ?? 0),
                    y: e.clientY - (r?.top ?? 0),
                  });
                }}
              />
            );
          })}
        </svg>
        {hover && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs text-white shadow-lg"
            style={{
              left: Math.min(hover.x + 12, width - 8),
              top: hover.y + 12,
            }}
          >
            <div className="font-medium">{hover.name}</div>
            {hover.stat ? (
              <div className="text-slate-300">
                {formatPrice(hover.stat.avg_price, "EUR")} · {hover.stat.listings}
              </div>
            ) : (
              <div className="text-slate-400">—</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
