import { useState } from "react";

// Saves ACT's counterexample #index on the run record (idempotent on the server).
export function SaveButton({ index, saved, onSave }: { index: number; saved: boolean; onSave: (index: number) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (saved) return <span className="chip good" title="saved on this run's record; export it under Saved counterexamples">saved #{index + 1}</span>;
  async function save() {
    setBusy(true);
    setErr(null);
    try {
      await onSave(index);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button className="secondary small" disabled={busy} onClick={save}>{busy ? "Saving…" : `Save counterexample #${index + 1}`}</button>
      {err && <span className="state bad">{err}</span>}
    </>
  );
}
