import type { Selection } from "./selection";

export function ContextBar({ sel }: { sel: Selection }) {
  return (
    <div className="context" aria-label="research context">
      <Ctx label="model" value={sel.modelId} />
      <Ctx label="run" value={sel.runId} />
      <Ctx label="layer" value={sel.layerId} />
      <Ctx label="index" value={sel.neuron} />
    </div>
  );
}

function Ctx({ label, value }: { label: string; value: string | number | null }) {
  return (
    <span className={value === null ? "ctx unset" : "ctx"}>
      <b>{label}</b> {value === null ? "—" : String(value)}
    </span>
  );
}
