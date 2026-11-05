// Queries/commands for /api/engine, /api/engine/source, /api/solvers/gurobi and /api/solvers/gurobi/license.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import * as api from "./api";
import type { EngineSwitchRequest } from "../generated/wire";

export const useEngine = () => useQuery({ queryKey: keys.engine(), queryFn: api.engine });
export const useGurobi = () => useQuery({ queryKey: keys.gurobi(), queryFn: api.gurobi });

// Why the active ACT checkout cannot serve a capability (its failed API check), or null when it can.
// Unknown until the engine probe answers: callers treat that as available and the service still gates.
export function useCapabilities() {
  const engine = useEngine();
  return (name: string): string | null => {
    if (engine.status !== "success") return null;
    if (!engine.data.usable) return "ACT is unavailable";
    const cap = engine.data.capabilities.find((c) => c.name === name);
    if (!cap) return `${name} is not declared by the bridge`;
    return cap.availability === "available" ? null : `ACT lacks ${name}: ${cap.source}`;
  };
}
export const useEngineSources = () => useQuery({ queryKey: keys.engineSources(), queryFn: api.engineSources });
export const useEngineBranches = (ref: api.RepoRef | null) => useQuery({
  queryKey: keys.engineBranches(ref ? ("url" in ref ? ref.url : ref.remote) : null),
  queryFn: () => api.engineBranches(ref!), enabled: ref !== null,
});

// A checked user-entered repository that imports as ACT joins the offered list.
export function useCheckEngine() {
  const client = useQueryClient();
  return useMutation({ mutationFn: api.checkEngine, onSuccess: () => client.invalidateQueries({ queryKey: keys.engineSources() }) });
}

const RESTART_TIMEOUT_MS = 180_000;
const RESTART_POLL_MS = 1_000;

// The service restarts itself onto the new checkout after answering; wait until a new process instance
// answers, then refetch all cached server data, since every engine-derived answer may have changed.
async function switchAndAwaitRestart(req: EngineSwitchRequest) {
  const before = (await api.health()).instance;
  const out = await api.switchEngine(req);
  const deadline = Date.now() + RESTART_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, RESTART_POLL_MS));
    try {
      if ((await api.health()).instance !== before) return out;
    } catch {
      // the old process has exited and the new one is not listening yet
    }
  }
  throw new Error("The workbench did not come back after switching ACT; reload the page.");
}

export function useSwitchEngine() {
  const client = useQueryClient();
  return useMutation({ mutationFn: switchAndAwaitRestart, onSuccess: () => client.invalidateQueries() });
}

export function useUploadGurobiLicense() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.uploadGurobiLicense,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.gurobi() }),
  });
}

export function useRemoveGurobiLicense() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.removeGurobiLicense,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.gurobi() }),
  });
}
