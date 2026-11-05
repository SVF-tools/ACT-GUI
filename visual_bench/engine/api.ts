// Routes: GET /api/health, GET /api/engine, GET/PUT /api/engine/source, POST /api/engine/source/check,
// GET /api/engine/branches?remote=|url=, GET /api/solvers/gurobi, PUT/DELETE /api/solvers/gurobi/license.
import { call } from "../shared/http";
import type {
  EngineBranchesOut, EngineInfoOut, EngineSourcesOut, EngineSwitchRequest, HealthOut, SolverLicenseUpload,
  SolverStatusOut,
} from "../generated/wire";

export const health = () => call<HealthOut>("/api/health");
export const checkEngine = (req: EngineSwitchRequest) =>
  call<EngineInfoOut>("/api/engine/source/check", { method: "POST", body: JSON.stringify(req) });

export const engine = () => call<EngineInfoOut>("/api/engine");
export const engineSources = () => call<EngineSourcesOut>("/api/engine/source");
export type RepoRef = { remote: string } | { url: string };
export const engineBranches = (ref: RepoRef) =>
  call<EngineBranchesOut>(`/api/engine/branches?${new URLSearchParams(ref).toString()}`);
export const switchEngine = (req: EngineSwitchRequest) =>
  call<EngineInfoOut>("/api/engine/source", { method: "PUT", body: JSON.stringify(req) });
export const gurobi = () => call<SolverStatusOut>("/api/solvers/gurobi");
export const uploadGurobiLicense = (req: SolverLicenseUpload) =>
  call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "PUT", body: JSON.stringify(req) });
export const removeGurobiLicense = () => call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "DELETE" });
