import type { RunRequest } from "../generated/wire";
type Method = RunRequest["method"];
export const METHOD_LABEL: Record<Method, string> = {
  fuzz: "fuzz (ACTFuzzer)", interval: "verify (verify_once)", bab: "BaB (verify_bab_batched)",
};
