import { describe, expect, it } from "vitest";
import { defaultMode, modeForId, modeForMethod, modes } from "./modes";

describe("run mode registry", () => {
  it("preserves mode order and the default verification method", () => {
    expect(modes.map((mode) => mode.id)).toEqual(["Fuzzing", "Verification", "BaB"]);
    expect(modeForId(defaultMode).method).toBe("interval");
  });

  it("maps every supported method to exactly one registered view and back", () => {
    expect(modes.map((mode) => mode.method)).toEqual(["fuzz", "interval", "bab"]);
    for (const mode of modes) {
      expect(modeForMethod(mode.method)).toBe(mode);
      expect(modeForId(mode.id)).toBe(mode);
      expect(typeof mode.View).toBe("function");
    }
    expect(new Set(modes.map((mode) => mode.method)).size).toBe(modes.length);
  });
});
