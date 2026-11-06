// Small choropleth of online browsers per country; loaded on first hover so the atlas stays out of the main bundle.
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import atlas from "world-atlas/countries-110m.json";
import type { CountryCount } from "../generated/wire";
import { ATLAS_ID } from "./countryCodes";

const W = 320, H = 160;
const topo = atlas as unknown as Topology<{ countries: GeometryCollection<{ name: string }> }>;
const land = feature(topo, topo.objects.countries).features.filter((f) => f.id !== "010"); // drop Antarctica
const path = geoPath(geoNaturalEarth1().fitSize([W, H], { type: "FeatureCollection", features: land }));
const SHAPES = land.map((f, i) => ({ key: String(f.id ?? i), id: f.id === undefined ? null : String(f.id), name: f.properties.name, d: path(f) ?? "" }));

export default function WorldMap({ countries }: { countries: CountryCount[] }) {
  const byId = new Map<string, number>();
  for (const c of countries) {
    const id = c.country ? ATLAS_ID[c.country] : undefined;
    if (id) byId.set(id, c.count);
  }
  const max = Math.max(1, ...byId.values());
  return (
    <svg className="worldmap" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Online visitors by country">
      {SHAPES.map((s) => {
        const n = s.id ? byId.get(s.id) : undefined;
        return (
          <path key={s.key} d={s.d} className={n ? "on" : undefined}
            style={n ? { fill: `color-mix(in srgb, var(--accent) ${Math.round(40 + 60 * n / max)}%, var(--panel2))` } : undefined}>
            <title>{n ? `${s.name}: ${n}` : s.name}</title>
          </path>
        );
      })}
    </svg>
  );
}
