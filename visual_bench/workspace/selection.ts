// Research context: the single source of the user's selection (WS-01/WS-02).
// Pure reducer; feature queries key their data by the selected identity.

export interface Selection {
  modelId: string | null;
  runId: string | null;
  layerId: number | null;
  neuron: number | null;
  /** Monotonic counter; every selection change creates a new revision. */
  revision: number;
}

export type SelectionAction =
  | { type: "selectModel"; modelId: string }
  | { type: "selectRun"; runId: string | null; modelId: string }
  | { type: "selectLayer"; layerId: number | null }
  | { type: "selectNeuron"; neuron: number | null };

export const initialSelection: Selection = { modelId: null, runId: null, layerId: null, neuron: null, revision: 0 };

export function selectionReducer(s: Selection, a: SelectionAction): Selection {
  switch (a.type) {
    case "selectModel":
      if (s.modelId === a.modelId) return s;
      // A different model invalidates run/layer/neuron: they belong to the old snapshot.
      return { modelId: a.modelId, runId: null, layerId: null, neuron: null, revision: s.revision + 1 };
    case "selectRun": {
      if (s.runId === a.runId && s.modelId === a.modelId) return s;
      const sameModel = s.modelId === a.modelId;
      return {
        modelId: a.modelId,
        runId: a.runId,
        layerId: sameModel ? s.layerId : null,
        neuron: sameModel ? s.neuron : null,
        revision: s.revision + 1,
      };
    }
    case "selectLayer":
      if (s.layerId === a.layerId) return s;
      return { ...s, layerId: a.layerId, neuron: null, revision: s.revision + 1 };
    case "selectNeuron":
      if (s.neuron === a.neuron) return s;
      return { ...s, neuron: a.neuron, revision: s.revision + 1 };
  }
}
