// Routes: GET/POST /api/runs, GET /api/runs/{id}, POST /api/runs/{id}/stop, /api/runs/{id}/saved-counterexample[/vnnlib],
// GET /api/runs/{id}/snapshot (reproduction zip), GET /api/verification/defaults, GET /api/verification/bab-options.
import { call } from "../shared/http";
import type { BabOptionsOut, RunList, RunOut, RunRequest, VerifyDefaults } from "../generated/wire";

export const runs = () => call<RunList>("/api/runs");
export const run = (id: string) => call<RunOut>(`/api/runs/${id}`);
export const startRun = (req: RunRequest) => call<RunOut>("/api/runs", { method: "POST", body: JSON.stringify(req) });
// row: the batch row whose counterexample to save/export; null means the run's summary counterexample.
const rowQuery = (row: number | null) => (row === null ? "" : `?row=${row}`);
export const saveCounterexample = (id: string, row: number | null) =>
  call<RunOut>(`/api/runs/${id}/saved-counterexample${rowQuery(row)}`, { method: "POST" });
export const savedCounterexampleUrl = (id: string, row: number | null) =>
  `/api/runs/${id}/saved-counterexample/vnnlib${rowQuery(row)}`;
export const snapshotUrl = (id: string) => `/api/runs/${id}/snapshot`;
export const stopRun = (id: string) => call<RunOut>(`/api/runs/${id}/stop`, { method: "POST" });
export const verificationDefaults = () => call<VerifyDefaults>("/api/verification/defaults");
export const babOptions = () => call<BabOptionsOut>("/api/verification/bab-options");
