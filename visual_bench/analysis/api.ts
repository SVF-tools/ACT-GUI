// Route: GET /api/runs/{id}/layers.
import { call } from "../shared/http";
import type { LayerStatesOut, PropagationIndexOut, PropagationLayerOut, PropagationKeyOut } from "../generated/wire";

export const layers = (id: string) => call<LayerStatesOut>(`/api/runs/${id}/layers`);

export type PropagationFilter = Pick<PropagationKeyOut, "scope" | "pass_" | "stage" | "version">;
export const propagation = (id: string) => call<PropagationIndexOut>(`/api/runs/${id}/propagation`);
/** fields: only these tensors (the neuron map); neuron: every tensor sliced to one neuron (the detail panel). */
export type PropagationSlice = { fields?: string[]; neuron?: number };
export const propagationLayer = (id: string, layer: number, filter: PropagationFilter, slice: PropagationSlice = {}) => {
  const params = new URLSearchParams({
    scope: filter.scope, pass_: filter.pass_, stage: filter.stage, version: String(filter.version),
  });
  if (slice.fields) params.set("fields", slice.fields.join(","));
  if (slice.neuron !== undefined) params.set("neuron", String(slice.neuron));
  return call<PropagationLayerOut>(`/api/runs/${id}/propagation/layers/${layer}?${params}`);
};
