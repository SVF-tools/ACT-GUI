import { lazy, Suspense, useState } from "react";
import type { CountryCount } from "../generated/wire";
import { usePresence } from "./hooks";

const WorldMap = lazy(() => import("./WorldMap"));
const regionNames = new Intl.DisplayNames(["en"], { type: "region" });

const flag = (code: string) => String.fromCodePoint(...[...code].map((ch) => 0x1f1a5 + ch.charCodeAt(0)));
const countryLabel = (code: string | null | undefined) => (code ? `${flag(code)} ${regionNames.of(code) ?? code}` : "Local / unknown");

// Footer bar under Run history: how many browsers have the workbench open, and from which countries on hover.
export function PresenceBar() {
  const presence = usePresence();
  const [open, setOpen] = useState(false);
  const n = presence.data?.online;
  return (
    <div className="presence" tabIndex={0} onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}>
      <span className={presence.isError ? "presencedot off" : "presencedot"} />
      {presence.isError ? "Online count unavailable"
        : n === undefined ? "Counting visitors…"
        : <><b key={n}>{n}</b> {n === 1 ? "person" : "people"} online</>}
      {open && presence.data && <CountryCard countries={presence.data.countries} windowS={presence.data.window_s} />}
    </div>
  );
}

function CountryCard({ countries, windowS }: { countries: CountryCount[]; windowS: number }) {
  return (
    <div className="presencepop" role="tooltip">
      <Suspense fallback={<div className="worldmap loading">Loading map…</div>}>
        <WorldMap countries={countries} />
      </Suspense>
      <ul className="presencelist">
        {countries.map((c) => (
          <li key={c.country ?? "unknown"}><span>{countryLabel(c.country)}</span><b>{c.count}</b></li>
        ))}
      </ul>
      <div className="note">Browsers active in the last {windowS} s, by Cloudflare country.</div>
    </div>
  );
}
