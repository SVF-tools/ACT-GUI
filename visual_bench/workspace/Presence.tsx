import { usePresence } from "./hooks";

// Footer bar under Run history: how many browsers have the workbench open right now.
export function PresenceBar() {
  const presence = usePresence();
  const n = presence.data?.online;
  return (
    <div className="presence" title="Browsers with the workbench open in the last 90 s">
      <span className={presence.isError ? "presencedot off" : "presencedot"} />
      {presence.isError ? "Online count unavailable"
        : n === undefined ? "Counting visitors…"
        : <><b key={n}>{n}</b> {n === 1 ? "person" : "people"} online</>}
    </div>
  );
}
