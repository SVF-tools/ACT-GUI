// Routes: GET /api/assistant/providers, POST /api/assistant/explain.
import { call } from "../shared/http";
import type { ExplainRequest, ExplainResponse, ProviderList } from "../generated/wire";

export const providers = () => call<ProviderList>("/api/assistant/providers");
export const explain = (req: ExplainRequest) =>
  call<ExplainResponse>("/api/assistant/explain", { method: "POST", body: JSON.stringify(req) });
