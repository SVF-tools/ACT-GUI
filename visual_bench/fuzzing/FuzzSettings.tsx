// ACTFuzzer settings of a fuzz run. Defaults come from GET /api/fuzz/defaults (the pinned ACT's pipeline.yaml).
import type { FuzzMutationWeights, FuzzOptions } from "../generated/wire";

export type FuzzSettingsValue = Required<Omit<FuzzOptions, "mutation_weights">> & {
  mutation_weights: Required<FuzzMutationWeights>;
};

const OPERATORS: [keyof FuzzMutationWeights, string][] = [
  ["pgd", "iterative PGD, projected each step"], ["activation", "DeepXplore-style, targets low-activation neurons"],
  ["boundary", "samples near the input-box boundary"], ["random", "Gaussian-noise baseline"],
  ["gradient", "single-step FGSM"],
];

export function FuzzSettings({ value, defaults, onChange }: {
  value: FuzzSettingsValue; defaults: FuzzSettingsValue; onChange: (v: FuzzSettingsValue) => void;
}) {
  const set = <K extends keyof FuzzSettingsValue>(k: K, v: FuzzSettingsValue[K]) => onChange({ ...value, [k]: v });
  const weight = (k: keyof FuzzMutationWeights, v: number) => set("mutation_weights", { ...value.mutation_weights, [k]: v });
  const w = value.mutation_weights;
  const total = w.gradient + w.pgd + w.activation + w.boundary + w.random;
  const changed = JSON.stringify(value) !== JSON.stringify(defaults);
  const num = (v: string) => (v === "" ? NaN : Number(v));

  return (
    <div className="fuzzsettings">
      <label>Max iterations
        <input type="number" min={1} max={1000000} value={value.max_iterations}
          onChange={(e) => set("max_iterations", num(e.target.value))} />
      </label>
      <label>RNG seed
        <input type="number" min={0} value={value.rng_seed} onChange={(e) => set("rng_seed", num(e.target.value))} />
      </label>
      <label className="check">
        <input type="checkbox" checked={value.stop_on_first} onChange={(e) => set("stop_on_first", e.target.checked)} />
        stop at first counterexample
      </label>
      <details className="fuzzadvanced" open={changed || undefined}>
        <summary>ACTFuzzer hyperparameters {changed && <span className="chip">modified</span>}</summary>
        <div className="fuzzgrid">
          <label title="GlobalCov: monotonic union over all inputs; BestInputCov: best per-input coverage">Coverage strategy
            <select value={value.coverage_strategy} onChange={(e) => set("coverage_strategy", e.target.value as FuzzSettingsValue["coverage_strategy"])}>
              <option value="GlobalCov">GlobalCov</option>
              <option value="BestInputCov">BestInputCov</option>
            </select>
          </label>
          <label title="a neuron counts as fired when its activation exceeds this">Activation threshold
            <input type="number" min={0} step="any" value={value.activation_threshold}
              onChange={(e) => set("activation_threshold", num(e.target.value))} />
          </label>
          <label title="energy: AFL-style prioritization; random: uniform">Seed selection
            <select value={value.seed_selection_strategy} onChange={(e) => set("seed_selection_strategy", e.target.value as FuzzSettingsValue["seed_selection_strategy"])}>
              <option value="energy">energy</option>
              <option value="random">random</option>
            </select>
          </label>
          <label title={"step per dimension = s·max(x−lb, ub−x), s = 1−(1−scale)^(n+1) for a seed selected n times. "
            + "isotropic: one step per sample (mean over dimensions); anisotropic: each dimension keeps its own step; "
            + "fixed: ACT's legacy constant steps"}>Perturb mode
            <select value={value.perturb_mode} onChange={(e) => set("perturb_mode", e.target.value as FuzzSettingsValue["perturb_mode"])}>
              <option value="adaptive_scalar">isotropic</option>
              <option value="adaptive_perdim">anisotropic</option>
              <option value="fixed">fixed</option>
            </select>
          </label>
          <label title="base fraction s₀ of the distance to the input-box boundary; grows with how often a seed is selected">Perturb scale
            <input type="number" min={0} max={1} step="any" value={value.perturb_scale}
              disabled={value.perturb_mode === "fixed"} onChange={(e) => set("perturb_scale", num(e.target.value))} />
          </label>
          <label title="independent PGD random starts per mutation">PGD restarts
            <input type="number" min={1} max={100} value={value.pgd_restarts} onChange={(e) => set("pgd_restarts", num(e.target.value))} />
          </label>
          <label title="PGD restarts used instead on a binarized network">PGD restarts (binarized)
            <input type="number" min={1} max={200} value={value.pgd_restarts_binarized}
              onChange={(e) => set("pgd_restarts_binarized", num(e.target.value))} />
          </label>
        </div>
        <div className="label">Mutation weights <small>relative; ACT normalizes them, 0 disables an operator</small></div>
        <div className="fuzzgrid">
          {OPERATORS.map(([k, hint]) => (
            <label key={k} title={hint}>{k} {total > 0 && <small>{Math.round((w[k] / total) * 100)}%</small>}
              <input type="number" min={0} step="any" value={w[k]} onChange={(e) => weight(k, num(e.target.value))} />
            </label>
          ))}
        </div>
        {!(total > 0) && <div className="error">At least one mutation weight must be above 0.</div>}
        <button type="button" disabled={!changed} onClick={() => onChange(defaults)}>Reset to ACT defaults</button>
      </details>
    </div>
  );
}
