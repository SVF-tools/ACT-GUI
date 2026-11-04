// Queries/commands for /api/fuzz/defaults and /api/runs/{id}/{fuzzing,saved-counterexamples}.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import type { FuzzSettingsValue } from "./FuzzSettings";
import * as api from "./api";

export const useFuzzDefaults = () => useQuery({ queryKey: keys.fuzzDefaults(), queryFn: api.fuzzDefaults });
export const useFuzzing = (id: string | null) =>
  useQuery({ queryKey: keys.fuzzing(id), queryFn: () => api.fuzzing(id!), enabled: id !== null });

export function useSaveCounterexample(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (index: number) => api.saveCounterexample(id, index),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.run(id) }),
  });
}

export function useFuzzConfiguration() {
  const query = useFuzzDefaults();
  const defaults = query.isSuccess ? query.data as FuzzSettingsValue : null;
  const [draft, setValue] = useState<FuzzSettingsValue | null>(null);
  return { query, defaults, value: draft ?? defaults, setValue };
}
