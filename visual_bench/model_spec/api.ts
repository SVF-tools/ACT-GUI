// Routes: GET/POST /api/models, GET /api/models/{id}, POST /api/models/{id}/rebuild, /api/sources, /api/sources/sample,
// GET /api/models/{id}/provenance, POST /api/models/{id}/provenance/nearest.
import { call } from "../shared/http";
import type { LoadModelBody, ModelDescriptionOut, ModelSummary, NearestOut, NearestRequest, ProvenanceOut, SampleOut,
  SourcesOut } from "../generated/wire";

export const models = () => call<ModelSummary[]>("/api/models");
export const model = (id: string) => call<ModelDescriptionOut>(`/api/models/${encodeURIComponent(id)}`);
export const loadModel = (body: LoadModelBody) => call<ModelSummary>("/api/models", { method: "POST", body: JSON.stringify(body) });
export const rebuildModel = (id: string) =>
  call<ModelSummary>(`/api/models/${encodeURIComponent(id)}/rebuild`, { method: "POST" });
export const sources = () => call<SourcesOut>("/api/sources");
export const sample = (dataset: string, index: number) =>
  call<SampleOut>(`/api/sources/sample?dataset=${encodeURIComponent(dataset)}&index=${index}`);
export const provenance = (id: string) => call<ProvenanceOut>(`/api/models/${encodeURIComponent(id)}/provenance`);
export const nearest = (id: string, body: NearestRequest) =>
  call<NearestOut>(`/api/models/${encodeURIComponent(id)}/provenance/nearest`, { method: "POST", body: JSON.stringify(body) });
