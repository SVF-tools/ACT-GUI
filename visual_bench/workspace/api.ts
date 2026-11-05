// Route: POST /api/presence (heartbeat in, online count out).
import { call } from "../shared/http";
import type { PresenceOut } from "../generated/wire";

export const heartbeat = (clientId: string) =>
  call<PresenceOut>("/api/presence", { method: "POST", body: JSON.stringify({ client_id: clientId }) });
