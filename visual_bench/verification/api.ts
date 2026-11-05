// Routes: GET/POST /api/runs, GET /api/runs/{id}, POST /api/runs/{id}/stop, /api/runs/{id}/saved-counterexample[/vnnlib],
// GET /api/runs/{id}/snapshot (reproduction zip).
import { call } from "../shared/http";
import type { RunList, RunOut, RunRequest } from "../generated/wire";

export const runs = () => call<RunList>("/api/runs");
export const run = (id: string) => call<RunOut>(`/api/runs/${id}`);
export const startRun = (req: RunRequest) => call<RunOut>("/api/runs", { method: "POST", body: JSON.stringify(req) });
export const saveCounterexample = (id: string) => call<RunOut>(`/api/runs/${id}/saved-counterexample`, { method: "POST" });
export const savedCounterexampleUrl = (id: string) => `/api/runs/${id}/saved-counterexample/vnnlib`;
export const snapshotUrl = (id: string) => `/api/runs/${id}/snapshot`;
export const stopRun = (id: string) => call<RunOut>(`/api/runs/${id}/stop`, { method: "POST" });
