// verify_once settings of a dual or hybridz run. Defaults come from GET /api/verification/defaults (ACT's DualConfig).
import type { DualOptions, HybridzOptions } from "../generated/wire";

export type VerifySettingsValue = { dual: Required<DualOptions>; hybridz: Required<HybridzOptions> };
type Dual = VerifySettingsValue["dual"];

const ALPHA: [Dual["alpha"], string, string][] = [
  ["fixed", "fixed slopes", "one backward pass with ACT's default ReLU slopes (no optimization)"],
  ["optimize", "optimize alpha", "Adam over the ReLU slopes alpha; the forward bounds stay fixed"],
  ["optimize_refresh", "optimize alpha + recompute bounds",
    "Adam over alpha; every iteration recomputes the forward pre-activation bounds from the current alpha"],
];

const num = (v: string) => (v === "" ? NaN : Number(v));

export function VerifySettings({ domain, value, defaults, onChange, optionsMissing }: {
  domain: "dual" | "hybridz"; value: VerifySettingsValue; defaults: VerifySettingsValue;
  onChange: (v: VerifySettingsValue) => void; optionsMissing: string | null;
}) {
  if (domain === "hybridz") {
    const h = value.hybridz;
    const changed = h.tolerance !== defaults.hybridz.tolerance;
    return (
      <div className="fuzzsettings">
        <details className="fuzzadvanced" open={changed || undefined}>
          <summary>HybridZ settings {changed && <span className="chip">modified</span>}</summary>
          <div className="fuzzgrid">
            <label title="MILP feasibility / spec tolerance of ACT's HybridZ verdict solver; its time limit is the run budget">Tolerance
              <input type="number" min={0} step="any" value={h.tolerance}
                onChange={(e) => onChange({ ...value, hybridz: { tolerance: num(e.target.value) } })} />
            </label>
          </div>
          <button type="button" disabled={!changed} onClick={() => onChange({ ...value, hybridz: defaults.hybridz })}>Reset to ACT defaults</button>
        </details>
      </div>
    );
  }
  const d = value.dual;
  const set = <K extends keyof Dual>(k: K, v: Dual[K]) => onChange({ ...value, dual: { ...d, [k]: v } });
  const fixed = d.alpha === "fixed";
  const off = optionsMissing !== null;
  const changed = JSON.stringify(d) !== JSON.stringify(defaults.dual);
  const advancedChanged = (Object.keys(d) as (keyof Dual)[])
    .some((k) => k !== "alpha" && k !== "iterations" && d[k] !== defaults.dual[k]);

  return (
    <div className="fuzzsettings">
      <label className="wide" title={ALPHA.find(([a]) => a === d.alpha)?.[2]}>Alpha
        <select value={d.alpha} disabled={off} onChange={(e) => set("alpha", e.target.value as Dual["alpha"])}>
          {ALPHA.map(([a, label, hint]) => <option key={a} value={a} title={hint}>{label}</option>)}
        </select>
      </label>
      <label title="Adam iterations over alpha (each one recomputes the forward bounds in the recompute mode)">Iterations
        <input type="number" min={1} max={10000} value={d.iterations} disabled={off || fixed}
          onChange={(e) => set("iterations", num(e.target.value))} />
      </label>
      <details className="fuzzadvanced" open={advancedChanged || undefined}>
        <summary>DualSolver hyperparameters {changed && <span className="chip">modified</span>}</summary>
        <div className="fuzzgrid">
          <label title="Adam learning rate of alpha">Learning rate α
            <input type="number" min={0} step="any" value={d.lr_alpha} disabled={off || fixed}
              onChange={(e) => set("lr_alpha", num(e.target.value))} />
          </label>
          <label title="multiplicative learning-rate decay per iteration (1 = none)">LR decay
            <input type="number" min={0} max={1} step="any" value={d.lr_decay} disabled={off || fixed}
              onChange={(e) => set("lr_decay", num(e.target.value))} />
          </label>
          <label title="stop after this many iterations without an improvement above the tolerance; 0 disables it">Stagnation patience
            <input type="number" min={0} value={d.stagnation_patience} disabled={off || fixed}
              onChange={(e) => set("stagnation_patience", num(e.target.value))} />
          </label>
          <label title="smallest bound improvement that counts as progress">Stagnation tolerance
            <input type="number" min={0} step="any" value={d.stagnation_tol} disabled={off || fixed}
              onChange={(e) => set("stagnation_tol", num(e.target.value))} />
          </label>
          <label title="optimization time limit in seconds; 0 disables it (the run budget still applies)">Max time (s)
            <input type="number" min={0} step="any" value={d.max_time_s} disabled={off || fixed}
              onChange={(e) => set("max_time_s", num(e.target.value))} />
          </label>
          <label title="above this many perturbed input dimensions the forward pass keeps interval bounds only">Forward linear cap
            <input type="number" min={0} value={d.forward_lin_max_perturbed} disabled={off}
              onChange={(e) => set("forward_lin_max_perturbed", num(e.target.value))} />
          </label>
          <label className="check" title="separate alpha per output specification row instead of one shared alpha">
            <input type="checkbox" checked={d.per_class_alpha} disabled={off || fixed}
              onChange={(e) => set("per_class_alpha", e.target.checked)} />
            per-class alpha
          </label>
        </div>
        <button type="button" disabled={!changed} onClick={() => onChange({ ...value, dual: defaults.dual })}>Reset to ACT defaults</button>
      </details>
      {off && <div className="note">Dual options are disabled on this ACT checkout. {optionsMissing}</div>}
    </div>
  );
}
