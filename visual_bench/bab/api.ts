// Routes: GET /api/runs/{id}/coverage, GET /api/runs/{id}/bab?root=&limit=, GET /api/runs/{id}/bab/nodes/{node_id}.
import { call } from "../shared/http";
import type { BabNodeDetailOut, BabTreeOut, CoverageOut } from "../generated/wire";

export const coverage = (id: string) => call<CoverageOut>(`/api/runs/${id}/coverage`);
export const babTree = (id: string, root: number) => call<BabTreeOut>(`/api/runs/${id}/bab?root=${root}`);
export const babNode = (id: string, node: number) => call<BabNodeDetailOut>(`/api/runs/${id}/bab/nodes/${node}`);
