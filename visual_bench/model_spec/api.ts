// Routes: GET/POST /api/models, GET /api/models/{id}, /api/sources, /api/sources/sample.
import { call } from "../shared/http";
import type { LoadModelBody, ModelDescriptionOut, ModelSummary, SampleOut, SourcesOut } from "../generated/wire";

export const models = () => call<ModelSummary[]>("/api/models");
export const model = (id: string) => call<ModelDescriptionOut>(`/api/models/${encodeURIComponent(id)}`);
export const loadModel = (body: LoadModelBody) => call<ModelSummary>("/api/models", { method: "POST", body: JSON.stringify(body) });
export const sources = () => call<SourcesOut>("/api/sources");
export const sample = (dataset: string, index: number) =>
  call<SampleOut>(`/api/sources/sample?dataset=${encodeURIComponent(dataset)}&index=${index}`);
