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
  runs: () => ["runs", "list"] as const,
  run,
  layers: (id: string | null) => [...run(id), "layers"] as const,
  coverage: (id: string | null) => [...run(id), "coverage"] as const,
  fuzzing: (id: string | null) => [...run(id), "fuzzing"] as const,
  fuzzDefaults: () => ["fuzz", "defaults"] as const,
  engine: () => ["engine"] as const,
  gurobi: () => ["engine", "gurobi"] as const,
  providers: () => ["assistant", "providers"] as const,
};
