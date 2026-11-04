// Route: GET /api/runs/{id}/layers.
import { call } from "../shared/http";
import type { LayerStatesOut } from "../generated/wire";

export const layers = (id: string) => call<LayerStatesOut>(`/api/runs/${id}/layers`);
