// Route: GET /api/runs/{id}/coverage.
import { call } from "../shared/http";
import type { CoverageOut } from "../generated/wire";

export const coverage = (id: string) => call<CoverageOut>(`/api/runs/${id}/coverage`);
