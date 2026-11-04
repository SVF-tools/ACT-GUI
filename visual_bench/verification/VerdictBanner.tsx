// ACT verdict of the selected run, shown at the top of the Verification and BaB modes.
// The verdict is ACT's (RunResultOut.verdict / act_status); this view only labels it.
import { fmt } from "../shared/wire";
import type { ModelDescriptionOut, RunOut } from "../generated/wire";
import { Pixels, specImageShape } from "../shared/ui/pixels";
import { useRun, useStopRun } from "./hooks";
import { StopButton } from "../shared/ui/StopButton";

const VERDICT: Record<string, { cls: string; title: string; text: string }> = {
  certified: { cls: "good", title: "CERTIFIED", text: "ACT proved the property holds for every input in the input spec." },
  falsified: { cls: "bad", title: "COUNTEREXAMPLE FOUND", text: "ACT found a concrete input inside the input spec whose output violates the property." },
  unknown: { cls: "warn", title: "UNKNOWN", text: "ACT could neither certify nor falsify the property with this method." },
  timeout: { cls: "warn", title: "TIMEOUT", text: "ACT ran out of budget before reaching a verdict." },
  error: { cls: "bad", title: "ERROR", text: "ACT reported an error instead of a verdict." },
};

export function VerdictBanner({ runId, model }: {
  runId: string | null; model: ModelDescriptionOut;
}) {
  const q = useRun(runId);
  const stopRun = useStopRun();
  if (!runId || q.status !== "success") return null;
  const run = q.data;
  if (run.status === "queued" || run.status === "running") {
    return (
      <div className="banner verdict bannerrow">
        <span><b className="vbig">RUNNING</b> {run.method}{run.domain ? ` · ${run.domain}` : ""} · {run.run_id} · no verdict yet.</span>
        <StopButton method={run.method} onStop={() => stopRun.mutateAsync(run.run_id)} />
      </div>
    );
  }
  if (run.status === "failed" || !run.result) {
    return (
      <div className="banner verdict bad">
        <b className="vbig">NO VERDICT</b> The run {run.error?.code === "stopped" ? "was stopped" : "failed"}: {run.error?.message ?? "no result recorded"}
      </div>
    );
  }
  const r = run.result;
  const v = VERDICT[r.verdict] ?? VERDICT.unknown!;
  return (
    <div className={`banner verdict ${v.cls}`}>
      <div className="verdicthead">
        <b className="vbig">{v.title}</b>
        <span className="chip">{run.method}{run.domain ? ` · ${run.domain}` : ""}</span>
        <span className="chip mono" title="raw ACT status">{r.act_status}</span>
        <span className="chip">{r.elapsed_s.toFixed(2)} s</span>
        {run.matches_native === true && <span className="chip good" title="matches the recorded native ACT result">= native</span>}
        {run.matches_native === false && <span className="chip warn" title={`native: ${run.native_reference?.status}`}>≠ native</span>}
      </div>
      <div>{v.text}</div>
      {r.verdict === "falsified" && r.counterexample && <Counterexample xs={r.counterexample} run={run} model={model} />}
    </div>
  );
}

function Counterexample({ xs, run, model }: { xs: number[]; run: RunOut; model: ModelDescriptionOut }) {
  const spec = model.model_id === run.model_id ? model.input_specs[0] : undefined;
  const s = spec ? specImageShape(spec.shape, spec.dataset) : null;
  const shape = s && s.c * s.h * s.w === xs.length ? s : null;
  const lo = Math.min(...xs), hi = Math.max(...xs);
  const unit = lo >= 0 && hi <= 1;
  return (
    <div className="verdictce">
      {shape && <Pixels xs={xs} shape={shape} lo={unit ? 0 : lo} hi={unit ? 1 : hi} label="counterexample input" size="big" />}
      <span className="mono muted">
        x = [{xs.slice(0, 8).map((v) => fmt(v, 3)).join(", ")}{xs.length > 8 ? `, … (${xs.length})` : ""}]
      </span>
    </div>
  );
}
