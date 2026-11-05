// Routes: /api/fuzz/defaults, /api/runs/{id}/fuzzing, /saved-counterexamples and /{index}/vnnlib.
import { call } from "../shared/http";
import type { FuzzingOut, FuzzOptions, SavedCounterexampleOut } from "../generated/wire";

export const fuzzDefaults = () => call<FuzzOptions>("/api/fuzz/defaults");
export const fuzzing = (id: string) => call<FuzzingOut>(`/api/runs/${id}/fuzzing`);
export const saveCounterexample = (id: string, index: number) =>
  call<SavedCounterexampleOut>(`/api/runs/${id}/saved-counterexamples`, { method: "POST", body: JSON.stringify({ index }) });
export const savedCounterexampleUrl = (id: string, index: number) => `/api/runs/${id}/saved-counterexamples/${index}/vnnlib`;
