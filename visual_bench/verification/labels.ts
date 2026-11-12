import type { RunOut, RunRequest } from "../generated/wire";
type Method = RunRequest["method"];
export const METHOD_LABEL: Record<Method, string> = {
  fuzz: "fuzz (ACTFuzzer)", interval: "verify (verify_once)", bab: "BaB (verify_bab_batched)",
};

// ACT's BaB solver tiers (bab_solver_tier): lp bounds every wave with interval bounds and its LP solver.
export const BAB_TIER_LABEL: Record<string, string> = {
  lp: "interval (LP)", dual: "dual (fixed α)", dual_alpha: "dual α", dual_alpha_eta: "dual α + η",
};
const ALPHA_LABEL = { fixed: "", optimize: "α×", optimize_refresh: "α+bounds×" } as const;
/** " · dual · α×50" style suffix of a run's method: its domain and, for dual runs, how alpha was optimized;
 * for BaB runs, the solver tier. */
export function runDomainLabel(run: Pick<RunOut, "domain" | "dual" | "bab">): string {
  const tier = run.bab?.bab_solver_tier;
  if (typeof tier === "string") return ` · ${BAB_TIER_LABEL[tier] ?? tier}`;
  if (!run.domain) return "";
  const alpha = run.dual?.alpha ?? "fixed";
  return ` · ${run.domain}${alpha === "fixed" ? "" : ` · ${ALPHA_LABEL[alpha]}${run.dual?.iterations ?? ""}`}`;
}
