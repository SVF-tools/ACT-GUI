import { QueryClient } from "@tanstack/react-query";

// Match the existing explicit refresh behavior: events and commands invalidate data.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: Infinity, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
});

const run = (id: string | null) => ["runs", "detail", id] as const;

export const keys = {
  models: () => ["models"] as const,
  model: (id: string | null) => ["models", id] as const,
  sources: () => ["sources"] as const,
  sample: (dataset: string | null, index: number) => ["sources", "sample", dataset, index] as const,
  provenance: (id: string | null) => ["models", id, "provenance"] as const,
  nearest: (id: string | null, row: number, point: string) => ["models", id, "provenance", "nearest", row, point] as const,
  runs: () => ["runs", "list"] as const,
  run,
  layers: (id: string | null) => [...run(id), "layers"] as const,
  propagation: (id: string | null) => [...run(id), "propagation"] as const,
  propagationLayer: (id: string | null, layer: number | null, scope: string, pass: string, stage: string, version: number,
    fields: string | null = null, neuron: number | null = null) =>
    [...run(id), "propagation-layer", layer, scope, pass, stage, version, fields, neuron] as const,
  coverage: (id: string | null) => [...run(id), "coverage"] as const,
  babTree: (id: string | null, root: number) => [...run(id), "bab", root] as const,
  babNode: (id: string | null, node: number | null) => [...run(id), "bab-node", node] as const,
  fuzzing: (id: string | null) => [...run(id), "fuzzing"] as const,
  fuzzDefaults: () => ["fuzz", "defaults"] as const,
  fuzzOptions: () => ["fuzz", "options"] as const,
  verificationDefaults: () => ["verification", "defaults"] as const,
  babOptions: () => ["verification", "bab-options"] as const,
  engine: () => ["engine"] as const,
  gurobi: () => ["engine", "gurobi"] as const,
  engineSources: () => ["engine", "source"] as const,
  engineBranches: (remote: string | null) => ["engine", "branches", remote] as const,
  providers: () => ["assistant", "providers"] as const,
  presence: () => ["presence"] as const,
};
