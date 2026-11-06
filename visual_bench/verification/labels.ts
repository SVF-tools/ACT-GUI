import type { RunOut, RunRequest } from "../generated/wire";
type Method = RunRequest["method"];
export const METHOD_LABEL: Record<Method, string> = {
  fuzz: "fuzz (ACTFuzzer)", interval: "verify (verify_once)", bab: "BaB (verify_bab_batched)",
};

const ALPHA_LABEL = { fixed: "", optimize: "α×", optimize_refresh: "α+bounds×" } as const;
/** " · dual · α×50" style suffix of a run's method: its domain and, for dual runs, how alpha was optimized. */
export function runDomainLabel(run: Pick<RunOut, "domain" | "dual">): string {
  if (!run.domain) return "";
  const alpha = run.dual?.alpha ?? "fixed";
  return ` · ${run.domain}${alpha === "fixed" ? "" : ` · ${ALPHA_LABEL[alpha]}${run.dual?.iterations ?? ""}`}`;
}
