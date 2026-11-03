// Typed browser client for the workbench service. Types are generated from Pydantic.
import type {
  CoverageOut, EngineInfoOut, ErrorResponse, ExplainRequest, ExplainResponse, FuzzingOut, LayerStatesOut,
  LoadModelBody, ModelDescriptionOut, ModelSummary, ProviderList, RunEvent, RunList, RunOut, RunRequest, SampleOut,
  SavedCounterexampleOut,
  SolverLicenseUpload, SolverStatusOut, SourcesOut,
} from "./generated/wire";

/** Mirrors schemas.WireNumber: finite float or an explicit non-finite marker. */
export type WireNumber = number | "Infinity" | "-Infinity" | "NaN";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err = (body as ErrorResponse | null)?.error;
    throw new ApiError(res.status, err?.code ?? "http_error", err?.message ?? `HTTP ${res.status}`);
  }
  return body as T;
}

export const api = {
  engine: () => call<EngineInfoOut>("/api/engine"),
  models: () => call<ModelSummary[]>("/api/models"),
  model: (id: string) => call<ModelDescriptionOut>(`/api/models/${encodeURIComponent(id)}`),
  loadModel: (body: LoadModelBody) => call<ModelSummary>("/api/models", { method: "POST", body: JSON.stringify(body) }),
  sources: () => call<SourcesOut>("/api/sources"),
  sample: (dataset: string, index: number) =>
    call<SampleOut>(`/api/sources/sample?dataset=${encodeURIComponent(dataset)}&index=${index}`),
  runs: () => call<RunList>("/api/runs"),
  run: (id: string) => call<RunOut>(`/api/runs/${id}`),
  startRun: (req: RunRequest) => call<RunOut>("/api/runs", { method: "POST", body: JSON.stringify(req) }),
  layers: (id: string) => call<LayerStatesOut>(`/api/runs/${id}/layers`),
  coverage: (id: string) => call<CoverageOut>(`/api/runs/${id}/coverage`),
  fuzzing: (id: string) => call<FuzzingOut>(`/api/runs/${id}/fuzzing`),
  stopRun: (id: string) => call<RunOut>(`/api/runs/${id}/stop`, { method: "POST" }),
  saveCounterexample: (id: string, index: number) =>
    call<SavedCounterexampleOut>(`/api/runs/${id}/saved-counterexamples`, { method: "POST", body: JSON.stringify({ index }) }),
  savedCounterexampleUrl: (id: string, index: number) => `/api/runs/${id}/saved-counterexamples/${index}/vnnlib`,
  providers: () => call<ProviderList>("/api/assistant/providers"),
  explain: (req: ExplainRequest) => call<ExplainResponse>("/api/assistant/explain", { method: "POST", body: JSON.stringify(req) }),
  exportUrl: (id: string) => `/api/runs/${id}/export`,
  gurobi: () => call<SolverStatusOut>("/api/solvers/gurobi"),
  uploadGurobiLicense: (req: SolverLicenseUpload) =>
    call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "PUT", body: JSON.stringify(req) }),
  removeGurobiLicense: () => call<SolverStatusOut>("/api/solvers/gurobi/license", { method: "DELETE" }),
};

/** Follow a run's committed events over SSE; the browser resumes with Last-Event-ID on reconnect. */
export function followRun(runId: string, onEvent: (ev: RunEvent) => void): () => void {
  const src = new EventSource(`/api/runs/${runId}/events`);
  src.addEventListener("run", (e) => onEvent(JSON.parse((e as MessageEvent<string>).data) as RunEvent));
  src.addEventListener("end", () => src.close());
  return () => src.close();
}

/** Decode the explicit non-finite encoding used on the wire. */
export function num(x: WireNumber): number {
  if (typeof x === "number") return x;
  return x === "Infinity" ? Infinity : x === "-Infinity" ? -Infinity : NaN;
}

export function fmt(x: number, digits = 4): string {
  if (!Number.isFinite(x)) return String(x);
  return Math.abs(x) >= 1e4 || (Math.abs(x) < 1e-3 && x !== 0) ? x.toExponential(2) : x.toFixed(digits);
}
