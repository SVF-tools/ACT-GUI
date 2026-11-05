// Onboarding tour: step content, first-visit persistence, and card placement (pure, testable without a DOM).

export type TourStep = {
  /** Value of the `data-tour` attribute to spotlight; null shows a centered card. */
  target: string | null;
  title: string;
  body: string;
  /** Shown instead of the spotlight when the target is not on screen (e.g. no model selected yet). */
  missing?: string;
  /** The step stays open, with only its region clickable, until a model is loaded and active; then the tour advances. */
  waitFor?: "model";
};

export const TOUR_STEPS: readonly TourStep[] = [
  {
    target: null,
    title: "Welcome to the ACT workbench",
    body: "This short tour shows where things are: load a network, run ACT, and read the results. Use the arrow keys or the buttons; press Esc or Skip to leave at any time.",
  },
  {
    target: "load",
    title: "1 · Build and load a model",
    body: "Pick a Torch image classifier with a test image and eps (or a VNN-COMP ONNX + VNN-LIB instance), then press Build and load. Each image/eps choice becomes its own model snapshot. The tour continues on the loaded model.",
    waitFor: "model",
  },
  {
    target: "models",
    title: "2 · Your models",
    body: "The model you just built is now active. Pinned catalog networks and every model you load are listed here; click one later to switch.",
  },
  {
    target: "network",
    title: "3 · Inspect the network",
    body: "The layer graph comes from ACT. Click a layer to select it; the specification and layer detail below follow your selection.",
    missing: "Select a model in the sidebar to see its layer graph here.",
  },
  {
    target: "runs",
    title: "4 · Configure and run ACT",
    body: "Choose a method (fuzzing, interval verification, or BaB), set the budget and its options, then press Run ACT. A running job can be stopped from the run history.",
    missing: "Run settings appear once a model is selected.",
  },
  {
    target: "modes",
    title: "5 · Read the results",
    body: "Fuzzing shows mutated inputs, coverage, and counterexamples live; Verification shows the ACT verdict and per-layer bounds; BaB shows the branch-and-bound search.",
    missing: "Result views appear once a model is selected.",
  },
  {
    target: "spec",
    title: "6 · Specification and layer detail",
    body: "The input domain (as images for MNIST/CIFAR) and the output property ACT checks, plus the parameters of the selected layer.",
    missing: "The specification appears once a model is selected.",
  },
  {
    target: "history",
    title: "7 · Run history",
    body: "Every run of the active model and method. Click one to reopen its results; live runs update as ACT commits events.",
    missing: "Run history appears once a model is selected.",
  },
  {
    target: "inspector",
    title: "8 · Engine, Records, Assistant",
    body: "Check the ACT engine and Gurobi license, browse run records, and ask the assistant about the selected layer (answers cite ACT evidence and never override its verdict).",
  },
  {
    target: "context",
    title: "9 · Research context",
    body: "The current model, run, layer, and index. Every view and the assistant use this same context. Engine and Gurobi status sit beside it.",
  },
  {
    target: "guide",
    title: "You are ready",
    body: "Reopen this tour any time with the Guide button.",
  },
];

const KEY = "act-gui.tour.v1";

/** True until the tour has been finished or skipped once in this browser. */
export function tourPending(): boolean {
  try {
    return localStorage.getItem(KEY) !== "done";
  } catch {
    return false; // storage blocked: do not show the tour on every load
  }
}

export function markTourDone() {
  try {
    localStorage.setItem(KEY, "done");
  } catch {
    // Without storage the tour will just not be remembered.
  }
}

export type Rect = { top: number; left: number; width: number; height: number };
export type Size = { width: number; height: number };

const GAP = 12;
const MARGIN = 8;

/** Top-left of the card: below the target, else above, else beside it, clamped inside the viewport. */
export function placeCard(target: Rect | null, card: Size, view: Size): { top: number; left: number } {
  const clamp = (v: number, max: number) => Math.max(MARGIN, Math.min(v, max - MARGIN));
  if (!target) return { top: clamp((view.height - card.height) / 2, view.height - card.height), left: clamp((view.width - card.width) / 2, view.width - card.width) };
  const left = clamp(target.left, view.width - card.width);
  const below = target.top + target.height + GAP;
  if (below + card.height <= view.height - MARGIN) return { top: below, left };
  const above = target.top - GAP - card.height;
  if (above >= MARGIN) return { top: above, left };
  const top = clamp(target.top, view.height - card.height);
  const right = target.left + target.width + GAP;
  if (right + card.width <= view.width - MARGIN) return { top, left: right };
  const beside = target.left - GAP - card.width;
  if (beside >= MARGIN) return { top, left: beside };
  return { top: clamp(view.height - card.height - MARGIN, view.height - card.height), left }; // overlaps a large target
}
