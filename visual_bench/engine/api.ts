// Routes: GET /api/engine, GET /api/solvers/gurobi, PUT/DELETE /api/solvers/gurobi/license.
import { call } from "../shared/http";
import type { EngineInfoOut, SolverLicenseUpload, SolverStatusOut } from "../generated/wire";

export const engine = () => call<EngineInfoOut>("/api/engine");
export const gurobi = () => call<SolverStatusOut>("/api/solvers/gurobi");
export const uploadGurobiLicense = (req: SolverLicenseUpload) =>
  call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "PUT", body: JSON.stringify(req) });
export const removeGurobiLicense = () => call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "DELETE" });
