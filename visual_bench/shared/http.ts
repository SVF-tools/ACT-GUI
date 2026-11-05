import type { ErrorResponse, RunEvent } from "../generated/wire";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err = (body as ErrorResponse | null)?.error;
    throw new ApiError(res.status, err?.code ?? "http_error", err?.message ?? `HTTP ${res.status}`);
  }
  return body as T;
}

/** Follow committed events; EventSource resumes with Last-Event-ID on reconnect. */
export function followRun(runId: string, onEvent: (ev: RunEvent) => void): () => void {
  const src = new EventSource(`/api/runs/${runId}/events`);
  src.addEventListener("run", (e) => onEvent(JSON.parse((e as MessageEvent<string>).data) as RunEvent));
  src.addEventListener("end", () => src.close());
  return () => src.close();
}
