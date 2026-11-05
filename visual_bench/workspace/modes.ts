import { createElement, Fragment, type ComponentType } from "react";
import type { ModelDescriptionOut, RunRequest } from "../generated/wire";
import { AnalysisView } from "../analysis/AnalysisView";
import { BabView } from "../bab/BabView";
import { FuzzView } from "../fuzzing/FuzzView";
import { VerdictBanner } from "../verification/VerdictBanner";
import type { Selection } from "./selection";

export type ModeId = "Fuzzing" | "Verification" | "BaB";
export type Method = RunRequest["method"];
type ModeProps = {
  sel: Selection;
  model: ModelDescriptionOut;
  onSelectLayer: (id: number) => void;
  onSelectNeuron: (neuron: number | null) => void;
};

function VerificationMode(props: ModeProps) {
  return createElement(Fragment, null,
    createElement(VerdictBanner, { runId: props.sel.runId, model: props.model }),
    createElement(AnalysisView, props));
}

function BabMode({ sel, model }: ModeProps) {
  return createElement(Fragment, null,
    createElement(VerdictBanner, { runId: sel.runId, model }),
    createElement(BabView, { runId: sel.runId }));
}

function FuzzMode({ sel, model }: ModeProps) {
  return createElement(FuzzView, { runId: sel.runId, model });
}

// capability: the engine capability (bridge API checks) a mode needs to run ACT.
export const modes: readonly { id: ModeId; label: string; method: Method; capability: string; View: ComponentType<ModeProps> }[] = [
  { id: "Fuzzing", label: "Fuzzing", method: "fuzz", capability: "fuzz.actfuzzer", View: FuzzMode },
  { id: "Verification", label: "Verification", method: "interval", capability: "verify.interval", View: VerificationMode },
  { id: "BaB", label: "BaB", method: "bab", capability: "verify.bab", View: BabMode },
];

export const defaultMode: ModeId = "Verification";
export const modeForMethod = (method: Method) => modes.find((mode) => mode.method === method)!;
export const modeForId = (id: ModeId) => modes.find((mode) => mode.id === id)!;
