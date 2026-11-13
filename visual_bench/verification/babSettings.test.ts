import { describe, expect, it } from "vitest";
import type { BabOptionOut } from "../generated/wire";
import { babChanges, babDefaults, babValid } from "./babSettings";

const option = (overrides: Partial<BabOptionOut> = {}): BabOptionOut => ({
  name: "bab_max_nodes", kind: "int", description: "", choices: [], minimum: 1, maximum: null,
  exclusive_minimum: false, default: 100, group: "search", ...overrides,
});
const tier = option({ name: "bab_solver_tier", kind: "choice", choices: ["lp", "dual_alpha_eta"], default: "dual_alpha_eta",
  minimum: null, group: "bounding" });
const lr = option({ name: "dual_lr_alpha", kind: "float", minimum: 0, exclusive_minimum: true, default: 0.1, group: "dual" });

describe("BaB run settings", () => {
  it("sends only the settings that differ from ACT's defaults", () => {
    const options = [tier, option(), lr];
    const value = { ...babDefaults(options), bab_solver_tier: "lp", bab_max_nodes: 100, stale_setting: 3 };
    expect(babChanges(value, options)).toEqual({ bab_solver_tier: "lp" });
  });
  it("checks values against ACT's kinds and limits", () => {
    expect([babValid(option(), 0), babValid(option(), 1.5), babValid(option(), 1)]).toEqual([false, false, true]);
    expect([babValid(lr, 0), babValid(lr, Number.NaN), babValid(lr, 0.01)]).toEqual([false, false, true]);
    expect([babValid(tier, "dual"), babValid(tier, "lp")]).toEqual([false, true]);
  });
});
