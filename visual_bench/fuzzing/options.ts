import type { FuzzOptionOut } from "./api";
import type { FuzzSettingsValue } from "./FuzzSettings";

export type FuzzOptionValue = FuzzOptionOut["default"];
export const WEIGHTS = ["pgd", "activation", "boundary", "random", "gradient"] as const;

const LABELS: Record<string, string> = {
  max_iterations: "Max iterations", rng_seed: "RNG seed", timeout_seconds: "Timeout (s)",
  stop_on_first_violation: "stop at first counterexample", stop_on_first: "stop at first counterexample",
  mutation_weights: "Mutation weights", perturb_mode: "Perturb mode", perturb_scale: "Perturb scale",
  seed_selection_strategy: "Seed selection", pgd_restarts: "PGD restarts",
  pgd_restarts_binarized: "PGD restarts (binarized)", coverage_strategy: "Coverage strategy",
  activation_threshold: "Activation threshold",
};
const CHOICES: Record<string, string> = {
  adaptive_scalar: "isotropic", adaptive_perdim: "anisotropic", fixed: "fixed",
  GlobalCov: "global", BestInputCov: "best input",
};
export const optionLabel = (name: string) => LABELS[name] ?? name.replaceAll("_", " ");
export const choiceLabel = (name: string) => CHOICES[name] ?? name.replaceAll("_", " ");
export const launchName = (name: string) => name === "stop_on_first_violation" ? "stop_on_first" : name;

// Older engines expose only defaults. Preserve their complete launch form.
export function launchOptions(defaults: FuzzSettingsValue, schema: FuzzOptionOut[] = []): FuzzOptionOut[] {
  const fallback: [keyof FuzzSettingsValue, FuzzOptionOut["kind"], number | null, number | null, string[]?][] = [
    ["max_iterations", "int", 1, 1000000], ["rng_seed", "int", 0, null],
    ["stop_on_first", "bool", null, null],
    ["coverage_strategy", "choice", null, null, ["GlobalCov", "BestInputCov"]],
    ["activation_threshold", "float", 0, null],
    ["seed_selection_strategy", "choice", null, null, ["energy", "random"]],
    ["perturb_mode", "choice", null, null, ["adaptive_scalar", "adaptive_perdim", "fixed"]],
    ["perturb_scale", "float", 0, 1], ["pgd_restarts", "int", 1, 100],
    ["pgd_restarts_binarized", "int", 1, 200], ["mutation_weights", "weights", 0, null],
  ];
  return fallback.map(([name, kind, minimum, maximum, choices = []]) =>
    schema.find((option) => launchName(option.name) === name) ?? {
      name, kind, minimum, maximum, choices, live: false, description: "",
      exclusive_minimum: false, default: defaults[name],
    });
}

export function launchDefaults(defaults: FuzzSettingsValue, schema: FuzzOptionOut[] = []): FuzzSettingsValue {
  const values = Object.fromEntries(schema
    .filter((option) => Object.hasOwn(defaults, launchName(option.name)))
    .map((option) => [launchName(option.name), option.default]));
  return { ...defaults, ...values };
}

export const parseNumber = (value: string) => value.trim() === "" ? NaN : Number(value);

export function validOption(option: FuzzOptionOut, value: unknown): boolean {
  if (option.kind === "bool") return typeof value === "boolean";
  if (option.kind === "choice") return typeof value === "string" && option.choices.includes(value);
  if (option.kind === "weights") {
    if (!value || typeof value !== "object") return false;
    const weights = value as Record<string, unknown>;
    return WEIGHTS.every((name) => typeof weights[name] === "number" && Number.isFinite(weights[name]) && weights[name] >= 0)
      && WEIGHTS.some((name) => Number(weights[name]) > 0);
  }
  return typeof value === "number" && Number.isFinite(value)
    && (option.kind !== "int" || Number.isInteger(value))
    && (option.minimum === null || (option.exclusive_minimum ? value > option.minimum : value >= option.minimum))
    && (option.maximum === null || value <= option.maximum);
}

function sameValue(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true;
  if (!left || !right || typeof left !== "object" || typeof right !== "object") return false;
  const a = Object.entries(left), b = Object.entries(right);
  return a.length === b.length && a.every(([key, value]) => Object.hasOwn(right, key)
    && sameValue(value, (right as Record<string, unknown>)[key]));
}

/** Only explicitly edited live fields are commands; unrelated SSE updates remain untouched. */
export function changedLiveOptions(options: FuzzOptionOut[], current: Record<string, FuzzOptionValue>, draft: Record<string, FuzzOptionValue>) {
  const liveNames = new Set(options.filter((option) => option.live).map((option) => option.name));
  return Object.fromEntries(Object.entries(draft)
    .filter(([name, value]) => liveNames.has(name) && !sameValue(value, current[name])));
}

export function displayOptionValue(value: unknown): string {
  if (value !== null && typeof value === "object") {
    return Object.entries(value).map(([key, item]) => `${optionLabel(key)}: ${displayOptionValue(item)}`).join(", ");
  }
  if (typeof value === "string") return choiceLabel(value);
  return value == null ? "none" : String(value);
}
