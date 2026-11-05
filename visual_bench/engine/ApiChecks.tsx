import type { ApiCheckOut } from "../generated/wire";

// Per capability: how many of the ACT symbols its bridge adapter calls resolved on the checkout.
export function ApiChecks({ checks }: { checks: ApiCheckOut[] }) {
  const byCap = new Map<string, ApiCheckOut[]>();
  for (const c of checks) byCap.set(c.capability, [...(byCap.get(c.capability) ?? []), c]);
  const failed = checks.filter((c) => !c.ok);
  if (checks.length === 0) return <p className="note">No API checks ran (ACT could not be imported).</p>;
  return (
    <details open={failed.length > 0}>
      <summary>
        API parity: <b className={failed.length ? "state bad" : "state good"}>
          {failed.length ? `${failed.length} of ${checks.length} checks failed` : `all ${checks.length} checks pass`}
        </b>
      </summary>
      <div className="kv">
        {[...byCap].map(([cap, cs]) => {
          const bad = cs.filter((c) => !c.ok);
          return [
            <span key={`${cap}-k`}>{cap}</span>,
            <b key={`${cap}-v`} className={bad.length ? "state bad" : "state good"}
              title={bad.map((c) => c.detail).join("\n")}>
              {bad[0] ? `${bad[0].detail}${bad.length > 1 ? ` (+${bad.length - 1} more)` : ""}` : `${cs.length} ok`}
            </b>,
          ];
        })}
      </div>
    </details>
  );
}
