import { describe, expect, it } from "vitest";
import { placeCard, TOUR_STEPS } from "./tourSteps";

const view = { width: 1280, height: 800 };
const card = { width: 360, height: 200 };
const inside = (p: { top: number; left: number }) =>
  p.top >= 0 && p.left >= 0 && p.top + card.height <= view.height && p.left + card.width <= view.width;

describe("tour card placement", () => {
  it("centers the card when the step has no target", () => {
    expect(placeCard(null, card, view)).toEqual({ top: 300, left: 460 });
  });

  it("prefers below, then above, then beside the target", () => {
    expect(placeCard({ top: 50, left: 100, width: 200, height: 100 }, card, view)).toEqual({ top: 162, left: 100 });
    expect(placeCard({ top: 600, left: 100, width: 200, height: 150 }, card, view)).toEqual({ top: 388, left: 100 });
    expect(placeCard({ top: 60, left: 20, width: 300, height: 700 }, card, view)).toEqual({ top: 60, left: 332 });
    expect(placeCard({ top: 60, left: 900, width: 370, height: 700 }, card, view)).toEqual({ top: 60, left: 528 });
  });

  it("keeps the card inside the viewport for targets at the edges or covering the screen", () => {
    for (const t of [
      { top: 0, left: 1200, width: 80, height: 40 },
      { top: 760, left: 1250, width: 30, height: 40 },
      { top: 0, left: 0, width: 1280, height: 800 },
    ]) expect(inside(placeCard(t, card, view))).toBe(true);
  });
});

describe("tour steps", () => {
  it("uses unique targets so each step spotlights one region", () => {
    const targets = TOUR_STEPS.map((s) => s.target).filter((t) => t !== null);
    expect(new Set(targets).size).toBe(targets.length);
  });
});
