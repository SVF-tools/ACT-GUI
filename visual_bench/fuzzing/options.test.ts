import { describe, expect, it } from "vitest";
import type { FuzzOptionOut } from "./api";
import type { FuzzSettingsValue } from "./FuzzSettings";
import { changedLiveOptions, launchDefaults, launchName, launchOptions, parseNumber, validOption } from "./options";

const option = (overrides: Partial<FuzzOptionOut> = {}): FuzzOptionOut => ({
  name: "perturb_scale", kind: "float", live: true, description: "", choices: [],
  minimum: 0, maximum: 1, exclusive_minimum: true, default: 0.1, ...overrides,
});
const defaults: FuzzSettingsValue = {
  max_iterations: 1000, rng_seed: 0, stop_on_first: true,
  coverage_strategy: "GlobalCov", activation_threshold: 0,
  seed_selection_strategy: "energy", perturb_mode: "adaptive_scalar", perturb_scale: 0.1,
  pgd_restarts: 10, pgd_restarts_binarized: 50,
  mutation_weights: { gradient: 1, pgd: 1, activation: 1, boundary: 1, random: 1 },
};

describe("schema-driven launch settings", () => {
  it("preserves every launch field when an older engine has no option schema", () => {
    expect(launchOptions(defaults).map((item) => launchName(item.name)).sort()).toEqual(Object.keys(defaults).sort());
  });
  it("uses schema constraints and keeps the legacy launch field name", () => {
    const stop = option({ name: "stop_on_first_violation", kind: "bool", default: false });
    const scale = option({ maximum: 0.5 });
    const options = launchOptions(defaults, [stop, scale]);
    expect(options.find((item) => launchName(item.name) === "stop_on_first")).toBe(stop);
    expect(options.find((item) => item.name === "perturb_scale")).toBe(scale);
    expect(options.find((item) => item.name === "rng_seed")?.default).toBe(0);
  });
  it("uses schema defaults without leaking live-only or unknown keys into the launch request", () => {
    const result = launchDefaults(defaults, [
      option({ default: 0.25 }),
      option({ name: "stop_on_first_violation", kind: "bool", default: false }),
      option({ name: "timeout_seconds", default: 30 }),
    ]);
    expect(result).toEqual({ ...defaults, perturb_scale: 0.25, stop_on_first: false });
    expect(defaults.perturb_scale).toBe(0.1);
  });
});

describe("option input parsing and validation", () => {
  it("does not convert an empty input to zero", () => {
    expect(parseNumber("")).toBeNaN();
    expect(parseNumber(" ")).toBeNaN();
    expect(parseNumber("0")).toBe(0);
    expect(parseNumber("1e-2")).toBe(0.01);
  });
  it("enforces finite numbers and exclusive lower bounds", () => {
    for (const value of [0, -1, 1.1, NaN, Infinity, "0.5"]) expect(validOption(option(), value)).toBe(false);
    expect(validOption(option(), 0.5)).toBe(true);
    expect(validOption(option(), 1)).toBe(true);
    expect(validOption(option({ exclusive_minimum: false }), 0)).toBe(true);
  });
  it("allows unbounded numbers but requires integer values for int options", () => {
    const count = option({ kind: "int", minimum: 1, maximum: null, exclusive_minimum: false });
    expect(validOption(count, 2000000)).toBe(true);
    expect(validOption(count, 1.5)).toBe(false);
    expect(validOption(count, 0)).toBe(false);
  });
  it("keeps booleans and choices typed", () => {
    const toggle = option({ kind: "bool" });
    expect(validOption(toggle, false)).toBe(true);
    expect(validOption(toggle, "false")).toBe(false);
    const mode = option({ kind: "choice", choices: ["fixed", "adaptive_scalar"] });
    expect(validOption(mode, "fixed")).toBe(true);
    expect(validOption(mode, "unknown")).toBe(false);
  });
  it("requires nonnegative complete mutation weights and at least one positive weight", () => {
    const weights = option({ kind: "weights" });
    expect(validOption(weights, defaults.mutation_weights)).toBe(true);
    expect(validOption(weights, { ...defaults.mutation_weights, pgd: -1 })).toBe(false);
    expect(validOption(weights, { ...defaults.mutation_weights, pgd: NaN })).toBe(false);
    expect(validOption(weights, { pgd: 1 })).toBe(false);
    expect(validOption(weights, Object.fromEntries(Object.keys(defaults.mutation_weights).map((key) => [key, 0])))).toBe(false);
  });
});

describe("live update payloads", () => {
  it("sends only edited live fields, never launch-only or unknown fields", () => {
    expect(changedLiveOptions([option(), option({ name: "rng_seed", live: false })],
      { perturb_scale: 0.1, max_iterations: 1000 },
      { perturb_scale: 0.2, rng_seed: 9, unknown: true })).toEqual({ perturb_scale: 0.2 });
  });
  it("does not resend a value already observed through SSE", () => {
    expect(changedLiveOptions([option()], { perturb_scale: 0.2 }, { perturb_scale: 0.2 })).toEqual({});
  });
  it("compares weight objects independently of key order", () => {
    const weights = option({ name: "mutation_weights", kind: "weights" });
    const current = { mutation_weights: defaults.mutation_weights };
    const reordered = Object.fromEntries(Object.entries(defaults.mutation_weights).reverse());
    expect(changedLiveOptions([weights], current, { mutation_weights: reordered })).toEqual({});
    const changed = { ...reordered, pgd: 2 };
    expect(changedLiveOptions([weights], current, { mutation_weights: changed })).toEqual({ mutation_weights: changed });
  });
  it("keeps zero and false changes instead of dropping falsy values", () => {
    const toggle = option({ name: "stop_on_first_violation", kind: "bool" });
    expect(changedLiveOptions([option({ exclusive_minimum: false }), toggle],
      { perturb_scale: 0.1, stop_on_first_violation: true },
      { perturb_scale: 0, stop_on_first_violation: false })).toEqual({ perturb_scale: 0, stop_on_first_violation: false });
  });
});
