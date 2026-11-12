// BaB run settings from GET /api/verification/bab-options: ACT owns the names, kinds, limits and defaults.
import type { BabOptionOut } from "../generated/wire";

export type BabValue = BabOptionOut["default"];
export type BabValues = Record<string, BabValue>;
// ACT's settings groups in display order; a group ACT adds later is shown after these.
export const BAB_GROUPS = ["bounding", "search", "dual", "advanced"] as const;

export const babOptionLabel = (name: string) => name.replace(/^(bab|dual)_/, "").replaceAll("_", " ");

export const babDefaults = (options: BabOptionOut[]): BabValues =>
  Object.fromEntries(options.map((o) => [o.name, o.default]));

export function babChanges(values: BabValues, options: BabOptionOut[]): BabValues {
  const changes: BabValues = {};
  for (const o of options) {
    const value = values[o.name];
    if (value !== undefined && value !== o.default) changes[o.name] = value;
  }
  return changes;
}

export function babValid(option: BabOptionOut, value: BabValue | undefined): boolean {
  if (option.kind === "bool") return typeof value === "boolean";
  if (option.kind === "choice") return typeof value === "string" && option.choices.includes(value);
  if (typeof value !== "number" || !Number.isFinite(value) || (option.kind === "int" && !Number.isInteger(value))) return false;
  const low = option.minimum;
  if (low !== null && (option.exclusive_minimum ? value <= low : value < low)) return false;
  return option.maximum === null || value <= option.maximum;
}
