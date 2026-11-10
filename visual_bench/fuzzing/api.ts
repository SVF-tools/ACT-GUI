// Fuzz options, live commands, run projections, and saved counterexample export.
import { call } from "../shared/http";
import type { FuzzingOut, FuzzOptions, SavedCounterexampleOut, FuzzOptionsSchemaOut,
  FuzzControlRequest, FuzzControlOut } from "../generated/wire";
export type { FuzzOptionOut, FuzzControlRequest } from "../generated/wire";

export const fuzzDefaults = () => call<FuzzOptions>("/api/fuzz/defaults");
export const fuzzOptions = () => call<FuzzOptionsSchemaOut>("/api/fuzz/options");
export const fuzzing = (id: string) => call<FuzzingOut>(`/api/runs/${id}/fuzzing`);
export const fuzzControl = (id: string, request: FuzzControlRequest) =>
  call<FuzzControlOut>(`/api/runs/${id}/fuzz/control`, { method: "POST", body: JSON.stringify(request) });
export const saveCounterexample = (id: string, index: number) =>
  call<SavedCounterexampleOut>(`/api/runs/${id}/saved-counterexamples`, { method: "POST", body: JSON.stringify({ index }) });
export const savedCounterexampleUrl = (id: string, index: number) => `/api/runs/${id}/saved-counterexamples/${index}/vnnlib`;
