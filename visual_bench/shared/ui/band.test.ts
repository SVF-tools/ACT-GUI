import { describe, expect, it } from "vitest";
import { bandRange } from "./BandChart";

describe("bandRange", () => {
  it("spans every bound and marker value", () => {
    expect(bandRange([-1, 0], [0.5, 2], [{ label: "point", cls: "ce", values: [3, -2] }])).toEqual([-2, 3]);
  });

  it("ignores non-finite values and widens a degenerate range", () => {
    expect(bandRange([1, Number.NEGATIVE_INFINITY], [1, Number.NaN])).toEqual([0, 2]);
    expect(bandRange([], [])).toEqual([0, 1]);
  });
});
