import { describe, expect, it } from "vitest";
import { fmt, indexRanges, num } from "./wire";

describe("wire numbers", () => {
  it("decodes finite numbers and all explicit non-finite markers", () => {
    expect(num(1.25)).toBe(1.25);
    expect(num(-0)).toBe(-0);
    expect(num("Infinity")).toBe(Infinity);
    expect(num("-Infinity")).toBe(-Infinity);
    expect(num("NaN")).toBeNaN();
  });

  it("formats ordinary values with the requested precision", () => {
    expect(fmt(0)).toBe("0.0000");
    expect(fmt(1.23456)).toBe("1.2346");
    expect(fmt(-1.25, 1)).toBe("-1.3");
    expect(fmt(0.001)).toBe("0.0010");
    expect(fmt(9999)).toBe("9999.0000");
  });

  it("uses exponential notation outside the display thresholds", () => {
    expect(fmt(10000)).toBe("1.00e+4");
    expect(fmt(-10000)).toBe("-1.00e+4");
    expect(fmt(0.0001)).toBe("1.00e-4");
    expect(fmt(-0.0001)).toBe("-1.00e-4");
    expect(fmt(Infinity)).toBe("Infinity");
    expect(fmt(-Infinity)).toBe("-Infinity");
    expect(fmt(NaN)).toBe("NaN");
  });
});

describe("indexRanges", () => {
  it("folds only ascending runs of at least three without sorting the batch", () => {
    expect(indexRanges([4024, 1, 9873, 3, 4, 5])).toBe("4024, 1, 9873, 3–5");
    expect(indexRanges([1, 2, 4, 5, 6, 9])).toBe("1, 2, 4–6, 9");
  });

  it("preserves empty, single, repeated, and descending indices", () => {
    expect(indexRanges([])).toBe("");
    expect(indexRanges([7])).toBe("7");
    expect(indexRanges([3, 3, 2, 1])).toBe("3, 3, 2, 1");
  });
});
