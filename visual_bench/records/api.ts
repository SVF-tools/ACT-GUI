// Routes: GET /api/runs/{id} and GET /api/runs/{id}/export.
import { call } from "../shared/http";
import type { RunOut } from "../generated/wire";

export const run = (id: string) => call<RunOut>(`/api/runs/${id}`);
export const exportUrl = (id: string) => `/api/runs/${id}/export`;
